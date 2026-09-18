from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.exceptions import TelegramBadRequest
from src.config.settings import settings
from src.infrastructure.container import Container
from src.core.exceptions import (
    GiftNotFoundError,
    InsufficientBotBalanceError,
    InsufficientUserBalanceError,
)

router = Router()


def _gift_button_text(gift) -> str:
    """Формирует текст кнопки выбора подарка (эмодзи берётся из данных стикера)."""
    emoji = ""
    if gift.sticker and isinstance(gift.sticker, dict):
        emoji = gift.sticker.get("emoji") or ""
    if emoji:
        return f"{emoji} {gift.star_count} звёзд"
    return f"Подарок за {gift.star_count} звёзд"


@router.message(F.text == "Получить подарок")
async def menu_gift(message: Message, container: Container):
    """Кнопка главного меню «Получить подарок»: показывает баланс и доступные подарки."""
    user_id = message.from_user.id

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    balance = await container.user_balance_service.get_balance(user_id)
    gifts = await container.gift_service.get_affordable_gifts(user_id)

    if not gifts:
        await message.answer(
            f"Ваш баланс: {balance} звёзд.\n"
            "Пока нет подарков, которые вы можете получить. "
            "Выполняйте задания, чтобы заработать больше звёзд!"
        )
        return

    keyboard = [
        [InlineKeyboardButton(text=_gift_button_text(g), callback_data=f"gift_select:{g.id}")]
        for g in gifts
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(
        f"Ваш баланс: {balance} звёзд.\nВыберите подарок:",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("gift_select:"))
async def cb_gift_select(callback: CallbackQuery, container: Container):
    """Выбор подарка: отправка пользователю и списание с внутреннего баланса."""
    await callback.answer()
    user_id = callback.from_user.id
    gift_id = callback.data.split(":", 1)[1]

    try:
        await container.gift_service.claim_gift(user_id, gift_id)
    except GiftNotFoundError:
        await callback.message.answer(
            "Этот подарок больше недоступен. Откройте меню подарков заново."
        )
        return
    except InsufficientUserBalanceError:
        await callback.message.answer(
            "Недостаточно звёзд для получения этого подарка. "
            "Выполняйте задания, чтобы заработать больше!"
        )
        return
    except InsufficientBotBalanceError:
        await callback.message.answer("Подарок временно недоступен, попробуйте позже.")
        for admin_id in settings.client_bot.admin_ids:
            await container.notification_service.notify_admin(
                admin_id,
                "Не хватает реального баланса звёзд бота для отправки подарка. Пополните баланс.",
            )
        return

    # Убираем клавиатуру выбора, чтобы избежать повторного нажатия.
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await callback.message.answer(
        "Подарок отправлен! Проверьте раздел подарков в вашем профиле Telegram."
    )