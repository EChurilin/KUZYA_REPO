import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from uuid import uuid4

from src.repositories.user_repo import UserRepository
from src.repositories.application_repo import ApplicationRepository
from src.repositories.campaign_repo import CampaignRepository
from src.core.enums import ApplicationStatus


@pytest.fixture
def mock_pool():
    return AsyncMock()


@pytest.mark.asyncio
async def test_user_repository_get_by_id(mock_pool):
    repo = UserRepository(mock_pool)
    user_id = 12345
    now = datetime.now()
    mock_row = {
        "id": user_id,
        "username": "testuser",
        "first_name": "Test",
        "language_code": "ru",
        "role": "user",
        "created_at": now,
        "updated_at": now,
    }
    repo.fetch_one = AsyncMock(return_value=mock_row)

    user = await repo.get_by_id(user_id)

    assert user is not None
    assert user.id == user_id
    assert user.username == "testuser"
    assert user.role == "user"
    repo.fetch_one.assert_called_once()


@pytest.mark.asyncio
async def test_user_repository_get_by_id_not_found(mock_pool):
    repo = UserRepository(mock_pool)
    repo.fetch_one = AsyncMock(return_value=None)

    user = await repo.get_by_id(999)

    assert user is None
    repo.fetch_one.assert_called_once()


@pytest.mark.asyncio
async def test_application_repository_get_pending(mock_pool):
    repo = ApplicationRepository(mock_pool)
    app_id = uuid4()
    user_id = 123
    campaign_id = uuid4()
    now = datetime.now()
    
    mock_rows = [
        {
            "id": app_id,
            "user_id": user_id,
            "campaign_id": campaign_id,
            "status": ApplicationStatus.PENDING,
            "screenshot_file_id": "file123",
            "moderator_comment": None,
            "submitted_at": now,
            "reviewed_at": None,
            "rewarded_at": None,
            "reviewed_by": None,
        }
    ]
    repo.fetch_all = AsyncMock(return_value=mock_rows)

    apps = await repo.get_pending(limit=10)

    assert len(apps) == 1
    assert apps[0].id == app_id
    assert apps[0].status == ApplicationStatus.PENDING
    repo.fetch_all.assert_called_once()


@pytest.mark.asyncio
async def test_campaign_repository_get_active(mock_pool):
    repo = CampaignRepository(mock_pool)
    campaign_id = uuid4()
    now = datetime.now()
    
    mock_rows = [
        {
            "id": campaign_id,
            "name": "Test Campaign",
            "description": "Desc",
            "reward_type": "stars",
            "reward_amount": 100,
            "starts_at": now,
            "ends_at": now,
            "max_rewards_per_user": 1,
            "is_active": True,
            "created_at": now,
        }
    ]
    repo.fetch_all = AsyncMock(return_value=mock_rows)

    campaigns = await repo.get_active()

    assert len(campaigns) == 1
    assert campaigns[0].name == "Test Campaign"
    assert campaigns[0].reward_amount == 100
    repo.fetch_all.assert_called_once()