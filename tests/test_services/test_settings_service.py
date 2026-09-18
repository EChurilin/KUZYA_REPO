import pytest
from unittest.mock import AsyncMock

from src.services.settings_service import SettingsService


@pytest.fixture
def settings_repo_mock():
    return AsyncMock()


class TestSettingsService:
    @pytest.mark.asyncio
    async def test_get_screenshot_price_from_db(self, settings_repo_mock):
        settings_repo_mock.get = AsyncMock(return_value="20")

        service = SettingsService(settings_repo_mock)
        price = await service.get_screenshot_price()

        assert price == 20
        settings_repo_mock.get.assert_awaited_once_with("screenshot_price")

    @pytest.mark.asyncio
    async def test_get_screenshot_price_default(self, settings_repo_mock):
        settings_repo_mock.get = AsyncMock(return_value=None)

        service = SettingsService(settings_repo_mock)
        price = await service.get_screenshot_price()

        assert price == 15

    @pytest.mark.asyncio
    async def test_set_screenshot_price(self, settings_repo_mock):
        settings_repo_mock.set = AsyncMock()

        service = SettingsService(settings_repo_mock)
        await service.set_screenshot_price(25)

        settings_repo_mock.set.assert_awaited_once_with("screenshot_price", "25")