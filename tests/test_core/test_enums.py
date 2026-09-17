import pytest
from src.core.enums import (
    UserRole,
    SessionStatus,
    ApplicationStatus,
    ScreenshotStatus,
    MediaType,
    CampaignStatus,
    RewardType,
    RewardStatus,
    TicketStatus,
    TicketPriority,
    SenderType,
    RateLimitAction,
)


class TestUserRole:
    def test_values(self):
        assert UserRole.USER.value == "user"
        assert UserRole.MODERATOR.value == "moderator"
        assert UserRole.ADMIN.value == "admin"

    def test_string_comparison(self):
        assert UserRole.USER == "user"
        assert UserRole.ADMIN != "moderator"


class TestSessionStatus:
    def test_values(self):
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.EXPIRED.value == "expired"
        assert SessionStatus.CANCELLED.value == "cancelled"

    def test_all_statuses_exist(self):
        assert len(SessionStatus) == 4


class TestApplicationStatus:
    def test_values(self):
        assert ApplicationStatus.PENDING_REVIEW.value == "pending_review"
        assert ApplicationStatus.APPROVED.value == "approved"
        assert ApplicationStatus.REJECTED.value == "rejected"
        assert ApplicationStatus.REWARDED.value == "rewarded"


class TestScreenshotStatus:
    def test_values(self):
        assert ScreenshotStatus.PENDING.value == "pending"
        assert ScreenshotStatus.APPROVED.value == "approved"
        assert ScreenshotStatus.REJECTED.value == "rejected"


class TestMediaType:
    def test_values(self):
        assert MediaType.TEXT.value == "text"
        assert MediaType.PHOTO.value == "photo"
        assert MediaType.VIDEO.value == "video"


class TestRewardType:
    def test_values(self):
        assert RewardType.STARS.value == "stars"
        assert RewardType.GIFT.value == "gift"


class TestRewardStatus:
    def test_values(self):
        assert RewardStatus.PENDING.value == "pending"
        assert RewardStatus.ISSUED.value == "issued"
        assert RewardStatus.FAILED.value == "failed"


class TestTicketStatus:
    def test_values(self):
        assert TicketStatus.OPEN.value == "open"
        assert TicketStatus.IN_PROGRESS.value == "in_progress"
        assert TicketStatus.CLOSED.value == "closed"


class TestTicketPriority:
    def test_values(self):
        assert TicketPriority.LOW.value == "low"
        assert TicketPriority.MEDIUM.value == "medium"
        assert TicketPriority.HIGH.value == "high"


class TestSenderType:
    def test_values(self):
        assert SenderType.USER.value == "user"
        assert SenderType.STAFF.value == "staff"


class TestRateLimitAction:
    def test_values(self):
        assert RateLimitAction.SCREENSHOT_SUBMISSION.value == "screenshot_submission"
        assert RateLimitAction.APPLICATION_SUBMISSION.value == "application_submission"


class TestEnumInheritance:
    def test_all_enums_inherit_from_str(self):
        for enum_class in [
            UserRole, SessionStatus, ApplicationStatus, ScreenshotStatus,
            MediaType, CampaignStatus, RewardType, RewardStatus,
            TicketStatus, TicketPriority, SenderType, RateLimitAction,
        ]:
            for member in enum_class:
                assert isinstance(member.value, str), f"{enum_class.__name__}.{member.name} is not a string"