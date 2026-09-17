from pathlib import Path
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    FSInputFile,
)
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from src.infrastructure.container import Container
from src.core.enums import MediaType

router = Router()


@router.callback_query(F.data == "instruction_start")
async def cb_instruction_start(
    callback: CallbackQuery, container: Container, state: FSMContext
):
    """Начинает показ инструкции с первого блока текущей опубликованной версии."""
    await callback.answer()

    version = await container.instruction_service.get_current_published_version()
    if version is None:
        await callback.message.answer(
            "Инструкция временно недоступна. Попробуйте позже."
        )
        return

    blocks = await container.instruction_service.get_blocks_by_version(version)
    if not blocks:
        await callback.message.answer(
            "Инструкция временно недоступна. Попробуйте позже."
        )
        return

    # Сохраняем версию и индекс, а не сами блоки
    await state.update_data(
        instruction_version=version,
        instruction_total=len(blocks),
        current_block_index=0,
    )

    # Удаляем исходное сообщение, чтобы отправить первое сообщение начисто
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    await _send_instruction_block(callback.message, blocks[0], 0, len(blocks))


@router.callback_query(F.data.startswith("instruction_next:"))
async def cb_instruction_next(
    callback: CallbackQuery, state: FSMContext, container: Container
):
    """Переходит к следующему блоку инструкции той же версии."""
    await callback.answer()

    data = await state.get_data()
    version = data.get("instruction_version")
    current_index = data.get("current_block_index", 0)
    total = data.get("instruction_total", 0)
    next_index = current_index + 1

    if version is None:
        await state.clear()
        await callback.message.answer(
            "Ошибка: версия инструкции не найдена. Начните заново с /start."
        )
        return

    if next_index >= total:
        # Инструкция завершена
        await state.clear()
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Подать заявку", callback_data="application_start"
                    )
                ]
            ]
        )
        # Удаляем последнее сообщение инструкции и отправляем финальное
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(
            "Инструкция завершена! Теперь ты готов начать зарабатывать.",
            reply_markup=kb,
        )
        return

    # Загружаем блоки сохранённой версии
    blocks = await container.instruction_service.get_blocks_by_version(version)
    if not blocks or next_index >= len(blocks):
        await state.clear()
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(
            "Эта версия инструкции больше недоступна. "
            "Пожалуйста, начните заново с /start."
        )
        return

    await state.update_data(current_block_index=next_index)

    # Удаляем предыдущее сообщение и отправляем новое
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    await _send_instruction_block(
        callback.message, blocks[next_index], next_index, len(blocks)
    )


async def _send_instruction_block(message, block, index: int, total: int):
    """Отправляет сообщение с текущим блоком инструкции."""
    btn_text = "Понятно, далее" if index < total - 1 else "Понятно, начать"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, callback_data=f"instruction_next:{index}")]
        ]
    )

    text = block.text or ""
    has_media = block.media_path and Path(block.media_path).exists()

    if has_media and block.media_type == MediaType.PHOTO.value:
        photo = FSInputFile(block.media_path)
        caption = text if text else "Изучите прикрепленный материал."
        await message.answer_photo(photo, caption=caption, reply_markup=kb)

    elif has_media and block.media_type == MediaType.VIDEO.value:
        video = FSInputFile(block.media_path)
        caption = text if text else "Изучите прикрепленный материал."
        await message.answer_video(video, caption=caption, reply_markup=kb)

    else:
        display_text = text if text else "Изучите материал."
        await message.answer(display_text, reply_markup=kb)