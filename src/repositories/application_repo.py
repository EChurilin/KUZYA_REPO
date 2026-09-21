import uuid
from datetime import datetime, timezone
from typing import List, Optional
import asyncpg
from src.core.entities import Application
from src.repositories.base import BaseRepository


class ApplicationRepositoryImpl(BaseRepository):
    async def create(self, application: Application) -> None:
        await self.execute(
            """
            INSERT INTO applications (
                id, user_id, session_id, campaign_id, status,
                actual_screenshot_count, approved_screenshot_count,
                moderator_comment, submitted_at, reviewed_at,
                rewarded_at, reviewed_by, auto_closed
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            application.id,
            application.user_id,
            application.session_id,
            application.campaign_id,
            application.status,
            application.actual_screenshot_count,
            application.approved_screenshot_count,
            application.moderator_comment,
            application.submitted_at,
            application.reviewed_at,
            application.rewarded_at,
            application.reviewed_by,
            application.auto_closed,
        )

    async def get_by_id(self, application_id: uuid.UUID) -> Optional[Application]:
        row = await self.fetchone(
            """
            SELECT id, user_id, session_id, campaign_id, status,
                   actual_screenshot_count, approved_screenshot_count,
                   moderator_comment, submitted_at, reviewed_at,
                   rewarded_at, reviewed_by, auto_closed, summary_message_id
            FROM applications
            WHERE id = $1
            """,
            application_id,
        )
        return self._row_to_application(row) if row else None

    async def get_pending_review(self, limit: int = 50) -> List[Application]:
        rows = await self.fetch(
            """
            SELECT id, user_id, session_id, campaign_id, status,
                   actual_screenshot_count, approved_screenshot_count,
                   moderator_comment, submitted_at, reviewed_at,
                   rewarded_at, reviewed_by, auto_closed, summary_message_id
            FROM applications
            WHERE status = 'pending_review'
            ORDER BY submitted_at ASC
            LIMIT $1
            """,
            limit,
        )
        return [self._row_to_application(row) for row in rows]

    async def update_status(
        self,
        application_id: uuid.UUID,
        status: str,
        reviewed_by: Optional[int],
        moderator_comment: Optional[str],
        approved_count: int,
    ) -> None:
        await self.execute(
            """
            UPDATE applications
            SET status = $1,
                reviewed_by = $2,
                moderator_comment = $3,
                approved_screenshot_count = $4,
                reviewed_at = NOW()
            WHERE id = $5
            """,
            status,
            reviewed_by,
            moderator_comment,
            approved_count,
            application_id,
        )

    async def mark_rewarded(self, application_id: uuid.UUID) -> None:
        await self.execute(
            """
            UPDATE applications
            SET status = 'rewarded', rewarded_at = NOW()
            WHERE id = $1
            """,
            application_id,
        )

    async def set_summary_message_id(self, application_id: uuid.UUID, message_id: int) -> None:
        """Сохраняет message_id итогового сообщения в чате стафф-бота."""
        await self.execute(
            "UPDATE applications SET summary_message_id = $1 WHERE id = $2",
            message_id,
            application_id,
        )

    async def get_by_user(self, user_id: int, limit: int = 20) -> List[Application]:
        rows = await self.fetch(
            """
            SELECT id, user_id, session_id, campaign_id, status,
                   actual_screenshot_count, approved_screenshot_count,
                   moderator_comment, submitted_at, reviewed_at,
                   rewarded_at, reviewed_by, auto_closed, summary_message_id
            FROM applications
            WHERE user_id = $1
            ORDER BY submitted_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )
        return [self._row_to_application(row) for row in rows]

    async def count_today_by_user(self, user_id: int) -> int:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await self.fetchval(
            """
            SELECT COUNT(*) FROM applications
            WHERE user_id = $1 AND submitted_at >= $2
            """,
            user_id,
            today_start,
        )
        return int(result)

    def _row_to_application(self, row: asyncpg.Record) -> Application:
        return Application(
            id=row["id"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            campaign_id=row["campaign_id"],
            status=row["status"],
            actual_screenshot_count=row["actual_screenshot_count"],
            approved_screenshot_count=row["approved_screenshot_count"],
            moderator_comment=row["moderator_comment"],
            submitted_at=row["submitted_at"],
            reviewed_at=row["reviewed_at"],
            rewarded_at=row["rewarded_at"],
            reviewed_by=row["reviewed_by"],
            auto_closed=row["auto_closed"],
            summary_message_id=row["summary_message_id"],
        )
