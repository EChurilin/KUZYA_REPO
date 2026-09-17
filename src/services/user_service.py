from typing import Optional
from datetime import datetime
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
        now = datetime.utcnow()
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