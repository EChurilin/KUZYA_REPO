import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.core.entities import Session, ApplicationScreenshot, Game, InstructionBlock
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
def game_repo_mock():
    return AsyncMock()

@pytest.fixture
def instruction_repo_mock():
    return AsyncMock()


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
    async def test_process_expired_sessions_success(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock, sample_expired_session):
        session_repo_mock.get_expired_active_sessions.return_value = [sample_expired_session]
        session_repo_mock.close_session.return_value = None

        screenshots = [
            ApplicationScreenshot(id=uuid.uuid4(), session_id=sample_expired_session.id, application_id=None, client_file_id="1", storage_path="p1", status="pending", created_at=datetime.now(timezone.utc)),
            ApplicationScreenshot(id=uuid.uuid4(), session_id=sample_expired_session.id, application_id=None, client_file_id="2", storage_path="p2", status="pending", created_at=datetime.now(timezone.utc)),
        ]
        screenshot_repo_mock.get_by_session.return_value = screenshots
        screenshot_repo_mock.link_to_application.return_value = None
        app_repo_mock.create.return_value = None

        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock)

        count = await service.process_expired_sessions()

        assert count == 1
        session_repo_mock.close_session.assert_awaited_once_with(sample_expired_session.id, "expired")
        app_repo_mock.create.assert_awaited_once()

        created_app = app_repo_mock.create.call_args[0][0]
        assert created_app.auto_closed is True
        assert "автоматически" in created_app.moderator_comment.lower()
        screenshot_repo_mock.link_to_application.assert_awaited_once_with(sample_expired_session.id, created_app.id)

    @pytest.mark.asyncio
    async def test_process_expired_sessions_empty(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock):
        session_repo_mock.get_expired_active_sessions.return_value = []

        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock)
        count = await service.process_expired_sessions()

        assert count == 0
        app_repo_mock.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cleanup_old_screenshots_success(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock):
        old_screenshot = ApplicationScreenshot(
            id=uuid.uuid4(), session_id=uuid.uuid4(), application_id=uuid.uuid4(),
            client_file_id="1", storage_path="storage/screenshots/old.jpg", status="pending", created_at=datetime.now(timezone.utc) - timedelta(days=35)
        )
        screenshot_repo_mock.get_old_screenshots_for_cleanup.return_value = [old_screenshot]
        screenshot_repo_mock.delete.return_value = None

        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock)
        deleted, errors = await service.cleanup_old_screenshots()

        assert deleted == 1
        assert errors == 0
        storage_mock.delete_file.assert_called_once_with("storage/screenshots/old.jpg")
        screenshot_repo_mock.delete.assert_awaited_once_with(old_screenshot.id)

    @pytest.mark.asyncio
    async def test_cleanup_old_screenshots_empty(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock):
        screenshot_repo_mock.get_old_screenshots_for_cleanup.return_value = []

        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock)
        deleted, errors = await service.cleanup_old_screenshots()

        assert deleted == 0
        assert errors == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_games_success(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock, tmp_path):
        temp_file = tmp_path / "old_game_photo.jpg"
        temp_file.write_text("fake image data")

        old_game = Game(
            id=uuid.uuid4(),
            name="Old Game",
            is_active=False,
            created_at=datetime.now() - timedelta(hours=40),
            updated_at=datetime.now() - timedelta(hours=40),
            link=None,
            photo_path=str(temp_file),
            deactivated_at=datetime.now() - timedelta(hours=40),
        )
        game_repo_mock.get_old_deactivated_games.return_value = [old_game]
        game_repo_mock.delete.return_value = None

        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock)
        deleted, errors = await service.cleanup_old_games(hours=36)

        assert deleted == 1
        assert errors == 0
        assert not Path(str(temp_file)).exists()
        game_repo_mock.delete.assert_awaited_once_with(old_game.id)

    @pytest.mark.asyncio
    async def test_cleanup_old_games_empty(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock):
        game_repo_mock.get_old_deactivated_games.return_value = []

        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock)
        deleted, errors = await service.cleanup_old_games(hours=36)

        assert deleted == 0
        assert errors == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_instruction_versions_success(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock, tmp_path):
        temp_file = tmp_path / "old_instruction_media.jpg"
        temp_file.write_text("fake media data")

        old_block = InstructionBlock(
            id=uuid.uuid4(),
            order=1,
            text="Old block",
            media_type="photo",
            media_path=str(temp_file),
            is_active=True,
            created_at=datetime.now() - timedelta(hours=30),
            updated_at=datetime.now() - timedelta(hours=30),
            version=1,
            is_published=True,
        )
        instruction_repo_mock.get_old_published_blocks.return_value = [old_block]
        instruction_repo_mock.delete.return_value = None

        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock)
        deleted, errors = await service.cleanup_old_instruction_versions(hours=24)

        assert deleted == 1
        assert errors == 0
        assert not Path(str(temp_file)).exists()
        instruction_repo_mock.delete.assert_awaited_once_with(old_block.id)

    @pytest.mark.asyncio
    async def test_cleanup_old_instruction_versions_empty(self, session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock):
        instruction_repo_mock.get_old_published_blocks.return_value = []

        service = CleanupService(session_repo_mock, screenshot_repo_mock, app_repo_mock, storage_mock, game_repo_mock, instruction_repo_mock)
        deleted, errors = await service.cleanup_old_instruction_versions(hours=24)

        assert deleted == 0
        assert errors == 0