import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from uuid import uuid4

from src.repositories.reward_repo import RewardRepository
from src.core.entities import Reward
from src.core.enums import RewardType, RewardStatus


@pytest.fixture
def mock_pool():
    return AsyncMock()


@pytest.mark.asyncio
async def test_reward_repository_create(mock_pool):
    """Проверяет создание записи о награде со статусом PENDING."""
    repo = RewardRepository(mock_pool)
    reward_id = uuid4()
    user_id = 123
    campaign_id = uuid4()
    app_id = uuid4()
    
    mock_row = {
        "id": reward_id,
        "user_id": user_id,
        "campaign_id": campaign_id,
        "application_id": app_id,
        "reward_type": RewardType.STARS,
        "amount": 100,
        "transaction_id": None,
        "status": RewardStatus.PENDING,
        "issued_at": None,
        "delivered_at": None,
    }
    repo.fetch_one = AsyncMock(return_value=mock_row)

    reward_entity = Reward(
        id=reward_id, user_id=user_id, campaign_id=campaign_id,
        application_id=app_id, reward_type=RewardType.STARS,
        amount=100, transaction_id=None, status=RewardStatus.PENDING,
        issued_at=None, delivered_at=None
    )
    
    created_reward = await repo.create(reward_entity)

    assert created_reward is not None
    assert created_reward.id == reward_id
    assert created_reward.status == RewardStatus.PENDING
    repo.fetch_one.assert_called_once()


@pytest.mark.asyncio
async def test_reward_repository_mark_as_issued(mock_pool):
    """Проверяет обновление статуса на ISSUED после успешной отправки."""
    repo = RewardRepository(mock_pool)
    reward_id = uuid4()
    now = datetime.now()
    tx_id = "tx_12345"
    
    mock_row = {
        "id": reward_id,
        "user_id": 123,
        "campaign_id": uuid4(),
        "application_id": uuid4(),
        "reward_type": RewardType.STARS,
        "amount": 100,
        "transaction_id": tx_id,
        "status": RewardStatus.ISSUED,
        "issued_at": now,
        "delivered_at": now,
    }
    repo.fetch_one = AsyncMock(return_value=mock_row)

    updated_reward = await repo.mark_as_issued(reward_id, tx_id, now, now)

    assert updated_reward is not None
    assert updated_reward.status == RewardStatus.ISSUED
    assert updated_reward.transaction_id == tx_id
    repo.fetch_one.assert_called_once()


@pytest.mark.asyncio
async def test_reward_repository_check_idempotency_true(mock_pool):
    """Проверяет, что метод возвращает True, если награда уже выдана."""
    repo = RewardRepository(mock_pool)
    app_id = uuid4()
    
    # fetch_val возвращает 1, если запись найдена (SELECT 1)
    repo.fetch_val = AsyncMock(return_value=1)

    is_issued = await repo.check_idempotency(app_id)

    assert is_issued is True
    repo.fetch_val.assert_called_once()


@pytest.mark.asyncio
async def test_reward_repository_check_idempotency_false(mock_pool):
    """Проверяет, что метод возвращает False, если награда ещё не выдана."""
    repo = RewardRepository(mock_pool)
    app_id = uuid4()
    
    # fetch_val возвращает None, если запись не найдена
    repo.fetch_val = AsyncMock(return_value=None)

    is_issued = await repo.check_idempotency(app_id)

    assert is_issued is False
    repo.fetch_val.assert_called_once()