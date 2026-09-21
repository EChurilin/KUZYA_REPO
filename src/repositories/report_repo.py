from typing import List, Optional
from datetime import datetime
import asyncpg
from src.repositories.base import BaseRepository


class ReportRepositoryImpl(BaseRepository):
    async def get_unique_users_count(self, since: Optional[datetime]) -> int:
        result = await self.fetchval(
            """
            SELECT COUNT(DISTINCT user_id)
            FROM sessions
            WHERE ($1::timestamptz IS NULL OR started_at >= $1::timestamptz)
            """,
            since
        )
        return int(result) if result is not None else 0

    async def get_screenshots_stats(self, since: Optional[datetime]) -> tuple[int, int]:
        row = await self.fetchone(
            """
            SELECT
                COUNT(*) FILTER (WHERE aps.status IN ('approved', 'rejected')) as sent_count,
                COUNT(*) FILTER (WHERE aps.status = 'approved' AND a.status = 'rewarded') as approved_count
            FROM application_screenshots aps
            LEFT JOIN applications a ON a.id = aps.application_id
            WHERE ($1::timestamptz IS NULL OR aps.created_at >= $1::timestamptz)
            """,
            since
        )
        if row is None:
            return (0, 0)
        return (int(row["sent_count"]), int(row["approved_count"]))

    async def get_top_users_by_screenshots(self, since: Optional[datetime], limit: int = 30) -> List[dict]:
        rows = await self.fetch(
            """
            SELECT
                s.user_id,
                u.username,
                u.first_name,
                COUNT(*) FILTER (WHERE aps.status IN ('approved', 'rejected')) as sent_count,
                COUNT(*) FILTER (WHERE aps.status = 'approved' AND a.status = 'rewarded') as approved_count
            FROM sessions s
            JOIN application_screenshots aps ON aps.session_id = s.id
            LEFT JOIN applications a ON a.id = aps.application_id
            LEFT JOIN users u ON u.id = s.user_id
            WHERE ($1::timestamptz IS NULL OR aps.created_at >= $1::timestamptz)
            GROUP BY s.user_id, u.username, u.first_name
            ORDER BY sent_count DESC
            LIMIT $2
            """,
            since, limit
        )
        return [dict(row) for row in rows]

    async def get_stats_by_game(self, since: Optional[datetime]) -> List[dict]:
        rows = await self.fetch(
            """
            SELECT
                g.name as game_name,
                COUNT(DISTINCT s.user_id) as user_count,
                COUNT(*) FILTER (WHERE aps.status IN ('approved', 'rejected')) as sent_count,
                COUNT(*) FILTER (WHERE aps.status = 'approved' AND a.status = 'rewarded') as approved_count
            FROM sessions s
            JOIN games g ON g.id = s.game_id
            JOIN application_screenshots aps ON aps.session_id = s.id
            LEFT JOIN applications a ON a.id = aps.application_id
            WHERE ($1::timestamptz IS NULL OR aps.created_at >= $1::timestamptz)
            GROUP BY g.name
            ORDER BY sent_count DESC
            """,
            since
        )
        return [dict(row) for row in rows]
