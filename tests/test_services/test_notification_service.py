import pytest
from unittest.mock import AsyncMock

from src.services.notification_service import NotificationService


@pytest.fixture
def client_bot_mock():
    return AsyncMock()


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_notify_user(self, client_bot_mock):
        client_bot_mock.send_message = AsyncMock()

        service = NotificationService(client_bot_mock)
        await service.notify_user(user_id=123, text="Ваша заявка одобрена")

        client_bot_mock.send_message.assert_awaited_once_with(
            chat_id=123, text="Ваша заявка одобрена"
        )

    @pytest.mark.asyncio
    async def test_notify_admin(self, client_bot_mock):
        client_bot_mock.send_message = AsyncMock()

        service = NotificationService(client_bot_mock)
        await service.notify_admin(admin_id=456, text="Нехватка баланса бота")

        client_bot_mock.send_message.assert_awaited_once_with(
            chat_id=456, text="Нехватка баланса бота"
        )