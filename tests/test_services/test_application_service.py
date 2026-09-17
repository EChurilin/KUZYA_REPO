import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest

from src.config.constants import MAX_APPLICATIONS_PER_DAY
from src.core.entities import Session, Application, ApplicationScreenshot
from src.core.exceptions import ApplicationLimitReachedError, SessionNotFoundError
from src.services.application_service import ApplicationService


@pytest.fixture
def app_repo_mock():
    return AsyncMock()

@pytest.fixture
def session_repo_mock():
    return AsyncMock()

@pytest.fixture
def screenshot_repo_mock():
    return AsyncMock()


@pytest.fixture
def sample_session():
    return Session(
        id=uuid.uuid4(),
        user_id=12345,
        game_id=uuid.uuid4(),
        status="active",
        started_at=datetime.now(timezone.utc),
        last_screenshot_at=None,
        screenshot_count=3,
        created_at=datetime.now(timezone.utc),
    )


class TestApplicationService:
    @pytest.mark.asyncio
    async def test_create_from_session_success(self, app_repo_mock, session_repo_mock, screenshot_repo_mock, sample_session):
        app_repo_mock.count_today_by_user.return_value = 10  # Лимит не превышен
        session_repo_mock.get_by_id.return_value = sample_session
        session_repo_mock.close_session.return_value = None
        
        screenshot = ApplicationScreenshot(
            id=uuid.uuid4(), session_id=sample_session.id, application_id=None,
            client_file_id="file1", storage_path="path1", status="pending", created_at=datetime.now(timezone.utc)
        )
        screenshot_repo_mock.get_by_session.return_value = [screenshot]
        screenshot_repo_mock.link_to_application.return_value = None
        app_repo_mock.create.return_value = None

        service = ApplicationService(app_repo_mock, session_repo_mock, screenshot_repo_mock)
        
        app = await service.create_from_session(session_id=sample_session.id, user_id=12345)
        
        assert app.user_id == 12345
        assert app.status == "pending_review"
        assert app.actual_screenshot_count == 1
        assert len(app.screenshots) == 1
        
        session_repo_mock.close_session.assert_awaited_once_with(sample_session.id, "completed")
        screenshot_repo_mock.link_to_application.assert_awaited_once_with(sample_session.id, app.id)
        app_repo_mock.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_from_session_limit_reached(self, app_repo_mock, session_repo_mock, screenshot_repo_mock):
        app_repo_mock.count_today_by_user.return_value = MAX_APPLICATIONS_PER_DAY
        
        service = ApplicationService(app_repo_mock, session_repo_mock, screenshot_repo_mock)
        
        with pytest.raises(ApplicationLimitReachedError):
            await service.create_from_session(session_id=uuid.uuid4(), user_id=12345)
            
        session_repo_mock.get_by_id.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_from_session_not_found(self, app_repo_mock, session_repo_mock, screenshot_repo_mock):
        app_repo_mock.count_today_by_user.return_value = 5
        session_repo_mock.get_by_id.return_value = None  # Сессия не найдена
        
        service = ApplicationService(app_repo_mock, session_repo_mock, screenshot_repo_mock)
        
        with pytest.raises(SessionNotFoundError):
            await service.create_from_session(session_id=uuid.uuid4(), user_id=12345)

    @pytest.mark.asyncio
    async def test_create_from_session_wrong_user(self, app_repo_mock, session_repo_mock, screenshot_repo_mock, sample_session):
        app_repo_mock.count_today_by_user.return_value = 5
        # Сессия принадлежит другому пользователю
        session_repo_mock.get_by_id.return_value = Session(**{**vars(sample_session), "user_id": 99999})
        
        service = ApplicationService(app_repo_mock, session_repo_mock, screenshot_repo_mock)
        
        with pytest.raises(SessionNotFoundError):
            await service.create_from_session(session_id=sample_session.id, user_id=12345)