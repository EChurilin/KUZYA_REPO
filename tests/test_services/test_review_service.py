import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, ANY
import pytest

from src.core.entities import Application, ApplicationScreenshot, Reward
from src.core.exceptions import RewardBalanceInsufficientError, SessionNotFoundError
from src.services.review_service import ReviewService


@pytest.fixture
def app_repo_mock():
    return AsyncMock()

@pytest.fixture
def screenshot_repo_mock():
    return AsyncMock()

@pytest.fixture
def reward_repo_mock():
    return AsyncMock()

@pytest.fixture
def balance_service_mock():
    return AsyncMock()

@pytest.fixture
def reward_issuer_mock():
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


class TestReviewService:
    @pytest.mark.asyncio
    async def test_approve_screenshot(self, screenshot_repo_mock):
        service = ReviewService(AsyncMock(), screenshot_repo_mock, AsyncMock(), AsyncMock(), AsyncMock())
        await service.approve_screenshot(uuid.uuid4(), 999)
        screenshot_repo_mock.update_status.assert_awaited_once_with(ANY, "approved")

    @pytest.mark.asyncio
    async def test_reject_screenshot(self, screenshot_repo_mock):
        service = ReviewService(AsyncMock(), screenshot_repo_mock, AsyncMock(), AsyncMock(), AsyncMock())
        await service.reject_screenshot(uuid.uuid4(), 999)
        screenshot_repo_mock.update_status.assert_awaited_once_with(ANY, "rejected")

    @pytest.mark.asyncio
    async def test_finalize_application_success(self, app_repo_mock, screenshot_repo_mock, reward_repo_mock, balance_service_mock, reward_issuer_mock, sample_app):
        app_repo_mock.get_by_id.return_value = sample_app
        
        # 2 одобрено, 1 отклонен
        screenshots = [
            ApplicationScreenshot(id=uuid.uuid4(), session_id=uuid.uuid4(), application_id=sample_app.id, client_file_id="1", storage_path="p1", status="approved", created_at=datetime.now(timezone.utc)),
            ApplicationScreenshot(id=uuid.uuid4(), session_id=uuid.uuid4(), application_id=sample_app.id, client_file_id="2", storage_path="p2", status="approved", created_at=datetime.now(timezone.utc)),
            ApplicationScreenshot(id=uuid.uuid4(), session_id=uuid.uuid4(), application_id=sample_app.id, client_file_id="3", storage_path="p3", status="rejected", created_at=datetime.now(timezone.utc)),
        ]
        screenshot_repo_mock.get_by_application.return_value = screenshots
        
        balance_service_mock.get_current_balance.return_value = 1000 # Баланс достаточный
        reward_issuer_mock.issue_reward.return_value = "tx_123"
        
        service = ReviewService(app_repo_mock, screenshot_repo_mock, reward_repo_mock, balance_service_mock, reward_issuer_mock)
        
        reward = await service.finalize_application(
            application_id=sample_app.id,
            moderator_id=999,
            reward_type="stars",
            reward_amount_per_screenshot=10, # 2 * 10 = 20
            comment="Good job"
        )
        
        assert reward is not None
        assert reward.amount == 20
        assert reward.transaction_id == "tx_123"
        
        app_repo_mock.update_status.assert_awaited_once()
        reward_repo_mock.create.assert_awaited_once()
        app_repo_mock.mark_rewarded.assert_awaited_once_with(sample_app.id)

    @pytest.mark.asyncio
    async def test_finalize_application_insufficient_balance(self, app_repo_mock, screenshot_repo_mock, reward_repo_mock, balance_service_mock, reward_issuer_mock, sample_app):
        app_repo_mock.get_by_id.return_value = sample_app
        screenshot_repo_mock.get_by_application.return_value = [
            ApplicationScreenshot(id=uuid.uuid4(), session_id=uuid.uuid4(), application_id=sample_app.id, client_file_id="1", storage_path="p1", status="approved", created_at=datetime.now(timezone.utc))
        ]
        
        # Баланс недостаточный (нужно 10, есть 5)
        balance_service_mock.get_current_balance.return_value = 5
        
        service = ReviewService(app_repo_mock, screenshot_repo_mock, reward_repo_mock, balance_service_mock, reward_issuer_mock)
        
        with pytest.raises(RewardBalanceInsufficientError):
            await service.finalize_application(
                application_id=sample_app.id,
                moderator_id=999,
                reward_type="stars",
                reward_amount_per_screenshot=10,
            )