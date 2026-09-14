from unittest.mock import AsyncMock, patch
import pytest

from src.infrastructure.container import Container, build_container
from src.services.game_service import GameService
from src.services.instruction_service import InstructionService
from src.services.balance_service import BalanceService
from src.services.session_service import SessionService
from src.services.application_service import ApplicationService
from src.services.review_service import ReviewService
from src.services.cleanup_service import CleanupService


class TestContainer:
    @patch("src.infrastructure.container.get_pool")
    def test_build_container_returns_all_services(self, mock_get_pool, tmp_path):
        # Мокаем пул БД, чтобы не требовать реального подключения
        mock_get_pool.return_value = AsyncMock()

        # Переопределяем путь хранилища на временную директорию
        with patch("src.infrastructure.container.settings") as mock_settings:
            mock_settings.storage.base_path = str(tmp_path / "storage" / "screenshots")

            container = build_container()

            # Проверяем, что контейнер — экземпляр Container
            assert isinstance(container, Container)

            # Проверяем наличие всех сервисов
            assert isinstance(container.game_service, GameService)
            assert isinstance(container.instruction_service, InstructionService)
            assert isinstance(container.balance_service, BalanceService)
            assert isinstance(container.session_service, SessionService)
            assert isinstance(container.application_service, ApplicationService)
            assert isinstance(container.review_service, ReviewService)
            assert isinstance(container.cleanup_service, CleanupService)

    @patch("src.infrastructure.container.get_pool")
    def test_build_container_creates_new_instance_each_time(self, mock_get_pool, tmp_path):
        mock_get_pool.return_value = AsyncMock()

        with patch("src.infrastructure.container.settings") as mock_settings:
            mock_settings.storage.base_path = str(tmp_path / "storage" / "screenshots")

            c1 = build_container()
            c2 = build_container()

            # Каждый вызов build_container должен создавать новый контейнер
            assert c1 is not c2
            assert c1.game_service is not c2.game_service