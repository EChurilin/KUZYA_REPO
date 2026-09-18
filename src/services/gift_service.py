import uuid
from datetime import datetime, timezone
from typing import List

from src.core.entities import Gift, GiftClaim
from src.core.exceptions import (
    GiftNotFoundError,
    InsufficientBotBalanceError,
    InsufficientUserBalanceError,
)
from src.core.interfaces import GiftClaimRepository
from src.integrations.rewards.gift_issuer import GiftIssuer
from src.services.balance_service import BalanceService
from src.services.user_balance_service import UserBalanceService


class GiftService:
    """Сервис для оркестрации получения подарков пользователями."""

    def __init__(
        self,
        gift_issuer: GiftIssuer,
        gift_claim_repo: GiftClaimRepository,
        user_balance_service: UserBalanceService,
        balance_service: BalanceService,
    ):
        self._gift_issuer = gift_issuer
        self._gift_claim_repo = gift_claim_repo
        self._user_balance_service = user_balance_service
        self._balance_service = balance_service

    async def get_available_gifts(self) -> List[Gift]:
        """Возвращает список всех доступных подарков из Telegram."""
        return await self._gift_issuer.get_available_gifts()

    async def get_affordable_gifts(self, user_id: int) -> List[Gift]:
        """Возвращает подарки, которые пользователь может получить по своему внутреннему балансу."""
        user_balance = await self._user_balance_service.get_balance(user_id)
        all_gifts = await self._gift_issuer.get_available_gifts()
        return [g for g in all_gifts if g.star_count <= user_balance]

    async def claim_gift(self, user_id: int, gift_id: str) -> GiftClaim:
        """
        Оркестрирует получение подарка пользователем:
        1. Находит подарок в списке доступных.
        2. Проверяет внутренний баланс пользователя.
        3. Проверяет реальный баланс бота.
        4. Создаёт GiftClaim со статусом 'pending'.
        5. Отправляет подарок через Telegram API.
        6. Списывает стоимость подарка с внутреннего баланса пользователя.
        7. Обновляет статус GiftClaim на 'sent'.
        """
        # 1. Находим подарок
        all_gifts = await self._gift_issuer.get_available_gifts()
        gift = next((g for g in all_gifts if g.id == gift_id), None)
        if gift is None:
            raise GiftNotFoundError(f"Подарок {gift_id} не найден.")

        # 2. Проверяем внутренний баланс пользователя
        user_balance = await self._user_balance_service.get_balance(user_id)
        if user_balance < gift.star_count:
            raise InsufficientUserBalanceError(
                f"Недостаточно звёзд. Требуется: {gift.star_count}, доступно: {user_balance}"
            )

        # 3. Проверяем реальный баланс бота
        bot_balance = await self._balance_service.get_current_balance()
        if bot_balance < gift.star_count:
            raise InsufficientBotBalanceError(
                f"Недостаточно звёзд на балансе бота. Требуется: {gift.star_count}, доступно: {bot_balance}"
            )

        # 4. Создаём GiftClaim со статусом 'pending'
        now = datetime.now(timezone.utc)
        claim = GiftClaim(
            id=uuid.uuid4(),
            user_id=user_id,
            gift_id=gift_id,
            gift_name=None,
            star_count=gift.star_count,
            status="pending",
            telegram_charge_id=None,
            created_at=now,
            sent_at=None,
        )
        await self._gift_claim_repo.create(claim)

        # 5. Отправляем подарок через Telegram API
        try:
            await self._gift_issuer.send_gift(user_id=user_id, gift_id=gift_id)
        except Exception:
            await self._gift_claim_repo.update_status(claim.id, "failed", None)
            raise

        # 6. Списываем стоимость подарка с внутреннего баланса пользователя
        await self._user_balance_service.debit_for_gift(user_id, claim.id, gift.star_count)

        # 7. Обновляем статус GiftClaim на 'sent'
        await self._gift_claim_repo.update_status(claim.id, "sent", None)

        claim.status = "sent"
        return claim