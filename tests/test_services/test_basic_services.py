import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest
from src.core.entities import Game, InstructionBlock
from src.services.game_service import GameService
from src.services.instruction_service import InstructionService


@pytest.fixture
def game_repo_mock():
    return AsyncMock()


@pytest.fixture
def instruction_repo_mock():
    return AsyncMock()


@pytest.fixture
def sample_game():
    return Game(
        id=uuid.uuid4(),
        name="Test Game",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_block():
    return InstructionBlock(
        id=uuid.uuid4(),
        order=1,
        text="Step 1",
        media_type="text",
        media_path=None,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestGameService:
    @pytest.mark.asyncio
    async def test_get_active_games(self, game_repo_mock, sample_game):
        game_repo_mock.get_all_active.return_value = [sample_game]
        service = GameService(game_repo_mock)

        games = await service.get_active_games()

        assert len(games) == 1
        assert games[0].name == "Test Game"
        game_repo_mock.get_all_active.assert_awaited_once()


class TestInstructionService:
    @pytest.mark.asyncio
    async def test_get_active_blocks(self, instruction_repo_mock, sample_block):
        instruction_repo_mock.get_all_active_ordered.return_value = [sample_block]
        service = InstructionService(instruction_repo_mock)

        blocks = await service.get_active_blocks()

        assert len(blocks) == 1
        assert blocks[0].order == 1
        assert blocks[0].text == "Step 1"
        instruction_repo_mock.get_all_active_ordered.assert_awaited_once()