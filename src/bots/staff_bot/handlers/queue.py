from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from src.infrastructure.container import Container
from src.config.settings import settings
import uuid

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.staff_bot.admin_ids

@router.message(Command("queue"))
async def cmd_queue(message: Message, container: Container):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для использования этой команды.")
        return

    applications = await container.application_service._app_repo.get_pending_review(limit=10)

    if not applications:
        await message.answer("Очередь пуста. Новых заявок на проверку пока нет.")
        return

    text = "В очереди на проверку:\n\nВыберите заявку для модерации:"

    keyboard = []
    for app in applications:
        btn_text = f"Заявка #{str(app.id)[:8]} ({app.actual_screenshot_count} скрин.)"
        if app.auto_closed:
            btn_text += " [авто]"

        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"review_app:{app.id}")
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text, reply_markup=kb)

@router.message(F.text == "Очередь заявок")
async def menu_queue(message: Message, container: Container):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return

    applications = await container.application_service._app_repo.get_pending_review(limit=10)

    if not applications:
        await message.answer("Очередь пуста. Новых заявок на проверку пока нет.")
        return

    text = "В очереди на проверку:\n\nВыберите заявку для модерации:"

    keyboard = []
    for app in applications:
        btn_text = f"Заявка #{str(app.id)[:8]} ({app.actual_screenshot_count} скрин.)"
        if app.auto_closed:
            btn_text += " [авто]"

        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"review_app:{app.id}")
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data.startswith("review_app:"))
async def cb_review_app(callback: CallbackQuery, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await callback.answer()

    app_id_str = callback.data.split(":")[1]
    try:
        app_id = uuid.UUID(app_id_str)
    except ValueError:
        await callback.message.edit_text("Ошибка: некорректный ID заявки.")
        return

    app = await container.application_service._app_repo.get_by_id(app_id)
    if not app:
        await callback.message.edit_text("Заявка не найдена.")
        return

    screenshots = await container.application_service._screenshot_repo.get_by_application(app_id)

    approved_count = sum(1 for s in screenshots if s.status == "approved")
    rejected_count = sum(1 for s in screenshots if s.status == "rejected")
    pending_count = sum(1 for s in screenshots if s.status == "pending")

    status_text = "Автозакрытие" if app.auto_closed else "Ручное завершение"

    report = (
        f"Модерация заявки #{str(app.id)[:8]}\n"
        f"Пользователь: {app.user_id}\n"
        f"Тип закрытия: {status_text}\n"
        f"Всего скриншотов: {app.actual_screenshot_count}\n"
        f"Одобрено: {approved_count}\n"
        f"Отклонено: {rejected_count}\n"
        f"На проверке: {pending_count}\n\n"
        f"Ниже будут отображены скриншоты для проверки. Используйте кнопки под каждым скриншотом."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Завершить проверку и начислить награду", callback_data=f"finalize_app:{app.id}")],
        [InlineKeyboardButton(text="Назад к очереди", callback_data="queue_back")]
    ])

    try:
        await callback.message.edit_text(report, reply_markup=kb)
    except TelegramBadRequest:
        await callback.message.answer(report, reply_markup=kb)

    for s in screenshots:
        if s.status == "approved":
            status_label = "[одобрено]"
        elif s.status == "rejected":
            status_label = "[отклонено]"
        else:
            status_label = "[на проверке]"

        screen_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Одобрить", callback_data=f"approve_scr:{s.id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"reject_scr:{s.id}")
            ]
        ])

        photo_path = Path(s.storage_path)
        if photo_path.exists():
            try:
                await callback.message.answer_photo(
                    FSInputFile(s.storage_path),
                    caption=f"Скриншот {status_label}",
                    reply_markup=screen_kb
                )
            except TelegramBadRequest:
                pass
        else:
            try:
                await callback.message.answer(
                    f"Скриншот {status_label}\nФайл не найден.",
                    reply_markup=screen_kb
                )
            except TelegramBadRequest:
                pass