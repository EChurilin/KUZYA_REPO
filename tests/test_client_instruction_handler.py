"""
Тесты хендлера инструкции клиента (Пункт 2).

Проверяют:
- Кнопка последнего блока называется «Начать играть».
- При завершении инструкции устанавливается флаг и сразу показывается список игр.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.bots.client_bot.handlers.instruction import (
    cb_instruction_next,
    _send_instruction_block,
)

USER_ID = 385567246


@pytest.mark.asyncio
async def test_last_block_button_text_is_start_playing():
    """Кнопка последнего блока — «Начать играть» (одна кнопка)."""
    block = MagicMock()
    block.text = "Последний блок"
    block.media_path = None
    block.media_type = "text"

    message = MagicMock()
    message.answer = AsyncMock(return_value=MagicMock(message_id=1))

    await _send_instruction_block(message, block, index=2, total=3)

    message.answer.assert_called_once()
    call_kwargs = message.answer.call_args[1]
    kb = call_kwargs["reply_markup"]
    button_text = kb.inline_keyboard[0][0].text
    assert button_text == "Начать играть"


@pytest.mark.asyncio
async def test_middle_block_button_text_is_next():
    """Кнопка не-последнего блока — «Понятно, далее»."""
    block = MagicMock()
    block.text = "Первый блок"
    block.media_path = None
    block.media_type = "text"

    message = MagicMock()
    message.answer = AsyncMock(return_value=MagicMock(message_id=1))

    await _send_instruction_block(message, block, index=0, total=3)

    call_kwargs = message.answer.call_args[1]
    kb = call_kwargs["reply_markup"]
    button_text = kb.inline_keyboard[0][0].text
    assert button_text == "Понятно, далее"


@pytest.mark.asyncio
async def test_finish_instruction_sets_flag_and_shows_game_list():
    """При завершении инструкции: флаг устанавливается и сразу показывается список игр."""
    callback = MagicMock()
    callback.from_user = MagicMock()
    callback.from_user.id = USER_ID
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.message_id = 133
    callback.message.edit_reply_markup = AsyncMock()

    state = MagicMock()
    state.get_data = AsyncMock(return_value={
        "instruction_version": 2,
        "instruction_total": 2,
        "current_block_index": 1,
    })
    state.clear = AsyncMock()
    state.update_data = AsyncMock()

    container = MagicMock()
    container.user_service = MagicMock()
    container.user_service.mark_instruction_passed = AsyncMock()
    container.user_service.save_last_instruction_message_id = AsyncMock()

    with patch(
        "src.bots.client_bot.handlers.game_selection._show_game_list",
        new_callable=AsyncMock,
    ) as mock_show_games:
        await cb_instruction_next(callback, state, container)

    container.user_service.mark_instruction_passed.assert_called_once_with(USER_ID)
    container.user_service.save_last_instruction_message_id.assert_called_once_with(
        USER_ID, 133
    )
    state.clear.assert_called_once()
    mock_show_games.assert_called_once()
