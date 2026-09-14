import uuid
from datetime import datetime
from unittest.mock import AsyncMock
import pytest
from src.core.entities import InstructionBlock
from src.repositories.instruction_block_repo import InstructionBlockRepositoryImpl


@pytest.fixture
def repo():
    mock_pool = AsyncMock()
    return InstructionBlockRepositoryImpl(mock_pool)


class TestInstructionBlockRepository:
    @pytest.mark.asyncio
    async def test_get_all_active_ordered(self, repo):
        now = datetime.now()
        block_id_1 = uuid.uuid4()
        block_id_2 = uuid.uuid4()
        repo.fetch = AsyncMock(return_value=[
            {
                "id": block_id_1,
                "order": 1,
                "text": "Block 1",
                "media_type": "text",
                "media_path": None,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": block_id_2,
                "order": 2,
                "text": "Block 2",
                "media_type": "photo",
                "media_path": "/path/to/photo.jpg",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        ])
        
        blocks = await repo.get_all_active_ordered()
        
        assert len(blocks) == 2
        assert blocks[0].order == 1
        assert blocks[0].text == "Block 1"
        assert blocks[0].media_type == "text"
        assert blocks[0].media_path is None
        assert blocks[1].order == 2
        assert blocks[1].media_type == "photo"

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo):
        block_id = uuid.uuid4()
        now = datetime.now()
        repo.fetchone = AsyncMock(return_value={
            "id": block_id,
            "order": 3,
            "text": "Test block",
            "media_type": "video",
            "media_path": "/path/to/video.mp4",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })
        
        block = await repo.get_by_id(block_id)
        
        assert block is not None
        assert block.id == block_id
        assert block.order == 3
        assert block.media_type == "video"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        repo.fetchone = AsyncMock(return_value=None)
        
        block = await repo.get_by_id(uuid.uuid4())
        
        assert block is None

    @pytest.mark.asyncio
    async def test_get_max_order_with_data(self, repo):
        repo.fetchval = AsyncMock(return_value=5)
        
        max_order = await repo.get_max_order()
        
        assert max_order == 5

    @pytest.mark.asyncio
    async def test_get_max_order_empty_table(self, repo):
        repo.fetchval = AsyncMock(return_value=0)
        
        max_order = await repo.get_max_order()
        
        assert max_order == 0

    @pytest.mark.asyncio
    async def test_create(self, repo):
        block = InstructionBlock(
            id=uuid.uuid4(),
            order=1,
            text="New block",
            media_type="text",
            media_path=None,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        repo.execute = AsyncMock()
        
        await repo.create(block)
        
        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update(self, repo):
        block = InstructionBlock(
            id=uuid.uuid4(),
            order=2,
            text="Updated block",
            media_type="photo",
            media_path="/new/path.jpg",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        repo.execute = AsyncMock()
        
        await repo.update(block)
        
        repo.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete(self, repo):
        block_id = uuid.uuid4()
        repo.execute = AsyncMock()
        
        await repo.delete(block_id)
        
        repo.execute.assert_called_once()