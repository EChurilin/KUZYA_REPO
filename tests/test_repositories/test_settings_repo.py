from unittest.mock import AsyncMock

import pytest

from src.repositories.settings_repo import SettingsRepositoryImpl


@pytest.fixture
def repo():
    return SettingsRepositoryImpl(AsyncMock())


class TestSettingsRepository:
    @pytest.mark.asyncio
    async def test_get_found(self, repo):
        repo.fetchval = AsyncMock(return_value="15")

        value = await repo.get("screenshot_price")

        assert value == "15"
        repo.fetchval.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_not_found(self, repo):
        repo.fetchval = AsyncMock(return_value=None)

        value = await repo.get("missing_key")

        assert value is None

    @pytest.mark.asyncio
    async def test_set(self, repo):
        repo.execute = AsyncMock()

        await repo.set("screenshot_price", "20")

        repo.execute.assert_called_once()