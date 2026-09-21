import uuid
from datetime import datetime
from typing import List, Optional
import asyncpg
from src.core.entities import ApplicationScreenshot
from src.repositories.base import BaseRepository


class ScreenshotRepositoryImpl(BaseRepository):
    async def create(self, screenshot: ApplicationScreenshot) -> None:
        await self.execute(
            """
            INSERT INTO application_screenshots
                (id, session_id, application_id, client_file_id, storage_path, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            screenshot.id,
            screenshot.session_id,
            screenshot.application_id,
            screenshot.client_file_id,
            screenshot.storage_path,
            screenshot.status,
            screenshot.created_at,
        )

    async def get_by_session(self, session_id: uuid.UUID) -> List[ApplicationScreenshot]:
        rows = await self.fetch(
            """
            SELECT id, session_id, application_id, client_file_id, storage_path, status, created_at, staff_message_id
            FROM application_screenshots
            WHERE session_id = $1
            ORDER BY created_at ASC
            """,
            session_id,
        )
        return [self._row_to_screenshot(row) for row in rows]

    async def get_by_application(self, application_id: uuid.UUID) -> List[ApplicationScreenshot]:
        rows = await self.fetch(
            """
            SELECT id, session_id, application_id, client_file_id, storage_path, status, created_at, staff_message_id
            FROM application_screenshots
            WHERE application_id = $1
            ORDER BY created_at ASC
            """,
            application_id,
        )
        return [self._row_to_screenshot(row) for row in rows]

    async def get_by_id(self, screenshot_id: uuid.UUID) -> Optional[ApplicationScreenshot]:
        row = await self.fetchone(
            """
            SELECT id, session_id, application_id, client_file_id, storage_path, status, created_at, staff_message_id
            FROM application_screenshots
            WHERE id = $1
            """,
            screenshot_id,
        )
        return self._row_to_screenshot(row) if row else None

    async def update_status(self, screenshot_id: uuid.UUID, status: str) -> None:
        await self.execute(
            "UPDATE application_screenshots SET status = $1 WHERE id = $2",
            status,
            screenshot_id,
        )

    async def set_staff_message_id(self, screenshot_id: uuid.UUID, message_id: int) -> None:
        """Сохраняет message_id сообщения скриншота в чате стафф-бота."""
        await self.execute(
            "UPDATE application_screenshots SET staff_message_id = $1 WHERE id = $2",
            message_id,
            screenshot_id,
        )

    async def link_to_application(
        self, session_id: uuid.UUID, application_id: uuid.UUID
    ) -> None:
        await self.execute(
            """
            UPDATE application_screenshots
            SET application_id = $1
            WHERE session_id = $2
            """,
            application_id,
            session_id,
        )

    async def get_old_screenshots_for_cleanup(
        self, retention_days: int
    ) -> List[ApplicationScreenshot]:
        rows = await self.fetch(
            """
            SELECT s.id, s.session_id, s.application_id, s.client_file_id,
                   s.storage_path, s.status, s.created_at, s.staff_message_id
            FROM application_screenshots s
            JOIN sessions sess ON s.session_id = sess.id
            WHERE sess.status IN ('completed', 'expired', 'cancelled')
              AND s.created_at < NOW() - ($1 || ' days')::INTERVAL
            """,
            str(retention_days),
        )
        return [self._row_to_screenshot(row) for row in rows]

    async def delete(self, screenshot_id: uuid.UUID) -> None:
        await self.execute(
            "DELETE FROM application_screenshots WHERE id = $1",
            screenshot_id,
        )

    def _row_to_screenshot(self, row: asyncpg.Record) -> ApplicationScreenshot:
        return ApplicationScreenshot(
            id=row["id"],
            session_id=row["session_id"],
            application_id=row["application_id"],
            client_file_id=row["client_file_id"],
            storage_path=row["storage_path"],
            status=row["status"],
            created_at=row["created_at"],
            staff_message_id=row["staff_message_id"],
        )
