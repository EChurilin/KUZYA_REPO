import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.core.entities import StarTopup
from src.repositories.topup_repo import TopupRepositoryImpl


@pytest.fixture
def repo():
    return TopupRepositoryImpl(AsyncMock())


@pytest.fixture
def sample_topup():
    return StarTopup(
        id=uuid.uuid4(),
        admin_id=123,
        amount=1000,
        status="pending",
        invoice_payload="topup_payload_abc",
        invoice_message_id=None,
        telegram_payment_charge_id=None,
        created_at=datetime.now(timezone.utc),
        paid_at=None,
    )


def _topup_to_dict(t: StarTopup) -> dict:
    return {
        "id": t.id,
        "admin_id": t.admin_id,
        "amount": t.amount,
        "status": t.status,
        "invoice_payload": t.invoice_payload,
        "invoice_message_id": t.invoice_message_id,
        "telegram_payment_charge_id": t.telegram_payment_charge_id,
        "created_at": t.created_at,
        "paid_at": t.paid_at,
    }


class TestTopupRepository:
    @pytest.mark.asyncio
    async def test_create(self, repo, sample_topup):
        repo.execute = AsyncMock()

        await repo.create(sample_topup)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, sample_topup):
        repo.fetchone = AsyncMock(return_value=_topup_to_dict(sample_topup))

        topup = await repo.get_by_id(sample_topup.id)

        assert topup is not None
        assert topup.amount == 1000
        assert topup.invoice_payload == "topup_payload_abc"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        topup = await repo.get_by_id(uuid.uuid4())

        assert topup is None

    @pytest.mark.asyncio
    async def test_get_by_payload_found(self, repo, sample_topup):
        repo.fetchone = AsyncMock(return_value=_topup_to_dict(sample_topup))

        topup = await repo.get_by_payload("topup_payload_abc")

        assert topup is not None
        assert topup.invoice_payload == "topup_payload_abc"

    @pytest.mark.asyncio
    async def test_get_by_payload_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        topup = await repo.get_by_payload("missing")

        assert topup is None

    @pytest.mark.asyncio
    async def test_update_status_paid(self, repo):
        repo.execute = AsyncMock()
        topup_id = uuid.uuid4()

        await repo.update_status(topup_id, "paid", "charge_xyz")

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_cancelled(self, repo):
        repo.execute = AsyncMock()
        topup_id = uuid.uuid4()

        await repo.update_status(topup_id, "cancelled", None)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_invoice_message_id(self, repo):
        repo.execute = AsyncMock()
        topup_id = uuid.uuid4()

        await repo.delete_invoice_message_id(topup_id)

        repo.execute.assert_called_once()