from typing import List, Optional
import uuid
import asyncpg

from src.core.entities import UserBalanceTransaction
from src.repositories.base import BaseRepository


class UserBalanceRepositoryImpl(BaseRepository):
    async def get_balance(self, user_id: int) -> int:
        balance = await self.fetchval(
            "SELECT star_balance FROM users WHERE id = $1",
            user_id,
        )
        return balance if balance is not None else 0

    async def credit(
        self, user_id: int, amount: int, reason: str, reference_id: Optional[uuid.UUID]
    ) -> int:
        # Атомарно: UPDATE баланса и INSERT в леджер одним выражением.
        new_balance = await self.fetchval(
            """
            WITH updated AS (
                UPDATE users
                SET star_balance = star_balance + $1
                WHERE id = $2
                RETURNING star_balance
            )
            INSERT INTO user_balance_transactions
                (user_id, amount, balance_after, reason, reference_id)
            SELECT $2, $1, updated.star_balance, $3, $4
            FROM updated
            RETURNING balance_after
            """,
            amount,
            user_id,
            reason,
            reference_id,
        )
        if new_balance is None:
            raise ValueError(f"User {user_id} not found for balance credit")
        return new_balance

    async def debit(
        self, user_id: int, amount: int, reason: str, reference_id: Optional[uuid.UUID]
    ) -> int:
        # Атомарно. Условие star_balance >= $1 защищает от ухода в минус.
        new_balance = await self.fetchval(
            """
            WITH updated AS (
                UPDATE users
                SET star_balance = star_balance - $1
                WHERE id = $2 AND star_balance >= $1
                RETURNING star_balance
            )
            INSERT INTO user_balance_transactions
                (user_id, amount, balance_after, reason, reference_id)
            SELECT $2, -$1, updated.star_balance, $3, $4
            FROM updated
            RETURNING balance_after
            """,
            amount,
            user_id,
            reason,
            reference_id,
        )
        if new_balance is None:
            raise ValueError(
                f"User {user_id} not found or insufficient balance for debit"
            )
        return new_balance

    async def get_transactions(
        self, user_id: int, limit: int = 50
    ) -> List[UserBalanceTransaction]:
        rows = await self.fetch(
            """
            SELECT id, user_id, amount, balance_after, reason, reference_id, created_at
            FROM user_balance_transactions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )
        return [self._row_to_transaction(row) for row in rows]

    def _row_to_transaction(self, row: asyncpg.Record) -> UserBalanceTransaction:
        return UserBalanceTransaction(
            id=row["id"],
            user_id=row["user_id"],
            amount=row["amount"],
            balance_after=row["balance_after"],
            reason=row["reason"],
            reference_id=row["reference_id"],
            created_at=row["created_at"],
        )