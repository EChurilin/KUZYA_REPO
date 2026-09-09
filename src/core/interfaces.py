from typing import Protocol, Any
from uuid import UUID
from dataclasses import dataclass


@dataclass
class ValidationResult:
    is_valid: bool
    error_message: str | None = None


@dataclass
class RewardResult:
    is_success: bool
    transaction_id: str | None = None
    error_message: str | None = None


class ValidationStrategy(Protocol):
    async def validate(self, screenshot_file_id: str, user_id: int) -> ValidationResult:
        ...


class RewardIssuer(Protocol):
    async def issue(self, user_id: int, reward_type: str, amount: int) -> RewardResult:
        ...


class ScreenshotStorage(Protocol):
    async def save(self, file_id: str) -> str:
        ...
    
    async def delete(self, file_id: str) -> None:
        ...


class NotificationSender(Protocol):
    async def send(self, user_id: int, message: str) -> bool:
        ...


class AnalyticsSink(Protocol):
    async def track(self, event_name: str, properties: dict[str, Any]) -> None:
        ...


class ChatStorage(Protocol):
    async def save_message(
        self, 
        ticket_id: UUID, 
        sender_id: int, 
        sender_type: str, 
        text: str | None, 
        file_id: str | None
    ) -> None:
        ...