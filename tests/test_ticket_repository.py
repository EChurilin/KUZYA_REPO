import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from uuid import uuid4

from src.repositories.ticket_repo import TicketRepository
from src.core.entities import SupportTicket, SupportMessage
from src.core.enums import TicketStatus, SenderType


@pytest.fixture
def mock_pool():
    return AsyncMock()


@pytest.mark.asyncio
async def test_ticket_repository_create(mock_pool):
    repo = TicketRepository(mock_pool)
    ticket_id = uuid4()
    user_id = 123
    now = datetime.now()
    
    mock_row = {
        "id": ticket_id,
        "user_id": user_id,
        "status": TicketStatus.OPEN,
        "priority": "normal",
        "assigned_to": None,
        "created_at": now,
        "closed_at": None,
    }
    repo.fetch_one = AsyncMock(return_value=mock_row)

    ticket_entity = SupportTicket(
        id=ticket_id, user_id=user_id, status=TicketStatus.OPEN,
        priority="normal", assigned_to=None, created_at=now, closed_at=None
    )
    
    created_ticket = await repo.create_ticket(ticket_entity)

    assert created_ticket is not None
    assert created_ticket.id == ticket_id
    assert created_ticket.status == TicketStatus.OPEN
    repo.fetch_one.assert_called_once()


@pytest.mark.asyncio
async def test_ticket_repository_add_message(mock_pool):
    repo = TicketRepository(mock_pool)
    msg_id = uuid4()
    ticket_id = uuid4()
    now = datetime.now()
    
    mock_row = {
        "id": msg_id,
        "ticket_id": ticket_id,
        "sender_id": 123,
        "sender_type": SenderType.USER,
        "text": "Help me please",
        "file_id": None,
        "created_at": now,
    }
    repo.fetch_one = AsyncMock(return_value=mock_row)

    msg_entity = SupportMessage(
        id=msg_id, ticket_id=ticket_id, sender_id=123,
        sender_type=SenderType.USER, text="Help me please",
        file_id=None, created_at=now
    )
    
    created_msg = await repo.add_message(msg_entity)

    assert created_msg is not None
    assert created_msg.text == "Help me please"
    assert created_msg.sender_type == SenderType.USER
    repo.fetch_one.assert_called_once()


@pytest.mark.asyncio
async def test_ticket_repository_close_ticket(mock_pool):
    repo = TicketRepository(mock_pool)
    ticket_id = uuid4()
    now = datetime.now()
    
    mock_row = {
        "id": ticket_id,
        "user_id": 123,
        "status": TicketStatus.CLOSED,
        "priority": "normal",
        "assigned_to": 456,
        "created_at": now,
        "closed_at": now,
    }
    repo.fetch_one = AsyncMock(return_value=mock_row)

    closed_ticket = await repo.close_ticket(ticket_id, now)

    assert closed_ticket is not None
    assert closed_ticket.status == TicketStatus.CLOSED
    assert closed_ticket.closed_at == now
    repo.fetch_one.assert_called_once()