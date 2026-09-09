import os
import pytest


@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    """Автоматически подменяет переменные окружения для всех тестов.
    Это предотвращает падение тестов из-за отсутствия реального .env файла.
    """
    monkeypatch.setenv("BOT_TOKEN", "123456:TestToken")
    monkeypatch.setenv("STAFF_BOT_TOKEN", "789012:TestToken")
    monkeypatch.setenv("ADMIN_USER_IDS", "[123456789]")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")