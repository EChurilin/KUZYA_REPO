"""Тесты новых методов ReviewService (Партия 3, Пункт 1 ТЗ)."""
import uuid
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

import pytest

from src.services.review_service import ReviewService


@pytest.fixture
def mock_screenshot_repo():
    return AsyncMock()


@pytest.fixture
def mock_settings_service():
    service = AsyncMock()
    service.get_screenshot_price = AsyncMock(return_value=15)
    return service


@pytest.fixture
def review_service(mock_screenshot_repo, mock_settings_service):
    return ReviewService(
        app_repo=AsyncMock(),
        screenshot_repo=mock_screenshot_repo,
        user_balance_service=AsyncMock(),
        settings_service=mock_settings_service,
        notification_service=AsyncMock(),
    )


def _make_screenshot(status: str):
    """Создаёт мок скриншота с заданным статусом."""
    s = MagicMock()
    s.id = uuid.uuid4()
    s.status = status
    s.created_at = datetime.now(timezone.utc)
    return s


class TestGetScreenshotsSummary:
    @pytest.mark.asyncio
    async def test_summary_mixed_statuses(self, review_service, mock_screenshot_repo):
        """Сводка корректно считает одобренные, отклонённые и ожидающие."""
        mock_screenshot_repo.get_by_application = AsyncMock(return_value=[
            _make_screenshot("approved"),
            _make_screenshot("approved"),
            _make_screenshot("rejected"),
            _make_screenshot("pending"),
        ])

        result = await review_service.get_screenshots_summary(uuid.uuid4())

        assert result["approved"] == 2
        assert result["rejected"] == 1
        assert result["pending"] == 1
        assert result["total"] == 4
        # 2 одобренных × цена 15 = 30
        assert result["amount_to_credit"] == 30

    @pytest.mark.asyncio
    async def test_summary_all_approved(self, review_service, mock_screenshot_repo):
        """Сводка когда все скриншоты одобрены."""
        mock_screenshot_repo.get_by_application = AsyncMock(return_value=[
            _make_screenshot("approved"),
            _make_screenshot("approved"),
        ])

        result = await review_service.get_screenshots_summary(uuid.uuid4())

        assert result["approved"] == 2
        assert result["rejected"] == 0
        assert result["pending"] == 0
        assert result["amount_to_credit"] == 30

    @pytest.mark.asyncio
    async def test_summary_empty(self, review_service, mock_screenshot_repo):
        """Сводка для заявки без скриншотов."""
        mock_screenshot_repo.get_by_application = AsyncMock(return_value=[])

        result = await review_service.get_screenshots_summary(uuid.uuid4())

        assert result["total"] == 0
        assert result["amount_to_credit"] == 0


class TestAllScreenshotsReviewed:
    @pytest.mark.asyncio
    async def test_all_reviewed_true(self, review_service, mock_screenshot_repo):
        """Возвращает True, когда нет скриншотов со статусом 'на проверке'."""
        mock_screenshot_repo.get_by_application = AsyncMock(return_value=[
            _make_screenshot("approved"),
            _make_screenshot("rejected"),
        ])

        result = await review_service.all_screenshots_reviewed(uuid.uuid4())

        assert result is True

    @pytest.mark.asyncio
    async def test_all_reviewed_false(self, review_service, mock_screenshot_repo):
        """Возвращает False, когда есть скриншоты 'на проверке'."""
        mock_screenshot_repo.get_by_application = AsyncMock(return_value=[
            _make_screenshot("approved"),
            _make_screenshot("pending"),
        ])

        result = await review_service.all_screenshots_reviewed(uuid.uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_all_reviewed_empty(self, review_service, mock_screenshot_repo):
        """Возвращает False для заявки без скриншотов (нельзя финализировать)."""
        mock_screenshot_repo.get_by_application = AsyncMock(return_value=[])

        result = await review_service.all_screenshots_reviewed(uuid.uuid4())

        assert result is False


class TestResetScreenshot:
    @pytest.mark.asyncio
    async def test_reset_screenshot(self, review_service, mock_screenshot_repo):
        """reset_screenshot переводит скриншот в статус 'на проверке'."""
        mock_screenshot_repo.update_status = AsyncMock()
        scr_id = uuid.uuid4()

        await review_service.reset_screenshot(scr_id)

        mock_screenshot_repo.update_status.assert_called_once_with(scr_id, "pending")
