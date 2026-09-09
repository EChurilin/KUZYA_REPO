import json
from typing import Any

from src.config.constants import DatabaseTables
from src.repositories.base import BaseRepository


class AuditRepository(BaseRepository):
    """Репозиторий для записи и чтения журнала аудита."""

    async def log_action(
        self,
        entity_type: str,
        entity_id: str | int,
        actor_id: int,
        action: str,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
    ) -> None:
        """Записывает новое действие в журнал аудита."""
        query = f"""
            INSERT INTO {DatabaseTables.AUDIT_LOG}
            (entity_type, entity_id, actor_id, action, old_values, new_values, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """
        # Сериализуем словари в JSON-строки. 
        # default=str страховка на случай, если в словаре попадется UUID или datetime.
        old_json = json.dumps(old_values, default=str) if old_values else None
        new_json = json.dumps(new_values, default=str) if new_values else None
        
        await self.execute(
            query,
            entity_type,
            str(entity_id),
            actor_id,
            action,
            old_json,
            new_json,
        )

    async def get_history_for_entity(
        self, entity_type: str, entity_id: str | int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Возвращает историю изменений для конкретной сущности (например, заявки)."""
        query = f"""
            SELECT id, entity_type, entity_id, actor_id, action, 
                   old_values, new_values, created_at
            FROM {DatabaseTables.AUDIT_LOG}
            WHERE entity_type = $1 AND entity_id = $2
            ORDER BY created_at DESC
            LIMIT $3
        """
        return await self.fetch_all(query, entity_type, str(entity_id), limit)

    async def get_history_for_actor(
        self, actor_id: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Возвращает историю действий конкретного модератора/админа."""
        query = f"""
            SELECT id, entity_type, entity_id, actor_id, action, 
                   old_values, new_values, created_at
            FROM {DatabaseTables.AUDIT_LOG}
            WHERE actor_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        return await self.fetch_all(query, actor_id, limit)