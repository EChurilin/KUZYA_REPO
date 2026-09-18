import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.core.entities import GiftClaim
from src.repositories.gift_claim_repo import GiftClaimRepositoryImpl


@pytest.fixture
def repo():
    return GiftClaimRepositoryImpl(AsyncMock())


@pytest.fixture
def sample_claim():
    return GiftClaim(
        id=uuid.uuid4(),
        user_id=123,
        gift_id="gift_star_001",
        gift_name="Star Gift",
        star_count=50,
        status="pending",
        telegram_charge_id=None,
        created_at=datetime.now(timezone.utc),
        sent_at=None,
    )


def _claim_to_dict(c: GiftClaim) -> dict:
    return {
        "id": c.id,
        "user_id": c.user_id,
        "gift_id": c.gift_id,
        "gift_name": c.gift_name,
        "star_count": c.star_count,
        "status": c.status,
        "telegram_charge_id": c.telegram_charge_id,
        "created_at": c.created_at,
        "sent_at": c.sent_at,
    }


class TestGiftClaimRepository:
    @pytest.mark.asyncio
    async def test_create(self, repo, sample_claim):
        repo.execute = AsyncMock()

        await repo.create(sample_claim)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, sample_claim):
        repo.fetchone = AsyncMock(return_value=_claim_to_dict(sample_claim))

        claim = await repo.get_by_id(sample_claim.id)

        assert claim is not None
        assert claim.gift_id == "gift_star_001"
        assert claim.star_count == 50

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        claim = await repo.get_by_id(uuid.uuid4())

        assert claim is None

    @pytest.mark.asyncio
    async def test_update_status_sent(self, repo):
        repo.execute = AsyncMock()
        claim_id = uuid.uuid4()

        await repo.update_status(claim_id, "sent", "charge_123")

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_failed(self, repo):
        repo.execute = AsyncMock()
        claim_id = uuid.uuid4()

        await repo.update_status(claim_id, "failed", None)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_user(self, repo, sample_claim):
        repo.fetch = AsyncMock(return_value=[_claim_to_dict(sample_claim)])

        claims = await repo.get_by_user(123)

        assert len(claims) == 1
        assert claims[0].user_id == 123

    @pytest.mark.asyncio
    async def test_get_by_user_empty(self, repo):
        repo.fetch = AsyncMock(return_value=[])

        claims = await repo.get_by_user(123)

        assert claims == []