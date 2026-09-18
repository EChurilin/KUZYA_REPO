from aiogram import Bot


class NotificationService:
    """Сервис для отправки сообщений от имени клиентского бота."""

    def __init__(self, client_bot: Bot):
        self._client_bot = client_bot

    async def notify_user(self, user_id: int, text: str) -> None:
        """Отправляет сообщение пользователю от имени клиентского бота."""
        await self._client_bot.send_message(chat_id=user_id, text=text)

    async def notify_admin(self, admin_id: int, text: str) -> None:
        """Отправляет сообщение администратору от имени клиентского бота."""
        await self._client_bot.send_message(chat_id=admin_id, text=text)