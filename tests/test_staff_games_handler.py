"""
Тесты хендлеров управления играми (staff_bot).

Покрывают Пункт 3 ТЗ:
- Корректность клавиатур в edit_text (InlineKeyboard, не Reply).
- Режимы add / replace различаются и правильно сохраняют игры.
- Вызовы GameService (публичные методы) вместо приватных полей.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import InlineKeyboardMarkup

from src.bots.staff_bot.handlers import games as games_handlers

ADMIN_ID = 385567246


@pytest.fixture
def mock_container():
    container = MagicMock()
    container.game_service = AsyncMock()
    container.game_service.add_game = AsyncMock()
    container.game_service.replace_game_list = AsyncMock()
    container.game_service.delete_game = AsyncMock()
    container.media_service = AsyncMock()
    return container


@pytest.fixture
def mock_state():
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.fixture
def mock_callback():
    cb = MagicMock()
    cb.from_user = MagicMock()
    cb.from_user.id = ADMIN_ID
    cb.answer = AsyncMock()
    cb.message = MagicMock()
    cb.message.edit_text = AsyncMock()
    cb.message.answer = AsyncMock()
    return cb


# ==== finish_adding_games: корректность клавиатуры ====

@pytest.mark.asyncio
async def test_finish_add_mode_uses_inline_keyboard(
    mock_callback, mock_container, mock_state
):
    """В режиме add edit_text использует InlineKeyboardMarkup (не Reply)."""
    mock_state.get_data = AsyncMock(return_value={
        "mode": "add",
        "current_game": {
            "name": "TestGame",
            "link": "https://test",
            "photo_path": "/tmp/test.jpg",
        },
        "draft_games": [],
        "last_added_game_id": None,
    })

    with patch.object(games_handlers.settings, "staff_bot", MagicMock(admin_ids=[ADMIN_ID])):
        await games_handlers.finish_adding_games(mock_callback, mock_state, mock_container)

    mock_callback.message.edit_text.assert_called_once()
    kwargs = mock_callback.message.edit_text.call_args[1]
    assert isinstance(kwargs.get("reply_markup"), InlineKeyboardMarkup)


@pytest.mark.asyncio
async def test_finish_add_mode_saves_current_game_via_service(
    mock_callback, mock_container, mock_state
):
    """В режиме add текущая игра сохраняется через game_service.add_game (публичный метод)."""
    mock_state.get_data = AsyncMock(return_value={
        "mode": "add",
        "current_game": {
            "name": "TestGame",
            "link": "https://test",
            "photo_path": "/tmp/test.jpg",
        },
        "draft_games": [],
        "last_added_game_id": None,
    })

    with patch.object(games_handlers.settings, "staff_bot", MagicMock(admin_ids=[ADMIN_ID])):
        await games_handlers.finish_adding_games(mock_callback, mock_state, mock_container)

    mock_container.game_service.add_game.assert_called_once()


@pytest.mark.asyncio
async def test_finish_replace_mode_calls_replace_game_list(
    mock_callback, mock_container, mock_state
):
    """В режиме replace вызывается game_service.replace_game_list (публичный метод)."""
    mock_state.get_data = AsyncMock(return_value={
        "mode": "replace",
        "current_game": {
            "name": "NewGame",
            "link": "https://new",
            "photo_path": "/tmp/new.jpg",
        },
        "draft_games": [],
    })

    with patch.object(games_handlers.settings, "staff_bot", MagicMock(admin_ids=[ADMIN_ID])):
        await games_handlers.finish_adding_games(mock_callback, mock_state, mock_container)

    mock_container.game_service.replace_game_list.assert_called_once()
    # replace_game_list получил список из одной игры
    call_args = mock_container.game_service.replace_game_list.call_args[0][0]
    assert len(call_args) == 1
    assert call_args[0].name == "NewGame"


@pytest.mark.asyncio
async def test_finish_replace_with_empty_draft_shows_cancel_message(
    mock_callback, mock_container, mock_state
):
    """В режиме replace без draft_games показывается сообщение об отмене."""
    mock_state.get_data = AsyncMock(return_value={
        "mode": "replace",
        "current_game": None,
        "draft_games": [],
    })

    with patch.object(games_handlers.settings, "staff_bot", MagicMock(admin_ids=[ADMIN_ID])):
        await games_handlers.finish_adding_games(mock_callback, mock_state, mock_container)

    mock_callback.message.edit_text.assert_called_once()
    text = mock_callback.message.edit_text.call_args[0][0]
    assert "Нет игр" in text or "отменена" in text


# ==== cancel_game_operation: корректность клавиатуры ====

@pytest.mark.asyncio
async def test_cancel_uses_inline_keyboard(
    mock_callback, mock_container, mock_state
):
    """Отмена использует InlineKeyboardMarkup в edit_text."""
    mock_state.get_data = AsyncMock(return_value={
        "mode": "add",
        "current_game": None,
        "draft_games": [],
        "last_added_game_id": None,
    })

    with patch.object(games_handlers.settings, "staff_bot", MagicMock(admin_ids=[ADMIN_ID])):
        await games_handlers.cancel_game_operation(mock_callback, mock_state, mock_container)

    kwargs = mock_callback.message.edit_text.call_args[1]
    assert isinstance(kwargs.get("reply_markup"), InlineKeyboardMarkup)


@pytest.mark.asyncio
async def test_cancel_in_add_mode_deletes_last_added_game(
    mock_callback, mock_container, mock_state
):
    """В режиме add отмена удаляет последнюю добавленную игру через game_service.delete_game."""
    game_id = "11111111-1111-1111-1111-111111111111"
    mock_state.get_data = AsyncMock(return_value={
        "mode": "add",
        "current_game": None,
        "draft_games": [],
        "last_added_game_id": game_id,
    })

    with patch.object(games_handlers.settings, "staff_bot", MagicMock(admin_ids=[ADMIN_ID])):
        await games_handlers.cancel_game_operation(mock_callback, mock_state, mock_container)

    mock_container.game_service.delete_game.assert_called_once()
