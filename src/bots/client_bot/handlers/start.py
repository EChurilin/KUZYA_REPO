from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command
from src.infrastructure.container import Container
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(CommandStart())
@router.message(Command("start"))
async def cmd_start(message: Message, container: Container, state: FSMContext):
    """Обработчик команды /start"""
    # Очищаем состояние на случай, если пользователь начал заново
    await state.clear()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Прочитать инструкцию", callback_data="instruction_start")]
    ])
    
    welcome_text = (
        "Привет! Добро пожаловать в Kizya Bot.\n\n"
        "Здесь ты можешь получать награды за выполнение заданий в играх.\n"
        "Прежде чем начать, обязательно ознакомься с инструкцией."
    )
    
    await message.answer(welcome_text, reply_markup=kb)