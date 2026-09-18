from typing import Optional
from datetime import datetime, timezone
from src.core.entities import User
from src.core.interfaces import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def get_user(self, user_id: int) -> Optional[User]:
        """Возвращает пользователя по его идентификатору или None."""
        return await self._user_repo.get_by_id(user_id)

    async def get_or_create_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        language_code: Optional[str],
    ) -> User:
        """Возвращает существующего пользователя или создаёт нового с ролью 'user'."""
        user = await self._user_repo.get_by_id(user_id)
        if user is not None:
            return user
        now = datetime.now(timezone.utc)
        new_user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            language_code=language_code,
            role="user",
            created_at=now,
            updated_at=now,
        )
        await self._user_repo.create(new_user)
        return new_user

    async def mark_instruction_passed(self, user_id: int) -> None:
        """Устанавливает флаг 'инструкция пройдена'."""
        await self._user_repo.set_instruction_passed(user_id, True)

    async def save_last_instruction_message_id(self, user_id: int, message_id: int) -> None:
        """Сохраняет message_id последнего блока инструкции."""
        await self._user_repo.set_last_instruction_message_id(user_id, message_id)

    async def clear_last_instruction_message_id(self, user_id: int) -> None:
        """Очищает сохранённый message_id последнего блока инструкции."""
        await self._user_repo.set_last_instruction_message_id(user_id, None)