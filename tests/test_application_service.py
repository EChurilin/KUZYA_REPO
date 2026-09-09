import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from src.services.application_service import ApplicationService
from src.core.entities import Application, Campaign
from src.core.enums import ApplicationStatus, RewardType
from src.core.exceptions import RateLimitExceededError


@pytest.fixture
def mock_repos():
    return {
        "app_repo": AsyncMock(),
        "campaign_repo": AsyncMock(),
        "audit_repo": AsyncMock(),
    }

@pytest.fixture
def active_campaign():
    now = datetime.now(timezone.utc)
    return Campaign(
        id=uuid4(),
        name="Test Campaign",
        description="Desc",
        reward_type=RewardType.STARS,
        reward_amount=100,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
        max_rewards_per_user=2,
        is_active=True,
        created_at=now,
    )


@pytest.mark.asyncio
async def test_submit_application_success(mock_repos, active_campaign):
    """Успешная подача заявки: кампания активна, лимит не превышен."""
    service = ApplicationService(**mock_repos)
    user_id = 123
    screenshot_id = "file_123"
    
    mock_repos["campaign_repo"].get_by_id.return_value = active_campaign
    mock_repos["app_repo"].count_user_campaign_submissions.return_value = 0
    
    expected_app = Application(
        id=uuid4(), user_id=user_id, campaign_id=active_campaign.id,
        status=ApplicationStatus.PENDING, screenshot_file_id=screenshot_id,
        moderator_comment=None, submitted_at=datetime.now(timezone.utc),
        reviewed_at=None, rewarded_at=None, reviewed_by=None
    )
    mock_repos["app_repo"].create.return_value = expected_app

    result = await service.submit_application(user_id, active_campaign.id, screenshot_id)

    assert result.status == ApplicationStatus.PENDING
    assert result.user_id == user_id
    mock_repos["app_repo"].create.assert_called_once()
    mock_repos["audit_repo"].log_action.assert_called_once()


@pytest.mark.asyncio
async def test_submit_application_campaign_not_found(mock_repos):
    """Ошибка: кампания не найдена или неактивна."""
    service = ApplicationService(**mock_repos)
    mock_repos["campaign_repo"].get_by_id.return_value = None

    with pytest.raises(ValueError, match="Campaign not found or inactive"):
        await service.submit_application(123, uuid4(), "file_123")
        
    # Убеждаемся, что при ошибке валидации запись в БД даже не attempted
    mock_repos["app_repo"].create.assert_not_called()


@pytest.mark.asyncio
async def test_submit_application_limit_exceeded(mock_repos, active_campaign):
    """Ошибка: пользователь исчерпал лимит попыток для этой кампании."""
    service = ApplicationService(**mock_repos)
    user_id = 123
    
    mock_repos["campaign_repo"].get_by_id.return_value = active_campaign
    # Возвращаем 2, что равно max_rewards_per_user (2)
    mock_repos["app_repo"].count_user_campaign_submissions.return_value = 2

    with pytest.raises(RateLimitExceededError):
        await service.submit_application(user_id, active_campaign.id, "file_123")
        
    # Убеждаемся, что при превышении лимита запись в БД не создается
    mock_repos["app_repo"].create.assert_not_called()