from aiogram import Bot
from aiogram.types import LabeledPrice


class InvoiceSender:
    """Обёртка над Telegram Bot API для отправки и удаления инвойсов."""

    def __init__(self, bot: Bot):
        self._bot = bot

    async def send_invoice(
        self, chat_id: int, title: str, description: str, payload: str, amount: int
    ) -> int:
        message = await self._bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Пополнение баланса", amount=amount)],
        )
        return message.message_id

    async def delete_message(self, chat_id: int, message_id: int) -> None:
        await self._bot.delete_message(chat_id=chat_id, message_id=message_id)