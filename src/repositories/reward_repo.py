from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.entities import Reward
from src.core.enums import RewardStatus
from src.config.constants import DatabaseTables
from src.repositories.base import BaseRepository


class RewardRepository(BaseRepository):
    """Репозиторий для работы с наградами (звёзды, промокоды)."""

    async def create(self, reward: Reward) -> Reward:
        """Создает запись о награде со статусом PENDING."""
        query = f"""
            INSERT INTO {DatabaseTables.REWARDS}
            (id, user_id, campaign_id, application_id, reward_type, amount, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, user_id, campaign_id, application_id, reward_type, amount, 
                      transaction_id, status, issued_at, delivered_at
        """
        row = await self.fetch_one(
            query,
            reward.id,
            reward.user_id,
            reward.campaign_id,
            reward.application_id,
            reward.reward_type,
            reward.amount,
            reward.status,
        )
        return self._map_row_to_entity(row)

    async def mark_as_issued(
        self,
        reward_id: UUID,
        transaction_id: str,
        issued_at: datetime,
        delivered_at: datetime,
    ) -> Reward | None:
        """Обновляет статус награды на ISSUED после успешной отправки через API."""
        query = f"""
            UPDATE {DatabaseTables.REWARDS}
            SET status = $2, transaction_id = $3, issued_at = $4, delivered_at = $5
            WHERE id = $1
            RETURNING id, user_id, campaign_id, application_id, reward_type, amount, 
                      transaction_id, status, issued_at, delivered_at
        """
        row = await self.fetch_one(
            query,
            reward_id,
            RewardStatus.ISSUED,
            transaction_id,
            issued_at,
            delivered_at,
        )
        return self._map_row_to_entity(row) if row else None

    async def mark_as_failed(self, reward_id: UUID, issued_at: datetime) -> Reward | None:
        """Обновляет статус награды на FAILED, если отправка через API не удалась."""
        query = f"""
            UPDATE {DatabaseTables.REWARDS}
            SET status = $2, issued_at = $3
            WHERE id = $1
            RETURNING id, user_id, campaign_id, application_id, reward_type, amount, 
                      transaction_id, status, issued_at, delivered_at
        """
        row = await self.fetch_one(query, reward_id, RewardStatus.FAILED, issued_at)
        return self._map_row_to_entity(row) if row else None

    async def get_by_application_id(self, application_id: UUID) -> Reward | None:
        """Возвращает запись о награде для конкретной заявки."""
        query = f"""
            SELECT id, user_id, campaign_id, application_id, reward_type, amount, 
                   transaction_id, status, issued_at, delivered_at
            FROM {DatabaseTables.REWARDS}
            WHERE application_id = $1
        """
        row = await self.fetch_one(query, application_id)
        return self._map_row_to_entity(row) if row else None

    async def check_idempotency(self, application_id: UUID) -> bool:
        """Проверяет, была ли уже успешно выдана награда за эту заявку.
        Возвращает True, если награда уже в статусе ISSUED.
        Это защита от повторного начисления при повторном нажатии кнопки модератором.
        """
        query = f"""
            SELECT 1 
            FROM {DatabaseTables.REWARDS}
            WHERE application_id = $1 AND status = $2
        """
        result = await self.fetch_val(query, application_id, RewardStatus.ISSUED)
        return result is not None

    async def get_user_history(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[Reward]:
        """Возвращает историю наград пользователя для личного кабинета."""
        query = f"""
            SELECT id, user_id, campaign_id, application_id, reward_type, amount, 
                   transaction_id, status, issued_at, delivered_at
            FROM {DatabaseTables.REWARDS}
            WHERE user_id = $1
            ORDER BY issued_at DESC NULLS LAST
            LIMIT $2 OFFSET $3
        """
        rows = await self.fetch_all(query, user_id, limit, offset)
        return [self._map_row_to_entity(row) for row in rows]

    @staticmethod
    def _map_row_to_entity(row: dict[str, Any]) -> Reward:
        """Преобразует словарь из БД в доменную сущность Reward."""
        return Reward(
            id=row["id"],
            user_id=row["user_id"],
            campaign_id=row["campaign_id"],
            application_id=row["application_id"],
            reward_type=row["reward_type"],
            amount=row["amount"],
            transaction_id=row["transaction_id"],
            status=row["status"],
            issued_at=row["issued_at"],
            delivered_at=row["delivered_at"],
        )