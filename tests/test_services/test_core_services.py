import uuid
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.config.constants import MIN_SCREENSHOT_INTERVAL_SECONDS, MAX_SCREENSHOTS_PER_SESSION
from src.core.entities import Session, ApplicationScreenshot, BalanceSnapshot
from src.core.exceptions import (
    SessionAlreadyActiveError,
    SessionNotFoundError,
    ScreenshotIntervalTooShortError,
    ScreenshotLimitReachedError,
)
from src.services.balance_service import BalanceService
from src.services.session_service import SessionService


# --- Fixtures ---

@pytest.fixture
def balance_repo_mock():
    return AsyncMock()

@pytest.fixture
def gift_issuer_mock():
    return AsyncMock()

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


# --- Tests for BalanceService ---

class TestBalanceService:
    @pytest.mark.asyncio
    async def test_get_current_balance_from_cache(self, balance_repo_mock, gift_issuer_mock):
        # Снапшот создан только что (не устарел)
        fresh_snapshot = BalanceSnapshot(
            id=uuid.uuid4(), reward_type="stars", balance=500, fetched_at=datetime.now(timezone.utc)
        )
        balance_repo_mock.get_latest.return_value = fresh_snapshot

        service = BalanceService(balance_repo_mock, gift_issuer_mock)
        balance = await service.get_current_balance()

        assert balance == 500
        gift_issuer_mock.get_bot_balance.assert_not_awaited()
        balance_repo_mock.save_snapshot.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_current_balance_expired_cache(self, balance_repo_mock, gift_issuer_mock):
        # Снапшот устарел (создан 1 час назад)
        old_snapshot = BalanceSnapshot(
            id=uuid.uuid4(), reward_type="stars", balance=100,
            fetched_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        balance_repo_mock.get_latest.return_value = old_snapshot
        gift_issuer_mock.get_bot_balance.return_value = 999

        service = BalanceService(balance_repo_mock, gift_issuer_mock)
        balance = await service.get_current_balance()

        assert balance == 999
        gift_issuer_mock.get_bot_balance.assert_awaited_once()
        balance_repo_mock.save_snapshot.assert_awaited_once()


# --- Tests for SessionService ---

class TestSessionService:
    @pytest.mark.asyncio
    async def test_start_session_success(self, session_repo_mock, screenshot_repo_mock, storage_mock):
        session_repo_mock.get_active_by_user.return_value = None
        session_repo_mock.create.return_value = None

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)
        game_id = uuid.uuid4()
        session = await service.start_session(user_id=123, game_id=game_id)

        assert session.user_id == 123
        assert session.game_id == game_id
        assert session.status == "active"
        assert session.screenshot_count == 0
        session_repo_mock.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_session_already_active(self, session_repo_mock, screenshot_repo_mock, storage_mock):
        session_repo_mock.get_active_by_user.return_value = MagicMock() # Есть активная сессия

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)

        with pytest.raises(SessionAlreadyActiveError):
            await service.start_session(user_id=123, game_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_add_screenshot_success(self, session_repo_mock, screenshot_repo_mock, storage_mock):
        # Активная сессия без предыдущих скриншотов
        active_session = Session(
            id=uuid.uuid4(), user_id=123, game_id=uuid.uuid4(), status="active",
            started_at=datetime.now(timezone.utc), last_screenshot_at=None, screenshot_count=0, created_at=datetime.now(timezone.utc)
        )
        session_repo_mock.get_by_id.return_value = active_session

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)
        screenshot, count = await service.add_screenshot(
            session_id=active_session.id, file_bytes=b"data", extension="jpg", client_file_id="tg_123"
        )

        assert count == 1
        assert screenshot.client_file_id == "tg_123"
        storage_mock.save_file.assert_called_once_with(b"data", "jpg")
        session_repo_mock.update_last_screenshot.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_screenshot_interval_too_short(self, session_repo_mock, screenshot_repo_mock, storage_mock):
        # Последний скриншот был 5 минут назад
        active_session = Session(
            id=uuid.uuid4(), user_id=123, game_id=uuid.uuid4(), status="active",
            started_at=datetime.now(timezone.utc),
            last_screenshot_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            screenshot_count=1, created_at=datetime.now(timezone.utc)
        )
        session_repo_mock.get_by_id.return_value = active_session

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)

        with pytest.raises(ScreenshotIntervalTooShortError):
            await service.add_screenshot(active_session.id, b"data", "jpg", "tg_123")

        storage_mock.save_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_screenshot_limit_reached(self, session_repo_mock, screenshot_repo_mock, storage_mock):
        # Сессия с 150 скриншотами (лимит)
        active_session = Session(
            id=uuid.uuid4(), user_id=123, game_id=uuid.uuid4(), status="active",
            started_at=datetime.now(timezone.utc),
            last_screenshot_at=datetime.now(timezone.utc) - timedelta(hours=1),
            screenshot_count=MAX_SCREENSHOTS_PER_SESSION, created_at=datetime.now(timezone.utc)
        )
        session_repo_mock.get_by_id.return_value = active_session

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)

        with pytest.raises(ScreenshotLimitReachedError):
            await service.add_screenshot(active_session.id, b"data", "jpg", "tg_123")

    @pytest.mark.asyncio
    async def test_close_session_success(self, session_repo_mock, screenshot_repo_mock, storage_mock):
        active_session = Session(
            id=uuid.uuid4(), user_id=123, game_id=uuid.uuid4(), status="active",
            started_at=datetime.now(timezone.utc), last_screenshot_at=None, screenshot_count=0, created_at=datetime.now(timezone.utc)
        )
        session_repo_mock.get_by_id.return_value = active_session

        service = SessionService(session_repo_mock, screenshot_repo_mock, storage_mock)
        await service.close_session(active_session.id)

        session_repo_mock.close_session.assert_awaited_once_with(active_session.id, "completed")