from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from src.infrastructure.container import Container


router = Router()


@router.callback_query(F.data == "application_start")
async def cb_application_start(callback: CallbackQuery, container: Container, state: FSMContext):
    """Показывает список доступных игр для выбора"""
    await callback.answer()
    
    # Получаем список активных игр
    games = await container.game_service.get_active_games()
    
    if not games:
        await callback.message.edit_text("Временно нет доступных игр. Попробуйте позже.")
        return
    
    # Формируем inline-клавиатуру со списком игр
    keyboard = []
    for game in games:
        keyboard.append([
            InlineKeyboardButton(
                text=game.name,
                callback_data=f"game_select:{game.id}"
            )
        ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        "Выберите игру, в которой вы хотите заработать награду:",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("game_select:"))
async def cb_game_select(callback: CallbackQuery, container: Container, state: FSMContext):
    """Показывает карточку выбранной игры и кнопку 'Начать'"""
    await callback.answer()
    
    # Извлекаем game_id из callback_data
    game_id_str = callback.data.split(":")[1]
    
    try:
        import uuid
        game_id = uuid.UUID(game_id_str)
    except ValueError:
        await callback.message.edit_text("Ошибка: некорректный идентификатор игры.")
        return
    
    # Получаем информацию об игре
    game = await container.game_service.game_repo.get_by_id(game_id)
    
    if not game or not game.is_active:
        await callback.message.edit_text("Эта игра больше недоступна. Выберите другую.")
        return
    
    # Сохраняем game_id в состоянии FSM
    await state.update_data(selected_game_id=game_id_str)
    
    # Формируем карточку игры
    # Примечание: реальное фото игры будет добавлено позже через загрузку в Telegram
    game_card_text = (
        f"Игра: {game.name}\n\n"
        f"Ссылка на игру: [будет добавлена позже]\n\n"
        f"Нажмите 'Начать', чтобы открыть сессию и начать зарабатывать."
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="session_start")],
        [InlineKeyboardButton(text="Назад к списку игр", callback_data="application_start")]
    ])
    
    await callback.message.edit_text(game_card_text, reply_markup=kb)