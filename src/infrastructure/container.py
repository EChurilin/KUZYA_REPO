from asyncpg.pool import Pool
from redis.asyncio import Redis

from src.config.settings import settings
from src.integrations.database.connection import init_db_pool, close_db_pool
from src.integrations.cache.redis_client import init_redis, close_redis
from src.integrations.rewards.stub_issuer import StubRewardIssuer

from src.repositories.user_repo import UserRepository
from src.repositories.campaign_repo import CampaignRepository
from src.repositories.application_repo import ApplicationRepository
from src.repositories.reward_repo import RewardRepository
from src.repositories.ticket_repo import TicketRepository
from src.repositories.audit_repo import AuditRepository

from src.services.user_service import UserService
from src.services.application_service import ApplicationService
from src.services.review_service import ReviewService
from src.services.support_service import SupportService
from src.utils.logger import logger


class Container:
    """Контейнер зависимостей (Dependency Injection).
    Управляет жизненным циклом подключений к БД/Redis и создает экземпляры
    репозиториев и сервисов, связывая их друг с другом.
    """

    def __init__(self) -> None:
        self.settings = settings
        self.db_pool: Pool | None = None
        self.redis_client: Redis | None = None

        self.user_repo: UserRepository | None = None
        self.campaign_repo: CampaignRepository | None = None
        self.app_repo: ApplicationRepository | None = None
        self.reward_repo: RewardRepository | None = None
        self.ticket_repo: TicketRepository | None = None
        self.audit_repo: AuditRepository | None = None

        self.user_service: UserService | None = None
        self.app_service: ApplicationService | None = None
        self.review_service: ReviewService | None = None
        self.support_service: SupportService | None = None

    async def init(self) -> None:
        """Инициализирует подключения и создает граф зависимостей."""
        logger.info("Initializing application container...")
        self.db_pool = await init_db_pool()
        self.redis_client = await init_redis()

        self.user_repo = UserRepository(self.db_pool)
        self.campaign_repo = CampaignRepository(self.db_pool)
        self.app_repo = ApplicationRepository(self.db_pool)
        self.reward_repo = RewardRepository(self.db_pool)
        self.ticket_repo = TicketRepository(self.db_pool)
        self.audit_repo = AuditRepository(self.db_pool)

        self.user_service = UserService(self.user_repo)
        self.app_service = ApplicationService(
            app_repo=self.app_repo,
            campaign_repo=self.campaign_repo,
            audit_repo=self.audit_repo,
        )
        self.review_service = ReviewService(
            app_repo=self.app_repo,
            campaign_repo=self.campaign_repo,
            reward_repo=self.reward_repo,
            audit_repo=self.audit_repo,
            reward_issuer=StubRewardIssuer(),
        )
        self.support_service = SupportService(
            ticket_repo=self.ticket_repo,
            audit_repo=self.audit_repo,
        )
        logger.info("Application container initialized.")

    async def shutdown(self) -> None:
        """Безопасно закрывает все внешние подключения."""
        logger.info("Shutting down application container...")
        if self.db_pool:
            await close_db_pool(self.db_pool)
        if self.redis_client:
            await close_redis(self.redis_client)