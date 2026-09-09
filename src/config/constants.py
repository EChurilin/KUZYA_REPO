from typing import Final


class DatabaseTables:
    """Названия таблиц в PostgreSQL."""
    USERS: Final[str] = "users"
    CAMPAIGNS: Final[str] = "campaigns"
    APPLICATIONS: Final[str] = "applications"
    REWARDS: Final[str] = "rewards"
    SUPPORT_TICKETS: Final[str] = "support_tickets"
    SUPPORT_MESSAGES: Final[str] = "support_messages"
    AUDIT_LOG: Final[str] = "audit_log"
    RATE_LIMITS: Final[str] = "rate_limits"


class RateLimits:
    """Лимиты запросов для защиты от спама."""
    APPLICATIONS_PER_DAY_PER_USER: Final[int] = 10
    MESSAGES_PER_MINUTE_PER_USER: Final[int] = 20
    SCREENSHOT_UPLOADS_PER_HOUR: Final[int] = 50


class Validation:
    """Параметры валидации скриншотов."""
    MAX_FILE_SIZE_MB: Final[int] = 10
    ALLOWED_IMAGE_FORMATS: Final[tuple[str, ...]] = ("jpg", "jpeg", "png", "webp")
    MIN_IMAGE_DIMENSION: Final[int] = 100
    MAX_IMAGE_DIMENSION: Final[int] = 4096


class SupportChat:
    """Настройки чата поддержки."""
    MAX_MESSAGES_PER_TICKET: Final[int] = 100
    TICKET_AUTO_CLOSE_HOURS: Final[int] = 72
    MAX_ATTACHMENTS_PER_MESSAGE: Final[int] = 5


class Session:
    """Настройки сессий и кэширования."""
    USER_SESSION_TTL_SECONDS: Final[int] = 3600
    STAFF_SESSION_TTL_SECONDS: Final[int] = 7200
    CAMPAIGN_CACHE_TTL_SECONDS: Final[int] = 300