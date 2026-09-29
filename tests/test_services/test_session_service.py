import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.config.constants import SESSION_RESTART_COOLDOWN_SECONDS
from src.core.entities import Session
from src.core.exceptions import (
    SessionAlreadyActiveError,
    SessionCooldownError,
    SessionNotFoundError,
    ScreenshotIntervalTooShortError,
    ScreenshotLimitReachedError,
)
from src.services.session_service import SessionService


@pytest.fixture
def session_repo_mock():
    return AsyncMock()


@pytest.fixture
def screenshot_repo_mock():
    return AsyncMock()


@pytest.fixture
def storage_mock():
    mock = MagicMock()
    mock.save_file.return_value = "storage/screenshots/test.jpg"
    return mock


@pytest.fixture
def game_id():
    return uuid.uuid4()


class TestSessionService:
    @pytest.mark.asyncio
    async def test_start_session_success_no_cooldown(self, session_repo_mock, screenshot_repo_mock, storage_mock, game_id):
        """Успешный старт сессии: нет активной, нет последней completed в пределах кулдауна."""
        session_repo_mock.get_active_by_user.return_value = None
        session_repo_mock.get_last_completed_session.return_value = None
        session_repo_mock.create.return_value = None

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)
        session = await service.start_session(user_id=12345, game_id=game_id)

        assert session.user_id == 12345
        assert session.game_id == game_id
        assert session.status == "active"
        assert session.screenshot_count == 0
        session_repo_mock.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_session_already_active(self, session_repo_mock, screenshot_repo_mock, storage_mock, game_id):
        """Ошибка: у пользователя уже есть активная сессия."""
        active_session = Session(
            id=uuid.uuid4(), user_id=12345, game_id=game_id, status="active",
            started_at=datetime.now(timezone.utc), last_screenshot_at=None,
            screenshot_count=1, created_at=datetime.now(timezone.utc), closed_at=None,
        )
        session_repo_mock.get_active_by_user.return_value = active_session

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)

        with pytest.raises(SessionAlreadyActiveError):
            await service.start_session(user_id=12345, game_id=game_id)

        session_repo_mock.get_last_completed_session.assert_not_awaited()
        session_repo_mock.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_start_session_cooldown_blocks(self, session_repo_mock, screenshot_repo_mock, storage_mock, game_id):
        """Кулдаун: последняя completed сессия закрыта 5 минут назад (< 10 минут)."""
        now = datetime.now(timezone.utc)
        session_repo_mock.get_active_by_user.return_value = None

        last_completed = Session(
            id=uuid.uuid4(), user_id=12345, game_id=game_id, status="completed",
            started_at=now - timedelta(hours=1), last_screenshot_at=now - timedelta(minutes=30),
            screenshot_count=3, created_at=now - timedelta(hours=1),
            closed_at=now - timedelta(minutes=5),
        )
        session_repo_mock.get_last_completed_session.return_value = last_completed

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)

        with pytest.raises(SessionCooldownError) as exc_info:
            await service.start_session(user_id=12345, game_id=game_id)

        assert "мин" in str(exc_info.value).lower()
        session_repo_mock.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_start_session_cooldown_expired_allows(self, session_repo_mock, screenshot_repo_mock, storage_mock, game_id):
        """Кулдаун истёк: последняя completed сессия закрыта 15 минут назад (>= 10 минут)."""
        now = datetime.now(timezone.utc)
        session_repo_mock.get_active_by_user.return_value = None
        session_repo_mock.create.return_value = None

        last_completed = Session(
            id=uuid.uuid4(), user_id=12345, game_id=game_id, status="completed",
            started_at=now - timedelta(hours=1), last_screenshot_at=now - timedelta(minutes=45),
            screenshot_count=3, created_at=now - timedelta(hours=1),
            closed_at=now - timedelta(minutes=15),
        )
        session_repo_mock.get_last_completed_session.return_value = last_completed

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)
        session = await service.start_session(user_id=12345, game_id=game_id)

        assert session.status == "active"
        session_repo_mock.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_session_cooldown_not_applied_to_cancelled(self, session_repo_mock, screenshot_repo_mock, storage_mock, game_id):
        """Кулдаун не применяется к cancelled (пустым) сессиям."""
        session_repo_mock.get_active_by_user.return_value = None
        session_repo_mock.get_last_completed_session.return_value = None
        session_repo_mock.create.return_value = None

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)
        session = await service.start_session(user_id=12345, game_id=game_id)

        assert session.status == "active"
        session_repo_mock.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_session_cooldown_not_applied_to_expired(self, session_repo_mock, screenshot_repo_mock, storage_mock, game_id):
        """Кулдаун не применяется к expired сессиям."""
        session_repo_mock.get_active_by_user.return_value = None
        session_repo_mock.get_last_completed_session.return_value = None
        session_repo_mock.create.return_value = None

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)
        session = await service.start_session(user_id=12345, game_id=game_id)

        assert session.status == "active"
        session_repo_mock.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_screenshot_success(self, session_repo_mock, screenshot_repo_mock, storage_mock):
        """Успешное добавление скриншота."""
        session_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        session = Session(
            id=session_id, user_id=12345, game_id=uuid.uuid4(), status="active",
            started_at=now - timedelta(hours=1), last_screenshot_at=now - timedelta(minutes=15),
            screenshot_count=2, created_at=now - timedelta(hours=1), closed_at=None,
        )
        session_repo_mock.get_by_id.return_value = session
        screenshot_repo_mock.create.return_value = None
        session_repo_mock.update_last_screenshot.return_value = None

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)
        screenshot, count = await service.add_screenshot(
            session_id=session_id, file_bytes=b"fake", extension="jpg", client_file_id="file_123"
        )

        assert count == 3
        assert screenshot.session_id == session_id
        storage_mock.save_file.assert_called_once_with(b"fake", "jpg")
        screenshot_repo_mock.create.assert_awaited_once()
        session_repo_mock.update_last_screenshot.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_screenshot_interval_too_short(self, session_repo_mock, screenshot_repo_mock, storage_mock):
        """Ошибка: интервал между скриншотами < 10 минут."""
        session_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        session = Session(
            id=session_id, user_id=12345, game_id=uuid.uuid4(), status="active",
            started_at=now - timedelta(hours=1), last_screenshot_at=now - timedelta(minutes=5),
            screenshot_count=2, created_at=now - timedelta(hours=1), closed_at=None,
        )
        session_repo_mock.get_by_id.return_value = session

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)

        with pytest.raises(ScreenshotIntervalTooShortError):
            await service.add_screenshot(
                session_id=session_id, file_bytes=b"fake", extension="jpg", client_file_id="file_123"
            )

        screenshot_repo_mock.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_add_screenshot_limit_reached(self, session_repo_mock, screenshot_repo_mock, storage_mock):
        """Ошибка: достигнут лимит 100 скриншотов."""
        session_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        session = Session(
            id=session_id, user_id=12345, game_id=uuid.uuid4(), status="active",
            started_at=now - timedelta(hours=5), last_screenshot_at=now - timedelta(minutes=15),
            screenshot_count=100, created_at=now - timedelta(hours=5), closed_at=None,
        )
        session_repo_mock.get_by_id.return_value = session

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)

        with pytest.raises(ScreenshotLimitReachedError):
            await service.add_screenshot(
                session_id=session_id, file_bytes=b"fake", extension="jpg", client_file_id="file_123"
            )

        screenshot_repo_mock.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_add_screenshot_session_not_found(self, session_repo_mock, screenshot_repo_mock, storage_mock):
        """Ошибка: сессия не найдена."""
        session_repo_mock.get_by_id.return_value = None

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)

        with pytest.raises(SessionNotFoundError):
            await service.add_screenshot(
                session_id=uuid.uuid4(), file_bytes=b"fake", extension="jpg", client_file_id="file_123"
            )