import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from src.infrastructure.container import Container
from src.config.settings import settings
from src.config.constants import APPLICATION_STATUS_REWARDED
from src.bots.staff_bot.keyboards.review_kb import (
    get_screenshot_review_kb,
    get_screenshot_decided_kb,
)
from src.bots.staff_bot.handlers.queue import _send_summary_message

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.staff_bot.admin_ids


async def _update_screenshot_message(callback: CallbackQuery, status_label: str, screen_kb: InlineKeyboardMarkup) -> None:
    """Обновляет сообщение скриншота: текст статуса и клавиатуру."""
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=f"Скриншот {status_label}",
                reply_markup=screen_kb,
            )
        else:
            await callback.message.edit_text(
                f"Скриншот {status_label}\nФайл не найден.",
                reply_markup=screen_kb,
            )
    except TelegramBadRequest:
        pass  # Сообщение не изменилось или не может быть отредактировано


@router.callback_query(F.data.startswith("approve_scr:"))
async def cb_approve_scr(callback: CallbackQuery, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    scr_id_str = callback.data.split(":")[1]
    try:
        scr_id = uuid.UUID(scr_id_str)
    except ValueError:
        await callback.answer("Ошибка ID", show_alert=True)
        return

    # Получаем скриншот для определения application_id
    screenshot = await container.application_service._screenshot_repo.get_by_id(scr_id)
    if not screenshot or screenshot.application_id is None:
        await callback.answer("Скриншот не найден", show_alert=True)
        return

    application_id = screenshot.application_id

    # Обновляем статус в БД
    await container.review_service.approve_screenshot(scr_id, callback.from_user.id)

    # Обновляем сообщение скриншота: статус и кнопка «Изменить решение»
    await _update_screenshot_message(callback, "[одобрено]", get_screenshot_decided_kb(scr_id))

    # Если все скриншоты оценены — отправляем/обновляем итоговое сообщение
    if await container.review_service.all_screenshots_reviewed(application_id):
        await _send_summary_message(callback, container, application_id)

    await callback.answer("Скриншот одобрен")


@router.callback_query(F.data.startswith("reject_scr:"))
async def cb_reject_scr(callback: CallbackQuery, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    scr_id_str = callback.data.split(":")[1]
    try:
        scr_id = uuid.UUID(scr_id_str)
    except ValueError:
        await callback.answer("Ошибка ID", show_alert=True)
        return

    # Получаем скриншот для определения application_id
    screenshot = await container.application_service._screenshot_repo.get_by_id(scr_id)
    if not screenshot or screenshot.application_id is None:
        await callback.answer("Скриншот не найден", show_alert=True)
        return

    application_id = screenshot.application_id

    # Обновляем статус в БД
    await container.review_service.reject_screenshot(scr_id, callback.from_user.id)

    # Обновляем сообщение скриншота: статус и кнопка «Изменить решение»
    await _update_screenshot_message(callback, "[отклонено]", get_screenshot_decided_kb(scr_id))

    # Если все скриншоты оценены — отправляем/обновляем итоговое сообщение
    if await container.review_service.all_screenshots_reviewed(application_id):
        await _send_summary_message(callback, container, application_id)

    await callback.answer("Скриншот отклонен")


@router.callback_query(F.data.startswith("change_dec:"))
async def cb_change_dec(callback: CallbackQuery, container: Container):
    """Возвращает скриншот в состояние 'на проверке' и удаляет итоговое сообщение."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await callback.answer()

    scr_id_str = callback.data.split(":")[1]
    try:
        scr_id = uuid.UUID(scr_id_str)
    except ValueError:
        await callback.answer("Ошибка ID", show_alert=True)
        return

    # Получаем скриншот для определения application_id
    screenshot = await container.application_service._screenshot_repo.get_by_id(scr_id)
    if not screenshot or screenshot.application_id is None:
        await callback.answer("Скриншот не найден", show_alert=True)
        return

    application_id = screenshot.application_id

    # Получаем заявку для удаления итогового сообщения
    app = await container.application_service._app_repo.get_by_id(application_id)
    if not app:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    # Удаляем итоговое сообщение (если оно есть), потому что теперь не все скриншоты оценены
    if app.summary_message_id is not None:
        try:
            await callback.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=app.summary_message_id,
            )
        except TelegramBadRequest:
            pass  # Сообщение уже удалено или не найдено

    # Сбрасываем статус скриншота на 'на проверке'
    await container.review_service.reset_screenshot(scr_id)

    # Обновляем сообщение скриншота: статус и кнопки «Одобрить/Отклонить»
    await _update_screenshot_message(callback, "[на проверке]", get_screenshot_review_kb(scr_id))


@router.callback_query(F.data.startswith("reward_app:"))
async def cb_reward_app(callback: CallbackQuery, container: Container):
    """Финализация заявки: начисление, удаление сообщений, финальный текст."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await callback.answer("Обработка заявки...")

    app_id_str = callback.data.split(":")[1]
    try:
        app_id = uuid.UUID(app_id_str)
    except ValueError:
        await callback.answer("Ошибка ID", show_alert=True)
        return

    # Получаем заявку и проверяем идемпотентность
    app = await container.application_service._app_repo.get_by_id(app_id)
    if not app:
        await callback.message.answer("Заявка не найдена.")
        return
    if app.status == APPLICATION_STATUS_REWARDED:
        await callback.message.answer("Награда уже начислена по этой заявке.")
        return

    # Проверяем, что все скриншоты оценены
    if not await container.review_service.all_screenshots_reviewed(app_id):
        await callback.message.answer("Не все скриншоты оценены. Завершите проверку перед начислением.")
        return

    # Сохраняем chat_id до удаления сообщений
    chat_id = callback.message.chat.id

    # Финализируем заявку (начисление + уведомление пользователю)
    try:
        credited_amount = await container.review_service.finalize_application(
            application_id=app_id,
            moderator_id=callback.from_user.id,
            comment="Проверено администратором"
        )
    except Exception as e:
        await callback.message.answer(f"Ошибка при финализации: {str(e)}")
        return

    # Удаляем все сообщения скриншотов
    screenshots = await container.application_service._screenshot_repo.get_by_application(app_id)
    for s in screenshots:
        if s.staff_message_id is not None:
            try:
                await callback.bot.delete_message(chat_id=chat_id, message_id=s.staff_message_id)
            except TelegramBadRequest:
                pass  # Сообщение уже удалено или не найдено

    # Удаляем итоговое сообщение (на котором нажата кнопка)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass  # Сообщение уже удалено или не найдено

    # Получаем данные пользователя для финального сообщения
    user = await container.user_service.get_user(app.user_id)
    if user and user.username:
        user_display = f"@{user.username}"
    else:
        user_display = str(app.user_id)

    # Отправляем финальное сообщение
    if credited_amount > 0:
        new_balance = await container.user_balance_service.get_balance(app.user_id)
        final_text = (
            f"Начислено {credited_amount} звёзд пользователю {user_display}. "
            f"Баланс пользователя: {new_balance}"
        )
    else:
        final_text = (
            f"Заявка #{str(app_id)[:8]} отклонена (нет одобренных скриншотов). "
            f"Пользователь {user_display} уведомлён."
        )

    await callback.bot.send_message(chat_id=chat_id, text=final_text)


@router.callback_query(F.data == "queue_back")
async def cb_queue_back(callback: CallbackQuery, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await callback.answer()
    applications = await container.application_service._app_repo.get_pending_review(limit=10)
    if not applications:
        await callback.message.edit_text("Очередь пуста.")
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
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=kb)
