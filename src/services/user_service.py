from datetime import datetime, timezone

from src.core.entities import User
from src.core.enums import UserRole
from src.repositories.user_repo import UserRepository
from src.utils.logger import logger


class UserService:
    """Сервис для управления пользователями."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def register_or_update(
        self,
        user_id: int,
        username: str | None,
        first_name: str,
        language_code: str,
    ) -> User:
        """Регистрирует нового пользователя или обновляет данные существующего.
        Вызывается при каждом взаимодействии пользователя с ботом (например, /start).
        """
        existing_user = await self._user_repo.get_by_id(user_id)
        now = datetime.now(timezone.utc)

        if not existing_user:
            logger.info(f"Registering new user: {user_id}")
            new_user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                language_code=language_code,
                role=UserRole.USER,
                created_at=now,
                updated_at=now,
            )
            return await self._user_repo.create(new_user)

        # Обновляем запись в БД только если реальные данные изменились, 
        # чтобы избежать лишних UPDATE-запросов и нагрузки на базу.
        if (
            existing_user.username != username
            or existing_user.first_name != first_name
            or existing_user.language_code != language_code
        ):
            logger.debug(f"Updating user data for: {user_id}")
            existing_user.username = username
            existing_user.first_name = first_name
            existing_user.language_code = language_code
            existing_user.updated_at = now
            return await self._user_repo.update(existing_user)

        return existing_user