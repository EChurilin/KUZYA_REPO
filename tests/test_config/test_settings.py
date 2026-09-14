import os
import pytest
from src.config.settings import Settings, DatabaseSettings


class TestDatabaseSettings:
    def test_dsn_formation(self):
        db = DatabaseSettings(
            host="localhost",
            port=5432,
            user="postgres",
            password="secret",
            database="test_db"
        )
        assert db.dsn == "postgresql://postgres:secret@localhost:5432/test_db"

    def test_dsn_with_different_port(self):
        db = DatabaseSettings(
            host="db.example.com",
            port=5433,
            user="admin",
            password="pass123",
            database="production"
        )
        assert db.dsn == "postgresql://admin:pass123@db.example.com:5433/production"


class TestSettingsFromEnv:
    def test_loads_from_env_variables(self, monkeypatch):
        # Устанавливаем переменные окружения
        monkeypatch.setenv("DB_HOST", "testhost")
        monkeypatch.setenv("DB_PORT", "5433")
        monkeypatch.setenv("DB_USER", "testuser")
        monkeypatch.setenv("DB_PASSWORD", "testpass")
        monkeypatch.setenv("DB_NAME", "testdb")
        
        monkeypatch.setenv("REDIS_HOST", "redishost")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_DB", "1")
        monkeypatch.setenv("REDIS_PASSWORD", "redispass")
        
        monkeypatch.setenv("CLIENT_BOT_TOKEN", "client_token_123")
        monkeypatch.setenv("STAFF_BOT_TOKEN", "staff_token_456")
        monkeypatch.setenv("ADMIN_IDS", "111,222,333")
        
        monkeypatch.setenv("STORAGE_PATH", "/custom/storage")
        monkeypatch.setenv("MAX_FILE_SIZE_MB", "20")
        monkeypatch.setenv("DEBUG", "true")
        
        settings = Settings.from_env()
        
        # Проверяем database
        assert settings.database.host == "testhost"
        assert settings.database.port == 5433
        assert settings.database.user == "testuser"
        assert settings.database.password == "testpass"
        assert settings.database.database == "testdb"
        
        # Проверяем redis
        assert settings.redis.host == "redishost"
        assert settings.redis.port == 6380
        assert settings.redis.db == 1
        assert settings.redis.password == "redispass"
        
        # Проверяем telegram bots
        assert settings.client_bot.token == "client_token_123"
        assert settings.staff_bot.token == "staff_token_456"
        assert settings.client_bot.admin_ids == [111, 222, 333]
        assert settings.staff_bot.admin_ids == [111, 222, 333]
        
        # Проверяем storage
        assert settings.storage.base_path == "/custom/storage"
        assert settings.storage.max_file_size_mb == 20
        
        # Проверяем debug
        assert settings.debug is True

    def test_default_values(self, monkeypatch):
        # Очищаем все переменные окружения
        for key in ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME",
                    "REDIS_HOST", "REDIS_PORT", "REDIS_DB", "REDIS_PASSWORD",
                    "CLIENT_BOT_TOKEN", "STAFF_BOT_TOKEN", "ADMIN_IDS",
                    "STORAGE_PATH", "MAX_FILE_SIZE_MB", "DEBUG"]:
            monkeypatch.delenv(key, raising=False)
        
        settings = Settings.from_env()
        
        # Проверяем дефолтные значения
        assert settings.database.host == "localhost"
        assert settings.database.port == 5432
        assert settings.database.user == "postgres"
        assert settings.database.password == "postgres"
        assert settings.database.database == "kizya_bot"
        
        assert settings.redis.host == "localhost"
        assert settings.redis.port == 6379
        assert settings.redis.db == 0
        assert settings.redis.password is None
        
        assert settings.storage.base_path == "storage/screenshots"
        assert settings.storage.max_file_size_mb == 10
        
        assert settings.debug is False

    def test_admin_ids_parsing(self, monkeypatch):
        monkeypatch.setenv("ADMIN_IDS", "100, 200, 300")
        settings = Settings.from_env()
        assert settings.client_bot.admin_ids == [100, 200, 300]

    def test_empty_admin_ids(self, monkeypatch):
        monkeypatch.setenv("ADMIN_IDS", "")
        settings = Settings.from_env()
        assert settings.client_bot.admin_ids == []

    def test_debug_false_variations(self, monkeypatch):
        for value in ["false", "False", "FALSE", "0", "no"]:
            monkeypatch.setenv("DEBUG", value)
            settings = Settings.from_env()
            assert settings.debug is False

    def test_debug_true_variations(self, monkeypatch):
        for value in ["true", "True", "TRUE", "1", "yes"]:
            monkeypatch.setenv("DEBUG", value)
            settings = Settings.from_env()
            assert settings.debug is True