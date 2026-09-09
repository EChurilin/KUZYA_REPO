import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from uuid import uuid4

from src.services.support_service import SupportService
from src.core.entities import SupportTicket, SupportMessage
from src.core.enums import TicketStatus, SenderType


@pytest.fixture
def mock_deps():
    return {
        "ticket_repo": AsyncMock(),
        "audit_repo": AsyncMock(),
    }


@pytest.mark.asyncio
async def test_open_ticket_with_message(mock_deps):
    """Проверяет создание тикета вместе с первым сообщением пользователя."""
    service = SupportService(**mock_deps)
    user_id = 123
    ticket_id = uuid4()
    now = datetime.now(timezone.utc)
    
    created_ticket = SupportTicket(
        id=ticket_id, user_id=user_id, status=TicketStatus.OPEN,
        priority="normal", assigned_to=None, created_at=now, closed_at=None
    )
    mock_deps["ticket_repo"].create_ticket.return_value = created_ticket

    result = await service.open_ticket(
        user_id=user_id,
        priority="normal",
        initial_text="Help me",
        initial_file_id=None
    )

    assert result.id == ticket_id
    assert result.status == TicketStatus.OPEN
    mock_deps["ticket_repo"].create_ticket.assert_called_once()
    # Проверяем, что метод добавления сообщения тоже был вызван
    mock_deps["ticket_repo"].add_message.assert_called_once()
    mock_deps["audit_repo"].log_action.assert_called_once()


@pytest.mark.asyncio
async def test_add_message_from_staff(mock_deps):
    """Проверяет добавление ответа от модератора."""
    service = SupportService(**mock_deps)
    ticket_id = uuid4()
    staff_id = 999
    
    expected_msg = SupportMessage(
        id=uuid4(), ticket_id=ticket_id, sender_id=staff_id,
        sender_type=SenderType.STAFF, text="We are looking into it",
        file_id=None, created_at=datetime.now(timezone.utc)
    )
    mock_deps["ticket_repo"].add_message.return_value = expected_msg

    result = await service.add_message(
        ticket_id=ticket_id,
        sender_id=staff_id,
        sender_type=SenderType.STAFF,
        text="We are looking into it"
    )

    assert result.sender_type == SenderType.STAFF
    assert result.text == "We are looking into it"
    mock_deps["ticket_repo"].add_message.assert_called_once()


@pytest.mark.asyncio
async def test_close_ticket(mock_deps):
    """Проверяет закрытие тикета и запись в аудит."""
    service = SupportService(**mock_deps)
    ticket_id = uuid4()
    staff_id = 999
    now = datetime.now(timezone.utc)
    
    closed_ticket = SupportTicket(
        id=ticket_id, user_id=123, status=TicketStatus.CLOSED,
        priority="normal", assigned_to=staff_id, created_at=now, closed_at=now
    )
    mock_deps["ticket_repo"].close_ticket.return_value = closed_ticket

    result = await service.close_ticket(ticket_id, staff_id)

    assert result.status == TicketStatus.CLOSED
    mock_deps["ticket_repo"].close_ticket.assert_called_once()
    # Проверяем, что действие закрытия записано в аудит
    mock_deps["audit_repo"].log_action.assert_called_once()
    call_args = mock_deps["audit_repo"].log_action.call_args[1]
    assert call_args["action"] == "closed"
    assert call_args["actor_id"] == staff_id