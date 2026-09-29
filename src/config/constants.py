# Статусы сессий
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_COMPLETED = "completed"
SESSION_STATUS_EXPIRED = "expired"
SESSION_STATUS_CANCELLED = "cancelled"

# Статусы заявок
APPLICATION_STATUS_PENDING_REVIEW = "pending_review"
APPLICATION_STATUS_APPROVED = "approved"
APPLICATION_STATUS_REJECTED = "rejected"
APPLICATION_STATUS_REWARDED = "rewarded"

# Статусы скриншотов
SCREENSHOT_STATUS_PENDING = "pending"
SCREENSHOT_STATUS_APPROVED = "approved"
SCREENSHOT_STATUS_REJECTED = "rejected"

# Статусы наград
REWARD_STATUS_PENDING = "pending"
REWARD_STATUS_ISSUED = "issued"
REWARD_STATUS_FAILED = "failed"

# Лимиты
MAX_SCREENSHOTS_PER_SESSION = 100
MAX_APPLICATIONS_PER_DAY = 500

# Антифрод
MIN_SCREENSHOT_INTERVAL_SECONDS = 600
# Кулдаун на старт новой сессии: не раньше, чем через 10 минут после завершения
# предыдущей (то же значение, что интервал между скриншотами)
SESSION_RESTART_COOLDOWN_SECONDS = MIN_SCREENSHOT_INTERVAL_SECONDS

# Таймауты и очистка
# Автозакрытие сессии при неактивности (в часах):
# пустые сессии (0 скриншотов) закрываются как 'cancelled' БЕЗ создания заявки;
# непустые — как 'expired', скриншоты отправляются на валидацию (заявка с auto_closed)
SESSION_INACTIVITY_TIMEOUT_HOURS = 3
SCREENSHOT_RETENTION_DAYS = 30

# Кэш
BALANCE_CACHE_TTL_SECONDS = 30

# Награда по умолчанию (модератор может изменить при финализации)
DEFAULT_REWARD_TYPE = "stars"
DEFAULT_REWARD_AMOUNT_PER_SCREENSHOT = 10