from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.entities import SupportTicket, SupportMessage
from src.core.enums import TicketStatus
from src.config.constants import DatabaseTables
from src.repositories.base import BaseRepository


class TicketRepository(BaseRepository):
    """Репозиторий для работы с тикетами поддержки и сообщениями."""

    async def create_ticket(self, ticket: SupportTicket) -> SupportTicket:
        """Создает новый тикет поддержки."""
        query = f"""
            INSERT INTO {DatabaseTables.SUPPORT_TICKETS}
            (id, user_id, status, priority, assigned_to, created_at, closed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, user_id, status, priority, assigned_to, created_at, closed_at
        """
        row = await self.fetch_one(
            query,
            ticket.id,
            ticket.user_id,
            ticket.status,
            ticket.priority,
            ticket.assigned_to,
            ticket.created_at,
            ticket.closed_at,
        )
        return self._map_row_to_ticket(row)

    async def get_user_tickets(self, user_id: int, limit: int = 10) -> list[SupportTicket]:
        """Возвращает тикеты конкретного пользователя."""
        query = f"""
            SELECT id, user_id, status, priority, assigned_to, created_at, closed_at
            FROM {DatabaseTables.SUPPORT_TICKETS}
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        rows = await self.fetch_all(query, user_id, limit)
        return [self._map_row_to_ticket(row) for row in rows]

    async def get_open_tickets_for_staff(self, limit: int = 50) -> list[SupportTicket]:
        """Возвращает открытые тикеты для модераторов."""
        query = f"""
            SELECT id, user_id, status, priority, assigned_to, created_at, closed_at
            FROM {DatabaseTables.SUPPORT_TICKETS}
            WHERE status IN ($1, $2)
            ORDER BY priority DESC, created_at ASC
            LIMIT $3
        """
        rows = await self.fetch_all(query, TicketStatus.OPEN, TicketStatus.IN_PROGRESS, limit)
        return [self._map_row_to_ticket(row) for row in rows]

    async def add_message(self, message: SupportMessage) -> SupportMessage:
        """Добавляет сообщение в тикет."""
        query = f"""
            INSERT INTO {DatabaseTables.SUPPORT_MESSAGES}
            (id, ticket_id, sender_id, sender_type, text, file_id, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, ticket_id, sender_id, sender_type, text, file_id, created_at
        """
        row = await self.fetch_one(
            query,
            message.id,
            message.ticket_id,
            message.sender_id,
            message.sender_type,
            message.text,
            message.file_id,
            message.created_at,
        )
        return self._map_row_to_message(row)

    async def get_messages(self, ticket_id: UUID, limit: int = 50) -> list[SupportMessage]:
        """Возвращает историю сообщений тикета."""
        query = f"""
            SELECT id, ticket_id, sender_id, sender_type, text, file_id, created_at
            FROM {DatabaseTables.SUPPORT_MESSAGES}
            WHERE ticket_id = $1
            ORDER BY created_at ASC
            LIMIT $2
        """
        rows = await self.fetch_all(query, ticket_id, limit)
        return [self._map_row_to_message(row) for row in rows]

    async def close_ticket(self, ticket_id: UUID, closed_at: datetime) -> SupportTicket | None:
        """Закрывает тикет."""
        query = f"""
            UPDATE {DatabaseTables.SUPPORT_TICKETS}
            SET status = $2, closed_at = $3
            WHERE id = $1
            RETURNING id, user_id, status, priority, assigned_to, created_at, closed_at
        """
        row = await self.fetch_one(query, ticket_id, TicketStatus.CLOSED, closed_at)
        return self._map_row_to_ticket(row) if row else None

    @staticmethod
    def _map_row_to_ticket(row: dict[str, Any]) -> SupportTicket:
        return SupportTicket(
            id=row["id"],
            user_id=row["user_id"],
            status=row["status"],
            priority=row["priority"],
            assigned_to=row["assigned_to"],
            created_at=row["created_at"],
            closed_at=row["closed_at"],
        )

    @staticmethod
    def _map_row_to_message(row: dict[str, Any]) -> SupportMessage:
        return SupportMessage(
            id=row["id"],
            ticket_id=row["ticket_id"],
            sender_id=row["sender_id"],
            sender_type=row["sender_type"],
            text=row["text"],
            file_id=row["file_id"],
            created_at=row["created_at"],
        )