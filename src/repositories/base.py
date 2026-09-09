from typing import Any

from asyncpg import Record
from asyncpg.pool import Pool


class BaseRepository:
    """Базовый класс для всех репозиториев.

    Инкапсулирует работу с пулом соединений и предоставляет
    унифицированные методы для выполнения запросов.
    """

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        """Выполняет запрос и возвращает одну запись как словарь или None."""
        async with self._pool.acquire() as conn:
            row: Record | None = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """Выполняет запрос и возвращает список записей как словарей."""
        async with self._pool.acquire() as conn:
            rows: list[Record] = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetch_val(self, query: str, *args: Any) -> Any:
        """Выполняет запрос и возвращает одно значение (например, COUNT или id)."""
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        """Выполняет запрос без возврата данных (INSERT, UPDATE, DELETE)."""
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)