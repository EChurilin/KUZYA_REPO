from typing import List
from src.core.entities import InstructionBlock
from src.core.interfaces import InstructionBlockRepository


class InstructionService:
    def __init__(self, instruction_repo: InstructionBlockRepository):
        self._instruction_repo = instruction_repo

    async def get_active_blocks(self) -> List[InstructionBlock]:
        """Возвращает все активные блоки инструкции, отсортированные по порядку."""
        return await self._instruction_repo.get_all_active_ordered()