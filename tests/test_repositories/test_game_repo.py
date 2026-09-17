import uuid
from datetime import datetime
from unittest.mock import AsyncMock
import pytest
from src.core.entities import Game
from src.repositories.game_repo import GameRepositoryImpl


@pytest.fixture
def repo():
    mock_pool = AsyncMock()
    return GameRepositoryImpl(mock_pool)


class TestGameRepository:
    @pytest.mark.asyncio
    async def test_get_all_active(self, repo):
        game_id = uuid.uuid4()
        now = datetime.now()
        repo.fetch = AsyncMock(return_value=[
            {
                "id": game_id,
                "name": "Game 1",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
                "link": "https://example.com",
                "photo_path": "/path/to/photo.jpg",
                "deactivated_at": None,
            }
        ])

        games = await repo.get_all_active()

        assert len(games) == 1
        assert games[0].name == "Game 1"
        assert games[0].is_active is True
        assert games[0].id == game_id
        assert games[0].link == "https://example.com"
        assert games[0].photo_path == "/path/to/photo.jpg"
        assert games[0].deactivated_at is None

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo):
        game_id = uuid.uuid4()
        now = datetime.now()
        repo.fetchone = AsyncMock(return_value={
            "id": game_id,
            "name": "Game 2",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "link": None,
            "photo_path": None,
            "deactivated_at": None,
        })

        game = await repo.get_by_id(game_id)

        assert game is not None
        assert game.name == "Game 2"
        assert game.id == game_id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)

        game = await repo.get_by_id(uuid.uuid4())

        assert game is None

    @pytest.mark.asyncio
    async def test_create(self, repo):
        game = Game(
            id=uuid.uuid4(),
            name="New Game",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        repo.execute = AsyncMock()

        await repo.create(game)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update(self, repo):
        game = Game(
            id=uuid.uuid4(),
            name="Updated Game",
            is_active=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        repo.execute = AsyncMock()

        await repo.update(game)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete(self, repo):
        game_id = uuid.uuid4()
        repo.execute = AsyncMock()

        await repo.delete(game_id)

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_all(self, repo):
        repo.execute = AsyncMock()

        await repo.deactivate_all()

        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_old_deactivated_games(self, repo):
        game_id = uuid.uuid4()
        now = datetime.now()
        repo.fetch = AsyncMock(return_value=[
            {
                "id": game_id,
                "name": "Old Game",
                "is_active": False,
                "created_at": now,
                "updated_at": now,
                "link": None,
                "photo_path": "/path/to/old_photo.jpg",
                "deactivated_at": now,
            }
        ])

        games = await repo.get_old_deactivated_games(hours=36)

        assert len(games) == 1
        assert games[0].name == "Old Game"
        assert games[0].is_active is False
        assert games[0].photo_path == "/path/to/old_photo.jpg"

    @pytest.mark.asyncio
    async def test_get_old_deactivated_games_empty(self, repo):
        repo.fetch = AsyncMock(return_value=[])

        games = await repo.get_old_deactivated_games(hours=36)

        assert len(games) == 0