from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.core.entities import SupportTicket, SupportMessage
from src.core.enums import TicketStatus, SenderType
from src.repositories.ticket_repo import TicketRepository
from src.repositories.audit_repo import AuditRepository
from src.utils.logger import logger


class SupportService:
    """Сервис для управления тикетами поддержки и перепиской."""

    def __init__(
        self,
        ticket_repo: TicketRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self._ticket_repo = ticket_repo
        self._audit_repo = audit_repo

    async def open_ticket(
        self,
        user_id: int,
        priority: str = "normal",
        initial_text: str | None = None,
        initial_file_id: str | None = None,
    ) -> SupportTicket:
        """Создает новый тикет и сразу добавляет в него первое сообщение пользователя."""
        logger.info(f"User {user_id} opening a new support ticket")
        now = datetime.now(timezone.utc)
        
        ticket = SupportTicket(
            id=uuid4(),
            user_id=user_id,
            status=TicketStatus.OPEN,
            priority=priority,
            assigned_to=None,
            created_at=now,
            closed_at=None,
        )
        created_ticket = await self._ticket_repo.create_ticket(ticket)

        # Если пользователь сразу прислал текст или файл, сохраняем это как первое сообщение
        if initial_text or initial_file_id:
            message = SupportMessage(
                id=uuid4(),
                ticket_id=created_ticket.id,
                sender_id=user_id,
                sender_type=SenderType.USER,
                text=initial_text,
                file_id=initial_file_id,
                created_at=now,
            )
            await self._ticket_repo.add_message(message)

        await self._audit_repo.log_action(
            entity_type="support_ticket",
            entity_id=str(created_ticket.id),
            actor_id=user_id,
            action="opened",
            new_values={"priority": priority},
        )

        return created_ticket

    async def add_message(
        self,
        ticket_id: UUID,
        sender_id: int,
        sender_type: str,
        text: str | None = None,
        file_id: str | None = None,
    ) -> SupportMessage:
        """Добавляет новое сообщение в существующий тикет.
        Примечание: Мы полагаемся на Foreign Key в БД. Если ticket_id не существует,
        asyncpg выбросит исключение ForeignKeyViolationError.
        """
        now = datetime.now(timezone.utc)
        message = SupportMessage(
            id=uuid4(),
            ticket_id=ticket_id,
            sender_id=sender_id,
            sender_type=sender_type,
            text=text,
            file_id=file_id,
            created_at=now,
        )
        return await self._ticket_repo.add_message(message)

    async def close_ticket(self, ticket_id: UUID, closed_by: int) -> SupportTicket | None:
        """Закрывает тикет и логирует действие модератора/админа."""
        now = datetime.now(timezone.utc)
        closed_ticket = await self._ticket_repo.close_ticket(ticket_id, now)
        
        if closed_ticket:
            logger.info(f"Ticket {ticket_id} closed by staff member {closed_by}")
            await self._audit_repo.log_action(
                entity_type="support_ticket",
                entity_id=str(ticket_id),
                actor_id=closed_by,
                action="closed",
                new_values={"status": TicketStatus.CLOSED},
            )
            
        return closed_ticket