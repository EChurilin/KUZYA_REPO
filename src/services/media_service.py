import uuid
from pathlib import Path
from typing import Tuple
from aiogram.types import Message

from src.integrations.media.media_downloader import MediaDownloader


class MediaService:
    """Сервис для работы с медиафайлами: скачивание и сохранение."""

    def __init__(self, media_downloader: MediaDownloader, storage_base_path: str):
        self._downloader = media_downloader
        self._storage_base_path = storage_base_path

    async def save_instruction_media(self, message: Message) -> Tuple[str, str]:
        """
        Скачивает медиа из сообщения инструкции и сохраняет локально.
        Возвращает кортеж (media_type, file_path).
        """
        instruction_dir = Path(self._storage_base_path) / "instruction"
        instruction_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}"

        if message.photo:
            photo = message.photo[-1]
            file = await self._downloader.get_file(photo.file_id)
            file_path = instruction_dir / f"{filename}.jpg"
            await self._downloader.download_file(file.file_path, file_path)
            return "photo", str(file_path)

        elif message.video:
            video = message.video
            file = await self._downloader.get_file(video.file_id)
            extension = Path(video.file_name).suffix if video.file_name else ".mp4"
            file_path = instruction_dir / f"{filename}{extension}"
            await self._downloader.download_file(file.file_path, file_path)
            return "video", str(file_path)

        return "text", ""

    async def save_game_photo(self, message: Message) -> str:
        """
        Скачивает фото игры и сохраняет локально.
        Возвращает путь к сохранённому файлу.
        """
        game_dir = Path(self._storage_base_path) / "games"
        game_dir.mkdir(parents=True, exist_ok=True)

        photo = message.photo[-1]
        file = await self._downloader.get_file(photo.file_id)

        filename = f"{uuid.uuid4()}.jpg"
        file_path = game_dir / filename

        await self._downloader.download_file(file.file_path, file_path)
        return str(file_path)
