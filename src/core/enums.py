from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApplicationStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REWARDED = "rewarded"


class ScreenshotStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MediaType(str, Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"


class CampaignStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class RewardType(str, Enum):
    STARS = "stars"
    GIFT = "gift"


class RewardStatus(str, Enum):
    PENDING = "pending"
    ISSUED = "issued"
    FAILED = "failed"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SenderType(str, Enum):
    USER = "user"
    STAFF = "staff"


class RateLimitAction(str, Enum):
    SCREENSHOT_SUBMISSION = "screenshot_submission"
    APPLICATION_SUBMISSION = "application_submission"