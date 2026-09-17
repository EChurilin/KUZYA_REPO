import uuid
from datetime import datetime, timezone
from typing import List, Optional

from src.config.constants import (
    MAX_APPLICATIONS_PER_DAY,
    APPLICATION_STATUS_PENDING_REVIEW,
)
from src.core.entities import Application
from src.core.interfaces import ApplicationRepository, SessionRepository, ScreenshotRepository
from src.core.exceptions import ApplicationLimitReachedError, SessionNotFoundError


class ApplicationService:
    def __init__(
        self,
        app_repo: ApplicationRepository,
        session_repo: SessionRepository,
        screenshot_repo: ScreenshotRepository,
    ):
        self._app_repo = app_repo
        self._session_repo = session_repo
        self._screenshot_repo = screenshot_repo

    async def get_user_applications(self, user_id: int, limit: int = 5) -> List[Application]:
        """Возвращает последние заявки пользователя."""
        return await self._app_repo.get_by_user(user_id, limit)

    async def create_from_session(
        self, session_id: uuid.UUID, user_id: int, campaign_id: Optional[uuid.UUID] = None
    ) -> Application:
        # 1. Проверка дневного лимита
        count = await self._app_repo.count_today_by_user(user_id)
        if count >= MAX_APPLICATIONS_PER_DAY:
            raise ApplicationLimitReachedError(
                f"Достигнут лимит {MAX_APPLICATIONS_PER_DAY} заявок в день."
            )

        # 2. Получаем сессию
        session = await self._session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise SessionNotFoundError("Сессия не найдена или не принадлежит пользователю!")

        # 3. Если сессия ещё активна, закрываем её как завершенную
        if session.status == "active":
            await self._session_repo.close_session(session_id, "completed")

        # 4. Получаем все скриншоты сессии
        screenshots = await self._screenshot_repo.get_by_session(session_id)
        actual_count = len(screenshots)

        # 5. Создаем заявку
        now = datetime.now(timezone.utc)
        application = Application(
            id=uuid.uuid4(),
            user_id=user_id,
            session_id=session_id,
            campaign_id=campaign_id,
            status=APPLICATION_STATUS_PENDING_REVIEW,
            actual_screenshot_count=actual_count,
            approved_screenshot_count=0,
            moderator_comment=None,
            submitted_at=now,
            reviewed_at=None,
            rewarded_at=None,
            reviewed_by=None,
            auto_closed=False,
        )
        await self._app_repo.create(application)

        # 6. Привязываем скриншоты к заявке (массовое обновление)
        if actual_count > 0:
            await self._screenshot_repo.link_to_application(session_id, application.id)

        # Возвращаем заявку с прикрепленными скриншотами для удобства
        application.screenshots = screenshots
        return application