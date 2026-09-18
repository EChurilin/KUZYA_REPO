import uuid
from typing import List

from src.core.entities import UserBalanceTransaction
from src.core.interfaces import UserBalanceRepository


class UserBalanceService:
    """Сервис для работы с внутренним балансом пользователя."""

    def __init__(self, user_balance_repo: UserBalanceRepository):
        self._user_balance_repo = user_balance_repo

    async def get_balance(self, user_id: int) -> int:
        """Возвращает текущий внутренний баланс пользователя."""
        return await self._user_balance_repo.get_balance(user_id)

    async def credit_from_application(
        self,
        user_id: int,
        application_id: uuid.UUID,
        approved_count: int,
        price_per_screenshot: int,
    ) -> int:
        """Начисляет звёзды за одобренные скриншоты. Возвращает новый баланс."""
        amount = approved_count * price_per_screenshot
        return await self._user_balance_repo.credit(
            user_id=user_id,
            amount=amount,
            reason="application_reward",
            reference_id=application_id,
        )

    async def debit_for_gift(
        self,
        user_id: int,
        gift_claim_id: uuid.UUID,
        amount: int,
    ) -> int:
        """Списывает звёзды за подарок. Возвращает новый баланс."""
        return await self._user_balance_repo.debit(
            user_id=user_id,
            amount=amount,
            reason="gift_claim",
            reference_id=gift_claim_id,
        )

    async def get_transactions(
        self, user_id: int, limit: int = 50
    ) -> List[UserBalanceTransaction]:
        """Возвращает последние операции по балансу пользователя."""
        return await self._user_balance_repo.get_transactions(user_id, limit)