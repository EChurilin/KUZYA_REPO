import uuid
from typing import Optional

from src.core.exceptions import SessionNotFoundError
from src.core.interfaces import (
    ApplicationRepository,
    ScreenshotRepository,
)
from src.services.user_balance_service import UserBalanceService
from src.services.settings_service import SettingsService
from src.services.notification_service import NotificationService


class ReviewService:
    """Сервис модерации заявок: одобрение/отклонение скриншотов и финализация."""

    def __init__(
        self,
        app_repo: ApplicationRepository,
        screenshot_repo: ScreenshotRepository,
        user_balance_service: UserBalanceService,
        settings_service: SettingsService,
        notification_service: NotificationService,
    ):
        self._app_repo = app_repo
        self._screenshot_repo = screenshot_repo
        self._user_balance_service = user_balance_service
        self._settings_service = settings_service
        self._notification_service = notification_service

    async def approve_screenshot(self, screenshot_id: uuid.UUID, moderator_id: int) -> None:
        """Одобряет конкретный скриншот."""
        await self._screenshot_repo.update_status(screenshot_id, "approved")

    async def reject_screenshot(self, screenshot_id: uuid.UUID, moderator_id: int) -> None:
        """Отклоняет конкретный скриншот."""
        await self._screenshot_repo.update_status(screenshot_id, "rejected")

    async def reset_screenshot(self, screenshot_id: uuid.UUID) -> None:
        """Возвращает скриншот в состояние 'на проверке' (для «Изменить решение»)."""
        await self._screenshot_repo.update_status(screenshot_id, "pending")

    async def get_screenshots_summary(self, application_id: uuid.UUID) -> dict:
        """Возвращает сводку по скриншотам заявки.

        Возвращает словарь:
        - approved: количество одобренных
        - rejected: количество отклонённых
        - pending: количество на проверке
        - total: всего скриншотов
        - amount_to_credit: сумма к начислению (одобренные × цена)
        """
        screenshots = await self._screenshot_repo.get_by_application(application_id)
        approved = sum(1 for s in screenshots if s.status == "approved")
        rejected = sum(1 for s in screenshots if s.status == "rejected")
        pending = sum(1 for s in screenshots if s.status == "pending")
        total = len(screenshots)
        price = await self._settings_service.get_screenshot_price()
        amount_to_credit = approved * price
        return {
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "total": total,
            "amount_to_credit": amount_to_credit,
        }

    async def all_screenshots_reviewed(self, application_id: uuid.UUID) -> bool:
        """Возвращает True, если все скриншоты заявки оценены (нет 'на проверке')."""
        summary = await self.get_screenshots_summary(application_id)
        return summary["pending"] == 0 and summary["total"] > 0

    async def finalize_application(
        self,
        application_id: uuid.UUID,
        moderator_id: int,
        comment: Optional[str] = None,
    ) -> int:
        """
        Финализирует заявку: считает одобренные скриншоты, начисляет звёзды
        на внутренний баланс пользователя и отправляет уведомление.
        Возвращает сумму начисленных звёзд.
        Идемпотентно: повторная финализация не начисляет повторно.
        """
        # 1. Получаем заявку
        app = await self._app_repo.get_by_id(application_id)
        if not app:
            raise SessionNotFoundError("Заявка не найдена.")

        # 2. Идемпотентность: если уже вознаграждена, не начисляем повторно
        if app.status == "rewarded":
            return 0

        # 3. Считаем одобренные скриншоты
        screenshots = await self._screenshot_repo.get_by_application(application_id)
        approved_count = sum(1 for s in screenshots if s.status == "approved")

        # 4. Определяем статус заявки
        if approved_count == 0:
            app_status = "rejected"
        else:
            app_status = "approved"

        # 5. Обновляем статус заявки и счётчик одобренных
        await self._app_repo.update_status(
            application_id=application_id,
            status=app_status,
            reviewed_by=moderator_id,
            moderator_comment=comment,
            approved_count=approved_count,
        )

        # 6. Если есть одобренные скриншоты — начисляем баланс
        if approved_count > 0:
            price = await self._settings_service.get_screenshot_price()
            total_amount = approved_count * price

            await self._user_balance_service.credit_from_application(
                user_id=app.user_id,
                application_id=application_id,
                approved_count=approved_count,
                price_per_screenshot=price,
            )

            await self._app_repo.mark_rewarded(application_id)

            await self._notification_service.notify_user(
                user_id=app.user_id,
                text=f"Ваша заявка одобрена. Начислено звёзд: {total_amount}.",
            )

            return total_amount

        # 7. Если одобренных нет — уведомляем об отклонении
        await self._notification_service.notify_user(
            user_id=app.user_id,
            text="Ваши скриншоты не прошли модерацию.",
        )
        return 0
