import uuid
import time
from datetime import datetime, timezone
from src.config.constants import BALANCE_CACHE_TTL_SECONDS
from src.core.entities import BalanceSnapshot
from src.core.interfaces import BalanceRepository
from src.integrations.rewards.stub_issuer import StubRewardIssuer


class BalanceService:
    def __init__(self, balance_repo: BalanceRepository, reward_issuer: StubRewardIssuer):
        self._balance_repo = balance_repo
        self._reward_issuer = reward_issuer

    async def get_current_balance(self, reward_type: str) -> int:
        """
        Возвращает актуальный баланс.
        Если последний снапшот в БД новее, чем TTL кэша, берем его.
        Иначе запрашиваем у Telegram (через issuer) и сохраняем новый снапшот.
        """
        snapshot = await self._balance_repo.get_latest(reward_type)
        now_ts = time.time()
        
        if snapshot and (now_ts - snapshot.fetched_at.timestamp()) < BALANCE_CACHE_TTL_SECONDS:
            return snapshot.balance
            
        # Снапшот устарел или отсутствует, запрашиваем свежий баланс
        balance = await self._reward_issuer.get_balance(reward_type)
        
        new_snapshot = BalanceSnapshot(
            id=uuid.uuid4(),
            reward_type=reward_type,
            balance=balance,
            fetched_at=datetime.now(timezone.utc),
        )
        await self._balance_repo.save_snapshot(new_snapshot)
        return balance