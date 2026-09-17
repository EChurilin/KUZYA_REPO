import uuid
from datetime import datetime, timezone
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from src.infrastructure.container import Container
from src.config.settings import settings
from src.core.entities import Game
from src.bots.staff_bot.states import GameManagement, GameReplaceMode
from src.bots.staff_bot.keyboards.games_kb import (
    get_games_list_kb,
    get_game_added_actions_kb,
    get_cancel_kb,
    get_games_confirm_replace_kb,
)
from src.bots.staff_bot.keyboards.menu_kb import get_main_menu_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.staff_bot.admin_ids


@router.message(F.text == "Список игр")
async def show_games_list(message: Message, container: Container, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return
    await state.clear()
    games = await container.game_service.get_active_games()
    
    if not games:
        await message.answer(
            "Список активных игр пуст.\n\nДобавьте игры для отображения пользователям.",
            reply_markup=get_games_list_kb([])
        )
        return
    
    text = f"Активные игры ({len(games)}):\n\n"
    for i, game in enumerate(games, 1):
        text += f"{i}. {game.name}\n"
    
    await message.answer(text, reply_markup=get_games_list_kb(games))


@router.callback_query(F.data == "games_add")
async def start_add_game(callback: CallbackQuery, container: Container, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()
    
    # Проверяем, не в режиме ли замены мы уже
    current_state = await state.get_state()
    if current_state == GameReplaceMode.active:
        await callback.message.answer(
            "Вы в режиме обновления списка. Добавьте первую игру.\n\nВведите название игры:",
            reply_markup=get_cancel_kb()
        )
        await state.set_state(GameManagement.waiting_for_name)
    else:
        await callback.message.answer(
            "Добавление новой игры.\n\nВведите название игры:",
            reply_markup=get_cancel_kb()
        )
        await state.set_state(GameManagement.waiting_for_name)


@router.callback_query(F.data == "games_replace")
async def start_replace_games(callback: CallbackQuery, container: Container, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()
    
    await callback.message.answer(
        "Режим обновления списка игр.\n\n"
        "Все текущие активные игры будут деактивированы после подтверждения.\n\n"
        "Введите название первой игры:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(GameReplaceMode.active)
    await state.update_data(draft_games=[], current_game={})
    await state.set_state(GameManagement.waiting_for_name)


@router.message(StateFilter(GameManagement.waiting_for_name), F.text)
async def process_game_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return
    
    name = message.text.strip()
    if not name:
        await message.answer("Название не может быть пустым. Введите название игры:")
        return
    
    await state.update_data(name=name)
    await message.answer(
        f"Название: {name}\n\nВведите ссылку на игру:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(GameManagement.waiting_for_link)


@router.message(StateFilter(GameManagement.waiting_for_link), F.text)
async def process_game_link(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return
    
    link = message.text.strip()
    if not link:
        await message.answer("Ссылка не может быть пустой. Введите ссылку на игру:")
        return
    
    await state.update_data(link=link)
    await message.answer(
        f"Ссылка: {link}\n\nОтправьте фотографию игры:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(GameManagement.waiting_for_photo)


@router.message(StateFilter(GameManagement.waiting_for_photo), F.photo)
async def process_game_photo(message: Message, state: FSMContext, container: Container):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return
    
    # Берём фото максимального размера
    photo = message.photo[-1]
    
    # Скачиваем и сохраняем локально
    file = await container.bot.get_file(photo.file_id)
    
    # Формируем путь для сохранения
    game_dir = Path(settings.storage.base_path) / "games"
    game_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{uuid.uuid4()}.jpg"
    file_path = game_dir / filename
    
    await container.bot.download_file(file.file_path, file_path)
    
    data = await state.get_data()
    name = data["name"]
    link = data["link"]
    photo_path = str(file_path)
    
    # Сохраняем во временные данные
    current_game = {
        "name": name,
        "link": link,
        "photo_path": photo_path,
    }
    
    await state.update_data(current_game=current_game)
    
    await message.answer(
        f"Игра готова к добавлению:\n\n"
        f"Название: {name}\n"
        f"Ссылка: {link}\n"
        f"Фото: сохранено",
        reply_markup=get_game_added_actions_kb()
    )
    await state.set_state(GameManagement.confirming_save)


@router.callback_query(F.data == "games_finish")
async def finish_adding_games(callback: CallbackQuery, state: FSMContext, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()
    
    data = await state.get_data()
    current_state = await state.get_state()
    
    # Если мы были в режиме замены, применяем изменения
    if "draft_games" in data and data.get("draft_games"):
        draft_games = data["draft_games"]
        
        # Деактивируем старые игры
        await container.game_service._game_repo.deactivate_all()
        
        # Создаём новые
        for game_data in draft_games:
            game = Game(
                id=uuid.uuid4(),
                name=game_data["name"],
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                link=game_data["link"],
                photo_path=game_data["photo_path"],
                deactivated_at=None,
            )
            await container.game_service.add_game(game)
        
        await callback.message.edit_text(
            f"Список игр обновлён. Добавлено {len(draft_games)} игр.\n\n"
            f"Старые игры деактивированы и будут удалены через 36 часов.",
            reply_markup=get_main_menu_kb()
        )
    else:
        await callback.message.edit_text(
            "Добавление игр завершено.",
            reply_markup=get_main_menu_kb()
        )
    
    await state.clear()


@router.callback_query(F.data == "games_add_another")
async def add_another_game(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()
    
    data = await state.get_data()
    
    # Сохраняем текущую игру в черновик
    if "current_game" in data:
        draft_games = data.get("draft_games", [])
        draft_games.append(data["current_game"])
        await state.update_data(draft_games=draft_games)
    
    await callback.message.edit_text(
        "Введите название следующей игры:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(GameManagement.waiting_for_name)


@router.callback_query(F.data == "games_cancel")
async def cancel_game_operation(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer("Операция отменена")
    
    # Удаляем временные файлы, если они есть
    data = await state.get_data()
    if "current_game" in data and "photo_path" in data["current_game"]:
        photo_path = Path(data["current_game"]["photo_path"])
        if photo_path.exists():
            photo_path.unlink()
    
    await state.clear()
    await callback.message.edit_text(
        "Операция отменена.",
        reply_markup=get_main_menu_kb()
    )


@router.callback_query(F.data == "games_confirm_replace")
async def confirm_replace_games(callback: CallbackQuery, state: FSMContext, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()
    
    data = await state.get_data()
    draft_games = data.get("draft_games", [])
    
    if not draft_games:
        await callback.message.edit_text(
            "Нет игр для добавления. Операция отменена.",
            reply_markup=get_main_menu_kb()
        )
        await state.clear()
        return
    
    # Деактивируем старые игры
    await container.game_service._game_repo.deactivate_all()
    
    # Создаём новые
    for game_data in draft_games:
        game = Game(
            id=uuid.uuid4(),
            name=game_data["name"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            link=game_data["link"],
            photo_path=game_data["photo_path"],
            deactivated_at=None,
        )
        await container.game_service.add_game(game)
    
    await callback.message.edit_text(
        f"Список игр полностью обновлён. Добавлено {len(draft_games)} игр.\n\n"
        f"Старые игры деактивированы и будут удалены через 36 часов.",
        reply_markup=get_main_menu_kb()
    )
    await state.clear()


@router.callback_query(F.data.startswith("game_info:"))
async def show_game_info(callback: CallbackQuery, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()
    
    game_id_str = callback.data.split(":")[1]
    try:
        game_id = uuid.UUID(game_id_str)
    except ValueError:
        await callback.message.answer("Ошибка: некорректный ID игры.")
        return
    
    game = await container.game_service.get_game_by_id(game_id)
    if not game:
        await callback.message.answer("Игра не найдена.")
        return
    
    text = (
        f"Информация об игре:\n\n"
        f"Название: {game.name}\n"
        f"Ссылка: {game.link or 'не указана'}\n"
        f"Активна: {'да' if game.is_active else 'нет'}\n"
        f"Создана: {game.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    
    if game.photo_path and Path(game.photo_path).exists():
        photo = FSInputFile(game.photo_path)
        await callback.message.answer_photo(photo, caption=text)
    else:
        await callback.message.answer(text)