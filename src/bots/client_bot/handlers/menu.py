from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from src.infrastructure.container import Container

router = Router()

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Показывает справку по командам"""
    text = (
        "📚 *Справка*\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/status - Проверить статус ваших заявок\n"
        "/support - Связаться с поддержкой"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("status"))
async def cmd_status(message: Message, container: Container):
    """Показывает последние заявки пользователя"""
    user_id = message.from_user.id
    apps = await container.application_service.get_user_applications(user_id, limit=5)
    
    if not apps:
        await message.answer("📭 У вас пока нет заявок. Начните с команды /start!")
        return
        
    text = "📋 *Ваши последние заявки:*\n\n"
    for app in apps:
        status_map = {
            "pending_review": "⏳ На проверке",
            "approved": "✅ Одобрено",
            "rejected": "❌ Отклонено",
            "rewarded": "🎁 Награда выдана"
        }
        status_text = status_map.get(app.status, app.status)
        text += f"• Заявка #{str(app.id)[:8]}: {status_text}\n"
        if app.moderator_comment:
            text += f"  _Комментарий: {app.moderator_comment}_\n"
        text += "\n"
        
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("support"))
async def cmd_support(message: Message):
    """Показывает контактную информацию поддержки"""
    text = (
        "🛠 *Поддержка*\n\n"
        "Если у вас возникли вопросы или проблемы, пожалуйста, свяжитесь с нами:\n"
        "@kizya_support_admin\n\n"
        "Мы стараемся отвечать в течение 24 часов."
    )
    await message.answer(text, parse_mode="Markdown")