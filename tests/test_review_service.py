import pytest
from unittest.mock import AsyncMock
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from src.services.review_service import ReviewService
from src.core.entities import Application, Campaign, Reward
from src.core.enums import ApplicationStatus, RewardType, RewardStatus
from src.core.exceptions import ApplicationNotFoundError, IdempotencyError
from src.core.interfaces import RewardResult


@pytest.fixture
def mock_deps():
    return {
        "app_repo": AsyncMock(),
        "campaign_repo": AsyncMock(),
        "reward_repo": AsyncMock(),
        "audit_repo": AsyncMock(),
        "reward_issuer": AsyncMock(),
    }

@pytest.fixture
def pending_app():
    return Application(
        id=uuid4(), user_id=123, campaign_id=uuid4(),
        status=ApplicationStatus.PENDING, screenshot_file_id="file",
        moderator_comment=None, submitted_at=datetime.now(timezone.utc),
        reviewed_at=None, rewarded_at=None, reviewed_by=None
    )

@pytest.fixture
def active_campaign():
    return Campaign(
        id=uuid4(), name="Test", description="", reward_type=RewardType.STARS,
        reward_amount=100, starts_at=datetime.now(timezone.utc),
        ends_at=datetime.now(timezone.utc), max_rewards_per_user=1,
        is_active=True, created_at=datetime.now(timezone.utc)
    )


@pytest.mark.asyncio
async def test_review_approve_success(mock_deps, pending_app, active_campaign):
    """Успешное одобрение: заявка обновлена, награда создана и выдана."""
    pending_app.campaign_id = active_campaign.id
    
    mock_deps["app_repo"].get_by_id.return_value = pending_app
    
    # ИСПРАВЛЕНИЕ: Создаем копию объекта с обновленным статусом, 
    # чтобы симулировать корректный ответ репозитория из БД.
    approved_app = replace(pending_app, status=ApplicationStatus.APPROVED)
    mock_deps["app_repo"].update_status.return_value = approved_app
    
    mock_deps["campaign_repo"].get_by_id.return_value = active_campaign
    mock_deps["reward_repo"].check_idempotency.return_value = False
    
    created_reward = Reward(
        id=uuid4(), user_id=123, campaign_id=active_campaign.id,
        application_id=pending_app.id, reward_type=RewardType.STARS,
        amount=100, transaction_id=None, status=RewardStatus.PENDING,
        issued_at=None, delivered_at=None
    )
    mock_deps["reward_repo"].create.return_value = created_reward
    mock_deps["reward_issuer"].issue.return_value = RewardResult(is_success=True, transaction_id="tx_123")

    service = ReviewService(**mock_deps)
    result = await service.review_application(pending_app.id, 999, True, "Good")

    assert result.status == ApplicationStatus.APPROVED
    mock_deps["reward_repo"].create.assert_called_once()
    mock_deps["reward_issuer"].issue.assert_called_once()
    mock_deps["reward_repo"].mark_as_issued.assert_called_once()
    mock_deps["audit_repo"].log_action.assert_called_once()


@pytest.mark.asyncio
async def test_review_reject(mock_deps, pending_app):
    """Отклонение заявки: награда не создается и не выдается."""
    mock_deps["app_repo"].get_by_id.return_value = pending_app
    
    # ИСПРАВЛЕНИЕ: Создаем копию объекта со статусом REJECTED
    rejected_app = replace(pending_app, status=ApplicationStatus.REJECTED)
    mock_deps["app_repo"].update_status.return_value = rejected_app

    service = ReviewService(**mock_deps)
    result = await service.review_application(pending_app.id, 999, False, "Bad screenshot")

    assert result.status == ApplicationStatus.REJECTED
    mock_deps["campaign_repo"].get_by_id.assert_not_called()
    mock_deps["reward_repo"].create.assert_not_called()
    mock_deps["reward_issuer"].issue.assert_not_called()


@pytest.mark.asyncio
async def test_review_already_reviewed(mock_deps, pending_app):
    """Защита от повторной проверки (идемпотентность)."""
    pending_app.status = ApplicationStatus.APPROVED
    mock_deps["app_repo"].get_by_id.return_value = pending_app

    service = ReviewService(**mock_deps)
    
    with pytest.raises(IdempotencyError):
        await service.review_application(pending_app.id, 999, True)
        
    mock_deps["app_repo"].update_status.assert_not_called()


@pytest.mark.asyncio
async def test_review_issuer_fails(mock_deps, pending_app, active_campaign):
    """Сценарий, когда API выдачи наград упал. Статус награды должен стать FAILED."""
    pending_app.campaign_id = active_campaign.id
    
    mock_deps["app_repo"].get_by_id.return_value = pending_app
    
    approved_app = replace(pending_app, status=ApplicationStatus.APPROVED)
    mock_deps["app_repo"].update_status.return_value = approved_app
    
    mock_deps["campaign_repo"].get_by_id.return_value = active_campaign
    mock_deps["reward_repo"].check_idempotency.return_value = False
    
    created_reward = Reward(
        id=uuid4(), user_id=123, campaign_id=active_campaign.id,
        application_id=pending_app.id, reward_type=RewardType.STARS,
        amount=100, transaction_id=None, status=RewardStatus.PENDING,
        issued_at=None, delivered_at=None
    )
    mock_deps["reward_repo"].create.return_value = created_reward
    mock_deps["reward_issuer"].issue.return_value = RewardResult(is_success=False, error_message="API timeout")

    service = ReviewService(**mock_deps)
    await service.review_application(pending_app.id, 999, True)

    mock_deps["reward_repo"].mark_as_failed.assert_called_once()
    mock_deps["reward_repo"].mark_as_issued.assert_not_called()