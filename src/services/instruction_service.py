from typing import List, Optional
from src.core.entities import InstructionBlock
from src.core.interfaces import InstructionBlockRepository


class InstructionService:
    def __init__(self, instruction_repo: InstructionBlockRepository):
        self._instruction_repo = instruction_repo

    async def get_active_blocks(self) -> List[InstructionBlock]:
        """Возвращает блоки текущей опубликованной версии инструкции."""
        return await self._instruction_repo.get_all_active_ordered()

    async def get_blocks_by_version(self, version: int) -> List[InstructionBlock]:
        """Возвращает блоки конкретной версии (для продолжения старой инструкции)."""
        return await self._instruction_repo.get_blocks_by_version(version)

    async def get_current_published_version(self) -> Optional[int]:
        """Возвращает номер текущей опубликованной версии."""
        return await self._instruction_repo.get_current_published_version()

    async def get_max_version(self) -> int:
        """Возвращает максимальный номер версии (включая черновики)."""
        return await self._instruction_repo.get_max_version()

    async def create_draft(self, blocks: List[InstructionBlock], version: int) -> None:
        """Создаёт черновик новой версии инструкции из списка блоков."""
        for block in blocks:
            block.version = version
            block.is_published = False
            await self._instruction_repo.create_draft_block(block)

    async def publish_version(self, version: int) -> None:
        """Публикует указанную версию инструкции."""
        await self._instruction_repo.publish_version(version)

    async def get_draft_blocks(self, version: int) -> List[InstructionBlock]:
        """Возвращает блоки черновика для предпросмотра."""
        return await self._instruction_repo.get_blocks_by_version(version)

    async def delete_draft(self, version: int) -> None:
        """Удаляет черновик указанной версии."""
        await self._instruction_repo.delete_blocks_by_version(version)

    async def get_old_published_blocks(self, hours: int = 24) -> List[InstructionBlock]:
        """Возвращает старые опубликованные блоки (не текущей версии) для очистки."""
        return await self._instruction_repo.get_old_published_blocks(hours)