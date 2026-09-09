from typing import Any
from uuid import UUID

from src.core.entities import Campaign
from src.config.constants import DatabaseTables
from src.repositories.base import BaseRepository


class CampaignRepository(BaseRepository):
    """Репозиторий для работы с рекламными кампаниями."""

    async def get_active(self) -> list[Campaign]:
        """Возвращает список активных кампаний для пользователей.
        Кампания считается активной, если is_active = True и текущее время
        находится в диапазоне между starts_at и ends_at.
        """
        query = f"""
            SELECT id, name, description, reward_type, reward_amount,
                   starts_at, ends_at, max_rewards_per_user, is_active, created_at
            FROM {DatabaseTables.CAMPAIGNS}
            WHERE is_active = True 
              AND starts_at <= NOW() 
              AND ends_at >= NOW()
            ORDER BY created_at DESC
        """
        rows = await self.fetch_all(query)
        return [self._map_row_to_entity(row) for row in rows]

    async def get_all_for_staff(self, limit: int = 50, offset: int = 0) -> list[Campaign]:
        """Возвращает все кампании (включая неактивные) для модераторов и админов."""
        query = f"""
            SELECT id, name, description, reward_type, reward_amount,
                   starts_at, ends_at, max_rewards_per_user, is_active, created_at
            FROM {DatabaseTables.CAMPAIGNS}
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        rows = await self.fetch_all(query, limit, offset)
        return [self._map_row_to_entity(row) for row in rows]

    async def get_by_id(self, campaign_id: UUID) -> Campaign | None:
        """Возвращает кампанию по её UUID."""
        query = f"""
            SELECT id, name, description, reward_type, reward_amount,
                   starts_at, ends_at, max_rewards_per_user, is_active, created_at
            FROM {DatabaseTables.CAMPAIGNS}
            WHERE id = $1
        """
        row = await self.fetch_one(query, campaign_id)
        return self._map_row_to_entity(row) if row else None

    @staticmethod
    def _map_row_to_entity(row: dict[str, Any]) -> Campaign:
        """Преобразует словарь из БД в доменную сущность Campaign."""
        return Campaign(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            reward_type=row["reward_type"],
            reward_amount=row["reward_amount"],
            starts_at=row["starts_at"],
            ends_at=row["ends_at"],
            max_rewards_per_user=row["max_rewards_per_user"],
            is_active=row["is_active"],
            created_at=row["created_at"],
        )