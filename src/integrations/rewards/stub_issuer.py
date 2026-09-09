from src.core.interfaces import RewardResult
from src.utils.logger import logger


class StubRewardIssuer:
    """Заглушка для выдачи наград.
    Используется, пока не реализована реальная интеграция с Telegram Stars API.
    Всегда возвращает успех и фейковый transaction_id.
    """

    async def issue(self, user_id: int, reward_type: str, amount: int) -> RewardResult:
        logger.info(f"[STUB] Issuing {amount} {reward_type} to user {user_id}")
        return RewardResult(
            is_success=True,
            transaction_id=f"stub_tx_{user_id}_{amount}",
            error_message=None,
        )