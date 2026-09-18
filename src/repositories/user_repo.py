from typing import Optional
import asyncpg
from src.core.entities import User
from src.repositories.base import BaseRepository


class UserRepositoryImpl(BaseRepository):
    async def get_by_id(self, user_id: int) -> Optional[User]:
        row = await self.fetchone(
            "SELECT id, username, first_name, language_code, role, created_at, updated_at, "
            "star_balance, instruction_passed, last_instruction_message_id "
            "FROM users WHERE id = $1",
            user_id
        )
        return self._row_to_user(row) if row else None

    async def create(self, user: User) -> None:
        # Новые колонки (star_balance, instruction_passed, last_instruction_message_id)
        # получают значения по умолчанию из БД при создании пользователя.
        await self.execute(
            """
            INSERT INTO users (id, username, first_name, language_code, role, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            user.id, user.username, user.first_name, user.language_code,
            user.role, user.created_at, user.updated_at
        )

    async def update(self, user: User) -> None:
        await self.execute(
            """
            UPDATE users
            SET username = $1, first_name = $2, language_code = $3, role = $4, updated_at = $5
            WHERE id = $6
            """,
            user.username, user.first_name, user.language_code,
            user.role, user.updated_at, user.id
        )

    async def update_star_balance(self, user_id: int, new_balance: int) -> None:
        await self.execute(
            "UPDATE users SET star_balance = $2, updated_at = NOW() WHERE id = $1",
            user_id, new_balance
        )

    async def set_instruction_passed(self, user_id: int, passed: bool) -> None:
        await self.execute(
            "UPDATE users SET instruction_passed = $2, updated_at = NOW() WHERE id = $1",
            user_id, passed
        )

    async def set_last_instruction_message_id(self, user_id: int, message_id: Optional[int]) -> None:
        await self.execute(
            "UPDATE users SET last_instruction_message_id = $2, updated_at = NOW() WHERE id = $1",
            user_id, message_id
        )

    def _row_to_user(self, row: asyncpg.Record) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            first_name=row["first_name"],
            language_code=row["language_code"],
            role=row["role"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            star_balance=row["star_balance"],
            instruction_passed=row["instruction_passed"],
            last_instruction_message_id=row["last_instruction_message_id"],
        )