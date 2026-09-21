"""Тесты вспомогательной функции _send_summary_message (Партия 4, Пункт 1 ТЗ)."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bots.staff_bot.handlers.queue import _send_summary_message


def _make_container(summary_message_id=None):
    """Создаёт мок контейнера с нужными сервисами."""
    container = MagicMock()
    container.review_service = MagicMock()
    container.review_service.get_screenshots_summary = AsyncMock(return_value={
        "approved": 2,
        "rejected": 1,
        "pending": 0,
        "total": 3,
        "amount_to_credit": 30,
    })
    app = MagicMock()
    app.id = uuid.uuid4()
    app.user_id = 385567246
    app.auto_closed = False
    app.summary_message_id = summary_message_id
    container.application_service = MagicMock()
    container.application_service._app_repo = MagicMock()
    container.application_service._app_repo.get_by_id = AsyncMock(return_value=app)
    container.application_service._app_repo.set_summary_message_id = AsyncMock()
    return container


def _make_callback():
    """Создаёт мок CallbackQuery."""
    callback = MagicMock()
    callback.bot = MagicMock()
    callback.bot.edit_message_text = AsyncMock()
    callback.message = MagicMock()
    callback.message.chat = MagicMock()
    callback.message.chat.id = 123
    callback.message.answer = AsyncMock(return_value=MagicMock(message_id=999))
    return callback


@pytest.mark.asyncio
async def test_send_summary_creates_new_message():
    """Если итогового сообщения нет — отправляется новое и сохраняется message_id."""
    callback = _make_callback()
    container = _make_container(summary_message_id=None)
    app_id = uuid.uuid4()

    await _send_summary_message(callback, container, app_id)

    callback.message.answer.assert_called_once()
    container.application_service._app_repo.set_summary_message_id.assert_called_once_with(
        app_id, 999
    )


@pytest.mark.asyncio
async def test_send_summary_updates_existing_message():
    """Если итоговое сообщение есть — оно обновляется, новое не отправляется."""
    callback = _make_callback()
    container = _make_container(summary_message_id=555)
    app_id = uuid.uuid4()

    await _send_summary_message(callback, container, app_id)

    callback.bot.edit_message_text.assert_called_once()
    callback.message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_send_summary_contains_amount():
    """Текст итогового сообщения содержит сумму к начислению."""
    callback = _make_callback()
    container = _make_container(summary_message_id=None)
    app_id = uuid.uuid4()

    await _send_summary_message(callback, container, app_id)

    sent_text = callback.message.answer.call_args[1].get("text") or callback.message.answer.call_args[0][0]
    assert "Будет начислено: 30" in sent_text
    assert "Одобрено: 2" in sent_text
    assert "Отклонено: 1" in sent_text
