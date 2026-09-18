import uuid
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from src.infrastructure.container import Container
from src.config.settings import settings as app_settings
from src.bots.staff_bot.states import TopupManagement
from src.bots.staff_bot.keyboards.menu_kb import get_main_menu_kb
from src.bots.staff_bot.keyboards.topup_kb import get_topup_cancel_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in app_settings.staff_bot.admin_ids


@router.message(F.text == "Пополнить баланс")
async def menu_topup(message: Message, container: Container, state: FSMContext):
    """Кнопка меню «Пополнить баланс»: запускает ввод суммы."""
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return

    await state.set_state(TopupManagement.waiting_for_amount)
    await message.answer(
        "Введите количество звёзд для пополнения (положительное целое число) или «Отмена».",
        reply_markup=get_main_menu_kb(),
    )


@router.message(TopupManagement.waiting_for_amount)
async def process_topup_amount(message: Message, container: Container, state: FSMContext):
    """Приём суммы: создаёт запись и отправляет инвойс от имени клиентского бота."""
    if not is_admin(message.from_user.id):
        return

    text = (message.text or "").strip()
    if text == "Отмена":
        await state.clear()
        await message.answer("Пополнение отменено.", reply_markup=get_main_menu_kb())
        return

    try:
        amount = int(text)
    except ValueError:
        await message.answer("Введите целое число или «Отмена».")
        return

    if amount <= 0:
        await message.answer("Количество должно быть положительным числом.")
        return

    topup = await container.topup_service.create_topup_request(message.from_user.id, amount)

    try:
        await container.topup_service.send_invoice(topup)
    except Exception as e:
        await state.clear()
        await message.answer(
            f"Не удалось отправить счёт: {e}",
            reply_markup=get_main_menu_kb(),
        )
        return

    await state.clear()
    await message.answer(
        f"Счёт на {amount} звёзд отправлен в чат с клиентским ботом.\n"
        "Нажмите «Оплатить» там. До оплаты пополнение можно отменить кнопкой ниже.",
        reply_markup=get_topup_cancel_kb(topup.id),
    )


@router.callback_query(F.data.startswith("topup_cancel:"))
async def cb_topup_cancel(callback: CallbackQuery, container: Container):
    """Отмена пополнения после отправки инвойса: удаляет счёт и помечает cancelled."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    topup_id_str = callback.data.split(":", 1)[1]
    try:
        topup_id = uuid.UUID(topup_id_str)
    except ValueError:
        await callback.answer("Ошибка ID", show_alert=True)
        return

    try:
        await container.topup_service.cancel_topup(topup_id)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
        return

    await callback.answer("Пополнение отменено")
    try:
        await callback.message.edit_text("Пополнение отменено. Счёт удалён.")
    except TelegramBadRequest:
        pass