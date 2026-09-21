from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from src.infrastructure.container import Container
from src.bots.client_bot.keyboards.main_kb import get_main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, container: Container, state: FSMContext):
    """Обработчик команды /start — показывает главное меню."""
    await state.clear()

    # Регистрируем или получаем существующего пользователя
    await container.user_service.get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        language_code=message.from_user.language_code,
    )

    welcome_text = (
        "Привет! Добро пожаловать в Kuzya Bot.\n\n"
        "Здесь ты можешь получать награды за выполнение заданий в играх.\n"
        "Используй кнопки меню для навигации."
    )

    await message.answer(welcome_text, reply_markup=get_main_menu_kb())
