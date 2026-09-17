from typing import List, Optional
import uuid
from src.core.entities import Game
from src.core.interfaces import GameRepository


class GameService:
    def __init__(self, game_repo: GameRepository):
        self._game_repo = game_repo

    async def get_active_games(self) -> List[Game]:
        """Возвращает список всех активных игр для выбора пользователем."""
        return await self._game_repo.get_all_active()

    async def get_game_by_id(self, game_id: uuid.UUID) -> Optional[Game]:
        """Возвращает игру по её идентификатору."""
        return await self._game_repo.get_by_id(game_id)

    async def add_game(self, game: Game) -> None:
        """Добавляет одну новую игру к текущему активному списку."""
        await self._game_repo.create(game)

    async def replace_game_list(self, new_games: List[Game]) -> None:
        """Полная замена списка игр: деактивирует все текущие активные игры и создаёт новые."""
        await self._game_repo.deactivate_all()
        for game in new_games:
            await self._game_repo.create(game)

    async def get_old_deactivated_games(self, hours: int = 36) -> List[Game]:
        """Возвращает деактивированные игры старше N часов для последующей очистки."""
        return await self._game_repo.get_old_deactivated_games(hours)

    async def delete_game(self, game_id: uuid.UUID) -> None:
        """Удаляет игру по её идентификатору."""
        await self._game_repo.delete(game_id)