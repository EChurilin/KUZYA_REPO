import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock

from src.core.entities import UserBalanceTransaction
from src.services.user_balance_service import UserBalanceService


@pytest.fixture
def user_balance_repo_mock():
    return AsyncMock()


class TestUserBalanceService:
    @pytest.mark.asyncio
    async def test_get_balance(self, user_balance_repo_mock):
        user_balance_repo_mock.get_balance = AsyncMock(return_value=145)

        service = UserBalanceService(user_balance_repo_mock)
        balance = await service.get_balance(123)

        assert balance == 145
        user_balance_repo_mock.get_balance.assert_awaited_once_with(123)

    @pytest.mark.asyncio
    async def test_credit_from_application(self, user_balance_repo_mock):
        user_balance_repo_mock.credit = AsyncMock(return_value=145)
        app_id = uuid.uuid4()

        service = UserBalanceService(user_balance_repo_mock)
        new_balance = await service.credit_from_application(
            user_id=123,
            application_id=app_id,
            approved_count=3,
            price_per_screenshot=15,
        )

        assert new_balance == 145
        user_balance_repo_mock.credit.assert_awaited_once_with(
            user_id=123,
            amount=45,
            reason="application_reward",
            reference_id=app_id,
        )

    @pytest.mark.asyncio
    async def test_debit_for_gift(self, user_balance_repo_mock):
        user_balance_repo_mock.debit = AsyncMock(return_value=100)
        claim_id = uuid.uuid4()

        service = UserBalanceService(user_balance_repo_mock)
        new_balance = await service.debit_for_gift(
            user_id=123,
            gift_claim_id=claim_id,
            amount=45,
        )

        assert new_balance == 100
        user_balance_repo_mock.debit.assert_awaited_once_with(
            user_id=123,
            amount=45,
            reason="gift_claim",
            reference_id=claim_id,
        )

    @pytest.mark.asyncio
    async def test_get_transactions(self, user_balance_repo_mock):
        tx = UserBalanceTransaction(
            id=uuid.uuid4(),
            user_id=123,
            amount=45,
            balance_after=145,
            reason="application_reward",
            reference_id=uuid.uuid4(),
            created_at=datetime.now(timezone.utc),
        )
        user_balance_repo_mock.get_transactions = AsyncMock(return_value=[tx])

        service = UserBalanceService(user_balance_repo_mock)
        txs = await service.get_transactions(123)

        assert len(txs) == 1
        assert txs[0].balance_after == 145