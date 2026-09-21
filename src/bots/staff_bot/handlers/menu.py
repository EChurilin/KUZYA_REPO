from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from src.infrastructure.container import Container
from src.config.settings import settings
from src.bots.staff_bot.keyboards.menu_kb import get_main_menu_kb, remove_menu_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.staff_bot.admin_ids


@router.message(CommandStart())
async def cmd_start(message: Message, container: Container, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return
    await state.clear()
    await message.answer(
        "Привет! Я бот для управления Kuzya Bot.\n\n"
        "Используй меню ниже для навигации.",
        reply_markup=get_main_menu_kb()
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, container: Container, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return
    await state.clear()
    await message.answer("Главное меню:", reply_markup=get_main_menu_kb())


@router.message(F.text == "Скрыть меню")
async def hide_menu(message: Message, container: Container, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("Меню скрыто. Введите /menu, чтобы вернуть.", reply_markup=remove_menu_kb())


@router.message(F.text == "Техническая поддержка")
async def menu_support(message: Message, container: Container, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return
    await state.clear()
    await message.answer("Раздел в разработке.", reply_markup=get_main_menu_kb())
