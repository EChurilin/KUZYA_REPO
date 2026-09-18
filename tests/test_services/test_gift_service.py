import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock

from src.core.entities import Gift, GiftClaim
from src.core.exceptions import (
    GiftNotFoundError,
    InsufficientBotBalanceError,
    InsufficientUserBalanceError,
)
from src.services.gift_service import GiftService


@pytest.fixture
def gift_issuer_mock():
    return AsyncMock()

@pytest.fixture
def gift_claim_repo_mock():
    return AsyncMock()

@pytest.fixture
def user_balance_service_mock():
    return AsyncMock()

@pytest.fixture
def balance_service_mock():
    return AsyncMock()

@pytest.fixture
def sample_gift():
    return Gift(id="gift_1", star_count=50)

@pytest.fixture
def service(gift_issuer_mock, gift_claim_repo_mock, user_balance_service_mock, balance_service_mock):
    return GiftService(
        gift_issuer_mock,
        gift_claim_repo_mock,
        user_balance_service_mock,
        balance_service_mock,
    )


class TestGiftService:
    @pytest.mark.asyncio
    async def test_get_available_gifts(self, service, gift_issuer_mock, sample_gift):
        gift_issuer_mock.get_available_gifts = AsyncMock(return_value=[sample_gift])

        gifts = await service.get_available_gifts()

        assert len(gifts) == 1
        assert gifts[0].id == "gift_1"
        gift_issuer_mock.get_available_gifts.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_affordable_gifts(self, service, gift_issuer_mock, user_balance_service_mock):
        gift1 = Gift(id="gift_1", star_count=50)
        gift2 = Gift(id="gift_2", star_count=200)
        gift_issuer_mock.get_available_gifts = AsyncMock(return_value=[gift1, gift2])
        user_balance_service_mock.get_balance = AsyncMock(return_value=100)

        affordable = await service.get_affordable_gifts(123)

        assert len(affordable) == 1
        assert affordable[0].id == "gift_1"

    @pytest.mark.asyncio
    async def test_get_affordable_gifts_empty_balance(self, service, gift_issuer_mock, user_balance_service_mock):
        gift1 = Gift(id="gift_1", star_count=50)
        gift_issuer_mock.get_available_gifts = AsyncMock(return_value=[gift1])
        user_balance_service_mock.get_balance = AsyncMock(return_value=0)

        affordable = await service.get_affordable_gifts(123)

        assert affordable == []

    @pytest.mark.asyncio
    async def test_claim_gift_success(
        self, service, gift_issuer_mock, gift_claim_repo_mock,
        user_balance_service_mock, balance_service_mock, sample_gift
    ):
        gift_issuer_mock.get_available_gifts = AsyncMock(return_value=[sample_gift])
        user_balance_service_mock.get_balance = AsyncMock(return_value=100)
        balance_service_mock.get_current_balance = AsyncMock(return_value=1000)
        gift_issuer_mock.send_gift = AsyncMock(return_value=True)
        gift_claim_repo_mock.create = AsyncMock()
        user_balance_service_mock.debit_for_gift = AsyncMock(return_value=50)
        gift_claim_repo_mock.update_status = AsyncMock()

        claim = await service.claim_gift(123, "gift_1")

        assert claim.status == "sent"
        assert claim.star_count == 50
        assert claim.user_id == 123
        gift_claim_repo_mock.create.assert_awaited_once()
        gift_issuer_mock.send_gift.assert_awaited_once_with(user_id=123, gift_id="gift_1")
        user_balance_service_mock.debit_for_gift.assert_awaited_once()
        gift_claim_repo_mock.update_status.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_claim_gift_not_found(self, service, gift_issuer_mock):
        gift_issuer_mock.get_available_gifts = AsyncMock(return_value=[])

        with pytest.raises(GiftNotFoundError):
            await service.claim_gift(123, "gift_999")

    @pytest.mark.asyncio
    async def test_claim_gift_insufficient_user_balance(
        self, service, gift_issuer_mock, user_balance_service_mock, sample_gift
    ):
        gift_issuer_mock.get_available_gifts = AsyncMock(return_value=[sample_gift])
        user_balance_service_mock.get_balance = AsyncMock(return_value=10)  # меньше 50

        with pytest.raises(InsufficientUserBalanceError):
            await service.claim_gift(123, "gift_1")

    @pytest.mark.asyncio
    async def test_claim_gift_insufficient_bot_balance(
        self, service, gift_issuer_mock, user_balance_service_mock, balance_service_mock, sample_gift
    ):
        gift_issuer_mock.get_available_gifts = AsyncMock(return_value=[sample_gift])
        user_balance_service_mock.get_balance = AsyncMock(return_value=100)
        balance_service_mock.get_current_balance = AsyncMock(return_value=10)  # меньше 50

        with pytest.raises(InsufficientBotBalanceError):
            await service.claim_gift(123, "gift_1")

    @pytest.mark.asyncio
    async def test_claim_gift_send_failed_marks_claim_as_failed(
        self, service, gift_issuer_mock, gift_claim_repo_mock,
        user_balance_service_mock, balance_service_mock, sample_gift
    ):
        gift_issuer_mock.get_available_gifts = AsyncMock(return_value=[sample_gift])
        user_balance_service_mock.get_balance = AsyncMock(return_value=100)
        balance_service_mock.get_current_balance = AsyncMock(return_value=1000)
        gift_issuer_mock.send_gift = AsyncMock(side_effect=Exception("API error"))
        gift_claim_repo_mock.create = AsyncMock()
        gift_claim_repo_mock.update_status = AsyncMock()

        with pytest.raises(Exception, match="API error"):
            await service.claim_gift(123, "gift_1")

        # GiftClaim должен быть помечен как 'failed'
        gift_claim_repo_mock.update_status.assert_awaited_once()
        call_args = gift_claim_repo_mock.update_status.call_args[0]
        assert call_args[1] == "failed"

        # Баланс пользователя НЕ должен быть списан
        user_balance_service_mock.debit_for_gift.assert_not_awaited()