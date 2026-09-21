"""Тесты хендлеров модерации (Партия 4, Пункт 1 ТЗ)."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bots.staff_bot.handlers.review import _update_screenshot_message


def _make_callback_with_photo():
    """Мок CallbackQuery с сообщением-фото."""
    callback = MagicMock()
    callback.message = MagicMock()
    callback.message.photo = [MagicMock()]  # Не пустой список = фото
    callback.message.edit_caption = AsyncMock()
    callback.message.edit_text = AsyncMock()
    return callback


def _make_callback_with_text():
    """Мок CallbackQuery с текстовым сообщением."""
    callback = MagicMock()
    callback.message = MagicMock()
    callback.message.photo = None  # Нет фото = текст
    callback.message.edit_text = AsyncMock()
    callback.message.edit_caption = AsyncMock()
    return callback


@pytest.mark.asyncio
async def test_update_screenshot_message_photo():
    """Для фото-сообщения вызывается edit_caption."""
    callback = _make_callback_with_photo()
    kb = MagicMock()

    await _update_screenshot_message(callback, "[одобрено]", kb)

    callback.message.edit_caption.assert_called_once_with(
        caption="Скриншот [одобрено]",
        reply_markup=kb,
    )
    callback.message.edit_text.assert_not_called()


@pytest.mark.asyncio
async def test_update_screenshot_message_text():
    """Для текстового сообщения вызывается edit_text."""
    callback = _make_callback_with_text()
    kb = MagicMock()

    await _update_screenshot_message(callback, "[отклонено]", kb)

    callback.message.edit_text.assert_called_once()
    callback.message.edit_caption.assert_not_called()
