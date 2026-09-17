import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
import pytest
from src.core.entities import Session
from src.repositories.session_repo import SessionRepositoryImpl


@pytest.fixture
def repo():
    mock_pool = AsyncMock()
    return SessionRepositoryImpl(mock_pool)


@pytest.fixture
def sample_session():
    now = datetime.now(timezone.utc)
    return Session(
        id=uuid.uuid4(),
        user_id=12345,
        game_id=uuid.uuid4(),
        status="active",
        started_at=now,
        last_screenshot_at=None,
        screenshot_count=0,
        created_at=now,
    )


def _session_to_dict(session: Session) -> dict:
    return {
        "id": session.id,
        "user_id": session.user_id,
        "game_id": session.game_id,
        "status": session.status,
        "started_at": session.started_at,
        "last_screenshot_at": session.last_screenshot_at,
        "screenshot_count": session.screenshot_count,
        "created_at": session.created_at,
    }


class TestSessionRepository:
    @pytest.mark.asyncio
    async def test_create(self, repo, sample_session):
        repo.execute = AsyncMock()

        await repo.create(sample_session)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, sample_session):
        repo.fetchone = AsyncMock(return_value=_session_to_dict(sample_session))

        session = await repo.get_by_id(sample_session.id)

        assert session is not None
        assert session.id == sample_session.id
        assert session.user_id == 12345
        assert session.status == "active"
        assert session.screenshot_count == 0

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        session = await repo.get_by_id(uuid.uuid4())

        assert session is None

    @pytest.mark.asyncio
    async def test_get_active_by_user_found(self, repo, sample_session):
        repo.fetchone = AsyncMock(return_value=_session_to_dict(sample_session))

        session = await repo.get_active_by_user(12345)

        assert session is not None
        assert session.user_id == 12345
        assert session.status == "active"

    @pytest.mark.asyncio
    async def test_get_active_by_user_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        session = await repo.get_active_by_user(99999)

        assert session is None

    @pytest.mark.asyncio
    async def test_update_last_screenshot(self, repo, sample_session):
        repo.execute = AsyncMock()
        now = datetime.now(timezone.utc)

        await repo.update_last_screenshot(sample_session.id, now)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_session_completed(self, repo, sample_session):
        repo.execute = AsyncMock()

        await repo.close_session(sample_session.id, "completed")

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_session_expired(self, repo, sample_session):
        repo.execute = AsyncMock()

        await repo.close_session(sample_session.id, "expired")

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_expired_active_sessions(self, repo):
        now = datetime.now(timezone.utc)
        old_session = Session(
            id=uuid.uuid4(),
            user_id=111,
            game_id=uuid.uuid4(),
            status="active",
            started_at=now - timedelta(hours=25),
            last_screenshot_at=now - timedelta(hours=25),
            screenshot_count=3,
            created_at=now - timedelta(hours=25),
        )
        repo.fetch = AsyncMock(return_value=[_session_to_dict(old_session)])

        sessions = await repo.get_expired_active_sessions(24)

        assert len(sessions) == 1
        assert sessions[0].user_id == 111
        assert sessions[0].screenshot_count == 3

    @pytest.mark.asyncio
    async def test_get_expired_active_sessions_empty(self, repo):
        repo.fetch = AsyncMock(return_value=[])

        sessions = await repo.get_expired_active_sessions(24)

        assert len(sessions) == 0