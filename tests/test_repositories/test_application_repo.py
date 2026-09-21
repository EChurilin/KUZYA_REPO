import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest
from src.core.entities import Application
from src.repositories.application_repo import ApplicationRepositoryImpl


@pytest.fixture
def repo():
    mock_pool = AsyncMock()
    return ApplicationRepositoryImpl(mock_pool)


@pytest.fixture
def sample_application():
    now = datetime.now(timezone.utc)
    return Application(
        id=uuid.uuid4(),
        user_id=12345,
        session_id=uuid.uuid4(),
        campaign_id=None,
        status="pending_review",
        actual_screenshot_count=5,
        approved_screenshot_count=0,
        moderator_comment=None,
        submitted_at=now,
        reviewed_at=None,
        rewarded_at=None,
        reviewed_by=None,
        auto_closed=False,
    )


def _app_to_dict(a: Application) -> dict:
    return {
        "id": a.id,
        "user_id": a.user_id,
        "session_id": a.session_id,
        "campaign_id": a.campaign_id,
        "status": a.status,
        "actual_screenshot_count": a.actual_screenshot_count,
        "approved_screenshot_count": a.approved_screenshot_count,
        "moderator_comment": a.moderator_comment,
        "submitted_at": a.submitted_at,
        "reviewed_at": a.reviewed_at,
        "rewarded_at": a.rewarded_at,
        "reviewed_by": a.reviewed_by,
        "auto_closed": a.auto_closed,
        "summary_message_id": a.summary_message_id,
    }


class TestApplicationRepository:
    @pytest.mark.asyncio
    async def test_create(self, repo, sample_application):
        repo.execute = AsyncMock()

        await repo.create(sample_application)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, sample_application):
        repo.fetchone = AsyncMock(return_value=_app_to_dict(sample_application))

        app = await repo.get_by_id(sample_application.id)

        assert app is not None
        assert app.id == sample_application.id
        assert app.user_id == 12345
        assert app.status == "pending_review"
        assert app.actual_screenshot_count == 5
        assert app.campaign_id is None

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        app = await repo.get_by_id(uuid.uuid4())

        assert app is None

    @pytest.mark.asyncio
    async def test_get_pending_review(self, repo, sample_application):
        repo.fetch = AsyncMock(return_value=[_app_to_dict(sample_application)])

        apps = await repo.get_pending_review(limit=10)

        assert len(apps) == 1
        assert apps[0].status == "pending_review"

    @pytest.mark.asyncio
    async def test_get_pending_review_empty(self, repo):
        repo.fetch = AsyncMock(return_value=[])

        apps = await repo.get_pending_review()

        assert len(apps) == 0

    @pytest.mark.asyncio
    async def test_update_status(self, repo, sample_application):
        repo.execute = AsyncMock()

        await repo.update_status(
            application_id=sample_application.id,
            status="approved",
            reviewed_by=999,
            moderator_comment="All good",
            approved_count=5,
        )

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_rewarded(self, repo, sample_application):
        repo.execute = AsyncMock()

        await repo.mark_rewarded(sample_application.id)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_user(self, repo, sample_application):
        repo.fetch = AsyncMock(return_value=[_app_to_dict(sample_application)])

        apps = await repo.get_by_user(12345, limit=10)

        assert len(apps) == 1
        assert apps[0].user_id == 12345

    @pytest.mark.asyncio
    async def test_get_by_user_empty(self, repo):
        repo.fetch = AsyncMock(return_value=[])

        apps = await repo.get_by_user(99999)

        assert len(apps) == 0

    @pytest.mark.asyncio
    async def test_count_today_by_user(self, repo):
        repo.fetchval = AsyncMock(return_value=7)

        count = await repo.count_today_by_user(12345)

        assert count == 7

    @pytest.mark.asyncio
    async def test_count_today_by_user_zero(self, repo):
        repo.fetchval = AsyncMock(return_value=0)

        count = await repo.count_today_by_user(12345)

        assert count == 0
