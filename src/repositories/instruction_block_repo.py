import uuid
from datetime import datetime
from typing import List, Optional
import asyncpg
from src.core.entities import InstructionBlock
from src.repositories.base import BaseRepository


class InstructionBlockRepositoryImpl(BaseRepository):
    async def get_all_active_ordered(self) -> List[InstructionBlock]:
        rows = await self.fetch(
            """
            SELECT id, "order", text, media_type, media_path, is_active, created_at, updated_at
            FROM instruction_blocks
            WHERE is_active = true
            ORDER BY "order" ASC
            """
        )
        return [self._row_to_block(row) for row in rows]

    async def get_by_id(self, block_id: uuid.UUID) -> Optional[InstructionBlock]:
        row = await self.fetchone(
            """
            SELECT id, "order", text, media_type, media_path, is_active, created_at, updated_at
            FROM instruction_blocks
            WHERE id = $1
            """,
            block_id
        )
        return self._row_to_block(row) if row else None

    async def get_max_order(self) -> int:
        result = await self.fetchval("SELECT COALESCE(MAX(\"order\"), 0) FROM instruction_blocks")
        return int(result)

    async def create(self, block: InstructionBlock) -> None:
        await self.execute(
            """
            INSERT INTO instruction_blocks (id, "order", text, media_type, media_path, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            block.id, block.order, block.text, block.media_type, block.media_path,
            block.is_active, block.created_at, block.updated_at
        )

    async def update(self, block: InstructionBlock) -> None:
        await self.execute(
            """
            UPDATE instruction_blocks
            SET "order" = $1, text = $2, media_type = $3, media_path = $4,
                is_active = $5, updated_at = $6
            WHERE id = $7
            """,
            block.order, block.text, block.media_type, block.media_path,
            block.is_active, block.updated_at, block.id
        )

    async def delete(self, block_id: uuid.UUID) -> None:
        await self.execute("DELETE FROM instruction_blocks WHERE id = $1", block_id)

    def _row_to_block(self, row: asyncpg.Record) -> InstructionBlock:
        return InstructionBlock(
            id=row["id"],
            order=row["order"],
            text=row["text"],
            media_type=row["media_type"],
            media_path=row["media_path"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )