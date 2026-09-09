import logging
import sys

from src.config.settings import settings


class SecretMaskingFilter(logging.Filter):
    """Маскирует секреты в логах для соблюдения Privacy by Design."""

    def __init__(self, secrets: list[str]) -> None:
        super().__init__()
        # Игнорируем пустые строки и очень короткие секреты, чтобы не ломать логи
        self._secrets = [s for s in secrets if s and len(s) > 3]

    def filter(self, record: logging.LogRecord) -> bool:
        if not self._secrets:
            return True

        # Маскируем основное сообщение
        if isinstance(record.msg, str):
            for secret in self._secrets:
                record.msg = record.msg.replace(secret, "***")
                
        # Маскируем аргументы, если они передаются в логгер (например, logger.info("User %s", token))
        if record.args:
            if isinstance(record.args, dict):
                for key, value in record.args.items():
                    if isinstance(value, str):
                        for secret in self._secrets:
                            record.args[key] = value.replace(secret, "***")
            elif isinstance(record.args, tuple):
                masked_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        for secret in self._secrets:
                            arg = arg.replace(secret, "***")
                    masked_args.append(arg)
                record.args = tuple(masked_args)
                
        return True


def setup_logger() -> logging.Logger:
    """Настраивает и возвращает корневой логгер приложения."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    logger = logging.getLogger("kizya_bot")
    logger.setLevel(log_level)

    # Защита от дублирования хендлеров при повторном импорте или перезагрузке
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Собираем все секреты из конфига, которые нужно прятать
        secrets_to_mask = [
            settings.bot_token,
            settings.staff_bot_token,
            settings.database_url,
            settings.redis_url,
        ]
        
        handler.addFilter(SecretMaskingFilter(secrets_to_mask))
        logger.addHandler(handler)

    return logger


# Создаем единый экземпляр логгера для импорта в другие модули
logger = setup_logger()