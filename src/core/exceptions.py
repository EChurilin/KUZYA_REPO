class SessionAlreadyActiveError(Exception):
    """У пользователя уже есть активная сессия."""
    pass

class SessionNotFoundError(Exception):
    """Сессия не найдена или не активна."""
    pass

class ScreenshotIntervalTooShortError(Exception):
    """Интервал между скриншотами менее 10 минут."""
    pass

class ScreenshotLimitReachedError(Exception):
    """Достигнут лимит скриншотов в сессии (150)."""
    pass

class ApplicationLimitReachedError(Exception):
    """Достигнут лимит заявок в день (500)."""
    pass

class RewardBalanceInsufficientError(Exception):
    """Недостаточно средств на балансе бота для выдачи награды."""
    pass

# --- Новые исключения v4.0 ---

class InsufficientUserBalanceError(Exception):
    """Недостаточно звёзд на внутреннем балансе пользователя для получения подарка."""
    pass

class InsufficientBotBalanceError(Exception):
    """Недостаточно звёзд на реальном балансе бота для отправки подарка."""
    pass

class GiftNotFoundError(Exception):
    """Подарок не найден в списке доступных."""
    pass

class TopupNotFoundError(Exception):
    """Запрос на пополнение не найден."""
    pass