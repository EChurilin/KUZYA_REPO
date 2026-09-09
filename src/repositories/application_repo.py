from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.entities import Application
from src.core.enums import ApplicationStatus
from src.config.constants import DatabaseTables
from src.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository):
    """Репозиторий для работы с заявками на участие в кампаниях."""

    async def create(self, app: Application) -> Application:
        """Создает новую заявку со скриншотом."""
        query = f"""
            INSERT INTO {DatabaseTables.APPLICATIONS}
            (id, user_id, campaign_id, status, screenshot_file_id, submitted_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, user_id, campaign_id, status, screenshot_file_id, 
                      moderator_comment, submitted_at, reviewed_at, rewarded_at, reviewed_by
        """
        row = await self.fetch_one(
            query,
            app.id,
            app.user_id,
            app.campaign_id,
            app.status,
            app.screenshot_file_id,
            app.submitted_at,
        )
        return self._map_row_to_entity(row)

    async def get_by_id(self, app_id: UUID) -> Application | None:
        """Возвращает заявку по её UUID."""
        query = f"""
            SELECT id, user_id, campaign_id, status, screenshot_file_id,
                   moderator_comment, submitted_at, reviewed_at, rewarded_at, reviewed_by
            FROM {DatabaseTables.APPLICATIONS}
            WHERE id = $1
        """
        row = await self.fetch_one(query, app_id)
        return self._map_row_to_entity(row) if row else None

    async def get_pending(self, limit: int = 10) -> list[Application]:
        """Возвращает очередь заявок, ожидающих модерации (для staff_bot)."""
        query = f"""
            SELECT id, user_id, campaign_id, status, screenshot_file_id,
                   moderator_comment, submitted_at, reviewed_at, rewarded_at, reviewed_by
            FROM {DatabaseTables.APPLICATIONS}
            WHERE status = $1
            ORDER BY submitted_at ASC
            LIMIT $2
        """
        rows = await self.fetch_all(query, ApplicationStatus.PENDING, limit)
        return [self._map_row_to_entity(row) for row in rows]

    async def update_status(
        self,
        app_id: UUID,
        status: str,
        reviewed_by: int,
        reviewed_at: datetime,
        moderator_comment: str | None = None,
    ) -> Application | None:
        """Обновляет статус заявки после проверки модератором."""
        query = f"""
            UPDATE {DatabaseTables.APPLICATIONS}
            SET status = $2, reviewed_by = $3, reviewed_at = $4, moderator_comment = $5
            WHERE id = $1
            RETURNING id, user_id, campaign_id, status, screenshot_file_id,
                      moderator_comment, submitted_at, reviewed_at, rewarded_at, reviewed_by
        """
        row = await self.fetch_one(
            query, app_id, status, reviewed_by, reviewed_at, moderator_comment
        )
        return self._map_row_to_entity(row) if row else None

    async def count_user_campaign_submissions(self, user_id: int, campaign_id: UUID) -> int:
        """Считает, сколько раз пользователь уже подавал заявку на эту кампанию.
        Нужен для проверки идемпотентности и лимитов.
        """
        query = f"""
            SELECT COUNT(*) 
            FROM {DatabaseTables.APPLICATIONS}
            WHERE user_id = $1 AND campaign_id = $2 AND status != $3
        """
        # Мы не считаем отклоненные заявки (REJECTED), чтобы дать шанс переотправить
        count = await self.fetch_val(query, user_id, campaign_id, ApplicationStatus.REJECTED)
        return int(count) if count else 0

    @staticmethod
    def _map_row_to_entity(row: dict[str, Any]) -> Application:
        """Преобразует словарь из БД в доменную сущность Application."""
        return Application(
            id=row["id"],
            user_id=row["user_id"],
            campaign_id=row["campaign_id"],
            status=row["status"],
            screenshot_file_id=row["screenshot_file_id"],
            moderator_comment=row["moderator_comment"],
            submitted_at=row["submitted_at"],
            reviewed_at=row["reviewed_at"],
            rewarded_at=row["rewarded_at"],
            reviewed_by=row["reviewed_by"],
        )