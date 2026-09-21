from pathlib import Path
from aiogram import Bot


class MediaDownloader:
    """Интеграция с Telegram Bot API для скачивания медиафайлов."""

    def __init__(self, bot: Bot):
        self._bot = bot

    async def get_file(self, file_id: str):
        """Получает информацию о файле из Telegram."""
        return await self._bot.get_file(file_id)

    async def download_file(self, file_path: str, destination: Path) -> None:
        """Скачивает файл из Telegram и сохраняет локально."""
        await self._bot.download_file(file_path, destination)
