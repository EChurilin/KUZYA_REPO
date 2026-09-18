import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from src.config.settings import settings
from src.integrations.database.connection import init_pool, close_pool
from src.infrastructure.container import build_container
from src.infrastructure.background_tasks import run_cleanup_loop
from src.bots.staff_bot.middlewares.container_middleware import ContainerMiddleware

from src.bots.staff_bot.handlers import (
    menu,
    queue,
    review,
    games,
    instruction,
    report,
    settings as settings_handler,
    topup,
    balance,
)

async def main():
    logging.basicConfig(
        level=logging.INFO if not settings.debug else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    logger.info("Запуск staff_bot...")

    await init_pool()
    logger.info("Пул БД инициализирован")

    container = build_container()
    logger.info("Контейнер зависимостей создан")

    bot = Bot(token=settings.staff_bot.token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware(ContainerMiddleware(container))
    logger.info("Middleware зарегистрирован")

    dp.include_router(menu.router)
    dp.include_router(queue.router)
    dp.include_router(review.router)
    dp.include_router(games.router)
    dp.include_router(instruction.router)
    dp.include_router(report.router)
    dp.include_router(settings_handler.router)
    dp.include_router(topup.router)
    dp.include_router(balance.router)
    logger.info("Роутеры зарегистрированы")

    # Запуск фоновой задачи очистки
    cleanup_task = asyncio.create_task(run_cleanup_loop(container, interval_seconds=3600))
    logger.info("Фоновая задача очистки запущена")

    logger.info("Staff_bot запущен и готов к работе")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        await close_pool()
        await bot.session.close()
        logger.info("Staff_bot остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")