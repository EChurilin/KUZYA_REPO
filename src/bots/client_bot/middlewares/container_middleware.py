from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from src.infrastructure.container import Container


class ContainerMiddleware(BaseMiddleware):
    """
    Middleware для инъекции Container в хендлеры.
    Автоматически добавляет параметр 'container' в kwargs хендлера.
    """
    
    def __init__(self, container: Container):
        self.container = container
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data["container"] = self.container
        return await handler(event, data)