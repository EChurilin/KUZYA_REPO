import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from aiogram.types import Message, User, PhotoSize

from src.bots.client_bot.handlers.campaigns import handle_campaigns_list, handle_screenshot
from src.core.entities import Campaign
from src.core.enums import RewardType
from src.core.exceptions import RateLimitExceededError


@pytest.fixture
def mock_container():
    container = MagicMock()
    container.campaign_repo = AsyncMock()
    container.app_service = AsyncMock()
    return container


@pytest.fixture
def mock_message():
    user = User(id=123, is_bot=False, first_name="Test", username="test", language_code="ru")
    msg = MagicMock(spec=Message)
    msg.from_user = user
    msg.answer = AsyncMock()
    return msg


@pytest.fixture
def active_campaign():
    return Campaign(
        id=uuid4(), name="Test Camp", description="Desc", reward_type=RewardType.STARS,
        reward_amount=100, starts_at=datetime.now(timezone.utc), ends_at=datetime.now(timezone.utc),
        max_rewards_per_user=1, is_active=True, created_at=datetime.now(timezone.utc)
    )


@pytest.mark.asyncio
async def test_handle_campaigns_list_empty(mock_container, mock_message):
    """Проверяет сообщение, если активных кампаний нет."""
    mock_container.campaign_repo.get_active.return_value = []
    await handle_campaigns_list(mock_message, mock_container)
    
    mock_message.answer.assert_called_once()
    assert "нет активных кампаний" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_campaigns_list_success(mock_container, mock_message, active_campaign):
    """Проверяет корректный вывод списка кампаний."""
    mock_container.campaign_repo.get_active.return_value = [active_campaign]
    await handle_campaigns_list(mock_message, mock_container)
    
    mock_message.answer.assert_called_once()
    sent_text = mock_message.answer.call_args[0][0]
    assert "Test Camp" in sent_text
    assert str(active_campaign.id) in sent_text


@pytest.mark.asyncio
async def test_handle_screenshot_success(mock_container, mock_message, active_campaign):
    """Проверяет успешный приём скриншота и вызов сервиса."""
    photo_size = MagicMock(spec=PhotoSize)
    photo_size.file_id = "test_file_id_123"
    
    mock_message.photo = [photo_size]
    mock_message.caption = str(active_campaign.id)
    
    await handle_screenshot(mock_message, mock_container)
    
    mock_container.app_service.submit_application.assert_called_once()
    call_kwargs = mock_container.app_service.submit_application.call_args[1]
    
    assert call_kwargs["user_id"] == 123
    assert call_kwargs["campaign_id"] == active_campaign.id
    assert call_kwargs["screenshot_file_id"] == "test_file_id_123"
    
    mock_message.answer.assert_called_once_with("Скриншот успешно принят и отправлен на проверку модератором!")


@pytest.mark.asyncio
async def test_handle_screenshot_rate_limit(mock_container, mock_message, active_campaign):
    """Проверяет, что хендлер корректно обрабатывает исключение RateLimitExceededError."""
    photo_size = MagicMock(spec=PhotoSize)
    photo_size.file_id = "test_file_id_123"
    
    mock_message.photo = [photo_size]
    mock_message.caption = str(active_campaign.id)
    
    mock_container.app_service.submit_application.side_effect = RateLimitExceededError("Limit reached")
    
    await handle_screenshot(mock_message, mock_container)
    
    mock_message.answer.assert_called_once()
    assert "Лимит превышен" in mock_message.answer.call_args[0][0]