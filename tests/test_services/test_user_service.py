from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock

from src.core.entities import User
from src.services.user_service import UserService


@pytest.fixture
def user_repo_mock():
    return AsyncMock()


class TestUserService:
    @pytest.mark.asyncio
    async def test_mark_instruction_passed(self, user_repo_mock):
        user_repo_mock.set_instruction_passed = AsyncMock()

        service = UserService(user_repo_mock)
        await service.mark_instruction_passed(123)

        user_repo_mock.set_instruction_passed.assert_awaited_once_with(123, True)

    @pytest.mark.asyncio
    async def test_save_last_instruction_message_id(self, user_repo_mock):
        user_repo_mock.set_last_instruction_message_id = AsyncMock()

        service = UserService(user_repo_mock)
        await service.save_last_instruction_message_id(123, 42)

        user_repo_mock.set_last_instruction_message_id.assert_awaited_once_with(123, 42)

    @pytest.mark.asyncio
    async def test_clear_last_instruction_message_id(self, user_repo_mock):
        user_repo_mock.set_last_instruction_message_id = AsyncMock()

        service = UserService(user_repo_mock)
        await service.clear_last_instruction_message_id(123)

        user_repo_mock.set_last_instruction_message_id.assert_awaited_once_with(123, None)

    @pytest.mark.asyncio
    async def test_get_or_create_user_creates_new(self, user_repo_mock):
        user_repo_mock.get_by_id = AsyncMock(return_value=None)
        user_repo_mock.create = AsyncMock()

        service = UserService(user_repo_mock)
        user = await service.get_or_create_user(123, "testuser", "Test", "ru")

        assert user.id == 123
        assert user.username == "testuser"
        assert user.role == "user"
        user_repo_mock.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_or_create_user_returns_existing(self, user_repo_mock):
        existing = User(
            id=123,
            username="existing",
            first_name="Ex",
            language_code="ru",
            role="user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        user_repo_mock.get_by_id = AsyncMock(return_value=existing)

        service = UserService(user_repo_mock)
        user = await service.get_or_create_user(123, "newname", "New", "ru")

        assert user.username == "existing"
        user_repo_mock.create.assert_not_awaited()