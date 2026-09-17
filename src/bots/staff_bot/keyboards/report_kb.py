from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_report_period_kb() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру для выбора периода отчёта."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Сегодня", callback_data="report:today"),
                InlineKeyboardButton(text="30 дней", callback_data="report:30_days"),
            ],
            [
                InlineKeyboardButton(text="Всё время", callback_data="report:all_time"),
            ],
            [
                InlineKeyboardButton(text="Назад в меню", callback_data="menu_back"),
            ],
        ]
    )