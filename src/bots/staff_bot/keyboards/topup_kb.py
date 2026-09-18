import uuid
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_topup_cancel_kb(topup_id: uuid.UUID) -> InlineKeyboardMarkup:
    """Inline-кнопка отмены пополнения (после отправки инвойса)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data=f"topup_cancel:{topup_id}")]
        ]
    )