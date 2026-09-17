import uuid
from datetime import datetime, timezone
from pathlib import Path
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
    GameRepository,
    InstructionBlockRepository,
)
from src.integrations.storage.local_storage import LocalScreenshotStorage


class CleanupService:
    def __init__(
        self,
        session_repo: SessionRepository,
        screenshot_repo: ScreenshotRepository,
        app_repo: ApplicationRepository,
        storage: LocalScreenshotStorage,
        game_repo: GameRepository,
        instruction_repo: InstructionBlockRepository,
    ):
        self._session_repo = session_repo
        self._screenshot_repo = screenshot_repo
        self._app_repo = app_repo
        self._storage = storage
        self._game_repo = game_repo
        self._instruction_repo = instruction_repo

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
                await self._session_repo.close_session(session.id, "expired")

                screenshots = await self._screenshot_repo.get_by_session(session.id)
                actual_count = len(screenshots)

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

                if actual_count > 0:
                    await self._screenshot_repo.link_to_application(session.id, application.id)

                processed_count += 1
            except Exception:
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
                self._storage.delete_file(screenshot.storage_path)
                await self._screenshot_repo.delete(screenshot.id)
                deleted_count += 1
            except Exception:
                error_count += 1
                continue

        return deleted_count, error_count

    async def cleanup_old_games(self, hours: int = 36) -> Tuple[int, int]:
        """
        Удаляет файлы фото деактивированных игр старше N часов
        и удаляет записи из БД.
        Возвращает кортеж: (количество удалённых игр, количество ошибок).
        """
        games = await self._game_repo.get_old_deactivated_games(hours)
        deleted_count = 0
        error_count = 0

        for game in games:
            try:
                if game.photo_path:
                    file_path = Path(game.photo_path)
                    if file_path.exists():
                        file_path.unlink()
                await self._game_repo.delete(game.id)
                deleted_count += 1
            except Exception:
                error_count += 1
                continue

        return deleted_count, error_count

    async def cleanup_old_instruction_versions(self, hours: int = 24) -> Tuple[int, int]:
        """
        Удаляет файлы медиа старых опубликованных блоков инструкции,
        не являющихся текущей версией, старше N часов,
        и удаляет записи из БД.
        Возвращает кортеж: (количество удалённых блоков, количество ошибок).
        """
        blocks = await self._instruction_repo.get_old_published_blocks(hours)
        deleted_count = 0
        error_count = 0

        for block in blocks:
            try:
                if block.media_path:
                    file_path = Path(block.media_path)
                    if file_path.exists():
                        file_path.unlink()
                await self._instruction_repo.delete(block.id)
                deleted_count += 1
            except Exception:
                error_count += 1
                continue

        return deleted_count, error_count