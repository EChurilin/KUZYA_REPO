from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
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


async def start_instruction_flow(
    anchor_message: Message, bot: Bot, container: Container, state: FSMContext
) -> None:
    """Общая логика запуска инструкции (для кнопки меню и inline-callback)."""
    user_id = anchor_message.from_user.id
    chat_id = anchor_message.chat.id

    # [v4.0] Удаляем «зависший» последний блок завершённой инструкции (если был).
    user = await container.user_service.get_user(user_id)
    if user is not None and user.last_instruction_message_id is not None:
        try:
            await bot.delete_message(
                chat_id=chat_id,
                message_id=user.last_instruction_message_id,
            )
        except TelegramBadRequest:
            pass
        await container.user_service.clear_last_instruction_message_id(user_id)

    # [v4.0] Удаляем текущий блок незавершённого прохождения (если был).
    data = await state.get_data()
    in_progress_msg_id = data.get("current_instruction_message_id")
    if in_progress_msg_id is not None:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=in_progress_msg_id)
        except TelegramBadRequest:
            pass

    version = await container.instruction_service.get_current_published_version()
    if version is None:
        await anchor_message.answer(
            "Инструкция временно недоступна. Попробуйте позже."
        )
        return

    blocks = await container.instruction_service.get_blocks_by_version(version)
    if not blocks:
        await anchor_message.answer(
            "Инструкция временно недоступна. Попробуйте позже."
        )
        return

    # Сохраняем версию и индекс, а не сами блоки.
    await state.update_data(
        instruction_version=version,
        instruction_total=len(blocks),
        current_block_index=0,
    )

    # Удаляем исходное сообщение, чтобы отправить первое сообщение начисто.
    try:
        await anchor_message.delete()
    except TelegramBadRequest:
        pass

    sent = await _send_instruction_block(anchor_message, blocks[0], 0, len(blocks))
    await state.update_data(current_instruction_message_id=sent.message_id)


@router.message(F.text == "Посмотреть инструкцию")
async def menu_view_instruction(
    message: Message, bot: Bot, container: Container, state: FSMContext
):
    """Кнопка главного меню «Посмотреть инструкцию»."""
    await start_instruction_flow(message, bot, container, state)


@router.callback_query(F.data == "instruction_start")
async def cb_instruction_start(
    callback: CallbackQuery, container: Container, state: FSMContext
):
    """Начинает показ инструкции с первого блока текущей опубликованной версии."""
    await callback.answer()
    await start_instruction_flow(callback.message, callback.bot, container, state)


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
        # [v4.0] Инструкция завершена: последний блок НЕ удаляется.
        user_id = callback.from_user.id
        await container.user_service.mark_instruction_passed(user_id)
        await container.user_service.save_last_instruction_message_id(
            user_id, callback.message.message_id
        )
        await state.clear()

        # Заменяем кнопку последнего блока на «Начать играть» с callback «play_start»,
        # чтобы повторные нажатия обрабатывались единым хендлером cb_play_start.
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Начать играть", callback_data="play_start")]
            ]
        )
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except TelegramBadRequest:
            pass

        # [фикс Пункта 2] Сразу показываем список игр — один шаг вместо двух.
        # Локальный импорт внутри функции, чтобы избежать циклического импорта
        # на уровне модуля (game_selection импортирует instruction на уровне модуля).
        from src.bots.client_bot.handlers.game_selection import _show_game_list
        await _show_game_list(callback.message, container)
        return

    # Загружаем блоки сохранённой версии.
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

    # Удаляем предыдущее сообщение и отправляем новое.
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    sent = await _send_instruction_block(
        callback.message, blocks[next_index], next_index, len(blocks)
    )
    await state.update_data(current_instruction_message_id=sent.message_id)


async def _send_instruction_block(message, block, index: int, total: int) -> Message:
    """Отправляет сообщение с текущим блоком инструкции. Возвращает отправленное сообщение."""
    # [фикс Пункта 2] Кнопка последнего блока — «Начать играть» (одна кнопка,
    # после нажатия сразу показывается список игр). Для остальных — «Понятно, далее».
    btn_text = "Понятно, далее" if index < total - 1 else "Начать играть"
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
        return await message.answer_photo(photo, caption=caption, reply_markup=kb)

    if has_media and block.media_type == MediaType.VIDEO.value:
        video = FSInputFile(block.media_path)
        caption = text if text else "Изучите прикрепленный материал."
        return await message.answer_video(video, caption=caption, reply_markup=kb)

    display_text = text if text else "Изучите материал."
    return await message.answer(display_text, reply_markup=kb)
