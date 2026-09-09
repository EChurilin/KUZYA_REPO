from src.config.settings import settings
from src.core.enums import UserRole


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return user_id in settings.admin_user_ids


def is_moderator(user_id: int, role: str) -> bool:
    """Проверяет, является ли пользователь модератором."""
    return role == UserRole.MODERATOR


def validate_telegram_id(user_id: int) -> bool:
    """Проверяет корректность Telegram ID (должен быть положительным числом)."""
    return isinstance(user_id, int) and user_id > 0


def validate_file_size(size_bytes: int, max_mb: int = 10) -> bool:
    """Проверяет размер файла (по умолчанию максимум 10 МБ)."""
    max_bytes = max_mb * 1024 * 1024
    return 0 < size_bytes <= max_bytes


def sanitize_text(text: str | None) -> str | None:
    """Базовая очистка текста (удаление пробелов в начале и конце)."""
    if text is None:
        return None
    return text.strip()