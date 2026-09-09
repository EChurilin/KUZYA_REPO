import asyncio
from src.integrations.database.connection import db
from src.integrations.cache.redis_client import redis_client
from src.utils.logger import log_info

async def main():
    log_info("Starting connection checks...")
    
    # Проверяем PostgreSQL
    await db.connect()
    db_ok = await db.check_connection()
    log_info(f"PostgreSQL connection: {'OK' if db_ok else 'FAILED'}")
    
    # Проверяем Redis
    await redis_client.connect()
    redis_ok = await redis_client.check_connection()
    log_info(f"Redis connection: {'OK' if redis_ok else 'FAILED'}")
    
    # Закрываем подключения
    await db.disconnect()
    await redis_client.disconnect()
    
    if db_ok and redis_ok:
        log_info("All connections are working!")
    else:
        log_info("Some connections failed. Check Docker containers.")

if __name__ == "__main__":
    asyncio.run(main())