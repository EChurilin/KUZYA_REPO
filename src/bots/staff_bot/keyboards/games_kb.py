from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.core.entities import Game


def get_games_list_kb(games: List[Game]) -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру со списком активных игр и кнопками действий."""
    keyboard = []
    
    # Кнопки с названиями игр (пока только для отображения, без callback)
    for game in games:
        keyboard.append([
            InlineKeyboardButton(text=game.name, callback_data=f"game_info:{game.id}")
        ])
    
    # Кнопки действий
    keyboard.append([
        InlineKeyboardButton(text="Обновить список", callback_data="games_replace"),
        InlineKeyboardButton(text="Добавить новую игру", callback_data="games_add")
    ])
    
    # Кнопка назад в главное меню
    keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="menu_back")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_game_added_actions_kb() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру после успешного добавления игры."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Завершить редактирование",
                    callback_data="games_finish"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Добавить еще одну игру",
                    callback_data="games_add_another"
                )
            ],
            [
                InlineKeyboardButton(text="Отмена", callback_data="games_cancel")
            ]
        ]
    )


def get_cancel_kb() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру с кнопкой отмены."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="games_cancel")]
        ]
    )


def get_games_confirm_replace_kb() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру для подтверждения полной замены списка игр."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Подтвердить", callback_data="games_confirm_replace"),
                InlineKeyboardButton(text="Отмена", callback_data="games_cancel")
            ]
        ]
    )