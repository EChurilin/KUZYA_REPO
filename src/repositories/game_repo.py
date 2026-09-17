import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import asyncpg
from src.core.entities import Game
from src.repositories.base import BaseRepository


class GameRepositoryImpl(BaseRepository):
    async def get_all_active(self) -> List[Game]:
        rows = await self.fetch(
            "SELECT id, name, is_active, created_at, updated_at, link, photo_path, deactivated_at "
            "FROM games WHERE is_active = true ORDER BY name"
        )
        return [self._row_to_game(row) for row in rows]

    async def get_by_id(self, game_id: uuid.UUID) -> Optional[Game]:
        row = await self.fetchone(
            "SELECT id, name, is_active, created_at, updated_at, link, photo_path, deactivated_at "
            "FROM games WHERE id = $1",
            game_id
        )
        return self._row_to_game(row) if row else None

    async def create(self, game: Game) -> None:
        await self.execute(
            """
            INSERT INTO games (id, name, is_active, created_at, updated_at, link, photo_path, deactivated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            game.id, game.name, game.is_active, game.created_at, game.updated_at,
            game.link, game.photo_path, game.deactivated_at
        )

    async def update(self, game: Game) -> None:
        await self.execute(
            """
            UPDATE games
            SET name = $1, is_active = $2, updated_at = $3, link = $4, photo_path = $5, deactivated_at = $6
            WHERE id = $7
            """,
            game.name, game.is_active, game.updated_at,
            game.link, game.photo_path, game.deactivated_at,
            game.id
        )

    async def delete(self, game_id: uuid.UUID) -> None:
        await self.execute("DELETE FROM games WHERE id = $1", game_id)

    async def deactivate_all(self) -> None:
        now = datetime.now(timezone.utc)
        await self.execute(
            """
            UPDATE games
            SET is_active = false, deactivated_at = $1, updated_at = $1
            WHERE is_active = true
            """,
            now
        )

    async def get_old_deactivated_games(self, hours: int) -> List[Game]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        rows = await self.fetch(
            "SELECT id, name, is_active, created_at, updated_at, link, photo_path, deactivated_at "
            "FROM games WHERE is_active = false AND deactivated_at < $1 "
            "ORDER BY deactivated_at",
            cutoff
        )
        return [self._row_to_game(row) for row in rows]

    def _row_to_game(self, row: asyncpg.Record) -> Game:
        return Game(
            id=row["id"],
            name=row["name"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            link=row["link"],
            photo_path=row["photo_path"],
            deactivated_at=row["deactivated_at"],
        )