import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from src.services.media_service import MediaService
from src.integrations.media.media_downloader import MediaDownloader


@pytest.fixture
def mock_downloader():
    return AsyncMock(spec=MediaDownloader)


@pytest.fixture
def media_service(mock_downloader, tmp_path):
    return MediaService(mock_downloader, str(tmp_path))


class TestMediaService:
    @pytest.mark.asyncio
    async def test_save_instruction_media_photo(self, media_service, mock_downloader, tmp_path):
        """Проверяет сохранение фото для инструкции."""
        # Мокаем сообщение с фото
        message = MagicMock()
        message.photo = [MagicMock()]
        message.photo[-1].file_id = "test_photo_id"
        message.video = None

        # Мокаем get_file
        mock_file = MagicMock()
        mock_file.file_path = "photos/file_0.jpg"
        mock_downloader.get_file = AsyncMock(return_value=mock_file)
        mock_downloader.download_file = AsyncMock(return_value=None)

        media_type, file_path = await media_service.save_instruction_media(message)

        assert media_type == "photo"
        assert file_path.endswith(".jpg")
        assert "instruction" in file_path
        mock_downloader.get_file.assert_called_once_with("test_photo_id")
        mock_downloader.download_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_instruction_media_video(self, media_service, mock_downloader, tmp_path):
        """Проверяет сохранение видео для инструкции."""
        message = MagicMock()
        message.photo = None
        message.video = MagicMock()
        message.video.file_id = "test_video_id"
        message.video.file_name = "video.mp4"

        mock_file = MagicMock()
        mock_file.file_path = "videos/file_0.mp4"
        mock_downloader.get_file = AsyncMock(return_value=mock_file)
        mock_downloader.download_file = AsyncMock(return_value=None)

        media_type, file_path = await media_service.save_instruction_media(message)

        assert media_type == "video"
        assert file_path.endswith(".mp4")
        assert "instruction" in file_path

    @pytest.mark.asyncio
    async def test_save_instruction_media_text(self, media_service, mock_downloader):
        """Проверяет, что для текстового сообщения возвращается (text, '')."""
        message = MagicMock()
        message.photo = None
        message.video = None

        media_type, file_path = await media_service.save_instruction_media(message)

        assert media_type == "text"
        assert file_path == ""

    @pytest.mark.asyncio
    async def test_save_game_photo(self, media_service, mock_downloader, tmp_path):
        """Проверяет сохранение фото игры."""
        message = MagicMock()
        message.photo = [MagicMock()]
        message.photo[-1].file_id = "test_game_photo_id"

        mock_file = MagicMock()
        mock_file.file_path = "photos/game_0.jpg"
        mock_downloader.get_file = AsyncMock(return_value=mock_file)
        mock_downloader.download_file = AsyncMock(return_value=None)

        file_path = await media_service.save_game_photo(message)

        assert file_path.endswith(".jpg")
        assert "games" in file_path
        mock_downloader.get_file.assert_called_once_with("test_game_photo_id")
        mock_downloader.download_file.assert_called_once()
