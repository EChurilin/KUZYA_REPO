import uuid
from datetime import datetime, timezone
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from src.infrastructure.container import Container
from src.config.settings import settings
from src.core.entities import InstructionBlock
from src.bots.staff_bot.states import InstructionManagement
from src.bots.staff_bot.keyboards.instruction_kb import (
    get_instruction_publish_kb,
    get_instruction_cancel_kb,
    get_instruction_back_to_menu_kb,
)
from src.bots.staff_bot.keyboards.menu_kb import get_main_menu_kb

router = Router()

MAX_STAGES = 20


def is_admin(user_id: int) -> bool:
    return user_id in settings.staff_bot.admin_ids


@router.message(F.text == "Инструкция")
async def show_instruction(message: Message, container: Container, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return
    await state.clear()

    blocks = await container.instruction_service.get_active_blocks()

    if not blocks:
        await message.answer(
            "Текущая инструкция пуста.\n\n"
            "Нажмите «Начать редактирование», чтобы создать новую версию.",
            reply_markup=get_instruction_back_to_menu_kb()
        )
        return

    version = await container.instruction_service.get_current_published_version()
    text = f"Текущая инструкция (версия {version}, блоков: {len(blocks)}):\n\n"

    for i, block in enumerate(blocks, 1):
        parts = [f"Этап {i}:"]
        if block.text:
            text_preview = block.text[:100] + ("..." if len(block.text) > 100 else "")
            parts.append(f"  Текст: {text_preview}")
        if block.media_type and block.media_type != "text":
            parts.append(f"  Медиа: {block.media_type}")
        if not block.text and (not block.media_type or block.media_type == "text"):
            parts.append("  (пустой блок)")
        text += "\n".join(parts) + "\n\n"

    text += "Нажмите «Начать редактирование», чтобы создать новую версию инструкции."

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать редактирование", callback_data="instruction_start")],
        [InlineKeyboardButton(text="Назад в меню", callback_data="menu_back")]
    ])

    # Если текст слишком длинный, разбиваем на несколько сообщений
    if len(text) > 3500:
        await message.answer("Текущая инструкция очень длинная, показываю по частям...")
        for i, block in enumerate(blocks[:10], 1):
            parts = [f"Этап {i}:"]
            if block.text:
                text_preview = block.text[:200] + ("..." if len(block.text) > 200 else "")
                parts.append(f"  Текст: {text_preview}")
            if block.media_type and block.media_type != "text":
                parts.append(f"  Медиа: {block.media_type}")
            await message.answer("\n".join(parts))
        if len(blocks) > 10:
            await message.answer(f"... и ещё {len(blocks) - 10} блоков.", reply_markup=kb)
        else:
            await message.answer(".", reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "instruction_start")
async def start_instruction_edit(callback: CallbackQuery, state: FSMContext, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()

    max_version = await container.instruction_service.get_max_version()
    new_version = max_version + 1

    await state.update_data(
        version=new_version,
        blocks=[],
        current_block_index=0,
    )

    await callback.message.edit_text(
        f"Создание новой инструкции (версия {new_version}).\n\n"
        f"Введите количество этапов (от 1 до {MAX_STAGES}):",
        reply_markup=get_instruction_cancel_kb()
    )
    await state.set_state(InstructionManagement.waiting_for_count)


@router.message(StateFilter(InstructionManagement.waiting_for_count), F.text)
async def process_stage_count(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return

    text = message.text.strip()
    if not text.isdigit():
        await message.answer(
            f"Нужно ввести число от 1 до {MAX_STAGES}. Попробуйте снова:",
            reply_markup=get_instruction_cancel_kb()
        )
        return

    count = int(text)
    if count < 1 or count > MAX_STAGES:
        await message.answer(
            f"Количество этапов должно быть от 1 до {MAX_STAGES}. Попробуйте снова:",
            reply_markup=get_instruction_cancel_kb()
        )
        return

    data = await state.get_data()
    await state.update_data(total_blocks=count, blocks=[], current_block_index=0)

    await message.answer(
        f"Будет создано {count} этапов.\n\n"
        f"Этап 1 из {count}.\n"
        f"Отправьте одно сообщение для этого этапа.\n"
        f"Это может быть: текст, фото, видео или фото/видео с подписью.",
        reply_markup=get_instruction_cancel_kb()
    )
    await state.set_state(InstructionManagement.waiting_for_block)


@router.message(StateFilter(InstructionManagement.waiting_for_block))
async def process_block_content(message: Message, state: FSMContext, container: Container):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return

    # Проверяем, что сообщение допустимого типа
    if not (message.text or message.photo or message.video):
        await message.answer(
            "Неподдерживаемый тип сообщения.\n"
            "Отправьте текст, фото или видео.",
            reply_markup=get_instruction_cancel_kb()
        )
        return

    data = await state.get_data()
    total_blocks = data["total_blocks"]
    current_index = data["current_block_index"]
    blocks = data.get("blocks", [])

    # Обрабатываем контент
    text = message.text or message.caption
    media_type = "text"
    media_path = None

    if message.photo or message.video:
        media_type, media_path = await container.media_service.save_instruction_media(message)

    # Создаём блок
    now = datetime.now(timezone.utc)
    block = {
        "order": current_index + 1,
        "text": text,
        "media_type": media_type,
        "media_path": media_path,
        "created_at": now.isoformat(),
    }
    blocks.append(block)
    current_index += 1

    await state.update_data(blocks=blocks, current_block_index=current_index)

    if current_index >= total_blocks:
        # Все блоки собраны, переходим к предпросмотру
        await state.set_state(InstructionManagement.previewing)
        await _show_preview(message, state, container)
    else:
        await message.answer(
            f"Этап {current_index} сохранён.\n\n"
            f"Этап {current_index + 1} из {total_blocks}.\n"
            f"Отправьте следующее сообщение:",
            reply_markup=get_instruction_cancel_kb()
        )


async def _show_preview(message: Message, state: FSMContext, container: Container):
    """Показывает предпросмотр всей инструкции перед публикацией."""
    data = await state.get_data()
    version = data["version"]
    blocks = data["blocks"]

    text = f"Предпросмотр новой инструкции (версия {version}):\n\n"
    for i, block in enumerate(blocks, 1):
        parts = [f"Этап {i}:"]
        if block["text"]:
            text_preview = block["text"][:150] + ("..." if len(block["text"]) > 150 else "")
            parts.append(f"  Текст: {text_preview}")
        if block["media_type"] != "text":
            parts.append(f"  Медиа: {block['media_type']}")
        text += "\n".join(parts) + "\n\n"

    if len(text) > 3800:
        # Разбиваем предпросмотр на несколько сообщений
        await message.answer("Предпросмотр (часть 1):")
        chunk_size = 5
        for i in range(0, len(blocks), chunk_size):
            chunk = blocks[i:i + chunk_size]
            chunk_text = ""
            for j, block in enumerate(chunk, i + 1):
                parts = [f"Этап {j}:"]
                if block["text"]:
                    text_preview = block["text"][:100] + ("..." if len(block["text"]) > 100 else "")
                    parts.append(f"  Текст: {text_preview}")
                if block["media_type"] != "text":
                    parts.append(f"  Медиа: {block['media_type']}")
                chunk_text += "\n".join(parts) + "\n\n"

            if i + chunk_size >= len(blocks):
                # Последний чанк — добавляем клавиатуру
                await message.answer(
                    chunk_text + "\nОпубликовать эту инструкцию?",
                    reply_markup=get_instruction_publish_kb()
                )
            else:
                await message.answer(chunk_text)
    else:
        await message.answer(
            text + "Опубликовать эту инструкцию?",
            reply_markup=get_instruction_publish_kb()
        )


@router.callback_query(F.data == "instruction_publish")
async def publish_instruction(callback: CallbackQuery, state: FSMContext, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer("Публикация...")

    data = await state.get_data()
    version = data["version"]
    blocks_data = data["blocks"]

    now = datetime.now(timezone.utc)
    blocks = []
    for b in blocks_data:
        block = InstructionBlock(
            id=uuid.uuid4(),
            order=b["order"],
            text=b["text"],
            media_type=b["media_type"],
            media_path=b["media_path"],
            is_active=True,
            created_at=now,
            updated_at=now,
            version=version,
            is_published=False,
        )
        blocks.append(block)

    try:
        await container.instruction_service.create_draft(blocks, version)
        await container.instruction_service.publish_version(version)

        await callback.message.edit_text(
            f"Инструкция версии {version} успешно опубликована.\n"
            f"Блоков: {len(blocks)}\n\n"
            f"Новые пользователи увидят эту версию.\n"
            f"Пользователи, уже проходящие старую инструкцию, продолжат её до конца.\n"
            f"Старая версия будет автоматически удалена через 24 часа.",
            reply_markup=get_instruction_back_to_menu_kb()
        )
    except Exception as e:
        await callback.message.edit_text(
            f"Ошибка при публикации: {str(e)}",
            reply_markup=get_instruction_back_to_menu_kb()
        )

    await state.clear()


@router.callback_query(F.data == "instruction_cancel")
async def cancel_instruction(callback: CallbackQuery, state: FSMContext, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer("Редактирование отменено")

    data = await state.get_data()
    version = data.get("version")
    blocks = data.get("blocks", [])

    # Удаляем сохранённые медиафайлы
    for block in blocks:
        if block.get("media_path"):
            file_path = Path(block["media_path"])
            if file_path.exists():
                file_path.unlink()

    # Удаляем черновик из БД, если он был сохранён
    if version:
        try:
            await container.instruction_service.delete_draft(version)
        except Exception:
            pass

    await state.clear()
    await callback.message.edit_text(
        "Редактирование инструкции отменено. Черновик удалён.",
        reply_markup=get_instruction_back_to_menu_kb()
    )


@router.callback_query(F.data == "menu_back")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("Главное меню:")


