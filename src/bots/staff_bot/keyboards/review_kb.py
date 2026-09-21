"""Клавиатуры для модерации заявок в staff_bot."""
import uuid
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_screenshot_review_kb(screenshot_id: uuid.UUID) -> InlineKeyboardMarkup:
    """Клавиатура для скриншота, ожидающего решения: Одобрить / Отклонить."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Одобрить",
                    callback_data=f"approve_scr:{screenshot_id}",
                ),
                InlineKeyboardButton(
                    text="Отклонить",
                    callback_data=f"reject_scr:{screenshot_id}",
                ),
            ]
        ]
    )


def get_screenshot_decided_kb(screenshot_id: uuid.UUID) -> InlineKeyboardMarkup:
    """Клавиатура для скриншота, по которому принято решение: Изменить решение."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Изменить решение",
                    callback_data=f"change_dec:{screenshot_id}",
                )
            ]
        ]
    )


def get_reward_kb(application_id: uuid.UUID) -> InlineKeyboardMarkup:
    """Клавиатура итогового сообщения: Начислить награду."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Начислить награду",
                    callback_data=f"reward_app:{application_id}",
                )
            ]
        ]
    )
