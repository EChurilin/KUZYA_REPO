"""Тесты cb_session_start и cb_session_finish (гейт инструкции, кулдаун, пустая сессия, возврат меню)."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bots.client_bot.handlers.session import cb_session_start, cb_session_finish
from src.core.exceptions import SessionAlreadyActiveError, SessionCooldownError


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


def _make_state(session_id=None):
    state = MagicMock()
    state.get_data = AsyncMock(return_value={
        "selected_game_id": str(uuid.uuid4()),
        "session_id": str(session_id) if session_id else None,
    })
    state.update_data = AsyncMock()
    state.clear = AsyncMock()
    return state


def _make_container_with_passed_instruction(session_or_error, application=None):
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

    # application_service
    container.application_service = MagicMock()
    container.application_service.finish_session = AsyncMock(return_value=application)

    return container


class TestSessionStart:
    @pytest.mark.asyncio
    async def test_session_start_uses_answer_not_edit_text(self):
        """При успешном старте используется answer (не edit_text) — работает для фото."""
        callback = _make_callback_with_photo()
        state = _make_state()
        session = MagicMock()
        session.id = uuid.uuid4()

        container = _make_container_with_passed_instruction(session)

        await cb_session_start(callback, container, state)

        callback.message.answer.assert_called_once()
        callback.message.edit_text.assert_not_called()
        # Проверяем, что reply_markup содержит remove_menu_kb
        call_kwargs = callback.message.answer.call_args[1]
        assert "reply_markup" in call_kwargs

    @pytest.mark.asyncio
    async def test_session_start_already_active_uses_answer(self):
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
    async def test_session_start_gate_blocks_new_user(self):
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

    @pytest.mark.asyncio
    async def test_session_start_cooldown_blocks(self):
        """Кулдаун: SessionCooldownError → сообщение с текстом кулдауна."""
        callback = _make_callback_with_photo()
        state = _make_state()

        container = _make_container_with_passed_instruction(
            SessionCooldownError("Новую сессию можно начать через 7 мин.")
        )

        await cb_session_start(callback, container, state)

        callback.message.answer.assert_called_once()
        sent_text = callback.message.answer.call_args[0][0]
        assert "мин" in sent_text.lower()
        # Сессия не должна создаваться в state
        state.update_data.assert_not_called()


class TestSessionFinish:
    @pytest.mark.asyncio
    async def test_session_finish_empty_no_application(self):
        """Пустая сессия: finish_session возвращает None → сообщение без заявки + главное меню."""
        session_id = uuid.uuid4()
        callback = _make_callback_with_photo()
        state = _make_state(session_id=session_id)

        container = _make_container_with_passed_instruction(None, application=None)

        await cb_session_finish(callback, container, state)

        container.application_service.finish_session.assert_awaited_once()
        state.clear.assert_awaited_once()
        callback.message.answer.assert_called_once()
        sent_text = callback.message.answer.call_args[0][0]
        assert "скриншоты не были отправлены" in sent_text.lower()
        # Проверяем, что reply_markup содержит главное меню
        call_kwargs = callback.message.answer.call_args[1]
        assert "reply_markup" in call_kwargs

    @pytest.mark.asyncio
    async def test_session_finish_with_screenshots_creates_application(self):
        """Непустая сессия: finish_session возвращает Application → сообщение с заявкой + главное меню."""
        session_id = uuid.uuid4()
        callback = _make_callback_with_photo()
        state = _make_state(session_id=session_id)

        application = MagicMock()
        application.id = uuid.uuid4()
        application.status = "pending_review"

        container = _make_container_with_passed_instruction(None, application=application)

        await cb_session_finish(callback, container, state)

        container.application_service.finish_session.assert_awaited_once()
        state.clear.assert_awaited_once()
        callback.message.answer.assert_called_once()
        sent_text = callback.message.answer.call_args[0][0]
        assert "заявка отправлена" in sent_text.lower()
        # Проверяем, что reply_markup содержит главное меню
        call_kwargs = callback.message.answer.call_args[1]
        assert "reply_markup" in call_kwargs

    @pytest.mark.asyncio
    async def test_session_finish_no_session_id(self):
        """Нет session_id в state → сообщение об ошибке + главное меню."""
        callback = _make_callback_with_photo()
        state = _make_state(session_id=None)  # session_id = None

        container = _make_container_with_passed_instruction(None)

        await cb_session_finish(callback, container, state)

        container.application_service.finish_session.assert_not_awaited()
        callback.message.answer.assert_called_once()
        sent_text = callback.message.answer.call_args[0][0]
        assert "нет активной сессии" in sent_text.lower()
        call_kwargs = callback.message.answer.call_args[1]
        assert "reply_markup" in call_kwargs