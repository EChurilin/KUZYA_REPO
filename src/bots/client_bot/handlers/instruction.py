from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from src.infrastructure.container import Container
from src.core.enums import MediaType

router = Router()

@router.callback_query(F.data == "instruction_start")
async def cb_instruction_start(callback: CallbackQuery, container: Container, state: FSMContext):
    """Начинает показ инструкции с первого блока"""
    await callback.answer()
    
    blocks = await container.instruction_service.get_active_blocks()
    if not blocks:
        await callback.message.edit_text("Инструкция временно недоступна. Попробуйте позже.")
        return
    
    # Сохраняем блоки и текущий индекс в состоянии FSM
    await state.update_data(instruction_blocks=blocks, current_block_index=0)
    await _send_instruction_block(callback.message, blocks[0], 0, len(blocks))

@router.callback_query(F.data.startswith("instruction_next:"))
async def cb_instruction_next(callback: CallbackQuery, state: FSMContext, container: Container):
    """Переходит к следующему блоку инструкции"""
    await callback.answer()
    
    data = await state.get_data()
    blocks = data.get("instruction_blocks", [])
    current_index = data.get("current_block_index", 0)
    
    next_index = current_index + 1
    
    if next_index < len(blocks):
        # Есть следующий блок
        await state.update_data(current_block_index=next_index)
        await _send_instruction_block(callback.message, blocks[next_index], next_index, len(blocks))
    else:
        # Инструкция завершена
        await state.clear()
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подать заявку", callback_data="application_start")]
        ])
        await callback.message.edit_text(
            "Инструкция завершена! Теперь ты готов начать зарабатывать.",
            reply_markup=kb
        )

async def _send_instruction_block(message, block, index: int, total: int):
    """Отправляет или редактирует сообщение с текущим блоком инструкции"""
    # Формируем текст кнопки с номером блока
    btn_text = "Понятно, далее" if index < total - 1 else "Понятно, начать"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, callback_data=f"instruction_next:{index}")]
    ])
    
    # Формируем текст сообщения
    text = block.text or "Изучите прикрепленный материал."
    
    # Примечание: реальная отправка медиафайлов будет реализована позже через загрузку в Telegram.
    # Сейчас мы показываем текстовую заглушку для медиа, чтобы не ломать логику.
    if block.media_type == MediaType.PHOTO.value and block.media_path:
        text = f"{text}\n\n[Здесь будет отображено фото: {block.media_path}]"
    elif block.media_type == MediaType.VIDEO.value and block.media_path:
        text = f"{text}\n\n[Здесь будет отображено видео: {block.media_path}]"
    
    # Если это первый блок, используем answer, иначе edit_text
    if index == 0:
        await message.answer(text, reply_markup=kb)
    else:
        await message.edit_text(text, reply_markup=kb)