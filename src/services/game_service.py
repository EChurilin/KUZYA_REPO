from typing import List
from src.core.entities import Game, InstructionBlock
from src.core.interfaces import GameRepository, InstructionBlockRepository


class GameService:
    def __init__(self, game_repo: GameRepository):
        self._game_repo = game_repo

    async def get_active_games(self) -> List[Game]:
        """Возвращает список всех активных игр для выбора пользователем."""
        return await self._game_repo.get_all_active()


class InstructionService:
    def __init__(self, instruction_repo: InstructionBlockRepository):
        self._instruction_repo = instruction_repo

    async def get_active_blocks(self) -> List[InstructionBlock]:
        """Возвращает все активные блоки инструкции, отсортированные по порядку."""
        return await self._instruction_repo.get_all_active_ordered()