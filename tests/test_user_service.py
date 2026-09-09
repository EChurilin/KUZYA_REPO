import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from src.services.user_service import UserService
from src.core.entities import User
from src.core.enums import UserRole


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.mark.asyncio
async def test_register_new_user(mock_user_repo):
    """Проверяет сценарий регистрации совершенно нового пользователя."""
    service = UserService(mock_user_repo)
    mock_user_repo.get_by_id.return_value = None
    
    expected_user = User(
        id=123, username="test", first_name="Test", 
        language_code="ru", role=UserRole.USER,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_user_repo.create.return_value = expected_user

    result = await service.register_or_update(123, "test", "Test", "ru")

    assert result.id == 123
    assert result.role == UserRole.USER
    mock_user_repo.get_by_id.assert_called_once_with(123)
    mock_user_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_update_existing_user(mock_user_repo):
    """Проверяет сценарий, когда пользователь сменил имя в Telegram."""
    service = UserService(mock_user_repo)
    now = datetime.now(timezone.utc)
    existing_user = User(
        id=123, username="old_name", first_name="Old", 
        language_code="ru", role=UserRole.USER,
        created_at=now, updated_at=now
    )
    mock_user_repo.get_by_id.return_value = existing_user
    
    updated_user = User(
        id=123, username="new_name", first_name="New", 
        language_code="en", role=UserRole.USER,
        created_at=now, updated_at=datetime.now(timezone.utc)
    )
    mock_user_repo.update.return_value = updated_user

    result = await service.register_or_update(123, "new_name", "New", "en")

    assert result.username == "new_name"
    mock_user_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_no_update_if_unchanged(mock_user_repo):
    """Проверяет оптимизацию: если данные не изменились, UPDATE в БД не идет."""
    service = UserService(mock_user_repo)
    now = datetime.now(timezone.utc)
    existing_user = User(
        id=123, username="same", first_name="Same", 
        language_code="ru", role=UserRole.USER,
        created_at=now, updated_at=now
    )
    mock_user_repo.get_by_id.return_value = existing_user

    result = await service.register_or_update(123, "same", "Same", "ru")

    assert result == existing_user
    # Самое важное: метод update репозитория НЕ должен был вызваться
    mock_user_repo.update.assert_not_called()