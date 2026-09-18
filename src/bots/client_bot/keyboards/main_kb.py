from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное меню клиента — ReplyKeyboard из 3 кнопок."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Посмотреть инструкцию")],
            [KeyboardButton(text="Начать играть")],
            [KeyboardButton(text="Получить подарок")],
        ],
        resize_keyboard=True,
    )


def remove_menu_kb() -> ReplyKeyboardRemove:
    """Скрытие главного меню (на время сессии)."""
    return ReplyKeyboardRemove()