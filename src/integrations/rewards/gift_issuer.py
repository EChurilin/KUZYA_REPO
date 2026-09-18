from typing import List, Optional

from aiogram import Bot

from src.core.entities import Gift


class GiftIssuer:
    """Обёртка над Telegram Bot API для работы с подарками и балансом звёзд бота."""

    def __init__(self, bot: Bot):
        self._bot = bot

    async def get_available_gifts(self) -> List[Gift]:
        gifts_obj = await self._bot.get_available_gifts()
        result: List[Gift] = []
        for g in gifts_obj.gifts:
            sticker_data = g.sticker.model_dump() if g.sticker is not None else None
            result.append(
                Gift(
                    id=g.id,
                    star_count=g.star_count,
                    sticker=sticker_data,
                    upgrade_star_count=g.upgrade_star_count,
                    is_premium=g.is_premium,
                    total_count=g.total_count,
                    remaining_count=g.remaining_count,
                    personal_total_count=g.personal_total_count,
                    personal_remaining_count=g.personal_remaining_count,
                )
            )
        return result

    async def send_gift(self, user_id: int, gift_id: str, text: Optional[str] = None) -> bool:
        kwargs = {"user_id": user_id, "gift_id": gift_id}
        if text is not None:
            kwargs["text"] = text
        return await self._bot.send_gift(**kwargs)

    async def get_bot_balance(self) -> int:
        star_amount = await self._bot.get_my_star_balance()
        return star_amount.amount