import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.background_tasks import run_cleanup_loop


@pytest.fixture
def mock_container():
    container = MagicMock()
    container.cleanup_service = AsyncMock()
    container.cleanup_service.process_expired_sessions = AsyncMock(return_value=0)
    container.cleanup_service.cleanup_old_screenshots = AsyncMock(return_value=(0, 0))
    container.cleanup_service.cleanup_old_games = AsyncMock(return_value=(0, 0))
    container.cleanup_service.cleanup_old_instruction_versions = AsyncMock(return_value=(0, 0))
    return container


@pytest.mark.asyncio
async def test_cleanup_loop_calls_all_methods(mock_container):
    """Проверяет, что цикл очистки вызывает все методы CleanupService."""
    task = asyncio.create_task(run_cleanup_loop(mock_container, interval_seconds=0.1))
    
    await asyncio.sleep(0.15)
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    mock_container.cleanup_service.process_expired_sessions.assert_called()
    mock_container.cleanup_service.cleanup_old_screenshots.assert_called()
    mock_container.cleanup_service.cleanup_old_games.assert_called_with(hours=36)
    mock_container.cleanup_service.cleanup_old_instruction_versions.assert_called_with(hours=24)


@pytest.mark.asyncio
async def test_cleanup_loop_continues_when_one_step_fails(mock_container):
    """Проверяет, что падение одного шага очистки не блокирует остальные."""
    # Первый метод падает, остальные работают нормально.
    mock_container.cleanup_service.process_expired_sessions = AsyncMock(side_effect=Exception("Test error"))
    
    task = asyncio.create_task(run_cleanup_loop(mock_container, interval_seconds=0.1))
    
    await asyncio.sleep(0.15)
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    # Несмотря на падение process_expired_sessions, остальные три метода должны быть вызваны.
    mock_container.cleanup_service.cleanup_old_screenshots.assert_called()
    mock_container.cleanup_service.cleanup_old_games.assert_called()
    mock_container.cleanup_service.cleanup_old_instruction_versions.assert_called()


@pytest.mark.asyncio
async def test_cleanup_loop_can_be_cancelled(mock_container):
    """Проверяет, что задача корректно отменяется."""
    task = asyncio.create_task(run_cleanup_loop(mock_container, interval_seconds=10))
    
    await asyncio.sleep(0.05)
    task.cancel()
    
    with pytest.raises(asyncio.CancelledError):
        await task