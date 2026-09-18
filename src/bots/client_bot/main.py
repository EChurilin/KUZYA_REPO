import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from src.config.settings import settings
from src.integrations.database.connection import init_pool, close_pool
from src.infrastructure.container import build_container
from src.bots.client_bot.middlewares.container_middleware import ContainerMiddleware

# Импортируем роутеры
from src.bots.client_bot.handlers import (
    start,
    instruction,
    game_selection,
    session,
    gift_claim,
    menu,
)


async def main():
    """Главная функция запуска бота"""
    logging.basicConfig(
        level=logging.INFO if not settings.debug else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    logger.info("Запуск client_bot...")

    await init_pool()
    logger.info("Пул БД инициализирован")

    container = build_container()
    logger.info("Контейнер зависимостей создан")

    bot = Bot(token=settings.client_bot.token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware(ContainerMiddleware(container))
    logger.info("Middleware зарегистрирован")

    dp.include_router(start.router)
    dp.include_router(instruction.router)
    dp.include_router(game_selection.router)
    dp.include_router(session.router)
    dp.include_router(gift_claim.router)
    dp.include_router(menu.router)
    logger.info("Роутеры зарегистрированы")

    logger.info("Бот запущен и готов к работе")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_pool()
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")