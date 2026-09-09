from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    id: int
    username: str | None
    first_name: str
    language_code: str
    role: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Campaign:
    id: UUID
    name: str
    description: str
    reward_type: str
    reward_amount: int
    starts_at: datetime
    ends_at: datetime
    max_rewards_per_user: int
    is_active: bool
    created_at: datetime


@dataclass
class Application:
    id: UUID
    user_id: int
    campaign_id: UUID
    status: str
    screenshot_file_id: str | None
    moderator_comment: str | None
    submitted_at: datetime
    reviewed_at: datetime | None
    rewarded_at: datetime | None
    reviewed_by: int | None


@dataclass
class Reward:
    id: UUID
    user_id: int
    campaign_id: UUID
    application_id: UUID
    reward_type: str
    amount: int
    transaction_id: str | None
    status: str
    issued_at: datetime | None
    delivered_at: datetime | None


@dataclass
class SupportTicket:
    id: UUID
    user_id: int
    status: str
    priority: str
    assigned_to: int | None
    created_at: datetime
    closed_at: datetime | None


@dataclass
class SupportMessage:
    id: UUID
    ticket_id: UUID
    sender_id: int
    sender_type: str
    text: str | None
    file_id: str | None
    created_at: datetime