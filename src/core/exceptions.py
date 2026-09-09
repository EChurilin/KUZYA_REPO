class BaseBotException(Exception):
    """Базовое исключение для всех ошибок бота."""
    pass


class UserNotFoundError(BaseBotException):
    """Пользователь не найден в базе данных."""
    pass


class ApplicationNotFoundError(BaseBotException):
    """Заявка не найдена в базе данных."""
    pass


class IdempotencyError(BaseBotException):
    """Ошибка идемпотентности: операция уже была выполнена."""
    pass


class InsufficientBalanceError(BaseBotException):
    """Недостаточно средств на балансе для выдачи награды."""
    pass


class RateLimitExceededError(BaseBotException):
    """Превышен лимит запросов (rate limit)."""
    pass


class InvalidScreenshotError(BaseBotException):
    """Скриншот не прошел валидацию или имеет недопустимый формат."""
    pass