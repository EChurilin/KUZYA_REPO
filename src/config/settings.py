from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


@dataclass
class DatabaseSettings:
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisSettings:
    host: str
    port: int
    db: int
    password: Optional[str] = None


@dataclass
class TelegramBotSettings:
    token: str
    admin_ids: list[int]


@dataclass
class StorageSettings:
    base_path: str
    max_file_size_mb: int = 10


@dataclass
class Settings:
    database: DatabaseSettings
    redis: RedisSettings
    client_bot: TelegramBotSettings
    staff_bot: TelegramBotSettings
    storage: StorageSettings
    debug: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        # Database
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", "5432"))
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        db_name = os.getenv("DB_NAME", "kizya_bot")

        # Redis
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD")

        # Telegram bots
        client_bot_token = os.getenv("CLIENT_BOT_TOKEN", "")
        staff_bot_token = os.getenv("STAFF_BOT_TOKEN", "")
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]

        # Storage
        storage_path = os.getenv("STORAGE_PATH", "storage/screenshots")
        max_file_size = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

        # Debug - принимаем несколько вариантов "true"
        debug_value = os.getenv("DEBUG", "false").lower()
        debug = debug_value in ("true", "1", "yes", "on")

        return cls(
            database=DatabaseSettings(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database=db_name,
            ),
            redis=RedisSettings(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
            ),
            client_bot=TelegramBotSettings(
                token=client_bot_token,
                admin_ids=admin_ids,
            ),
            staff_bot=TelegramBotSettings(
                token=staff_bot_token,
                admin_ids=admin_ids,
            ),
            storage=StorageSettings(
                base_path=storage_path,
                max_file_size_mb=max_file_size,
            ),
            debug=debug,
        )


# Глобальный экземпляр настроек
settings = Settings.from_env()