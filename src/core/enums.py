class UserRole:
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class ApplicationStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RewardType:
    STARS = "stars"
    PROMO = "promo"


class RewardStatus:
    PENDING = "pending"
    ISSUED = "issued"
    FAILED = "failed"


class TicketStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class SenderType:
    USER = "user"
    STAFF = "staff"