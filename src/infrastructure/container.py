from dataclasses import dataclass
from aiogram import Bot

from src.config.settings import settings
from src.integrations.database.connection import get_pool
from src.integrations.storage.local_storage import LocalScreenshotStorage
from src.integrations.rewards.gift_issuer import GiftIssuer
from src.integrations.payments.invoice_sender import InvoiceSender
from src.integrations.media.media_downloader import MediaDownloader

from src.repositories.game_repo import GameRepositoryImpl
from src.repositories.instruction_block_repo import InstructionBlockRepositoryImpl
from src.repositories.session_repo import SessionRepositoryImpl
from src.repositories.screenshot_repo import ScreenshotRepositoryImpl
from src.repositories.balance_repo import BalanceRepositoryImpl
from src.repositories.application_repo import ApplicationRepositoryImpl
from src.repositories.user_repo import UserRepositoryImpl
from src.repositories.report_repo import ReportRepositoryImpl
from src.repositories.settings_repo import SettingsRepositoryImpl
from src.repositories.user_balance_repo import UserBalanceRepositoryImpl
from src.repositories.gift_claim_repo import GiftClaimRepositoryImpl
from src.repositories.topup_repo import TopupRepositoryImpl

from src.services.game_service import GameService
from src.services.instruction_service import InstructionService
from src.services.balance_service import BalanceService
from src.services.session_service import SessionService
from src.services.application_service import ApplicationService
from src.services.review_service import ReviewService
from src.services.cleanup_service import CleanupService
from src.services.user_service import UserService
from src.services.report_service import ReportService
from src.services.settings_service import SettingsService
from src.services.user_balance_service import UserBalanceService
from src.services.gift_service import GiftService
from src.services.topup_service import TopupService
from src.services.notification_service import NotificationService
from src.services.media_service import MediaService


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
    user_service: UserService
    report_service: ReportService
    settings_service: SettingsService
    user_balance_service: UserBalanceService
    gift_service: GiftService
    topup_service: TopupService
    notification_service: NotificationService
    media_service: MediaService


def build_container() -> Container:
    """Создаёт и возвращает полностью собранный контейнер."""
    pool = get_pool()

    client_bot = Bot(token=settings.client_bot.token)
    staff_bot = Bot(token=settings.staff_bot.token)

    # Репозитории
    game_repo = GameRepositoryImpl(pool)
    instruction_repo = InstructionBlockRepositoryImpl(pool)
    session_repo = SessionRepositoryImpl(pool)
    screenshot_repo = ScreenshotRepositoryImpl(pool)
    balance_repo = BalanceRepositoryImpl(pool)
    app_repo = ApplicationRepositoryImpl(pool)
    user_repo = UserRepositoryImpl(pool)
    report_repo = ReportRepositoryImpl(pool)
    settings_repo = SettingsRepositoryImpl(pool)
    user_balance_repo = UserBalanceRepositoryImpl(pool)
    gift_claim_repo = GiftClaimRepositoryImpl(pool)
    topup_repo = TopupRepositoryImpl(pool)

    # Инфраструктура
    storage = LocalScreenshotStorage(settings.storage.base_path)
    gift_issuer = GiftIssuer(client_bot)
    invoice_sender = InvoiceSender(client_bot)
    media_downloader = MediaDownloader(staff_bot)

    # Сервисы
    game_service = GameService(game_repo)
    instruction_service = InstructionService(instruction_repo)
    balance_service = BalanceService(balance_repo, gift_issuer)
    session_service = SessionService(session_repo, screenshot_repo, storage)
    application_service = ApplicationService(app_repo, session_repo, screenshot_repo)

    settings_service = SettingsService(settings_repo)
    user_balance_service = UserBalanceService(user_balance_repo)
    notification_service = NotificationService(client_bot)
    media_service = MediaService(media_downloader, settings.storage.base_path)

    review_service = ReviewService(
        app_repo, screenshot_repo, user_balance_service,
        settings_service, notification_service,
    )

    gift_service = GiftService(
        gift_issuer, gift_claim_repo, user_balance_service, balance_service,
    )
    topup_service = TopupService(topup_repo, invoice_sender, balance_service)

    cleanup_service = CleanupService(
        session_repo, screenshot_repo, app_repo, storage, game_repo, instruction_repo,
    )
    user_service = UserService(user_repo)
    report_service = ReportService(report_repo)

    return Container(
        game_service=game_service,
        instruction_service=instruction_service,
        balance_service=balance_service,
        session_service=session_service,
        application_service=application_service,
        review_service=review_service,
        cleanup_service=cleanup_service,
        user_service=user_service,
        report_service=report_service,
        settings_service=settings_service,
        user_balance_service=user_balance_service,
        gift_service=gift_service,
        topup_service=topup_service,
        notification_service=notification_service,
        media_service=media_service,
    )
