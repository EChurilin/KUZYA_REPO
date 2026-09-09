from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.core.entities import Application, Reward
from src.core.enums import ApplicationStatus, RewardStatus
from src.core.exceptions import ApplicationNotFoundError, IdempotencyError
from src.core.interfaces import RewardIssuer
from src.repositories.application_repo import ApplicationRepository
from src.repositories.campaign_repo import CampaignRepository
from src.repositories.reward_repo import RewardRepository
from src.repositories.audit_repo import AuditRepository
from src.utils.logger import logger


class ReviewService:
    """Сервис для модерации заявок и инициирования выдачи наград."""

    def __init__(
        self,
        app_repo: ApplicationRepository,
        campaign_repo: CampaignRepository,
        reward_repo: RewardRepository,
        audit_repo: AuditRepository,
        reward_issuer: RewardIssuer,
    ) -> None:
        self._app_repo = app_repo
        self._campaign_repo = campaign_repo
        self._reward_repo = reward_repo
        self._audit_repo = audit_repo
        self._reward_issuer = reward_issuer

    async def review_application(
        self,
        application_id: UUID,
        reviewer_id: int,
        is_approved: bool,
        comment: str | None = None,
    ) -> Application:
        """Проверяет заявку модератором и инициирует выдачу награды при одобрении."""
        app = await self._app_repo.get_by_id(application_id)
        if not app:
            raise ApplicationNotFoundError(f"Application {application_id} not found")

        # Защита от повторного нажатия кнопки "Одобрить/Отклонить"
        if app.status != ApplicationStatus.PENDING:
            raise IdempotencyError(f"Application {application_id} is already reviewed")

        now = datetime.now(timezone.utc)
        new_status = ApplicationStatus.APPROVED if is_approved else ApplicationStatus.REJECTED

        updated_app = await self._app_repo.update_status(
            app_id=application_id,
            status=new_status,
            reviewed_by=reviewer_id,
            reviewed_at=now,
            moderator_comment=comment,
        )

        if is_approved and updated_app:
            await self._process_reward(updated_app, now)

        await self._audit_repo.log_action(
            entity_type="application",
            entity_id=str(application_id),
            actor_id=reviewer_id,
            action="reviewed",
            old_values={"status": ApplicationStatus.PENDING},
            new_values={"status": new_status, "comment": comment},
        )

        return updated_app

    async def _process_reward(self, app: Application, now: datetime) -> None:
        """Создает запись о награде и вызывает интерфейс для её фактической выдачи."""
        campaign = await self._campaign_repo.get_by_id(app.campaign_id)
        if not campaign:
            logger.error(f"Campaign {app.campaign_id} not found during reward processing")
            return

        # Дополнительная проверка идемпотентности на уровне наград
        is_already_issued = await self._reward_repo.check_idempotency(app.id)
        if is_already_issued:
            logger.warning(f"Reward for application {app.id} already issued")
            return

        # Фаза 1: Создаем запись о награде со статусом PENDING
        reward = Reward(
            id=uuid4(),
            user_id=app.user_id,
            campaign_id=app.campaign_id,
            application_id=app.id,
            reward_type=campaign.reward_type,
            amount=campaign.reward_amount,
            transaction_id=None,
            status=RewardStatus.PENDING,
            issued_at=None,
            delivered_at=None,
        )
        created_reward = await self._reward_repo.create(reward)

        # Фаза 2: Пытаемся выдать награду через внешний API (интерфейс)
        result = await self._reward_issuer.issue(
            user_id=app.user_id,
            reward_type=campaign.reward_type,
            amount=campaign.reward_amount,
        )

        # Фаза 3: Фиксируем результат
        if result.is_success:
            await self._reward_repo.mark_as_issued(
                reward_id=created_reward.id,
                transaction_id=result.transaction_id or "unknown",
                issued_at=now,
                delivered_at=now,
            )
            logger.info(f"Reward successfully issued for application {app.id}")
        else:
            await self._reward_repo.mark_as_failed(created_reward.id, now)
            logger.error(f"Failed to issue reward for app {app.id}: {result.error_message}")