import uuid
from datetime import datetime, timezone
from typing import Optional

from src.core.entities import Reward, ApplicationScreenshot
from src.core.interfaces import (
    ApplicationRepository,
    ScreenshotRepository,
    RewardRepository,
)
from src.core.exceptions import RewardBalanceInsufficientError, SessionNotFoundError
from src.services.balance_service import BalanceService
from src.integrations.rewards.stub_issuer import StubRewardIssuer


class ReviewService:
    def __init__(
        self,
        app_repo: ApplicationRepository,
        screenshot_repo: ScreenshotRepository,
        reward_repo: RewardRepository,
        balance_service: BalanceService,
        reward_issuer: StubRewardIssuer,
    ):
        self._app_repo = app_repo
        self._screenshot_repo = screenshot_repo
        self._reward_repo = reward_repo
        self._balance_service = balance_service
        self._reward_issuer = reward_issuer

    async def approve_screenshot(self, screenshot_id: uuid.UUID, moderator_id: int) -> None:
        """Одобряет конкретный скриншот."""
        await self._screenshot_repo.update_status(screenshot_id, "approved")

    async def reject_screenshot(self, screenshot_id: uuid.UUID, moderator_id: int) -> None:
        """Отклоняет конкретный скриншот."""
        await self._screenshot_repo.update_status(screenshot_id, "rejected")

    async def finalize_application(
        self,
        application_id: uuid.UUID,
        moderator_id: int,
        reward_type: str,
        reward_amount_per_screenshot: int,
        comment: Optional[str] = None,
    ) -> Reward:
        """
        Финализирует заявку: считает одобренные скриншоты, проверяет баланс,
        создает запись о награде и обновляет статус заявки.
        """
        # 1. Получаем заявку и её скриншоты
        app = await self._app_repo.get_by_id(application_id)
        if not app:
            raise SessionNotFoundError("Заявка не найдена.")

        screenshots = await self._screenshot_repo.get_by_application(application_id)
        approved_count = sum(1 for s in screenshots if s.status == "approved")

        # 2. Обновляем статус заявки и счетчик одобренных
        if approved_count == 0:
            app_status = "rejected"
        else:
            app_status = "approved"

        await self._app_repo.update_status(
            application_id=application_id,
            status=app_status,
            reviewed_by=moderator_id,
            moderator_comment=comment,
            approved_count=approved_count,
        )

        # 3. Если есть одобренные скриншоты, выдаем награду
        if approved_count > 0:
            total_reward_amount = approved_count * reward_amount_per_screenshot

            # Проверка баланса
            current_balance = await self._balance_service.get_current_balance(reward_type)
            if current_balance < total_reward_amount:
                raise RewardBalanceInsufficientError(
                    f"Недостаточно средств на балансе. Требуется: {total_reward_amount}, доступно: {current_balance}"
                )

            # Выдача награды через issuer (заглушка или реальный API)
            transaction_id = await self._reward_issuer.issue_reward(
                user_id=app.user_id,
                reward_type=reward_type,
                amount=total_reward_amount,
            )

            # Создаем запись о награде в БД
            now = datetime.now(timezone.utc)
            reward = Reward(
                id=uuid.uuid4(),
                user_id=app.user_id,
                application_id=application_id,
                reward_type=reward_type,
                amount=total_reward_amount,
                transaction_id=transaction_id,
                status="issued",
                issued_at=now,
                delivered_at=now,
            )
            await self._reward_repo.create(reward)

            # Помечаем заявку как выданную
            await self._app_repo.mark_rewarded(application_id)

            return reward

        # Если одобренных скриншотов нет, возвращаем None или пустую заглушку
        return None