from typing import Optional
import uuid
import asyncpg

from src.core.entities import StarTopup
from src.repositories.base import BaseRepository


class TopupRepositoryImpl(BaseRepository):
    async def create(self, topup: StarTopup) -> None:
        await self.execute(
            """
            INSERT INTO star_topups (
                id, admin_id, amount, status, invoice_payload,
                invoice_message_id, telegram_payment_charge_id, created_at, paid_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            topup.id,
            topup.admin_id,
            topup.amount,
            topup.status,
            topup.invoice_payload,
            topup.invoice_message_id,
            topup.telegram_payment_charge_id,
            topup.created_at,
            topup.paid_at,
        )

    async def get_by_id(self, topup_id: uuid.UUID) -> Optional[StarTopup]:
        row = await self.fetchone(
            """
            SELECT id, admin_id, amount, status, invoice_payload,
                   invoice_message_id, telegram_payment_charge_id, created_at, paid_at
            FROM star_topups
            WHERE id = $1
            """,
            topup_id,
        )
        return self._row_to_topup(row) if row else None

    async def get_by_payload(self, payload: str) -> Optional[StarTopup]:
        row = await self.fetchone(
            """
            SELECT id, admin_id, amount, status, invoice_payload,
                   invoice_message_id, telegram_payment_charge_id, created_at, paid_at
            FROM star_topups
            WHERE invoice_payload = $1
            """,
            payload,
        )
        return self._row_to_topup(row) if row else None

    async def update_status(
        self, topup_id: uuid.UUID, status: str, telegram_payment_charge_id: Optional[str]
    ) -> None:
        if status == "paid":
            await self.execute(
                """
                UPDATE star_topups
                SET status = $2, telegram_payment_charge_id = $3, paid_at = NOW()
                WHERE id = $1
                """,
                topup_id,
                status,
                telegram_payment_charge_id,
            )
        else:
            await self.execute(
                """
                UPDATE star_topups
                SET status = $2, telegram_payment_charge_id = $3
                WHERE id = $1
                """,
                topup_id,
                status,
                telegram_payment_charge_id,
            )

    async def set_invoice_message_id(self, topup_id: uuid.UUID, message_id: int) -> None:
        await self.execute(
            "UPDATE star_topups SET invoice_message_id = $2 WHERE id = $1",
            topup_id,
            message_id,
        )

    async def delete_invoice_message_id(self, topup_id: uuid.UUID) -> None:
        await self.execute(
            "UPDATE star_topups SET invoice_message_id = NULL WHERE id = $1",
            topup_id,
        )

    def _row_to_topup(self, row: asyncpg.Record) -> StarTopup:
        return StarTopup(
            id=row["id"],
            admin_id=row["admin_id"],
            amount=row["amount"],
            status=row["status"],
            invoice_payload=row["invoice_payload"],
            invoice_message_id=row["invoice_message_id"],
            telegram_payment_charge_id=row["telegram_payment_charge_id"],
            created_at=row["created_at"],
            paid_at=row["paid_at"],
        )
