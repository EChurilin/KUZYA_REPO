import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, ANY
import pytest

from src.core.entities import Application, ApplicationScreenshot
from src.core.exceptions import SessionNotFoundError
from src.services.review_service import ReviewService


@pytest.fixture
def app_repo_mock():
    return AsyncMock()

@pytest.fixture
def screenshot_repo_mock():
    return AsyncMock()

@pytest.fixture
def user_balance_service_mock():
    return AsyncMock()

@pytest.fixture
def settings_service_mock():
    return AsyncMock()

@pytest.fixture
def notification_service_mock():
    return AsyncMock()

@pytest.fixture
def sample_app():
    return Application(
        id=uuid.uuid4(),
        user_id=12345,
        session_id=uuid.uuid4(),
        campaign_id=None,
        status="pending_review",
        actual_screenshot_count=3,
        approved_screenshot_count=0,
        moderator_comment=None,
        submitted_at=datetime.now(timezone.utc),
        reviewed_at=None,
        rewarded_at=None,
        reviewed_by=None,
        auto_closed=False,
    )


def _make_service(
    app_repo_mock,
    screenshot_repo_mock,
    user_balance_service_mock,
    settings_service_mock,
    notification_service_mock,
):
    return ReviewService(
        app_repo_mock,
        screenshot_repo_mock,
        user_balance_service_mock,
        settings_service_mock,
        notification_service_mock,
    )


class TestReviewService:
    @pytest.mark.asyncio
    async def test_approve_screenshot(
        self, app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
        settings_service_mock, notification_service_mock
    ):
        service = _make_service(
            app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
            settings_service_mock, notification_service_mock
        )

        await service.approve_screenshot(uuid.uuid4(), 999)

        screenshot_repo_mock.update_status.assert_awaited_once_with(ANY, "approved")

    @pytest.mark.asyncio
    async def test_reject_screenshot(
        self, app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
        settings_service_mock, notification_service_mock
    ):
        service = _make_service(
            app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
            settings_service_mock, notification_service_mock
        )

        await service.reject_screenshot(uuid.uuid4(), 999)

        screenshot_repo_mock.update_status.assert_awaited_once_with(ANY, "rejected")

    @pytest.mark.asyncio
    async def test_finalize_application_success(
        self, app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
        settings_service_mock, notification_service_mock, sample_app
    ):
        app_repo_mock.get_by_id = AsyncMock(return_value=sample_app)
        screenshot_repo_mock.get_by_application = AsyncMock(return_value=[
            ApplicationScreenshot(
                id=uuid.uuid4(), session_id=uuid.uuid4(), application_id=sample_app.id,
                client_file_id="1", storage_path="p1", status="approved",
                created_at=datetime.now(timezone.utc)
            ),
            ApplicationScreenshot(
                id=uuid.uuid4(), session_id=uuid.uuid4(), application_id=sample_app.id,
                client_file_id="2", storage_path="p2", status="approved",
                created_at=datetime.now(timezone.utc)
            ),
            ApplicationScreenshot(
                id=uuid.uuid4(), session_id=uuid.uuid4(), application_id=sample_app.id,
                client_file_id="3", storage_path="p3", status="rejected",
                created_at=datetime.now(timezone.utc)
            ),
        ])
        settings_service_mock.get_screenshot_price = AsyncMock(return_value=15)
        user_balance_service_mock.credit_from_application = AsyncMock(return_value=30)
        app_repo_mock.mark_rewarded = AsyncMock()
        notification_service_mock.notify_user = AsyncMock()

        service = _make_service(
            app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
            settings_service_mock, notification_service_mock
        )

        amount = await service.finalize_application(
            application_id=sample_app.id,
            moderator_id=999,
            comment="Good job",
        )

        assert amount == 30  # 2 approved * 15
        app_repo_mock.update_status.assert_awaited_once()
        user_balance_service_mock.credit_from_application.assert_awaited_once_with(
            user_id=sample_app.user_id,
            application_id=sample_app.id,
            approved_count=2,
            price_per_screenshot=15,
        )
        app_repo_mock.mark_rewarded.assert_awaited_once_with(sample_app.id)
        notification_service_mock.notify_user.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_finalize_application_all_rejected(
        self, app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
        settings_service_mock, notification_service_mock, sample_app
    ):
        app_repo_mock.get_by_id = AsyncMock(return_value=sample_app)
        screenshot_repo_mock.get_by_application = AsyncMock(return_value=[
            ApplicationScreenshot(
                id=uuid.uuid4(), session_id=uuid.uuid4(), application_id=sample_app.id,
                client_file_id="1", storage_path="p1", status="rejected",
                created_at=datetime.now(timezone.utc)
            ),
        ])
        notification_service_mock.notify_user = AsyncMock()

        service = _make_service(
            app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
            settings_service_mock, notification_service_mock
        )

        amount = await service.finalize_application(
            application_id=sample_app.id,
            moderator_id=999,
        )

        assert amount == 0
        user_balance_service_mock.credit_from_application.assert_not_awaited()
        app_repo_mock.mark_rewarded.assert_not_awaited()
        notification_service_mock.notify_user.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_finalize_application_idempotent(
        self, app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
        settings_service_mock, notification_service_mock, sample_app
    ):
        sample_app.status = "rewarded"
        app_repo_mock.get_by_id = AsyncMock(return_value=sample_app)

        service = _make_service(
            app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
            settings_service_mock, notification_service_mock
        )

        amount = await service.finalize_application(
            application_id=sample_app.id,
            moderator_id=999,
        )

        assert amount == 0
        screenshot_repo_mock.get_by_application.assert_not_awaited()
        user_balance_service_mock.credit_from_application.assert_not_awaited()
        app_repo_mock.update_status.assert_not_awaited()
        notification_service_mock.notify_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_finalize_application_not_found(
        self, app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
        settings_service_mock, notification_service_mock
    ):
        app_repo_mock.get_by_id = AsyncMock(return_value=None)

        service = _make_service(
            app_repo_mock, screenshot_repo_mock, user_balance_service_mock,
            settings_service_mock, notification_service_mock
        )

        with pytest.raises(SessionNotFoundError):
            await service.finalize_application(
                application_id=uuid.uuid4(),
                moderator_id=999,
            )