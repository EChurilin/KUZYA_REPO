import pytest
from unittest.mock import AsyncMock, patch

from src.infrastructure.container import Container


@pytest.mark.asyncio
async def test_container_init_and_shutdown():
    """Проверяет, что контейнер корректно инициализирует все зависимости
    и безопасно закрывает подключения (без поднятия реальных БД и Redis).
    """
    container = Container()

    # Мокаем функции подключения к БД и Redis
    with patch("src.infrastructure.container.init_db_pool", new_callable=AsyncMock) as mock_db, \
         patch("src.infrastructure.container.init_redis", new_callable=AsyncMock) as mock_redis, \
         patch("src.infrastructure.container.close_db_pool", new_callable=AsyncMock) as mock_close_db, \
         patch("src.infrastructure.container.close_redis", new_callable=AsyncMock) as mock_close_redis:
        
        mock_db.return_value = AsyncMock()
        mock_redis.return_value = AsyncMock()

        # 1. Инициализация
        await container.init()

        assert container.db_pool is not None
        assert container.redis_client is not None
        
        # Проверяем, что все репозитории созданы
        assert container.user_repo is not None
        assert container.app_repo is not None
        assert container.reward_repo is not None
        assert container.ticket_repo is not None
        assert container.audit_repo is not None
        
        # Проверяем, что все сервисы созданы
        assert container.user_service is not None
        assert container.app_service is not None
        assert container.review_service is not None
        assert container.support_service is not None

        # 2. Завершение работы
        await container.shutdown()

        mock_close_db.assert_called_once()
        mock_close_redis.assert_called_once()