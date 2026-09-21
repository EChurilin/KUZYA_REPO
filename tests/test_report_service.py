"""
Тесты для ReportService.

Покрывают пункт 5 ТЗ: корректная обработка таймзон при формировании отчётов.
Ключевое правило (03_OPERATIONS.md, правило 7.8): использовать только
datetime.now(timezone.utc). Все даты, передаваемые в репозиторий,
должны быть timezone-aware.
"""
import pytest
from unittest.mock import AsyncMock

from src.services.report_service import ReportService


@pytest.fixture
def mock_report_repo():
    """Мок репозитория отчётов."""
    return AsyncMock()


@pytest.fixture
def report_service(mock_report_repo):
    """ReportService с мокнутым репозиторием."""
    return ReportService(mock_report_repo)


class TestResolvePeriod:
    """Тесты _resolve_period: преобразование строкового периода в datetime."""

    def test_all_time_returns_none(self, report_service):
        """'all_time' -> None (без фильтра по дате)."""
        assert report_service._resolve_period("all_time") is None

    def test_unknown_period_returns_none(self, report_service):
        """Неизвестный период -> None."""
        assert report_service._resolve_period("unknown") is None

    def test_today_returns_timezone_aware(self, report_service):
        """'today' -> timezone-aware datetime (правило 7.8)."""
        result = report_service._resolve_period("today")
        assert result is not None
        assert result.tzinfo is not None, "datetime должен быть timezone-aware"

    def test_today_returns_midnight(self, report_service):
        """'today' -> начало дня (00:00:00)."""
        result = report_service._resolve_period("today")
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_30_days_returns_timezone_aware(self, report_service):
        """'30_days' -> timezone-aware datetime (правило 7.8)."""
        result = report_service._resolve_period("30_days")
        assert result is not None
        assert result.tzinfo is not None, "datetime должен быть timezone-aware"


class TestGetFullReport:
    """Тесты get_full_report: сборка полного отчёта."""

    @pytest.mark.asyncio
    async def test_get_full_report_passes_timezone_aware_datetime(
        self, report_service, mock_report_repo
    ):
        """get_full_report передаёт в репозиторий timezone-aware datetime."""
        mock_report_repo.get_unique_users_count = AsyncMock(return_value=5)
        mock_report_repo.get_screenshots_stats = AsyncMock(return_value=(10, 7))
        mock_report_repo.get_top_users_by_screenshots = AsyncMock(return_value=[])
        mock_report_repo.get_stats_by_game = AsyncMock(return_value=[])

        result = await report_service.get_full_report("today")

        assert result["period"] == "today"
        assert result["unique_users"] == 5

        # Ключевая проверка: в репозиторий передан timezone-aware datetime
        since = mock_report_repo.get_unique_users_count.call_args[0][0]
        assert since is not None
        assert since.tzinfo is not None, "в репозиторий должен передаваться timezone-aware datetime"

    @pytest.mark.asyncio
    async def test_get_full_report_all_time_passes_none(
        self, report_service, mock_report_repo
    ):
        """get_full_report для 'all_time' передаёт None (без фильтра по дате)."""
        mock_report_repo.get_unique_users_count = AsyncMock(return_value=5)
        mock_report_repo.get_screenshots_stats = AsyncMock(return_value=(10, 7))
        mock_report_repo.get_top_users_by_screenshots = AsyncMock(return_value=[])
        mock_report_repo.get_stats_by_game = AsyncMock(return_value=[])

        await report_service.get_full_report("all_time")

        since = mock_report_repo.get_unique_users_count.call_args[0][0]
        assert since is None
