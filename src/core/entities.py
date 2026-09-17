import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class User:
    id: int
    username: Optional[str]
    first_name: Optional[str]
    language_code: Optional[str]
    role: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Game:
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class InstructionBlock:
    id: uuid.UUID
    order: int
    text: Optional[str]
    media_type: str
    media_path: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class Session:
    id: uuid.UUID
    user_id: int
    game_id: uuid.UUID
    status: str
    started_at: datetime
    last_screenshot_at: Optional[datetime]
    screenshot_count: int
    created_at: datetime


@dataclass
class Campaign:
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class Application:
    id: uuid.UUID
    user_id: int
    session_id: uuid.UUID
    campaign_id: Optional[uuid.UUID]
    status: str
    actual_screenshot_count: int
    approved_screenshot_count: int
    moderator_comment: Optional[str]
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    rewarded_at: Optional[datetime]
    reviewed_by: Optional[int]
    auto_closed: bool
    screenshots: List["ApplicationScreenshot"] = field(default_factory=list)


@dataclass
class ApplicationScreenshot:
    id: uuid.UUID
    session_id: uuid.UUID
    application_id: Optional[uuid.UUID]
    client_file_id: str
    storage_path: str
    status: str
    created_at: datetime


@dataclass
class Reward:
    id: uuid.UUID
    user_id: int
    application_id: uuid.UUID
    reward_type: str
    amount: int
    transaction_id: Optional[str]
    status: str
    issued_at: Optional[datetime]
    delivered_at: Optional[datetime]


@dataclass
class BalanceSnapshot:
    id: uuid.UUID
    reward_type: str
    balance: int
    fetched_at: datetime


@dataclass
class SupportTicket:
    id: uuid.UUID
    user_id: int
    status: str
    priority: str
    assigned_to: Optional[int]
    created_at: datetime
    closed_at: Optional[datetime]


@dataclass
class SupportMessage:
    id: uuid.UUID
    ticket_id: uuid.UUID
    sender_id: int
    sender_type: str
    text: Optional[str]
    file_id: Optional[str]
    created_at: datetime


@dataclass
class AuditLog:
    id: uuid.UUID
    entity_type: str
    entity_id: str
    actor_id: int
    action: str
    old_values: Optional[dict]
    new_values: Optional[dict]
    created_at: datetime


@dataclass
class RateLimit:
    id: uuid.UUID
    user_id: int
    action_type: str
    counter: int
    window_start: datetime