"""
Тесты для новых методов репозиториев модерации (Партия 2, Пункт 1 ТЗ).

Проверяют:
- set_staff_message_id в ScreenshotRepositoryImpl
- set_summary_message_id в ApplicationRepositoryImpl
- Чтение новых полей из БД
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repositories.screenshot_repo import ScreenshotRepositoryImpl
from src.repositories.application_repo import ApplicationRepositoryImpl


# ==== ScreenshotRepositoryImpl ====


@pytest.fixture
def screenshot_repo():
    return ScreenshotRepositoryImpl(AsyncMock())


class TestScreenshotRepoStaffMessageId:
    @pytest.mark.asyncio
    async def test_set_staff_message_id(self, screenshot_repo):
        """set_staff_message_id вызывает execute с правильными аргументами."""
        screenshot_repo.execute = AsyncMock()
        scr_id = uuid.uuid4()

        await screenshot_repo.set_staff_message_id(scr_id, 42)

        screenshot_repo.execute.assert_called_once_with(
            "UPDATE application_screenshots SET staff_message_id = $1 WHERE id = $2",
            42,
            scr_id,
        )

    @pytest.mark.asyncio
    async def test_get_by_application_includes_staff_message_id(self, screenshot_repo):
        """get_by_application читает staff_message_id из БД."""
        row = {
            "id": uuid.uuid4(),
            "session_id": uuid.uuid4(),
            "application_id": uuid.uuid4(),
            "client_file_id": "file_123",
            "storage_path": "/tmp/test.jpg",
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "staff_message_id": 42,
        }
        screenshot_repo.fetch = AsyncMock(return_value=[row])

        result = await screenshot_repo.get_by_application(uuid.uuid4())

        assert len(result) == 1
        assert result[0].staff_message_id == 42

    @pytest.mark.asyncio
    async def test_get_by_id_includes_staff_message_id(self, screenshot_repo):
        """get_by_id читает staff_message_id из БД."""
        row = {
            "id": uuid.uuid4(),
            "session_id": uuid.uuid4(),
            "application_id": None,
            "client_file_id": "file_456",
            "storage_path": "/tmp/test2.jpg",
            "status": "approved",
            "created_at": datetime.now(timezone.utc),
            "staff_message_id": None,
        }
        screenshot_repo.fetchone = AsyncMock(return_value=row)

        result = await screenshot_repo.get_by_id(uuid.uuid4())

        assert result is not None
        assert result.staff_message_id is None


# ==== ApplicationRepositoryImpl ====


@pytest.fixture
def application_repo():
    return ApplicationRepositoryImpl(AsyncMock())


def _make_app_row(**overrides):
    """Создаёт строку БД для Application с дефолтными значениями."""
    row = {
        "id": uuid.uuid4(),
        "user_id": 385567246,
        "session_id": uuid.uuid4(),
        "campaign_id": None,
        "status": "pending_review",
        "actual_screenshot_count": 3,
        "approved_screenshot_count": 0,
        "moderator_comment": None,
        "submitted_at": datetime.now(timezone.utc),
        "reviewed_at": None,
        "rewarded_at": None,
        "reviewed_by": None,
        "auto_closed": False,
        "summary_message_id": None,
    }
    row.update(overrides)
    return row


class TestApplicationRepoSummaryMessageId:
    @pytest.mark.asyncio
    async def test_set_summary_message_id(self, application_repo):
        """set_summary_message_id вызывает execute с правильными аргументами."""
        application_repo.execute = AsyncMock()
        app_id = uuid.uuid4()

        await application_repo.set_summary_message_id(app_id, 99)

        application_repo.execute.assert_called_once_with(
            "UPDATE applications SET summary_message_id = $1 WHERE id = $2",
            99,
            app_id,
        )

    @pytest.mark.asyncio
    async def test_get_by_id_includes_summary_message_id(self, application_repo):
        """get_by_id читает summary_message_id из БД."""
        row = _make_app_row(summary_message_id=99)
        application_repo.fetchone = AsyncMock(return_value=row)

        result = await application_repo.get_by_id(uuid.uuid4())

        assert result is not None
        assert result.summary_message_id == 99

    @pytest.mark.asyncio
    async def test_get_pending_review_includes_summary_message_id(self, application_repo):
        """get_pending_review читает summary_message_id из БД."""
        row = _make_app_row(summary_message_id=None)
        application_repo.fetch = AsyncMock(return_value=[row])

        result = await application_repo.get_pending_review()

        assert len(result) == 1
        assert result[0].summary_message_id is None
