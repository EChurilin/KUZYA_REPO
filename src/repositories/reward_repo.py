import uuid
from typing import Optional
import asyncpg
from src.core.entities import Reward
from src.repositories.base import BaseRepository


class RewardRepositoryImpl(BaseRepository):
    async def create(self, reward: Reward) -> None:
        await self.execute(
            """
            INSERT INTO rewards (
                id, user_id, application_id, reward_type, amount,
                transaction_id, status, issued_at, delivered_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            reward.id,
            reward.user_id,
            reward.application_id,
            reward.reward_type,
            reward.amount,
            reward.transaction_id,
            reward.status,
            reward.issued_at,
            reward.delivered_at,
        )

    async def get_by_id(self, reward_id: uuid.UUID) -> Optional[Reward]:
        row = await self.fetchone(
            """
            SELECT id, user_id, application_id, reward_type, amount,
                   transaction_id, status, issued_at, delivered_at
            FROM rewards
            WHERE id = $1
            """,
            reward_id,
        )
        return self._row_to_reward(row) if row else None

    async def get_by_application(self, application_id: uuid.UUID) -> Optional[Reward]:
        row = await self.fetchone(
            """
            SELECT id, user_id, application_id, reward_type, amount,
                   transaction_id, status, issued_at, delivered_at
            FROM rewards
            WHERE application_id = $1
            LIMIT 1
            """,
            application_id,
        )
        return self._row_to_reward(row) if row else None

    async def update_status(
        self, reward_id: uuid.UUID, status: str, transaction_id: Optional[str]
    ) -> None:
        if status == "issued":
            await self.execute(
                """
                UPDATE rewards
                SET status = $2, transaction_id = $3, issued_at = NOW()
                WHERE id = $1
                """,
                reward_id,
                status,
                transaction_id,
            )
        else:
            await self.execute(
                """
                UPDATE rewards
                SET status = $2, transaction_id = $3
                WHERE id = $1
                """,
                reward_id,
                status,
                transaction_id,
            )

    def _row_to_reward(self, row: asyncpg.Record) -> Reward:
        return Reward(
            id=row["id"],
            user_id=row["user_id"],
            application_id=row["application_id"],
            reward_type=row["reward_type"],
            amount=row["amount"],
            transaction_id=row["transaction_id"],
            status=row["status"],
            issued_at=row["issued_at"],
            delivered_at=row["delivered_at"],
        )