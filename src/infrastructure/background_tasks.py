import asyncio
import logging
from src.infrastructure.container import Container

logger = logging.getLogger(__name__)


async def run_cleanup_loop(container: Container, interval_seconds: int = 3600) -> None:
    """
    Фоновая задача периодической очистки данных.
    Запускается в бесконечном цикле с интервалом interval_seconds.
    
    Каждый метод очистки обёрнут в свой try/except: падение одного вида
    очистки не блокирует остальные.
    
    Выполняет:
    - Закрытие просроченных сессий
    - Удаление старых скриншотов (30 дней)
    - Удаление деактивированных игр (36 часов)
    - Удаление старых версий инструкции (24 часа)
    """
    logger.info(f"Фоновая задача очистки запущена (интервал: {interval_seconds}с)")
    
    try:
        while True:
            # 1. Закрытие просроченных сессий
            try:
                closed_count = await container.cleanup_service.process_expired_sessions()
                if closed_count > 0:
                    logger.info(f"Закрыто просроченных сессий: {closed_count}")
            except Exception as e:
                logger.error(f"Ошибка при закрытии сессий: {e}", exc_info=True)
            
            # 2. Удаление старых скриншотов
            try:
                deleted_files, deleted_records = await container.cleanup_service.cleanup_old_screenshots()
                if deleted_files > 0 or deleted_records > 0:
                    logger.info(f"Удалено скриншотов: файлов={deleted_files}, записей={deleted_records}")
            except Exception as e:
                logger.error(f"Ошибка при очистке скриншотов: {e}", exc_info=True)
            
            # 3. Удаление деактивированных игр
            try:
                deleted_games, deleted_game_files = await container.cleanup_service.cleanup_old_games(hours=36)
                if deleted_games > 0 or deleted_game_files > 0:
                    logger.info(f"Удалено игр: записей={deleted_games}, файлов={deleted_game_files}")
            except Exception as e:
                logger.error(f"Ошибка при очистке игр: {e}", exc_info=True)
            
            # 4. Удаление старых версий инструкции
            try:
                deleted_blocks, deleted_instruction_files = await container.cleanup_service.cleanup_old_instruction_versions(hours=24)
                if deleted_blocks > 0 or deleted_instruction_files > 0:
                    logger.info(f"Удалено блоков инструкции: записей={deleted_blocks}, файлов={deleted_instruction_files}")
            except Exception as e:
                logger.error(f"Ошибка при очистке инструкций: {e}", exc_info=True)
            
            await asyncio.sleep(interval_seconds)
            
    except asyncio.CancelledError:
        logger.info("Фоновая задача очистки остановлена")
        raise