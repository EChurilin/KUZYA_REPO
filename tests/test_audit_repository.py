import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.repositories.audit_repo import AuditRepository


@pytest.fixture
def mock_pool():
    return AsyncMock()


@pytest.mark.asyncio
async def test_audit_repository_log_action(mock_pool):
    """Проверяет, что метод log_action корректно сериализует словари в JSON."""
    repo = AuditRepository(mock_pool)
    repo.execute = AsyncMock(return_value="INSERT 0 1")
    
    entity_id = uuid4()
    actor_id = 123
    
    await repo.log_action(
        entity_type="application",
        entity_id=entity_id,
        actor_id=actor_id,
        action="status_change",
        old_values={"status": "pending"},
        new_values={"status": "approved"},
    )

    repo.execute.assert_called_once()
    call_args = repo.execute.call_args[0]
    
    # Проверяем, что UUID был преобразован в строку для БД
    assert call_args[2] == str(entity_id)
    # Проверяем, что словари были сериализованы в JSON строки
    assert '"status": "pending"' in call_args[5] or '"status":"pending"' in call_args[5]
    assert '"status": "approved"' in call_args[6] or '"status":"approved"' in call_args[6]


@pytest.mark.asyncio
async def test_audit_repository_get_history(mock_pool):
    """Проверяет чтение истории аудита."""
    repo = AuditRepository(mock_pool)
    
    mock_rows = [
        {
            "id": uuid4(),
            "entity_type": "application",
            "entity_id": str(uuid4()),
            "actor_id": 123,
            "action": "status_change",
            "old_values": '{"status": "pending"}',
            "new_values": '{"status": "approved"}',
            "created_at": "2023-01-01T00:00:00",
        }
    ]
    repo.fetch_all = AsyncMock(return_value=mock_rows)

    history = await repo.get_history_for_entity("application", uuid4())

    assert len(history) == 1
    assert history[0]["action"] == "status_change"
    repo.fetch_all.assert_called_once()