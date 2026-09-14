import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.core.entities import Session, ApplicationScreenshot
from src.services.cleanup_service import CleanupService


@pytest.fixture
def session_repo_mock():
    return AsyncMock()

@pytest.fixture
def screenshot_repo_mock():
    return AsyncMock()

@pytest.fixture
def app_repo_mock():
    return AsyncMock()

@pytest.fixture
def storage_mock():
    mock = MagicMock()
    mock.delete_file.return_value = True
    return mock


@pytest.fixture
def sample_expired_session():
    now = datetime.now(timezone.utc)
    return Session(
        id=uuid.uuid4(),
        user_id=12345,
        game_id=uuid.uuid4(),
        status="active",
        started_at=now - timedelta(hours=25),
        last_screenshot_at=now - timedelta(hours=25),
        screenshot_count=2,
        created_at=now - timedelta(hours=25),
    )


class TestCleanupService:
    @pytest.mark.asyncio
    async def test_process_expired_sessions_success(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, sample_expired_session):
        session_repo_mock.get_expired_active_sessions.return_value = [sample_expired_session]
        session_repo_mock.close_session.return_value = None
        
        screenshots = [
            ApplicationScreenshot(id=uuid.uuid4(), session_id=sample_expired_session.id, application_id=None, client_file_id="1", storage_path="p1", status="pending", created_at=datetime.now(timezone.utc)),
            ApplicationScreenshot(id=uuid.uuid4(), session_id=sample_expired_session.id, application_id=None, client_file_id="2", storage_path="p2", status="pending", created_at=datetime.now(timezone.utc)),
        ]
        screenshot_repo_mock.get_by_session.return_value = screenshots
        screenshot_repo_mock.link_to_application.return_value = None
        app_repo_mock.create.return_value = None

        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock)
        
        count = await service.process_expired_sessions()
        
        assert count == 1
        session_repo_mock.close_session.assert_awaited_once_with(sample_expired_session.id, "expired")
        app_repo_mock.create.assert_awaited_once()
        
        # Проверяем, что заявка создана с auto_closed=True
        created_app = app_repo_mock.create.call_args[0][0]
        assert created_app.auto_closed is True
        assert "автоматически" in created_app.moderator_comment.lower()
        screenshot_repo_mock.link_to_application.assert_awaited_once_with(sample_expired_session.id, created_app.id)

    @pytest.mark.asyncio
    async def test_process_expired_sessions_empty(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock):
        session_repo_mock.get_expired_active_sessions.return_value = []
        
        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock)
        count = await service.process_expired_sessions()
        
        assert count == 0
        app_repo_mock.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cleanup_old_screenshots_success(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock):
        old_screenshot = ApplicationScreenshot(
            id=uuid.uuid4(), session_id=uuid.uuid4(), application_id=uuid.uuid4(),
            client_file_id="1", storage_path="storage/screenshots/old.jpg", status="pending", created_at=datetime.now(timezone.utc) - timedelta(days=35)
        )
        screenshot_repo_mock.get_old_screenshots_for_cleanup.return_value = [old_screenshot]
        screenshot_repo_mock.delete.return_value = None

        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock)
        deleted, errors = await service.cleanup_old_screenshots()
        
        assert deleted == 1
        assert errors == 0
        storage_mock.delete_file.assert_called_once_with("storage/screenshots/old.jpg")
        screenshot_repo_mock.delete.assert_awaited_once_with(old_screenshot.id)

    @pytest.mark.asyncio
    async def test_cleanup_old_screenshots_empty(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock):
        screenshot_repo_mock.get_old_screenshots_for_cleanup.return_value = []
        
        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock)
        deleted, errors = await service.cleanup_old_screenshots()
        
        assert deleted == 0
        assert errors == 0