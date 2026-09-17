import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import asyncpg
from src.core.entities import Session
from src.repositories.base import BaseRepository


class SessionRepositoryImpl(BaseRepository):
    async def create(self, session: Session) -> None:
        await self.execute(
            """
            INSERT INTO sessions (id, user_id, game_id, status, started_at,
                                  last_screenshot_at, screenshot_count, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            session.id,
            session.user_id,
            session.game_id,
            session.status,
            session.started_at,
            session.last_screenshot_at,
            session.screenshot_count,
            session.created_at,
        )

    async def get_by_id(self, session_id: uuid.UUID) -> Optional[Session]:
        row = await self.fetchone(
            """
            SELECT id, user_id, game_id, status, started_at,
                   last_screenshot_at, screenshot_count, created_at
            FROM sessions
            WHERE id = $1
            """,
            session_id,
        )
        return self._row_to_session(row) if row else None

    async def get_active_by_user(self, user_id: int) -> Optional[Session]:
        row = await self.fetchone(
            """
            SELECT id, user_id, game_id, status, started_at,
                   last_screenshot_at, screenshot_count, created_at
            FROM sessions
            WHERE user_id = $1 AND status = 'active'
            ORDER BY started_at DESC
            LIMIT 1
            """,
            user_id,
        )
        return self._row_to_session(row) if row else None

    async def update_last_screenshot(
        self, session_id: uuid.UUID, timestamp: datetime
    ) -> None:
        await self.execute(
            """
            UPDATE sessions
            SET last_screenshot_at = $1,
                screenshot_count = screenshot_count + 1
            WHERE id = $2
            """,
            timestamp,
            session_id,
        )

    async def close_session(self, session_id: uuid.UUID, status: str) -> None:
        await self.execute(
            "UPDATE sessions SET status = $1 WHERE id = $2",
            status,
            session_id,
        )

    async def get_expired_active_sessions(
        self, timeout_hours: int
    ) -> List[Session]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=timeout_hours)
        rows = await self.fetch(
            """
            SELECT id, user_id, game_id, status, started_at,
                   last_screenshot_at, screenshot_count, created_at
            FROM sessions
            WHERE status = 'active'
              AND (
                  (last_screenshot_at IS NOT NULL AND last_screenshot_at < $1)
                  OR
                  (last_screenshot_at IS NULL AND started_at < $1)
              )
            """,
            cutoff,
        )
        return [self._row_to_session(row) for row in rows]

    def _row_to_session(self, row: asyncpg.Record) -> Session:
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            game_id=row["game_id"],
            status=row["status"],
            started_at=row["started_at"],
            last_screenshot_at=row["last_screenshot_at"],
            screenshot_count=row["screenshot_count"],
            created_at=row["created_at"],
        )