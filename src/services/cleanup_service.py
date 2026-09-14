import uuid
from datetime import datetime, timezone
from typing import Tuple

from src.config.constants import (
    SESSION_TIMEOUT_HOURS,
    SCREENSHOT_RETENTION_DAYS,
    APPLICATION_STATUS_PENDING_REVIEW,
)
from src.core.entities import Application
from src.core.interfaces import (
    SessionRepository,
    ScreenshotRepository,
    ApplicationRepository,
)
from src.integrations.storage.local_storage import LocalScreenshotStorage


class CleanupService:
    def __init__(
        self,
        session_repo: SessionRepository,
        screenshot_repo: ScreenshotRepository,
        app_repo: ApplicationRepository,
        storage: LocalScreenshotStorage,
    ):
        self._session_repo = session_repo
        self._screenshot_repo = screenshot_repo
        self._app_repo = app_repo
        self._storage = storage

    async def process_expired_sessions(self) -> int:
        """
        Находит сессии, неактивные более SESSION_TIMEOUT_HOURS,
        закрывает их и автоматически создаёт заявку с пометкой auto_closed.
        Возвращает количество обработанных сессий.
        """
        sessions = await self._session_repo.get_expired_active_sessions(SESSION_TIMEOUT_HOURS)
        processed_count = 0

        for session in sessions:
            try:
                # 1. Закрываем сессию как истёкшую
                await self._session_repo.close_session(session.id, "expired")

                # 2. Получаем скриншоты для подсчёта
                screenshots = await self._screenshot_repo.get_by_session(session.id)
                actual_count = len(screenshots)

                # 3. Создаём заявку с пометкой auto_closed
                now = datetime.now(timezone.utc)
                application = Application(
                    id=uuid.uuid4(),
                    user_id=session.user_id,
                    session_id=session.id,
                    campaign_id=None,
                    status=APPLICATION_STATUS_PENDING_REVIEW,
                    actual_screenshot_count=actual_count,
                    approved_screenshot_count=0,
                    moderator_comment="Сессия закрыта автоматически из-за неактивности (24ч).",
                    submitted_at=now,
                    reviewed_at=None,
                    rewarded_at=None,
                    reviewed_by=None,
                    auto_closed=True,
                )
                await self._app_repo.create(application)

                # 4. Привязываем скриншоты к заявке
                if actual_count > 0:
                    await self._screenshot_repo.link_to_application(session.id, application.id)

                processed_count += 1
            except Exception:
                # Логируем ошибку, но продолжаем обработку остальных сессий
                # В реальном проекте здесь должен быть вызов logger.error(...)
                continue

        return processed_count

    async def cleanup_old_screenshots(self) -> Tuple[int, int]:
        """
        Удаляет файлы скриншотов старше SCREENSHOT_RETENTION_DAYS дней
        из завершённых/истёкших сессий и удаляет записи из БД.
        Возвращает кортеж: (количество удалённых файлов, количество ошибок).
        """
        screenshots = await self._screenshot_repo.get_old_screenshots_for_cleanup(SCREENSHOT_RETENTION_DAYS)
        deleted_count = 0
        error_count = 0

        for screenshot in screenshots:
            try:
                # Удаляем файл с диска
                self._storage.delete_file(screenshot.storage_path)
                # Удаляем запись из БД
                await self._screenshot_repo.delete(screenshot.id)
                deleted_count += 1
            except Exception:
                error_count += 1
                continue

        return deleted_count, error_count