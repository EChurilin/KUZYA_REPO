import pytest
from unittest.mock import AsyncMock, MagicMock

from src.integrations.payments.invoice_sender import InvoiceSender


@pytest.fixture
def mock_bot():
    return AsyncMock()


class TestInvoiceSender:
    @pytest.mark.asyncio
    async def test_send_invoice(self, mock_bot):
        message = MagicMock()
        message.message_id = 42
        mock_bot.send_invoice = AsyncMock(return_value=message)

        sender = InvoiceSender(mock_bot)
        message_id = await sender.send_invoice(
            chat_id=123,
            title="Пополнение баланса",
            description="Пополнение баланса бота на 100 звёзд",
            payload="topup_123",
            amount=100,
        )

        assert message_id == 42
        mock_bot.send_invoice.assert_called_once()
        call_kwargs = mock_bot.send_invoice.call_args[1]
        assert call_kwargs["chat_id"] == 123
        assert call_kwargs["currency"] == "XTR"
        assert call_kwargs["provider_token"] == ""
        assert len(call_kwargs["prices"]) == 1
        assert call_kwargs["prices"][0].amount == 100

    @pytest.mark.asyncio
    async def test_delete_message(self, mock_bot):
        mock_bot.delete_message = AsyncMock(return_value=True)

        sender = InvoiceSender(mock_bot)
        await sender.delete_message(chat_id=123, message_id=42)

        mock_bot.delete_message.assert_called_once()
        call_kwargs = mock_bot.delete_message.call_args[1]
        assert call_kwargs["chat_id"] == 123
        assert call_kwargs["message_id"] == 42