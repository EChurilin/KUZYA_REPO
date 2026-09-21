from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from src.infrastructure.container import Container
from src.config.settings import settings
from src.bots.staff_bot.keyboards.review_kb import (
    get_screenshot_review_kb,
    get_screenshot_decided_kb,
    get_reward_kb,
)
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


async def _send_summary_message(callback: CallbackQuery, container: Container, app_id: uuid.UUID) -> None:
    """Отправляет или обновляет итоговое сообщение для заявки.

    Вызывается, когда все скриншоты оценены. Содержит сводку и кнопку «Начислить награду».
    """
    summary = await container.review_service.get_screenshots_summary(app_id)
    app = await container.application_service._app_repo.get_by_id(app_id)
    if not app:
        return

    status_text = "Автозакрытие" if app.auto_closed else "Ручное завершение"
    text = (
        f"Модерация заявки #{str(app_id)[:8]}\n"
        f"Пользователь: {app.user_id}\n"
        f"Тип закрытия: {status_text}\n\n"
        f"Одобрено: {summary['approved']}\n"
        f"Отклонено: {summary['rejected']}\n"
        f"Будет начислено: {summary['amount_to_credit']} звёзд"
    )

    kb = get_reward_kb(app_id)

    # Если итоговое сообщение уже было — обновляем его
    if app.summary_message_id is not None:
        try:
            await callback.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=app.summary_message_id,
                text=text,
                reply_markup=kb,
            )
            return
        except TelegramBadRequest:
            pass  # Сообщение не найдено или не изменилось — отправляем новое

    # Отправляем новое итоговое сообщение и сохраняем его message_id
    sent = await callback.message.answer(text, reply_markup=kb)
    await container.application_service._app_repo.set_summary_message_id(app_id, sent.message_id)


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

    if not screenshots:
        await callback.message.edit_text("В заявке нет скриншотов.")
        return

    # [Партия 4] Удаляем старые сообщения скриншотов и итоговое сообщение (при повторном открытии)
    for s in screenshots:
        if s.staff_message_id is not None:
            try:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=s.staff_message_id,
                )
            except TelegramBadRequest:
                pass  # Сообщение уже удалено или не найдено

    if app.summary_message_id is not None:
        try:
            await callback.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=app.summary_message_id,
            )
        except TelegramBadRequest:
            pass

    # Заголовок: краткая информация о заявке
    status_text = "Автозакрытие" if app.auto_closed else "Ручное завершение"
    header = (
        f"Модерация заявки #{str(app.id)[:8]}\n"
        f"Пользователь: {app.user_id}\n"
        f"Тип закрытия: {status_text}\n"
        f"Всего скриншотов: {app.actual_screenshot_count}\n\n"
        f"Используйте кнопки под каждым скриншотом."
    )

    kb_back = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад к очереди", callback_data="queue_back")]
    ])

    try:
        await callback.message.edit_text(header, reply_markup=kb_back)
    except TelegramBadRequest:
        await callback.message.answer(header, reply_markup=kb_back)

    # Отправляем скриншоты с кнопками в зависимости от статуса
    for s in screenshots:
        if s.status == "approved":
            status_label = "[одобрено]"
            screen_kb = get_screenshot_decided_kb(s.id)
        elif s.status == "rejected":
            status_label = "[отклонено]"
            screen_kb = get_screenshot_decided_kb(s.id)
        else:
            status_label = "[на проверке]"
            screen_kb = get_screenshot_review_kb(s.id)

        photo_path = Path(s.storage_path)
        if photo_path.exists():
            try:
                sent = await callback.message.answer_photo(
                    FSInputFile(s.storage_path),
                    caption=f"Скриншот {status_label}",
                    reply_markup=screen_kb
                )
                # Сохраняем message_id для последующего удаления при финализации
                await container.application_service._screenshot_repo.set_staff_message_id(s.id, sent.message_id)
            except TelegramBadRequest:
                pass
        else:
            try:
                sent = await callback.message.answer(
                    f"Скриншот {status_label}\nФайл не найден.",
                    reply_markup=screen_kb
                )
                await container.application_service._screenshot_repo.set_staff_message_id(s.id, sent.message_id)
            except TelegramBadRequest:
                pass

    # Если все скриншоты уже оценены (возврат к заявке) — показываем итоговое сообщение
    if await container.review_service.all_screenshots_reviewed(app_id):
        await _send_summary_message(callback, container, app_id)
