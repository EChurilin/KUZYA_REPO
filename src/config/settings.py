from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., description="Token for client bot")
    staff_bot_token: str = Field(..., description="Token for staff bot")
    admin_user_ids: list[int] = Field(..., description="List of admin Telegram IDs")
    
    database_url: str = Field(..., description="PostgreSQL connection string")
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection string")
    
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")


# Создаем единый экземпляр настроек, который будем импортировать в других модулях
settings = Settings()