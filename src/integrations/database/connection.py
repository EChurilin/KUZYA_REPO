import asyncpg
from asyncpg.pool import Pool

from src.config.settings import settings
from src.utils.logger import logger


async def init_db_pool() -> Pool:
    """Инициализирует пул соединений с PostgreSQL."""
    logger.info("Connecting to PostgreSQL...")
    try:
        pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        logger.info("PostgreSQL connection pool established.")
        return pool
    except Exception as e:
        logger.critical(f"Failed to connect to PostgreSQL: {e}")
        raise


async def close_db_pool(pool: Pool) -> None:
    """Безопасно закрывает пул соединений с PostgreSQL."""
    if pool:
        await pool.close()
        logger.info("PostgreSQL connection pool closed.")