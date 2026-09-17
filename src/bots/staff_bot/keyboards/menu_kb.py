from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_menu_kb() -> ReplyKeyboardMarkup:
    """Возвращает reply-клавиатуру главного меню staff_bot."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Очередь заявок"),
                KeyboardButton(text="Список игр"),
            ],
            [
                KeyboardButton(text="Инструкция"),
                KeyboardButton(text="Отчет"),
            ],
            [KeyboardButton(text="Техническая поддержка")],
            [KeyboardButton(text="Скрыть меню")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def remove_menu_kb() -> ReplyKeyboardRemove:
    """Возвращает клавиатуру для скрытия меню."""
    return ReplyKeyboardRemove()