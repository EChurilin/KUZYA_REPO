import uuid
from datetime import datetime
from typing import List, Optional
import asyncpg
from src.core.entities import Game
from src.repositories.base import BaseRepository


class GameRepositoryImpl(BaseRepository):
    async def get_all_active(self) -> List[Game]:
        rows = await self.fetch(
            "SELECT id, name, is_active, created_at, updated_at FROM games WHERE is_active = true ORDER BY name"
        )
        return [self._row_to_game(row) for row in rows]

    async def get_by_id(self, game_id: uuid.UUID) -> Optional[Game]:
        row = await self.fetchone(
            "SELECT id, name, is_active, created_at, updated_at FROM games WHERE id = ",
            game_id
        )
        return self._row_to_game(row) if row else None

    async def create(self, game: Game) -> None:
        await self.execute(
            """
            INSERT INTO games (id, name, is_active, created_at, updated_at)
            VALUES (, , , , )
            """,
            game.id, game.name, game.is_active, game.created_at, game.updated_at
        )

    async def update(self, game: Game) -> None:
        await self.execute(
            """
            UPDATE games
            SET name = , is_active = , updated_at = 
            WHERE id = 
            """,
            game.id, game.name, game.is_active, game.updated_at
        )

    async def delete(self, game_id: uuid.UUID) -> None:
        await self.execute("DELETE FROM games WHERE id = ", game_id)

    def _row_to_game(self, row: asyncpg.Record) -> Game:
        return Game(
            id=row["id"],
            name=row["name"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )