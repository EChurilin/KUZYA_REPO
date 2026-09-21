from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from src.infrastructure.container import Container, build_container
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


class TestContainer:
    @patch("src.infrastructure.container.Bot")
    @patch("src.infrastructure.container.get_pool")
    def test_build_container_returns_all_services(self, mock_get_pool, mock_bot_cls, tmp_path):
        mock_get_pool.return_value = AsyncMock()
        mock_bot_cls.return_value = MagicMock()

        with patch("src.infrastructure.container.settings") as mock_settings:
            mock_settings.storage.base_path = str(tmp_path / "storage" / "screenshots")
            mock_settings.client_bot.token = "test_token"
            mock_settings.staff_bot.token = "test_staff_token"

            container = build_container()

            assert isinstance(container, Container)
            assert isinstance(container.game_service, GameService)
            assert isinstance(container.instruction_service, InstructionService)
            assert isinstance(container.balance_service, BalanceService)
            assert isinstance(container.session_service, SessionService)
            assert isinstance(container.application_service, ApplicationService)
            assert isinstance(container.review_service, ReviewService)
            assert isinstance(container.cleanup_service, CleanupService)
            assert isinstance(container.user_service, UserService)
            assert isinstance(container.report_service, ReportService)
            assert isinstance(container.settings_service, SettingsService)
            assert isinstance(container.user_balance_service, UserBalanceService)
            assert isinstance(container.gift_service, GiftService)
            assert isinstance(container.topup_service, TopupService)
            assert isinstance(container.notification_service, NotificationService)
            assert isinstance(container.media_service, MediaService)

    @patch("src.infrastructure.container.Bot")
    @patch("src.infrastructure.container.get_pool")
    def test_build_container_creates_new_instance_each_time(self, mock_get_pool, mock_bot_cls, tmp_path):
        mock_get_pool.return_value = AsyncMock()
        mock_bot_cls.return_value = MagicMock()

        with patch("src.infrastructure.container.settings") as mock_settings:
            mock_settings.storage.base_path = str(tmp_path / "storage" / "screenshots")
            mock_settings.client_bot.token = "test_token"
            mock_settings.staff_bot.token = "test_staff_token"

            c1 = build_container()
            c2 = build_container()

            assert c1 is not c2
            assert c1.game_service is not c2.game_service
