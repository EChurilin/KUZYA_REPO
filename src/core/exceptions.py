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