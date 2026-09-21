"""Тесты cb_session_start (fix: edit_text → answer для фото-сообщений + гейт инструкции)."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bots.client_bot.handlers.session import cb_session_start
from src.core.exceptions import SessionAlreadyActiveError


def _make_callback_with_photo():
    """Мок CallbackQuery с фото-сообщением (как карточка игры)."""
    callback = MagicMock()
    callback.from_user = MagicMock()
    callback.from_user.id = 385567246
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.photo = [MagicMock()]  # Не пустой список = фото
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    return callback


def _make_state():
    state = MagicMock()
    state.get_data = AsyncMock(return_value={
        "selected_game_id": str(uuid.uuid4())
    })
    state.update_data = AsyncMock()
    return state


def _make_container_with_passed_instruction(session_or_error):
    """Создаёт мок контейнера с пользователем, у которого инструкция пройдена."""
    container = MagicMock()

    # user_service — пользователь с instruction_passed=True (гейт пропускает)
    user = MagicMock()
    user.instruction_passed = True
    container.user_service = MagicMock()
    container.user_service.get_user = AsyncMock(return_value=user)

    # session_service
    container.session_service = MagicMock()
    if isinstance(session_or_error, Exception):
        container.session_service.start_session = AsyncMock(side_effect=session_or_error)
    else:
        container.session_service.start_session = AsyncMock(return_value=session_or_error)

    return container


@pytest.mark.asyncio
async def test_session_start_uses_answer_not_edit_text():
    """При успешном старте используется answer (не edit_text) — работает для фото."""
    callback = _make_callback_with_photo()
    state = _make_state()
    session = MagicMock()
    session.id = uuid.uuid4()

    container = _make_container_with_passed_instruction(session)

    await cb_session_start(callback, container, state)

    callback.message.answer.assert_called_once()
    callback.message.edit_text.assert_not_called()


@pytest.mark.asyncio
async def test_session_start_already_active_uses_answer():
    """При SessionAlreadyActiveError используется answer (не edit_text)."""
    callback = _make_callback_with_photo()
    state = _make_state()

    container = _make_container_with_passed_instruction(
        SessionAlreadyActiveError("Уже есть активная сессия")
    )

    await cb_session_start(callback, container, state)

    callback.message.answer.assert_called_once()
    callback.message.edit_text.assert_not_called()
    sent_text = callback.message.answer.call_args[0][0]
    assert "активная сессия" in sent_text.lower()


@pytest.mark.asyncio
async def test_session_start_gate_blocks_new_user():
    """Новый пользователь (instruction_passed=False) не может начать сессию."""
    callback = _make_callback_with_photo()
    state = _make_state()

    # Пользователь с НЕпройденной инструкцией
    user = MagicMock()
    user.instruction_passed = False
    container = MagicMock()
    container.user_service = MagicMock()
    container.user_service.get_user = AsyncMock(return_value=user)
    container.session_service = MagicMock()
    container.session_service.start_session = AsyncMock()

    await cb_session_start(callback, container, state)

    # Сессия НЕ должна создаваться
    container.session_service.start_session.assert_not_called()
    # Пользователю должно прийти сообщение о необходимости просмотра инструкции
    callback.message.answer.assert_called_once()
    sent_text = callback.message.answer.call_args[0][0]
    assert "инструкцию" in sent_text.lower()
