import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from src.integrations.media.media_downloader import MediaDownloader


@pytest.fixture
def mock_bot():
    return AsyncMock()


class TestMediaDownloader:
    @pytest.mark.asyncio
    async def test_get_file(self, mock_bot):
        """Проверяет, что get_file вызывает bot.get_file с правильным file_id."""
        mock_file = MagicMock()
        mock_file.file_path = "photos/file_0.jpg"
        mock_bot.get_file = AsyncMock(return_value=mock_file)

        downloader = MediaDownloader(mock_bot)
        result = await downloader.get_file("test_file_id")

        assert result == mock_file
        mock_bot.get_file.assert_called_once_with("test_file_id")

    @pytest.mark.asyncio
    async def test_download_file(self, mock_bot, tmp_path):
        """Проверяет, что download_file вызывает bot.download_file с правильными аргументами."""
        mock_bot.download_file = AsyncMock(return_value=None)
        destination = tmp_path / "test.jpg"

        downloader = MediaDownloader(mock_bot)
        await downloader.download_file("photos/file_0.jpg", destination)

        mock_bot.download_file.assert_called_once_with("photos/file_0.jpg", destination)
