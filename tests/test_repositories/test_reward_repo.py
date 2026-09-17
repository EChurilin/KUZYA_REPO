import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest
from src.core.entities import Reward
from src.repositories.reward_repo import RewardRepositoryImpl


@pytest.fixture
def repo():
    mock_pool = AsyncMock()
    return RewardRepositoryImpl(mock_pool)


@pytest.fixture
def sample_reward():
    now = datetime.now(timezone.utc)
    return Reward(
        id=uuid.uuid4(),
        user_id=12345,
        application_id=uuid.uuid4(),
        reward_type="stars",
        amount=50,
        transaction_id=None,
        status="pending",
        issued_at=None,
        delivered_at=None,
    )


def _reward_to_dict(r: Reward) -> dict:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "application_id": r.application_id,
        "reward_type": r.reward_type,
        "amount": r.amount,
        "transaction_id": r.transaction_id,
        "status": r.status,
        "issued_at": r.issued_at,
        "delivered_at": r.delivered_at,
    }


class TestRewardRepository:
    @pytest.mark.asyncio
    async def test_create(self, repo, sample_reward):
        repo.execute = AsyncMock()

        await repo.create(sample_reward)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, sample_reward):
        repo.fetchone = AsyncMock(return_value=_reward_to_dict(sample_reward))

        reward = await repo.get_by_id(sample_reward.id)

        assert reward is not None
        assert reward.id == sample_reward.id
        assert reward.amount == 50
        assert reward.status == "pending"
        assert reward.reward_type == "stars"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        reward = await repo.get_by_id(uuid.uuid4())

        assert reward is None

    @pytest.mark.asyncio
    async def test_get_by_application_found(self, repo, sample_reward):
        repo.fetchone = AsyncMock(return_value=_reward_to_dict(sample_reward))

        reward = await repo.get_by_application(sample_reward.application_id)

        assert reward is not None
        assert reward.application_id == sample_reward.application_id

    @pytest.mark.asyncio
    async def test_get_by_application_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        reward = await repo.get_by_application(uuid.uuid4())

        assert reward is None

    @pytest.mark.asyncio
    async def test_update_status_issued(self, repo, sample_reward):
        repo.execute = AsyncMock()

        await repo.update_status(
            reward_id=sample_reward.id,
            status="issued",
            transaction_id="tx_123",
        )

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_failed(self, repo, sample_reward):
        repo.execute = AsyncMock()

        await repo.update_status(
            reward_id=sample_reward.id,
            status="failed",
            transaction_id="error_reason",
        )

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_pending(self, repo, sample_reward):
        repo.execute = AsyncMock()

        await repo.update_status(
            reward_id=sample_reward.id,
            status="pending",
            transaction_id=None,
        )

        repo.execute.assert_called_once()