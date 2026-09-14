from typing import Protocol, List, Optional
from datetime import datetime
import uuid
from src.core.entities import (
    Game, InstructionBlock, Session, ApplicationScreenshot,
    BalanceSnapshot, Application, Reward,
)


class GameRepository(Protocol):
    async def get_all_active(self) -> List[Game]:
        ...

    async def get_by_id(self, game_id: uuid.UUID) -> Optional[Game]:
        ...

    async def create(self, game: Game) -> None:
        ...

    async def update(self, game: Game) -> None:
        ...

    async def delete(self, game_id: uuid.UUID) -> None:
        ...


class InstructionBlockRepository(Protocol):
    async def get_all_active_ordered(self) -> List[InstructionBlock]:
        ...

    async def get_by_id(self, block_id: uuid.UUID) -> Optional[InstructionBlock]:
        ...

    async def get_max_order(self) -> int:
        ...

    async def create(self, block: InstructionBlock) -> None:
        ...

    async def update(self, block: InstructionBlock) -> None:
        ...

    async def delete(self, block_id: uuid.UUID) -> None:
        ...


class SessionRepository(Protocol):
    async def create(self, session: Session) -> None:
        ...

    async def get_by_id(self, session_id: uuid.UUID) -> Optional[Session]:
        ...

    async def get_active_by_user(self, user_id: int) -> Optional[Session]:
        ...

    async def update_last_screenshot(self, session_id: uuid.UUID, timestamp: datetime) -> None:
        ...

    async def close_session(self, session_id: uuid.UUID, status: str) -> None:
        ...

    async def get_expired_active_sessions(self, timeout_hours: int) -> List[Session]:
        ...


class ScreenshotRepository(Protocol):
    async def create(self, screenshot: ApplicationScreenshot) -> None:
        ...

    async def get_by_session(self, session_id: uuid.UUID) -> List[ApplicationScreenshot]:
        ...

    async def get_by_application(self, application_id: uuid.UUID) -> List[ApplicationScreenshot]:
        ...

    async def get_by_id(self, screenshot_id: uuid.UUID) -> Optional[ApplicationScreenshot]:
        ...

    async def update_status(self, screenshot_id: uuid.UUID, status: str) -> None:
        ...

    async def link_to_application(self, session_id: uuid.UUID, application_id: uuid.UUID) -> None:
        ...

    async def get_old_screenshots_for_cleanup(self, retention_days: int) -> List[ApplicationScreenshot]:
        ...

    async def delete(self, screenshot_id: uuid.UUID) -> None:
        ...


class BalanceRepository(Protocol):
    async def save_snapshot(self, snapshot: BalanceSnapshot) -> None:
        ...

    async def get_latest(self, reward_type: str) -> Optional[BalanceSnapshot]:
        ...


class ApplicationRepository(Protocol):
    async def create(self, application: Application) -> None:
        ...

    async def get_by_id(self, application_id: uuid.UUID) -> Optional[Application]:
        ...

    async def get_pending_review(self, limit: int = 50) -> List[Application]:
        ...

    async def update_status(
        self,
        application_id: uuid.UUID,
        status: str,
        reviewed_by: Optional[int],
        moderator_comment: Optional[str],
        approved_count: int,
    ) -> None:
        ...

    async def mark_rewarded(self, application_id: uuid.UUID) -> None:
        ...

    async def get_by_user(self, user_id: int, limit: int = 20) -> List[Application]:
        ...

    async def count_today_by_user(self, user_id: int) -> int:
        ...


class RewardRepository(Protocol):
    async def create(self, reward: Reward) -> None:
        ...

    async def get_by_id(self, reward_id: uuid.UUID) -> Optional[Reward]:
        ...

    async def get_by_application(self, application_id: uuid.UUID) -> Optional[Reward]:
        ...

    async def update_status(
        self, reward_id: uuid.UUID, status: str, transaction_id: Optional[str]
    ) -> None:
        ...