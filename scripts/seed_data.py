"""
Скрипт для добавления тестовых данных в БД.
Запуск: python scripts/seed_data.py
"""
import asyncio
import uuid
from datetime import datetime, timezone
from src.integrations.database.connection import init_pool, close_pool, get_pool


async def seed_games():
    """Добавляет тестовые игры"""
    pool = get_pool()
    async with pool.acquire() as conn:
        # Проверяем, есть ли уже игры
        count = await conn.fetchval("SELECT COUNT(*) FROM games")
        if count > 0:
            print(f"Игры уже существуют ({count} шт.). Пропускаем.")
            return
        
        games = [
            {"name": "Clash Royale", "is_active": True},
            {"name": "Brawl Stars", "is_active": True},
            {"name": "Subway Surfers", "is_active": True},
        ]
        
        for game in games:
            await conn.execute(
                """
                INSERT INTO games (id, name, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                """,
                uuid.uuid4(),
                game["name"],
                game["is_active"]
            )
            print(f"Добавлена игра: {game['name']}")


async def seed_instruction_blocks():
    """Добавляет тестовые блоки инструкции"""
    pool = get_pool()
    async with pool.acquire() as conn:
        # Проверяем, есть ли уже блоки
        count = await conn.fetchval("SELECT COUNT(*) FROM instruction_blocks")
        if count > 0:
            print(f"Блоки инструкции уже существуют ({count} шт.). Пропускаем.")
            return
        
        blocks = [
            {
                "order": 1,
                "text": "Добро пожаловать! Это инструкция по получению награды.",
                "media_type": "text",
                "media_path": None,
                "is_active": True
            },
            {
                "order": 2,
                "text": "Шаг 1: Откройте игру и выполните задание.",
                "media_type": "text",
                "media_path": None,
                "is_active": True
            },
            {
                "order": 3,
                "text": "Шаг 2: Сделайте скриншот выполнения задания.",
                "media_type": "text",
                "media_path": None,
                "is_active": True
            },
            {
                "order": 4,
                "text": "Шаг 3: Отправьте скриншот в бот. Интервал между скриншотами - не менее 10 минут.",
                "media_type": "text",
                "media_path": None,
                "is_active": True
            },
            {
                "order": 5,
                "text": "Шаг 4: После отправки всех скриншотов нажмите 'Забрать награду'.",
                "media_type": "text",
                "media_path": None,
                "is_active": True
            },
            {
                "order": 6,
                "text": "Шаг 5: Дождитесь проверки администратором. Награда будет начислена автоматически.",
                "media_type": "text",
                "media_path": None,
                "is_active": True
            },
        ]
        
        for block in blocks:
            await conn.execute(
                """
                INSERT INTO instruction_blocks (id, "order", text, media_type, media_path, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                """,
                uuid.uuid4(),
                block["order"],
                block["text"],
                block["media_type"],
                block["media_path"],
                block["is_active"]
            )
            print(f"Добавлен блок инструкции #{block['order']}: {block['text'][:50]}...")


async def main():
    print("Запуск скрипта добавления тестовых данных...")
    
    # Инициализируем пул БД
    await init_pool()
    print("Подключение к БД установлено.")
    
    try:
        # Добавляем игры
        await seed_games()
        
        # Добавляем блоки инструкции
        await seed_instruction_blocks()
        
        print("\nТестовые данные успешно добавлены!")
        
    finally:
        # Закрываем соединение
        await close_pool()
        print("Соединение с БД закрыто.")


if __name__ == "__main__":
    asyncio.run(main())