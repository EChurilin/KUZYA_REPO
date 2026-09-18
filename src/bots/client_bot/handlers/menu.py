from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message):
    """
    Fallback для неизвестных команд.
    В клиентском боте навигация только через кнопки; единственная команда — /start,
    она обрабатывается раньше (в start.router). Сюда попадают все прочие команды.
    """
    await message.answer(
        "Такая команда мне неизвестна. Для управления ботом используйте кнопки меню."
    )