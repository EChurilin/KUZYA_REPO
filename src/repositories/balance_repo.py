import uuid
from datetime import datetime
from typing import Optional
import asyncpg
from src.core.entities import BalanceSnapshot
from src.repositories.base import BaseRepository


class BalanceRepositoryImpl(BaseRepository):
    async def save_snapshot(self, snapshot: BalanceSnapshot) -> None:
        await self.execute(
            """
            INSERT INTO balance_snapshots (id, reward_type, balance, fetched_at)
            VALUES (, , , )
            """,
            snapshot.id,
            snapshot.reward_type,
            snapshot.balance,
            snapshot.fetched_at,
        )

    async def get_latest(self, reward_type: str) -> Optional[BalanceSnapshot]:
        row = await self.fetchone(
            """
            SELECT id, reward_type, balance, fetched_at
            FROM balance_snapshots
            WHERE reward_type = 
            ORDER BY fetched_at DESC
            LIMIT 1
            """,
            reward_type,
        )
        return self._row_to_snapshot(row) if row else None

    def _row_to_snapshot(self, row: asyncpg.Record) -> BalanceSnapshot:
        return BalanceSnapshot(
            id=row["id"],
            reward_type=row["reward_type"],
            balance=row["balance"],
            fetched_at=row["fetched_at"],
        )