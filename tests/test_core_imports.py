def test_enums():
    from src.core import enums

    assert enums.UserRole.ADMIN == "admin"
    assert enums.UserRole.MODERATOR == "moderator"
    assert enums.UserRole.USER == "user"

    assert enums.ApplicationStatus.PENDING == "pending"
    assert enums.ApplicationStatus.APPROVED == "approved"
    assert enums.ApplicationStatus.REJECTED == "rejected"

    assert enums.RewardType.STARS == "stars"
    assert enums.RewardType.PROMO == "promo"

    assert enums.RewardStatus.PENDING == "pending"
    assert enums.RewardStatus.ISSUED == "issued"
    assert enums.RewardStatus.FAILED == "failed"

    assert enums.TicketStatus.OPEN == "open"
    assert enums.TicketStatus.IN_PROGRESS == "in_progress"
    assert enums.TicketStatus.CLOSED == "closed"

    assert enums.SenderType.USER == "user"
    assert enums.SenderType.STAFF == "staff"


def test_entities():
    from src.core import entities
    from datetime import datetime
    from uuid import uuid4

    user = entities.User(
        id=123,
        username="test",
        first_name="Test",
        language_code="ru",
        role="user",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert user.id == 123

    campaign = entities.Campaign(
        id=uuid4(),
        name="Test Campaign",
        description="Test",
        reward_type="stars",
        reward_amount=10,
        starts_at=datetime.now(),
        ends_at=datetime.now(),
        max_rewards_per_user=1,
        is_active=True,
        created_at=datetime.now(),
    )
    assert campaign.is_active is True

    application = entities.Application(
        id=uuid4(),
        user_id=123,
        campaign_id=campaign.id,
        status="pending",
        screenshot_file_id="file123",
        moderator_comment=None,
        submitted_at=datetime.now(),
        reviewed_at=None,
        rewarded_at=None,
        reviewed_by=None,
    )
    assert application.user_id == 123


def test_interfaces():
    from src.core import interfaces

    val_res = interfaces.ValidationResult(is_valid=True)
    assert val_res.is_valid is True
    assert val_res.error_message is None

    reward_res = interfaces.RewardResult(is_success=True, transaction_id="tx123")
    assert reward_res.is_success is True

    assert hasattr(interfaces, "ValidationStrategy")
    assert hasattr(interfaces, "RewardIssuer")
    assert hasattr(interfaces, "ScreenshotStorage")
    assert hasattr(interfaces, "NotificationSender")
    assert hasattr(interfaces, "AnalyticsSink")
    assert hasattr(interfaces, "ChatStorage")


def test_exceptions():
    from src.core import exceptions

    assert issubclass(exceptions.UserNotFoundError, exceptions.BaseBotException)
    assert issubclass(exceptions.ApplicationNotFoundError, exceptions.BaseBotException)
    assert issubclass(exceptions.IdempotencyError, exceptions.BaseBotException)
    assert issubclass(exceptions.InsufficientBalanceError, exceptions.BaseBotException)
    assert issubclass(exceptions.RateLimitExceededError, exceptions.BaseBotException)
    assert issubclass(exceptions.InvalidScreenshotError, exceptions.BaseBotException)