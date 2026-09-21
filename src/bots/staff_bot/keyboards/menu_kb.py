from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_kb() -> ReplyKeyboardMarkup:
    """Возвращает reply-клавиатуру главного меню staff_bot (9 кнопок)."""
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
            [KeyboardButton(text="Цена скриншота")],
            [
                KeyboardButton(text="Пополнить баланс"),
                KeyboardButton(text="Баланс звёзд"),
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


def get_back_to_menu_inline_kb() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру «Назад в меню».

    Используется в edit_text / answer_photo, где ReplyKeyboardMarkup недопустим
    (Telegram API требует InlineKeyboardMarkup для inline-сообщений).
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад в меню", callback_data="menu_back")]
        ]
    )
