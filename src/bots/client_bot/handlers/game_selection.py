import uuid
import logging
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    FSInputFile,
)
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from src.infrastructure.container import Container
from src.bots.client_bot.handlers.instruction import start_instruction_flow

router = Router()
logger = logging.getLogger(__name__)


async def _show_game_list(message: Message, container: Container) -> None:
    """Отправляет список доступных игр новым сообщением."""
    games = await container.game_service.get_active_games()

    if not games:
        await message.answer("Временно нет доступных игр. Попробуйте позже.")
        return

    keyboard = [
        [InlineKeyboardButton(text=game.name, callback_data=f"game_select:{game.id}")]
        for game in games
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(
        "Выберите игру, в которой вы хотите заработать награду:",
        reply_markup=kb,
    )


async def _handle_play_start(
    anchor_message: Message,
    bot: Bot,
    container: Container,
    state: FSMContext,
    user_id: int,
) -> None:
    """Общая логика «Начать играть»: гейт по инструкции и показ списка игр."""
    user = await container.user_service.get_user(user_id)

    logger.info(
        f"_handle_play_start: user_id={user_id}, "
        f"user_exists={user is not None}, "
        f"instruction_passed={user.instruction_passed if user else 'N/A'}"
    )

    if user is None or not user.instruction_passed:
        await anchor_message.answer("Сначала посмотрите инструкцию.")
        await start_instruction_flow(anchor_message, bot, container, state)
        return

    await _show_game_list(anchor_message, container)


@router.message(F.text == "Начать играть")
async def menu_play(message: Message, bot: Bot, container: Container, state: FSMContext):
    """Кнопка главного меню «Начать играть»."""
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    await _handle_play_start(message, bot, container, state, message.from_user.id)


@router.callback_query(F.data == "play_start")
async def cb_play_start(callback: CallbackQuery, container: Container, state: FSMContext):
    """Inline-кнопка «Начать играть» (под последним блоком инструкции или в карточке игры)."""
    await callback.answer()
    await _handle_play_start(
        callback.message, callback.bot, container, state, callback.from_user.id
    )


@router.callback_query(F.data.startswith("game_select:"))
async def cb_game_select(callback: CallbackQuery, container: Container, state: FSMContext):
    """Показывает карточку выбранной игры и кнопку «Начать»."""
    await callback.answer()

    game_id_str = callback.data.split(":")[1]

    try:
        game_id = uuid.UUID(game_id_str)
    except ValueError:
        await callback.message.edit_text("Ошибка: некорректный идентификатор игры.")
        return

    game = await container.game_service.get_game_by_id(game_id)

    if not game or not game.is_active:
        await callback.message.edit_text("Эта игра больше недоступна. Выберите другую.")
        return

    await state.update_data(selected_game_id=game_id_str)

    # [fix] Убран показ ссылки в карточке игры
    game_card_text = (
        f"Игра: {game.name}\n\n"
        f"Нажмите «Начать», чтобы открыть сессию и начать зарабатывать."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="session_start")],
        [InlineKeyboardButton(text="Список игр", callback_data="play_start")],
    ])

    if game.photo_path and Path(game.photo_path).exists():
        photo = FSInputFile(game.photo_path)
        await callback.message.answer_photo(photo, caption=game_card_text, reply_markup=kb)
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
    else:
        await callback.message.edit_text(game_card_text, reply_markup=kb)
