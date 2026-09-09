from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from src.infrastructure.container import Container
from src.utils.logger import logger


async def handle_start(message: Message, container: Container) -> None:
    """Логика обработки команды /start."""
    user = message.from_user
    if not user:
        return

    # Регистрируем или обновляем пользователя в БД
    await container.user_service.register_or_update(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name or "Unknown",
        language_code=user.language_code or "en",
    )
    logger.info(f"User {user.id} triggered /start")

    text = (
        f"Привет, {user.first_name}! Я бот для участия в рекламных кампаниях.\n\n"
        "Чтобы получить награду, тебе нужно выполнить простое задание "
        "и прислать мне скриншот-подтверждение.\n\n"
        "Используй команду /help, если нужна помощь, или /campaigns, "
        "чтобы посмотреть список доступных заданий."
    )
    await message.answer(text)


async def handle_help(message: Message) -> None:
    """Логика обработки команды /help."""
    text = (
        "Как это работает:\n"
        "1. Выбери активную кампанию через /campaigns.\n"
        "2. Выполни условие (например, подпишись на канал).\n"
        "3. Сделай скриншот и отправь его мне в ответ на сообщение кампании.\n"
        "4. Дождись проверки модератором и получения награды!\n\n"
        "Если возникли проблемы, напиши в поддержку: /support"
    )
    await message.answer(text)


def get_start_router(container: Container) -> Router:
    """Фабрика, создающая роутер с привязанными хендлерами."""
    router = Router(name="client_start")

    @router.message(CommandStart())
    async def cmd_start_wrapper(message: Message) -> None:
        await handle_start(message, container)

    @router.message(Command("help"))
    async def cmd_help_wrapper(message: Message) -> None:
        await handle_help(message)

    return router