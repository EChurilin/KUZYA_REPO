from typing import Protocol, List, Optional
from datetime import datetime
import uuid

from src.core.entities import (
    Game, InstructionBlock, Session, ApplicationScreenshot,
    BalanceSnapshot, Application, Reward, User,
    UserBalanceTransaction, GiftClaim, StarTopup,
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

    async def deactivate_all(self) -> None:
        """Деактивирует все активные игры, проставляя deactivated_at."""
        ...

    async def get_old_deactivated_games(self, hours: int) -> List[Game]:
        """Возвращает деактивированные игры старше N часов для очистки."""
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

    async def get_max_version(self) -> int:
        """Возвращает максимальную версию инструкции."""
        ...

    async def create_draft_block(self, block: InstructionBlock) -> None:
        """Создаёт блок черновика (is_published = False)."""
        ...

    async def publish_version(self, version: int) -> None:
        """Публикует все блоки указанной версии (is_published = True)."""
        ...

    async def get_blocks_by_version(self, version: int) -> List[InstructionBlock]:
        """Возвращает все блоки указанной версии, отсортированные по order."""
        ...

    async def get_current_published_version(self) -> Optional[int]:
        """Возвращает максимальную опубликованную версию."""
        ...

    async def delete_blocks_by_version(self, version: int) -> None:
        """Удаляет все блоки указанной версии (для очистки черновиков)."""
        ...

    async def get_old_published_blocks(self, hours: int) -> List[InstructionBlock]:
        """Возвращает опубликованные блоки, не являющиеся текущей версией, старше N часов."""
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


class UserRepository(Protocol):
    async def get_by_id(self, user_id: int) -> Optional[User]:
        ...

    async def create(self, user: User) -> None:
        ...

    async def update(self, user: User) -> None:
        ...

    async def update_star_balance(self, user_id: int, new_balance: int) -> None:
        """Обновляет внутренний баланс звёзд пользователя."""
        ...

    async def set_instruction_passed(self, user_id: int, passed: bool) -> None:
        """Устанавливает флаг прохождения инструкции."""
        ...

    async def set_last_instruction_message_id(self, user_id: int, message_id: Optional[int]) -> None:
        """Сохраняет message_id последнего блока инструкции."""
        ...


class ReportRepository(Protocol):
    async def get_unique_users_count(self, since: Optional[datetime]) -> int:
        """Количество уникальных пользователей, открывших хотя бы одну сессию за период."""
        ...

    async def get_screenshots_stats(self, since: Optional[datetime]) -> tuple[int, int]:
        """Возвращает (прислано_скриншотов, одобрено_скриншотов) за период."""
        ...

    async def get_top_users_by_screenshots(self, since: Optional[datetime], limit: int = 30) -> List[dict]:
        """Топ пользователей по количеству присланных скриншотов за период."""
        ...

    async def get_stats_by_game(self, since: Optional[datetime]) -> List[dict]:
        """Статистика по играм за период."""
        ...


# --- Новые интерфейсы v4.0 ---


class SettingsRepository(Protocol):
    async def get(self, key: str) -> Optional[str]:
        """Возвращает значение настройки по ключу или None."""
        ...

    async def set(self, key: str, value: str) -> None:
        """Создаёт или обновляет настройку по ключу."""
        ...


class UserBalanceRepository(Protocol):
    async def get_balance(self, user_id: int) -> int:
        """Возвращает текущий внутренний баланс пользователя."""
        ...

    async def credit(
        self, user_id: int, amount: int, reason: str, reference_id: Optional[uuid.UUID]
    ) -> int:
        """Начисляет сумму на внутренний баланс. Возвращает новый баланс."""
        ...

    async def debit(
        self, user_id: int, amount: int, reason: str, reference_id: Optional[uuid.UUID]
    ) -> int:
        """Списывает сумму с внутреннего баланса. Возвращает новый баланс."""
        ...

    async def get_transactions(self, user_id: int, limit: int = 50) -> List[UserBalanceTransaction]:
        """Возвращает последние операции по балансу пользователя."""
        ...


class GiftClaimRepository(Protocol):
    async def create(self, claim: GiftClaim) -> None:
        ...

    async def get_by_id(self, claim_id: uuid.UUID) -> Optional[GiftClaim]:
        ...

    async def update_status(
        self, claim_id: uuid.UUID, status: str, telegram_charge_id: Optional[str]
    ) -> None:
        ...

    async def get_by_user(self, user_id: int, limit: int = 20) -> List[GiftClaim]:
        ...


class TopupRepository(Protocol):
    async def create(self, topup: StarTopup) -> None:
        ...

    async def get_by_id(self, topup_id: uuid.UUID) -> Optional[StarTopup]:
        ...

    async def get_by_payload(self, payload: str) -> Optional[StarTopup]:
        ...

    async def update_status(
        self, topup_id: uuid.UUID, status: str, telegram_payment_charge_id: Optional[str]
    ) -> None:
        ...

    async def set_invoice_message_id(self, topup_id: uuid.UUID, message_id: int) -> None:
        """Сохраняет message_id отправленного инвойса."""
        ...

    async def delete_invoice_message_id(self, topup_id: uuid.UUID) -> None:
        """Обнуляет invoice_message_id после удаления сообщения-инвойса."""
        ...
