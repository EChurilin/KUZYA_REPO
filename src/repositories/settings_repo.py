from typing import Optional

from src.repositories.base import BaseRepository


class SettingsRepositoryImpl(BaseRepository):
    async def get(self, key: str) -> Optional[str]:
        return await self.fetchval(
            "SELECT value FROM bot_settings WHERE key = $1",
            key,
        )

    async def set(self, key: str, value: str) -> None:
        await self.execute(
            """
            INSERT INTO bot_settings (key, value, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = NOW()
            """,
            key,
            value,
        )