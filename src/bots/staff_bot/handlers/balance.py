from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.infrastructure.container import Container
from src.config.settings import settings as app_settings
from src.bots.staff_bot.keyboards.menu_kb import get_main_menu_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in app_settings.staff_bot.admin_ids


@router.message(F.text == "Баланс звёзд")
async def menu_balance(message: Message, container: Container, state: FSMContext):
    """Кнопка меню «Баланс звёзд»: показывает реальный баланс звёзд клиентского бота."""
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return

    balance = await container.topup_service.get_bot_balance()
    await message.answer(
        f"Реальный баланс звёзд клиентского бота: {balance}.",
        reply_markup=get_main_menu_kb(),
    )