from typing import List, Optional
import uuid
import asyncpg

from src.core.entities import GiftClaim
from src.repositories.base import BaseRepository


class GiftClaimRepositoryImpl(BaseRepository):
    async def create(self, claim: GiftClaim) -> None:
        await self.execute(
            """
            INSERT INTO gift_claims (
                id, user_id, gift_id, gift_name, star_count,
                status, telegram_charge_id, created_at, sent_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            claim.id,
            claim.user_id,
            claim.gift_id,
            claim.gift_name,
            claim.star_count,
            claim.status,
            claim.telegram_charge_id,
            claim.created_at,
            claim.sent_at,
        )

    async def get_by_id(self, claim_id: uuid.UUID) -> Optional[GiftClaim]:
        row = await self.fetchone(
            """
            SELECT id, user_id, gift_id, gift_name, star_count,
                   status, telegram_charge_id, created_at, sent_at
            FROM gift_claims
            WHERE id = $1
            """,
            claim_id,
        )
        return self._row_to_claim(row) if row else None

    async def update_status(
        self, claim_id: uuid.UUID, status: str, telegram_charge_id: Optional[str]
    ) -> None:
        if status == "sent":
            await self.execute(
                """
                UPDATE gift_claims
                SET status = $2, telegram_charge_id = $3, sent_at = NOW()
                WHERE id = $1
                """,
                claim_id,
                status,
                telegram_charge_id,
            )
        else:
            await self.execute(
                """
                UPDATE gift_claims
                SET status = $2, telegram_charge_id = $3
                WHERE id = $1
                """,
                claim_id,
                status,
                telegram_charge_id,
            )

    async def get_by_user(self, user_id: int, limit: int = 20) -> List[GiftClaim]:
        rows = await self.fetch(
            """
            SELECT id, user_id, gift_id, gift_name, star_count,
                   status, telegram_charge_id, created_at, sent_at
            FROM gift_claims
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )
        return [self._row_to_claim(row) for row in rows]

    def _row_to_claim(self, row: asyncpg.Record) -> GiftClaim:
        return GiftClaim(
            id=row["id"],
            user_id=row["user_id"],
            gift_id=row["gift_id"],
            gift_name=row["gift_name"],
            star_count=row["star_count"],
            status=row["status"],
            telegram_charge_id=row["telegram_charge_id"],
            created_at=row["created_at"],
            sent_at=row["sent_at"],
        )