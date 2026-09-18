from src.core.interfaces import SettingsRepository


class SettingsService:
    """Сервис для работы с глобальными настройками бота."""

    SCREENSHOT_PRICE_KEY = "screenshot_price"
    DEFAULT_SCREENSHOT_PRICE = 15

    def __init__(self, settings_repo: SettingsRepository):
        self._settings_repo = settings_repo

    async def get_screenshot_price(self) -> int:
        """Возвращает цену одного одобренного скриншота в звёздах (по умолчанию 15)."""
        value = await self._settings_repo.get(self.SCREENSHOT_PRICE_KEY)
        if value is None:
            return self.DEFAULT_SCREENSHOT_PRICE
        return int(value)

    async def set_screenshot_price(self, price: int) -> None:
        """Устанавливает цену одного одобренного скриншота в звёздах."""
        await self._settings_repo.set(self.SCREENSHOT_PRICE_KEY, str(price))