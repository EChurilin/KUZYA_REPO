import uuid
from datetime import datetime, timezone
from typing import Tuple

from src.config.constants import (
    MIN_SCREENSHOT_INTERVAL_SECONDS,
    MAX_SCREENSHOTS_PER_SESSION,
    SESSION_STATUS_ACTIVE,
    SESSION_STATUS_COMPLETED,
    SCREENSHOT_STATUS_PENDING,
)
from src.core.entities import Session, ApplicationScreenshot
from src.core.interfaces import SessionRepository, ScreenshotRepository
from src.core.exceptions import (
    SessionAlreadyActiveError,
    SessionNotFoundError,
    ScreenshotIntervalTooShortError,
    ScreenshotLimitReachedError,
)
from src.integrations.storage.local_storage import LocalScreenshotStorage


class SessionService:
    def __init__(
        self,
        session_repo: SessionRepository,
        screenshot_repo: ScreenshotRepository,
        storage: LocalScreenshotStorage,
    ):
        self._session_repo = session_repo
        self._screenshot_repo = screenshot_repo
        self._storage = storage

    async def start_session(self, user_id: int, game_id: uuid.UUID) -> Session:
        active_session = await self._session_repo.get_active_by_user(user_id)
        if active_session:
            raise SessionAlreadyActiveError("У вас уже есть активная сессия. Завершите её или дождитесь истечения.")

        now = datetime.now(timezone.utc)
        session = Session(
            id=uuid.uuid4(),
            user_id=user_id,
            game_id=game_id,
            status=SESSION_STATUS_ACTIVE,
            started_at=now,
            last_screenshot_at=None,
            screenshot_count=0,
            created_at=now,
        )
        await self._session_repo.create(session)
        return session

    async def add_screenshot(
        self,
        session_id: uuid.UUID,
        file_bytes: bytes,
        extension: str,
        client_file_id: str,
    ) -> Tuple[ApplicationScreenshot, int]:
        session = await self._session_repo.get_by_id(session_id)
        if not session or session.status != SESSION_STATUS_ACTIVE:
            raise SessionNotFoundError("Сессия не найдена или уже завершена.")

        now = datetime.now(timezone.utc)
        
        if session.last_screenshot_at:
            diff_seconds = (now - session.last_screenshot_at).total_seconds()
            if diff_seconds < MIN_SCREENSHOT_INTERVAL_SECONDS:
                raise ScreenshotIntervalTooShortError(
                    f"Нельзя переходить по рекламе чаще, чем раз в {MIN_SCREENSHOT_INTERVAL_SECONDS // 60} минут!"
                )

        if session.screenshot_count >= MAX_SCREENSHOTS_PER_SESSION:
            raise ScreenshotLimitReachedError(
                f"Достигнут лимит {MAX_SCREENSHOTS_PER_SESSION} скриншотов в одной сессии. Заберите награду."
            )

        storage_path = self._storage.save_file(file_bytes, extension)

        screenshot = ApplicationScreenshot(
            id=uuid.uuid4(),
            session_id=session_id,
            application_id=None,
            client_file_id=client_file_id,
            storage_path=storage_path,
            status=SCREENSHOT_STATUS_PENDING,
            created_at=now,
        )
        await self._screenshot_repo.create(screenshot)
        await self._session_repo.update_last_screenshot(session_id, now)
        
        return screenshot, session.screenshot_count + 1

    async def close_session(self, session_id: uuid.UUID, status: str = SESSION_STATUS_COMPLETED) -> None:
        session = await self._session_repo.get_by_id(session_id)
        if not session or session.status != SESSION_STATUS_ACTIVE:
            raise SessionNotFoundError("Сессия не найдена или уже завершена.")
            
        await self._session_repo.close_session(session_id, status)