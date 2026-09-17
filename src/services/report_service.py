from typing import Optional
from datetime import datetime, timedelta
from src.core.interfaces import ReportRepository


class ReportService:
    def __init__(self, report_repo: ReportRepository):
        self._report_repo = report_repo

    async def get_full_report(self, period: str) -> dict:
        """Собирает полный отчёт за указанный период.

        Периоды: 'today', '30_days', 'all_time'.
        """
        since = self._resolve_period(period)
        unique_users = await self._report_repo.get_unique_users_count(since)
        sent, approved = await self._report_repo.get_screenshots_stats(since)
        top_users = await self._report_repo.get_top_users_by_screenshots(since, limit=30)
        by_game = await self._report_repo.get_stats_by_game(since)
        return {
            "period": period,
            "unique_users": unique_users,
            "sent_screenshots": sent,
            "approved_screenshots": approved,
            "top_users": top_users,
            "by_game": by_game,
        }

    def _resolve_period(self, period: str) -> Optional[datetime]:
        """Преобразует строковый период в метку времени или None для 'всё время'."""
        if period == "all_time":
            return None
        now = datetime.utcnow()
        if period == "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "30_days":
            return now - timedelta(days=30)
        return None