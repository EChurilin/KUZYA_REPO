from typing import Any

from src.core.entities import User
from src.config.constants import DatabaseTables
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Репозиторий для работы с таблицей пользователей."""

    async def get_by_id(self, user_id: int) -> User | None:
        """Возвращает пользователя по Telegram ID или None."""
        query = f"""
            SELECT id, username, first_name, language_code, role, created_at, updated_at
            FROM {DatabaseTables.USERS}
            WHERE id = $1
        """
        row = await self.fetch_one(query, user_id)
        if not row:
            return None
        return self._map_row_to_entity(row)

    async def create(self, user: User) -> User:
        """Создает нового пользователя в базе данных."""
        query = f"""
            INSERT INTO {DatabaseTables.USERS} 
            (id, username, first_name, language_code, role, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, username, first_name, language_code, role, created_at, updated_at
        """
        row = await self.fetch_one(
            query,
            user.id,
            user.username,
            user.first_name,
            user.language_code,
            user.role,
            user.created_at,
            user.updated_at,
        )
        return self._map_row_to_entity(row)

    async def update(self, user: User) -> User:
        """Обновляет данные существующего пользователя (например, имя или username)."""
        query = f"""
            UPDATE {DatabaseTables.USERS}
            SET username = $2, first_name = $3, language_code = $4, 
                role = $5, updated_at = $6
            WHERE id = $1
            RETURNING id, username, first_name, language_code, role, created_at, updated_at
        """
        row = await self.fetch_one(
            query,
            user.id,
            user.username,
            user.first_name,
            user.language_code,
            user.role,
            user.updated_at,
        )
        return self._map_row_to_entity(row)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """Возвращает список пользователей с пагинацией (для админ-панели)."""
        query = f"""
            SELECT id, username, first_name, language_code, role, created_at, updated_at
            FROM {DatabaseTables.USERS}
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        rows = await self.fetch_all(query, limit, offset)
        return [self._map_row_to_entity(row) for row in rows]

    @staticmethod
    def _map_row_to_entity(row: dict[str, Any]) -> User:
        """Преобразует словарь из БД в доменную сущность User."""
        return User(
            id=row["id"],
            username=row["username"],
            first_name=row["first_name"],
            language_code=row["language_code"],
            role=row["role"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )