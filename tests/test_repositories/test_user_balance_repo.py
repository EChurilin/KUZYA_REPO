import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.core.entities import UserBalanceTransaction
from src.repositories.user_balance_repo import UserBalanceRepositoryImpl


@pytest.fixture
def repo():
    return UserBalanceRepositoryImpl(AsyncMock())


@pytest.fixture
def sample_transaction():
    return UserBalanceTransaction(
        id=uuid.uuid4(),
        user_id=123,
        amount=45,
        balance_after=145,
        reason="application_reward",
        reference_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
    )


def _tx_to_dict(t: UserBalanceTransaction) -> dict:
    return {
        "id": t.id,
        "user_id": t.user_id,
        "amount": t.amount,
        "balance_after": t.balance_after,
        "reason": t.reason,
        "reference_id": t.reference_id,
        "created_at": t.created_at,
    }


class TestUserBalanceRepository:
    @pytest.mark.asyncio
    async def test_get_balance(self, repo):
        repo.fetchval = AsyncMock(return_value=145)

        balance = await repo.get_balance(123)

        assert balance == 145

    @pytest.mark.asyncio
    async def test_get_balance_user_not_found(self, repo):
        repo.fetchval = AsyncMock(return_value=None)

        balance = await repo.get_balance(999)

        assert balance == 0

    @pytest.mark.asyncio
    async def test_credit(self, repo):
        repo.fetchval = AsyncMock(return_value=145)

        new_balance = await repo.credit(123, 45, "application_reward", uuid.uuid4())

        assert new_balance == 145
        repo.fetchval.assert_called_once()

    @pytest.mark.asyncio
    async def test_credit_user_not_found(self, repo):
        repo.fetchval = AsyncMock(return_value=None)

        with pytest.raises(ValueError):
            await repo.credit(999, 45, "application_reward", uuid.uuid4())

    @pytest.mark.asyncio
    async def test_debit(self, repo):
        repo.fetchval = AsyncMock(return_value=100)

        new_balance = await repo.debit(123, 45, "gift_claim", uuid.uuid4())

        assert new_balance == 100
        repo.fetchval.assert_called_once()

    @pytest.mark.asyncio
    async def test_debit_insufficient_balance(self, repo):
        repo.fetchval = AsyncMock(return_value=None)

        with pytest.raises(ValueError):
            await repo.debit(999, 45, "gift_claim", uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_transactions(self, repo, sample_transaction):
        repo.fetch = AsyncMock(return_value=[_tx_to_dict(sample_transaction)])

        txs = await repo.get_transactions(123)

        assert len(txs) == 1
        assert txs[0].balance_after == 145

    @pytest.mark.asyncio
    async def test_get_transactions_empty(self, repo):
        repo.fetch = AsyncMock(return_value=[])

        txs = await repo.get_transactions(123)

        assert txs == []