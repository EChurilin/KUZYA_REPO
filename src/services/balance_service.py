import uuid
import time
from datetime import datetime, timezone
from src.config.constants import BALANCE_CACHE_TTL_SECONDS
from src.core.entities import BalanceSnapshot
from src.core.interfaces import BalanceRepository
from src.integrations.rewards.gift_issuer import GiftIssuer


class BalanceService:
    """Сервис для получения и кэширования реального баланса звёзд бота."""

    def __init__(self, balance_repo: BalanceRepository, gift_issuer: GiftIssuer):
        self._balance_repo = balance_repo
        self._gift_issuer = gift_issuer

    async def get_current_balance(self) -> int:
        """
        Возвращает актуальный баланс звёзд бота.
        Если последний снапшот в БД новее, чем TTL кэша, берём его.
        Иначе запрашиваем у Telegram (через gift_issuer) и сохраняем новый снапшот.
        """
        reward_type = "stars"
        snapshot = await self._balance_repo.get_latest(reward_type)
        now_ts = time.time()

        if snapshot and (now_ts - snapshot.fetched_at.timestamp()) < BALANCE_CACHE_TTL_SECONDS:
            return snapshot.balance

        # Снапшот устарел или отсутствует, запрашиваем свежий баланс
        balance = await self._gift_issuer.get_bot_balance()

        new_snapshot = BalanceSnapshot(
            id=uuid.uuid4(),
            reward_type=reward_type,
            balance=balance,
            fetched_at=datetime.now(timezone.utc),
        )
        await self._balance_repo.save_snapshot(new_snapshot)
        return balance