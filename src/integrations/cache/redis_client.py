import redis.asyncio as aioredis
from redis.asyncio import Redis

from src.config.settings import settings
from src.utils.logger import logger


async def init_redis() -> Redis:
    """Инициализирует асинхронное подключение к Redis."""
    logger.info("Connecting to Redis...")
    try:
        client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
        # Проверяем соединение при старте, чтобы сразу понять, что Redis доступен
        await client.ping()
        logger.info("Redis connection established.")
        return client
    except Exception as e:
        logger.critical(f"Failed to connect to Redis: {e}")
        raise


async def close_redis(client: Redis) -> None:
    """Безопасно закрывает подключение к Redis."""
    if client:
        await client.close()
        logger.info("Redis connection closed.")