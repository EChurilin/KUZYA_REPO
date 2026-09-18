import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock

from src.core.entities import StarTopup
from src.core.exceptions import TopupNotFoundError
from src.services.topup_service import TopupService


@pytest.fixture
def topup_repo_mock():
    return AsyncMock()

@pytest.fixture
def invoice_sender_mock():
    return AsyncMock()

@pytest.fixture
def balance_service_mock():
    return AsyncMock()

@pytest.fixture
def service(topup_repo_mock, invoice_sender_mock, balance_service_mock):
    return TopupService(topup_repo_mock, invoice_sender_mock, balance_service_mock)

@pytest.fixture
def sample_topup():
    return StarTopup(
        id=uuid.uuid4(),
        admin_id=123,
        amount=1000,
        status="pending",
        invoice_payload="topup_abc123",
        invoice_message_id=42,
        telegram_payment_charge_id=None,
        created_at=datetime.now(timezone.utc),
        paid_at=None,
    )


class TestTopupService:
    @pytest.mark.asyncio
    async def test_create_topup_request(self, service, topup_repo_mock):
        topup_repo_mock.create = AsyncMock()

        topup = await service.create_topup_request(admin_id=123, amount=1000)

        assert topup.admin_id == 123
        assert topup.amount == 1000
        assert topup.status == "pending"
        assert topup.invoice_payload.startswith("topup_")
        assert topup.invoice_message_id is None
        topup_repo_mock.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_invoice(self, service, topup_repo_mock, invoice_sender_mock, sample_topup):
        invoice_sender_mock.send_invoice = AsyncMock(return_value=99)
        topup_repo_mock.set_invoice_message_id = AsyncMock()

        message_id = await service.send_invoice(sample_topup)

        assert message_id == 99
        invoice_sender_mock.send_invoice.assert_awaited_once()
        topup_repo_mock.set_invoice_message_id.assert_awaited_once_with(sample_topup.id, 99)

    @pytest.mark.asyncio
    async def test_cancel_topup_success(self, service, topup_repo_mock, invoice_sender_mock, sample_topup):
        topup_repo_mock.get_by_id = AsyncMock(return_value=sample_topup)
        invoice_sender_mock.delete_message = AsyncMock()
        topup_repo_mock.update_status = AsyncMock()

        await service.cancel_topup(sample_topup.id)

        invoice_sender_mock.delete_message.assert_awaited_once_with(
            chat_id=123, message_id=42
        )
        topup_repo_mock.update_status.assert_awaited_once_with(sample_topup.id, "cancelled", None)

    @pytest.mark.asyncio
    async def test_cancel_topup_not_found(self, service, topup_repo_mock):
        topup_repo_mock.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(TopupNotFoundError):
            await service.cancel_topup(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_cancel_topup_already_paid(self, service, topup_repo_mock, invoice_sender_mock, sample_topup):
        sample_topup.status = "paid"
        topup_repo_mock.get_by_id = AsyncMock(return_value=sample_topup)

        await service.cancel_topup(sample_topup.id)

        # Ничего не должно произойти
        invoice_sender_mock.delete_message.assert_not_awaited()
        topup_repo_mock.update_status.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_process_successful_payment(self, service, topup_repo_mock, sample_topup):
        topup_repo_mock.get_by_payload = AsyncMock(return_value=sample_topup)
        topup_repo_mock.update_status = AsyncMock()

        result = await service.process_successful_payment("topup_abc123", "charge_xyz")

        assert result is not None
        assert result.status == "paid"
        topup_repo_mock.update_status.assert_awaited_once_with(sample_topup.id, "paid", "charge_xyz")

    @pytest.mark.asyncio
    async def test_process_successful_payment_idempotent(self, service, topup_repo_mock, sample_topup):
        sample_topup.status = "paid"
        topup_repo_mock.get_by_payload = AsyncMock(return_value=sample_topup)

        result = await service.process_successful_payment("topup_abc123", "charge_xyz")

        assert result is not None
        assert result.status == "paid"
        topup_repo_mock.update_status.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_process_successful_payment_not_found(self, service, topup_repo_mock):
        topup_repo_mock.get_by_payload = AsyncMock(return_value=None)

        result = await service.process_successful_payment("missing_payload", "charge_xyz")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_bot_balance(self, service, balance_service_mock):
        balance_service_mock.get_current_balance = AsyncMock(return_value=5000)

        balance = await service.get_bot_balance()

        assert balance == 5000
        balance_service_mock.get_current_balance.assert_awaited_once()