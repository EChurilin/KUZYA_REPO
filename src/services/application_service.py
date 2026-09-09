from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.core.entities import Application
from src.core.enums import ApplicationStatus
from src.core.exceptions import RateLimitExceededError
from src.repositories.application_repo import ApplicationRepository
from src.repositories.campaign_repo import CampaignRepository
from src.repositories.audit_repo import AuditRepository
from src.utils.logger import logger


class ApplicationService:
    """Сервис для управления заявками на участие в кампаниях."""

    def __init__(
        self,
        app_repo: ApplicationRepository,
        campaign_repo: CampaignRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self._app_repo = app_repo
        self._campaign_repo = campaign_repo
        self._audit_repo = audit_repo

    async def submit_application(
        self,
        user_id: int,
        campaign_id: UUID,
        screenshot_file_id: str,
    ) -> Application:
        """Принимает скриншот от пользователя и создает заявку на модерацию."""
        
        # 1. Проверяем существование и базовую активность кампании
        campaign = await self._campaign_repo.get_by_id(campaign_id)
        if not campaign or not campaign.is_active:
            raise ValueError("Campaign not found or inactive")
            
        # Дополнительно проверяем даты (защита от рассинхрона флага is_active и реальных дат)
        now = datetime.now(timezone.utc)
        # asyncpg возвращает offset-aware datetime, поэтому сравниваем напрямую
        if campaign.starts_at > now or campaign.ends_at < now:
            raise ValueError("Campaign is not active by date")

        # 2. Проверяем лимиты (идемпотентность и защита от спама)
        submissions_count = await self._app_repo.count_user_campaign_submissions(
            user_id, campaign_id
        )
        if submissions_count >= campaign.max_rewards_per_user:
            logger.warning(
                f"User {user_id} exceeded submission limit for campaign {campaign_id}"
            )
            raise RateLimitExceededError(
                "You have already submitted the maximum number of applications for this campaign."
            )

        # 3. Создаем и сохраняем заявку
        logger.info(f"User {user_id} submitting application for campaign {campaign_id}")
        new_application = Application(
            id=uuid4(),
            user_id=user_id,
            campaign_id=campaign_id,
            status=ApplicationStatus.PENDING,
            screenshot_file_id=screenshot_file_id,
            moderator_comment=None,
            submitted_at=now,
            reviewed_at=None,
            rewarded_at=None,
            reviewed_by=None,
        )
        
        created_app = await self._app_repo.create(new_application)

        # 4. Аудируем действие пользователя
        await self._audit_repo.log_action(
            entity_type="application",
            entity_id=created_app.id,
            actor_id=user_id,
            action="submitted",
            new_values={"status": ApplicationStatus.PENDING, "campaign_id": str(campaign_id)},
        )

        return created_app