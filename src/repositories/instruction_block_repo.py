import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import asyncpg
from src.core.entities import InstructionBlock
from src.repositories.base import BaseRepository


class InstructionBlockRepositoryImpl(BaseRepository):
    async def get_all_active_ordered(self) -> List[InstructionBlock]:
        rows = await self.fetch(
            """
            SELECT id, "order", text, media_type, media_path, is_active, created_at, updated_at, version, is_published
            FROM instruction_blocks
            WHERE is_active = true AND is_published = true
              AND version = (
                  SELECT COALESCE(MAX(version), 0) FROM instruction_blocks WHERE is_published = true
              )
            ORDER BY "order" ASC
            """
        )
        return [self._row_to_block(row) for row in rows]

    async def get_by_id(self, block_id: uuid.UUID) -> Optional[InstructionBlock]:
        row = await self.fetchone(
            """
            SELECT id, "order", text, media_type, media_path, is_active, created_at, updated_at, version, is_published
            FROM instruction_blocks
            WHERE id = $1
            """,
            block_id
        )
        return self._row_to_block(row) if row else None

    async def get_max_order(self) -> int:
        result = await self.fetchval(
            """
            SELECT COALESCE(MAX("order"), 0)
            FROM instruction_blocks
            WHERE version = (
                SELECT COALESCE(MAX(version), 0) FROM instruction_blocks
            )
            """
        )
        return int(result)

    async def create(self, block: InstructionBlock) -> None:
        await self.execute(
            """
            INSERT INTO instruction_blocks (id, "order", text, media_type, media_path, is_active, created_at, updated_at, version, is_published)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            block.id, block.order, block.text, block.media_type, block.media_path,
            block.is_active, block.created_at, block.updated_at, block.version, block.is_published
        )

    async def update(self, block: InstructionBlock) -> None:
        await self.execute(
            """
            UPDATE instruction_blocks
            SET "order" = $1, text = $2, media_type = $3, media_path = $4,
                is_active = $5, updated_at = $6, version = $7, is_published = $8
            WHERE id = $9
            """,
            block.order, block.text, block.media_type, block.media_path,
            block.is_active, block.updated_at, block.version, block.is_published, block.id
        )

    async def delete(self, block_id: uuid.UUID) -> None:
        await self.execute("DELETE FROM instruction_blocks WHERE id = $1", block_id)

    async def get_max_version(self) -> int:
        result = await self.fetchval("SELECT COALESCE(MAX(version), 0) FROM instruction_blocks")
        return int(result)

    async def create_draft_block(self, block: InstructionBlock) -> None:
        await self.execute(
            """
            INSERT INTO instruction_blocks (id, "order", text, media_type, media_path, is_active, created_at, updated_at, version, is_published)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            block.id, block.order, block.text, block.media_type, block.media_path,
            block.is_active, block.created_at, block.updated_at, block.version, False
        )

    async def publish_version(self, version: int) -> None:
        now = datetime.now(timezone.utc)
        await self.execute(
            """
            UPDATE instruction_blocks
            SET is_published = true, updated_at = $2
            WHERE version = $1 AND is_active = true
            """,
            version, now
        )

    async def get_blocks_by_version(self, version: int) -> List[InstructionBlock]:
        rows = await self.fetch(
            """
            SELECT id, "order", text, media_type, media_path, is_active, created_at, updated_at, version, is_published
            FROM instruction_blocks
            WHERE version = $1
            ORDER BY "order" ASC
            """,
            version
        )
        return [self._row_to_block(row) for row in rows]

    async def get_current_published_version(self) -> Optional[int]:
        result = await self.fetchval(
            "SELECT COALESCE(MAX(version), NULL) FROM instruction_blocks WHERE is_published = true"
        )
        return int(result) if result is not None else None

    async def delete_blocks_by_version(self, version: int) -> None:
        await self.execute("DELETE FROM instruction_blocks WHERE version = $1", version)

    async def get_old_published_blocks(self, hours: int) -> List[InstructionBlock]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        rows = await self.fetch(
            """
            SELECT id, "order", text, media_type, media_path, is_active, created_at, updated_at, version, is_published
            FROM instruction_blocks
            WHERE is_published = true
              AND version < (
                  SELECT COALESCE(MAX(version), 0) FROM instruction_blocks WHERE is_published = true
              )
              AND updated_at < $1
            ORDER BY version, "order"
            """,
            cutoff
        )
        return [self._row_to_block(row) for row in rows]

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
            version=row["version"],
            is_published=row["is_published"],
        )