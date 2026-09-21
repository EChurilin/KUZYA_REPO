import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest
from src.core.entities import ApplicationScreenshot
from src.repositories.screenshot_repo import ScreenshotRepositoryImpl


@pytest.fixture
def repo():
    mock_pool = AsyncMock()
    return ScreenshotRepositoryImpl(mock_pool)


@pytest.fixture
def sample_screenshot():
    now = datetime.now(timezone.utc)
    return ApplicationScreenshot(
        id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        application_id=None,
        client_file_id="AgACAgIAAxkDAAI",
        storage_path="storage/screenshots/abc123.jpg",
        status="pending",
        created_at=now,
    )


def _screenshot_to_dict(s: ApplicationScreenshot) -> dict:
    return {
        "id": s.id,
        "session_id": s.session_id,
        "application_id": s.application_id,
        "client_file_id": s.client_file_id,
        "storage_path": s.storage_path,
        "status": s.status,
        "created_at": s.created_at,
        "staff_message_id": s.staff_message_id,
    }


class TestScreenshotRepository:
    @pytest.mark.asyncio
    async def test_create(self, repo, sample_screenshot):
        repo.execute = AsyncMock()

        await repo.create(sample_screenshot)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_session(self, repo, sample_screenshot):
        repo.fetch = AsyncMock(return_value=[_screenshot_to_dict(sample_screenshot)])

        screenshots = await repo.get_by_session(sample_screenshot.session_id)

        assert len(screenshots) == 1
        assert screenshots[0].id == sample_screenshot.id
        assert screenshots[0].status == "pending"
        assert screenshots[0].application_id is None

    @pytest.mark.asyncio
    async def test_get_by_session_empty(self, repo):
        repo.fetch = AsyncMock(return_value=[])

        screenshots = await repo.get_by_session(uuid.uuid4())

        assert len(screenshots) == 0

    @pytest.mark.asyncio
    async def test_get_by_application(self, repo, sample_screenshot):
        app_id = uuid.uuid4()
        sample_screenshot.application_id = app_id
        repo.fetch = AsyncMock(return_value=[_screenshot_to_dict(sample_screenshot)])

        screenshots = await repo.get_by_application(app_id)

        assert len(screenshots) == 1
        assert screenshots[0].application_id == app_id

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, sample_screenshot):
        repo.fetchone = AsyncMock(return_value=_screenshot_to_dict(sample_screenshot))

        screenshot = await repo.get_by_id(sample_screenshot.id)

        assert screenshot is not None
        assert screenshot.id == sample_screenshot.id
        assert screenshot.client_file_id == "AgACAgIAAxkDAAI"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        screenshot = await repo.get_by_id(uuid.uuid4())

        assert screenshot is None

    @pytest.mark.asyncio
    async def test_update_status(self, repo, sample_screenshot):
        repo.execute = AsyncMock()

        await repo.update_status(sample_screenshot.id, "approved")

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_link_to_application(self, repo, sample_screenshot):
        repo.execute = AsyncMock()
        app_id = uuid.uuid4()

        await repo.link_to_application(sample_screenshot.session_id, app_id)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_old_screenshots_for_cleanup(self, repo, sample_screenshot):
        repo.fetch = AsyncMock(return_value=[_screenshot_to_dict(sample_screenshot)])

        screenshots = await repo.get_old_screenshots_for_cleanup(30)

        assert len(screenshots) == 1
        assert screenshots[0].id == sample_screenshot.id

    @pytest.mark.asyncio
    async def test_get_old_screenshots_for_cleanup_empty(self, repo):
        repo.fetch = AsyncMock(return_value=[])

        screenshots = await repo.get_old_screenshots_for_cleanup(30)

        assert len(screenshots) == 0

    @pytest.mark.asyncio
    async def test_delete(self, repo, sample_screenshot):
        repo.execute = AsyncMock()

        await repo.delete(sample_screenshot.id)

        repo.execute.assert_called_once()
