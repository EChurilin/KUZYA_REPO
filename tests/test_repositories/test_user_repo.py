from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.core.entities import User
from src.repositories.user_repo import UserRepositoryImpl


@pytest.fixture
def repo():
    return UserRepositoryImpl(AsyncMock())


@pytest.fixture
def sample_user():
    return User(
        id=123,
        username="testuser",
        first_name="Test",
        language_code="ru",
        role="user",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        star_balance=100,
        instruction_passed=True,
        last_instruction_message_id=42,
    )


def _user_to_dict(u: User) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "first_name": u.first_name,
        "language_code": u.language_code,
        "role": u.role,
        "created_at": u.created_at,
        "updated_at": u.updated_at,
        "star_balance": u.star_balance,
        "instruction_passed": u.instruction_passed,
        "last_instruction_message_id": u.last_instruction_message_id,
    }


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, sample_user):
        repo.fetchone = AsyncMock(return_value=_user_to_dict(sample_user))

        user = await repo.get_by_id(123)

        assert user is not None
        assert user.id == 123
        assert user.star_balance == 100
        assert user.instruction_passed is True
        assert user.last_instruction_message_id == 42

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        user = await repo.get_by_id(999)

        assert user is None

    @pytest.mark.asyncio
    async def test_create(self, repo, sample_user):
        repo.execute = AsyncMock()

        await repo.create(sample_user)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update(self, repo, sample_user):
        repo.execute = AsyncMock()

        await repo.update(sample_user)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_star_balance(self, repo):
        repo.execute = AsyncMock()

        await repo.update_star_balance(123, 500)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_instruction_passed(self, repo):
        repo.execute = AsyncMock()

        await repo.set_instruction_passed(123, True)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_last_instruction_message_id(self, repo):
        repo.execute = AsyncMock()

        await repo.set_last_instruction_message_id(123, 42)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_last_instruction_message_id_clear(self, repo):
        repo.execute = AsyncMock()

        await repo.set_last_instruction_message_id(123, None)

        repo.execute.assert_called_once()