from uuid import UUID

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from src.infrastructure.container import Container
from src.core.exceptions import RateLimitExceededError, BaseBotException
from src.utils.logger import logger


async def handle_campaigns_list(message: Message, container: Container) -> None:
    """Выводит список активных кампаний."""
    # Напрямую обращаемся к репозиторию. 
    # В будущем здесь можно будет использовать CampaignService для кэширования в Redis.
    campaigns = await container.campaign_repo.get_active()
    
    if not campaigns:
        await message.answer("Сейчас нет активных кампаний. Загляни позже!")
        return

    text = "Доступные кампании:\n\n"
    for camp in campaigns:
        text += (
            f"Название: {camp.name}\n"
            f"Награда: {camp.reward_amount} {camp.reward_type}\n"
            f"Описание: {camp.description}\n"
            f"ID кампании: {camp.id}\n\n"
        )
    text += "Чтобы участвовать, отправь скриншот выполнения условий и укажи ID кампании в подписи к фото."
    await message.answer(text)


async def handle_screenshot(message: Message, container: Container) -> None:
    """Принимает скриншот (фото) и отправляет его на модерацию."""
    if not message.photo:
        await message.answer("Пожалуйста, отправь скриншот в виде фотографии.")
        return

    user = message.from_user
    if not user:
        return

    # Пытаемся извлечь campaign_id из подписи к фото (caption)
    if not message.caption:
        await message.answer("Не указан ID кампании. Отправь фото и в подписи укажи ID кампании.")
        return

    try:
        campaign_id = UUID(message.caption.strip())
    except ValueError:
        await message.answer("Неверный формат ID кампании. Убедись, что это UUID.")
        return

    # Берем file_id самого большого размера фото (последний элемент в списке)
    file_id = message.photo[-1].file_id

    try:
        await container.app_service.submit_application(
            user_id=user.id,
            campaign_id=campaign_id,
            screenshot_file_id=file_id,
        )
        await message.answer("Скриншот успешно принят и отправлен на проверку модератором!")
    except RateLimitExceededError as e:
        await message.answer(f"Лимит превышен: {e}")
    except ValueError as e:
        # Ошибка из ApplicationService (например, кампания не найдена или неактивна)
        await message.answer(f"Ошибка: {e}")
    except BaseBotException as e:
        logger.error(f"Bot error during screenshot submission: {e}")
        await message.answer("Произошла ошибка при обработке заявки. Попробуй позже.")


def get_campaigns_router(container: Container) -> Router:
    """Фабрика роутера для работы с кампаниями и скриншотами."""
    router = Router(name="client_campaigns")

    @router.message(Command("campaigns"))
    async def cmd_campaigns_wrapper(message: Message) -> None:
        await handle_campaigns_list(message, container)

    # Фильтр F.photo срабатывает на любое сообщение, содержащее фотографию
    @router.message(F.photo)
    async def photo_wrapper(message: Message) -> None:
        await handle_screenshot(message, container)

    return router