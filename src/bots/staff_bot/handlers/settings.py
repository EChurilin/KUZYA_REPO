from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.infrastructure.container import Container
from src.config.settings import settings as app_settings
from src.bots.staff_bot.states import SettingsManagement
from src.bots.staff_bot.keyboards.menu_kb import get_main_menu_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in app_settings.staff_bot.admin_ids


@router.message(F.text == "Цена скриншота")
async def menu_price(message: Message, container: Container, state: FSMContext):
    """Кнопка меню «Цена скриншота»: показывает текущую цену и запускает ввод новой."""
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return

    current = await container.settings_service.get_screenshot_price()
    await state.set_state(SettingsManagement.waiting_for_price)
    await message.answer(
        f"Текущая цена: {current} звёзд за скриншот.\n"
        "Введите новую цену (положительное целое число) или «Отмена».",
        reply_markup=get_main_menu_kb(),
    )


@router.message(SettingsManagement.waiting_for_price)
async def process_new_price(message: Message, container: Container, state: FSMContext):
    """Приём новой цены скриншота."""
    if not is_admin(message.from_user.id):
        return

    text = (message.text or "").strip()
    if text == "Отмена":
        await state.clear()
        await message.answer("Изменение цены отменено.", reply_markup=get_main_menu_kb())
        return

    try:
        price = int(text)
    except ValueError:
        await message.answer("Введите целое число или «Отмена».")
        return

    if price <= 0:
        await message.answer("Цена должна быть положительным числом.")
        return

    await container.settings_service.set_screenshot_price(price)
    await state.clear()
    await message.answer(
        f"Цена скриншота обновлена: {price} звёзд.\n"
        "Новая цена применяется только к будущим финализациям заявок.",
        reply_markup=get_main_menu_kb(),
    )