from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from src.infrastructure.container import Container
from src.config.settings import settings
from src.config.constants import DEFAULT_REWARD_TYPE, DEFAULT_REWARD_AMOUNT_PER_SCREENSHOT, APPLICATION_STATUS_REWARDED
import uuid

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.staff_bot.admin_ids

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

    await container.review_service.approve_screenshot(scr_id, callback.from_user.id)
    await callback.answer("✅ Скриншот одобрен")

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

    await container.review_service.reject_screenshot(scr_id, callback.from_user.id)
    await callback.answer("❌ Скриншот отклонен")

@router.callback_query(F.data.startswith("finalize_app:"))
async def cb_finalize_app(callback: CallbackQuery, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    app_id_str = callback.data.split(":")[1]
    try:
        app_id = uuid.UUID(app_id_str)
    except ValueError:
        await callback.answer("Ошибка ID", show_alert=True)
        return

    # Проверка идемпотентности: не выдаём награду повторно
    app = await container.application_service._app_repo.get_by_id(app_id)
    if not app:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    if app.status == APPLICATION_STATUS_REWARDED:
        await callback.answer("Награда уже выдана по этой заявке", show_alert=True)
        return

    await callback.answer("⏳ Обработка заявки...")

    try:
        reward = await container.review_service.finalize_application(
            application_id=app_id,
            moderator_id=callback.from_user.id,
            reward_type=DEFAULT_REWARD_TYPE,
            reward_amount_per_screenshot=DEFAULT_REWARD_AMOUNT_PER_SCREENSHOT,
            comment="Проверено администратором"
        )

        if reward:
            await callback.message.edit_text(
                f"✅ Заявка #{str(app_id)[:8]} успешно обработана!\n"
                f"👤 Пользователь: {reward.user_id}\n"
                f"💰 Выдано награды: {reward.amount} {reward.reward_type}\n"
                f"🔑 Транзакция: {reward.transaction_id}"
            )
        else:
            await callback.message.edit_text(
                f"❌ Заявка #{str(app_id)[:8]} отклонена (нет одобренных скриншотов)."
            )

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

@router.callback_query(F.data == "queue_back")
async def cb_queue_back(callback: CallbackQuery, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await callback.answer()
    applications = await container.application_service._app_repo.get_pending_review(limit=10)
    if not applications:
        await callback.message.edit_text("📭 Очередь пуста.")
        return

    text = "📋 В очереди на проверку:\n\nВыберите заявку для модерации:"
    keyboard = []
    for app in applications:
        btn_text = f"Заявка #{str(app.id)[:8]} ({app.actual_screenshot_count} скрин.)"
        if app.auto_closed:
            btn_text += " 🤖"
        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"review_app:{app.id}")
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=kb)