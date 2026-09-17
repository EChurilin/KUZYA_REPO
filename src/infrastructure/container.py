from dataclasses import dataclass

from src.config.settings import settings
from src.integrations.database.connection import get_pool
from src.integrations.storage.local_storage import LocalScreenshotStorage
from src.integrations.rewards.stub_issuer import StubRewardIssuer

from src.repositories.game_repo import GameRepositoryImpl
from src.repositories.instruction_block_repo import InstructionBlockRepositoryImpl
from src.repositories.session_repo import SessionRepositoryImpl
from src.repositories.screenshot_repo import ScreenshotRepositoryImpl
from src.repositories.balance_repo import BalanceRepositoryImpl
from src.repositories.application_repo import ApplicationRepositoryImpl
from src.repositories.reward_repo import RewardRepositoryImpl

from src.services.game_service import GameService
from src.services.instruction_service import InstructionService
from src.services.balance_service import BalanceService
from src.services.session_service import SessionService
from src.services.application_service import ApplicationService
from src.services.review_service import ReviewService
from src.services.cleanup_service import CleanupService


@dataclass
class Container:
    """
    DI-контейнер. Собирает все репозитории и сервисы.
    Боты получают отсюда готовые сервисы.
    """
    game_service: GameService
    instruction_service: InstructionService
    balance_service: BalanceService
    session_service: SessionService
    application_service: ApplicationService
    review_service: ReviewService
    cleanup_service: CleanupService


def build_container() -> Container:
    """Создаёт и возвращает полностью собранный контейнер."""
    pool = get_pool()

    # Репозитории
    game_repo = GameRepositoryImpl(pool)
    instruction_repo = InstructionBlockRepositoryImpl(pool)
    session_repo = SessionRepositoryImpl(pool)
    screenshot_repo = ScreenshotRepositoryImpl(pool)
    balance_repo = BalanceRepositoryImpl(pool)
    app_repo = ApplicationRepositoryImpl(pool)
    reward_repo = RewardRepositoryImpl(pool)

    # Инфраструктура
    storage = LocalScreenshotStorage(settings.storage.base_path)
    reward_issuer = StubRewardIssuer()

    # Сервисы
    game_service = GameService(game_repo)
    instruction_service = InstructionService(instruction_repo)
    balance_service = BalanceService(balance_repo, reward_issuer)
    session_service = SessionService(session_repo, screenshot_repo, storage)
    application_service = ApplicationService(app_repo, session_repo, screenshot_repo)
    review_service = ReviewService(
        app_repo, screenshot_repo, reward_repo, balance_service, reward_issuer
    )
    cleanup_service = CleanupService(session_repo, screenshot_repo, app_repo, storage)

    return Container(
        game_service=game_service,
        instruction_service=instruction_service,
        balance_service=balance_service,
        session_service=session_service,
        application_service=application_service,
        review_service=review_service,
        cleanup_service=cleanup_service,
    )