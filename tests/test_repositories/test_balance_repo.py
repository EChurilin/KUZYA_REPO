import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest
from src.core.entities import BalanceSnapshot
from src.repositories.balance_repo import BalanceRepositoryImpl


@pytest.fixture
def repo():
    mock_pool = AsyncMock()
    return BalanceRepositoryImpl(mock_pool)


@pytest.fixture
def sample_snapshot():
    return BalanceSnapshot(
        id=uuid.uuid4(),
        reward_type="stars",
        balance=1500,
        fetched_at=datetime.now(timezone.utc),
    )


def _snapshot_to_dict(s: BalanceSnapshot) -> dict:
    return {
        "id": s.id,
        "reward_type": s.reward_type,
        "balance": s.balance,
        "fetched_at": s.fetched_at,
    }


class TestBalanceRepository:
    @pytest.mark.asyncio
    async def test_save_snapshot(self, repo, sample_snapshot):
        repo.execute = AsyncMock()

        await repo.save_snapshot(sample_snapshot)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_found(self, repo, sample_snapshot):
        repo.fetchone = AsyncMock(return_value=_snapshot_to_dict(sample_snapshot))

        snapshot = await repo.get_latest("stars")

        assert snapshot is not None
        assert snapshot.reward_type == "stars"
        assert snapshot.balance == 1500

    @pytest.mark.asyncio
    async def test_get_latest_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        snapshot = await repo.get_latest("gift")

        assert snapshot is None