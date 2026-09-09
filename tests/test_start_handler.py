import pytest
from unittest.mock import AsyncMock, MagicMock

from aiogram.types import Message, User

from src.bots.client_bot.handlers.start import handle_start, handle_help


@pytest.fixture
def mock_container():
    container = MagicMock()
    container.user_service = AsyncMock()
    return container


@pytest.fixture
def mock_message():
    """Создает мок-объект Message.
    В aiogram 3.x (Pydantic V2) объекты Message frozen, поэтому мы используем MagicMock
    с заданными атрибутами вместо создания реального экземпляра.
    """
    # User мы можем создать реальный, так как нам нужны его конкретные поля
    user = User(id=123, is_bot=False, first_name="TestUser", username="tester", language_code="ru")
    
    msg = MagicMock(spec=Message)
    msg.from_user = user
    msg.answer = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_handle_start_registers_and_replies(mock_container, mock_message):
    """Проверяет, что /start регистрирует юзера и отправляет приветствие."""
    await handle_start(mock_message, mock_container)

    # 1. Проверяем вызов сервиса
    mock_container.user_service.register_or_update.assert_called_once_with(
        user_id=123,
        username="tester",
        first_name="TestUser",
        language_code="ru",
    )
    
    # 2. Проверяем отправку сообщения
    mock_message.answer.assert_called_once()
    sent_text = mock_message.answer.call_args[0][0]
    assert "Привет, TestUser" in sent_text
    assert "/campaigns" in sent_text


@pytest.mark.asyncio
async def test_handle_help_replies(mock_message):
    """Проверяет, что /help отправляет инструкцию."""
    await handle_help(mock_message)

    mock_message.answer.assert_called_once()
    sent_text = mock_message.answer.call_args[0][0]
    assert "Как это работает" in sent_text
    assert "/support" in sent_text