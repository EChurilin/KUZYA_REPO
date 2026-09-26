from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_instruction_publish_kb() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру для подтверждения публикации инструкции."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Опубликовать",
                    callback_data="instruction_publish"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data="instruction_cancel"
                )
            ]
        ]
    )


def get_instruction_cancel_kb() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру с кнопкой отмены редактирования инструкции."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="instruction_cancel")]
        ]
    )


def get_instruction_back_to_menu_kb() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру с кнопкой возврата в меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад в меню", callback_data="menu_back")]
        ]
    )

    

def get_instruction_empty_kb() -> InlineKeyboardMarkup:
    """Клавиатура для пустой инструкции: создать новую версию + назад в меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать редактирование", callback_data="instruction_start")],
            [InlineKeyboardButton(text="Назад в меню", callback_data="menu_back")]
        ]
    )