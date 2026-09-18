import pytest
from unittest.mock import AsyncMock, MagicMock

from src.integrations.rewards.gift_issuer import GiftIssuer


@pytest.fixture
def mock_bot():
    return AsyncMock()


class TestGiftIssuer:
    @pytest.mark.asyncio
    async def test_get_available_gifts(self, mock_bot):
        gift1 = MagicMock()
        gift1.id = "gift_1"
        gift1.star_count = 50
        gift1.sticker = None
        gift1.upgrade_star_count = None
        gift1.is_premium = None
        gift1.total_count = None
        gift1.remaining_count = None
        gift1.personal_total_count = None
        gift1.personal_remaining_count = None

        gifts_obj = MagicMock()
        gifts_obj.gifts = [gift1]
        mock_bot.get_available_gifts = AsyncMock(return_value=gifts_obj)

        issuer = GiftIssuer(mock_bot)
        gifts = await issuer.get_available_gifts()

        assert len(gifts) == 1
        assert gifts[0].id == "gift_1"
        assert gifts[0].star_count == 50
        mock_bot.get_available_gifts.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_gifts_empty(self, mock_bot):
        gifts_obj = MagicMock()
        gifts_obj.gifts = []
        mock_bot.get_available_gifts = AsyncMock(return_value=gifts_obj)

        issuer = GiftIssuer(mock_bot)
        gifts = await issuer.get_available_gifts()

        assert gifts == []

    @pytest.mark.asyncio
    async def test_send_gift_success(self, mock_bot):
        mock_bot.send_gift = AsyncMock(return_value=True)

        issuer = GiftIssuer(mock_bot)
        result = await issuer.send_gift(user_id=123, gift_id="gift_1")

        assert result is True
        mock_bot.send_gift.assert_called_once()
        call_kwargs = mock_bot.send_gift.call_args[1]
        assert call_kwargs["user_id"] == 123
        assert call_kwargs["gift_id"] == "gift_1"

    @pytest.mark.asyncio
    async def test_send_gift_with_text(self, mock_bot):
        mock_bot.send_gift = AsyncMock(return_value=True)

        issuer = GiftIssuer(mock_bot)
        result = await issuer.send_gift(user_id=123, gift_id="gift_1", text="Спасибо за игру")

        assert result is True
        mock_bot.send_gift.assert_called_once()
        call_kwargs = mock_bot.send_gift.call_args[1]
        assert call_kwargs["text"] == "Спасибо за игру"

    @pytest.mark.asyncio
    async def test_get_bot_balance(self, mock_bot):
        star_amount = MagicMock()
        star_amount.amount = 1500
        mock_bot.get_my_star_balance = AsyncMock(return_value=star_amount)

        issuer = GiftIssuer(mock_bot)
        balance = await issuer.get_bot_balance()

        assert balance == 1500
        mock_bot.get_my_star_balance.assert_called_once()