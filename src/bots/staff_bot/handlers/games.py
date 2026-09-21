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
from src.bots.staff_bot.keyboards.menu_kb import get_back_to_menu_inline_kb

router = Router()

# Идентификаторы режимов работы со списком игр.
MODE_ADD = "add"
MODE_REPLACE = "replace"


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
    """Запускает режим одиночного добавления игры."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()

    await state.update_data(
        mode=MODE_ADD,
        draft_games=[],
        current_game=None,
        last_added_game_id=None,
    )
    await callback.message.answer(
        "Добавление новой игры.\n\nВведите название игры:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(GameManagement.waiting_for_name)


@router.callback_query(F.data == "games_replace")
async def start_replace_games(callback: CallbackQuery, container: Container, state: FSMContext):
    """Запускает режим полной замены списка игр."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()

    await state.update_data(
        mode=MODE_REPLACE,
        draft_games=[],
        current_game=None,
        last_added_game_id=None,
    )
    await callback.message.answer(
        "Режим обновления списка игр.\n\n"
        "Все текущие активные игры будут деактивированы после подтверждения.\n\n"
        "Введите название первой игры:",
        reply_markup=get_cancel_kb()
    )
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
    # [fix] Сразу запрашиваем фото, шаг со ссылкой убран
    await message.answer(
        f"Название: {name}\n\nОтправьте фотографию игры:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(GameManagement.waiting_for_photo)


@router.message(StateFilter(GameManagement.waiting_for_photo), F.photo)
async def process_game_photo(message: Message, state: FSMContext, container: Container):
    """Сохраняет фото, формирует current_game и переходит к подтверждению."""
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return

    photo_path = await container.media_service.save_game_photo(message)

    data = await state.get_data()
    name = data["name"]

    current_game = {
        "name": name,
        "photo_path": photo_path,
    }
    await state.update_data(current_game=current_game)

    await message.answer(
        f"Игра готова к добавлению:\n\n"
        f"Название: {name}\n"
        f"Фото: сохранено",
        reply_markup=get_game_added_actions_kb()
    )
    await state.set_state(GameManagement.confirming_save)


async def _save_current_game_as_entity(
    container: Container, game_data: dict
) -> uuid.UUID:
    """Создаёт Game из словаря и сохраняет в БД. Возвращает id созданной игры."""
    game = Game(
        id=uuid.uuid4(),
        name=game_data["name"],
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        link=None,  # [fix] Ссылка не сохраняется
        photo_path=game_data["photo_path"],
        deactivated_at=None,
    )
    await container.game_service.add_game(game)
    return game.id


@router.callback_query(F.data == "games_finish")
async def finish_adding_games(callback: CallbackQuery, state: FSMContext, container: Container):
    """Завершает режим добавления/замены игр."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()

    data = await state.get_data()
    mode = data.get("mode", MODE_ADD)
    current_game = data.get("current_game")
    draft_games = data.get("draft_games", [])

    try:
        if mode == MODE_ADD:
            if current_game:
                await _save_current_game_as_entity(container, current_game)
                added_count = 1
            else:
                added_count = 0

            await callback.message.edit_text(
                f"Добавление игр завершено. Добавлено: {added_count}.",
                reply_markup=get_back_to_menu_inline_kb()
            )

        elif mode == MODE_REPLACE:
            if current_game:
                draft_games.append(current_game)

            if not draft_games:
                await callback.message.edit_text(
                    "Нет игр для добавления. Операция отменена.",
                    reply_markup=get_back_to_menu_inline_kb()
                )
                await state.clear()
                return

            new_games = [
                Game(
                    id=uuid.uuid4(),
                    name=g["name"],
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    link=None,  # [fix] Ссылка не сохраняется
                    photo_path=g["photo_path"],
                    deactivated_at=None,
                )
                for g in draft_games
            ]
            await container.game_service.replace_game_list(new_games)

            await callback.message.edit_text(
                f"Список игр обновлён. Добавлено {len(new_games)} игр.\n\n"
                f"Старые игры деактивированы и будут удалены через 36 часов.",
                reply_markup=get_back_to_menu_inline_kb()
            )

    except Exception as e:
        await callback.message.edit_text(
            f"Ошибка при сохранении: {e}",
            reply_markup=get_back_to_menu_inline_kb()
        )

    await state.clear()


@router.callback_query(F.data == "games_add_another")
async def add_another_game(callback: CallbackQuery, state: FSMContext, container: Container):
    """Переносит текущую игру в draft и начинает новый цикл ввода."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()

    data = await state.get_data()
    mode = data.get("mode", MODE_ADD)
    current_game = data.get("current_game")
    draft_games = data.get("draft_games", [])

    if current_game:
        if mode == MODE_REPLACE:
            draft_games.append(current_game)
            await state.update_data(draft_games=draft_games, current_game=None)
        else:
            try:
                added_id = await _save_current_game_as_entity(container, current_game)
                await state.update_data(
                    current_game=None,
                    last_added_game_id=str(added_id),
                )
            except Exception as e:
                await callback.message.answer(f"Не удалось сохранить игру: {e}")
                return

    await callback.message.answer(
        "Введите название следующей игры:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(GameManagement.waiting_for_name)


@router.callback_query(F.data == "games_cancel")
async def cancel_game_operation(callback: CallbackQuery, state: FSMContext, container: Container):
    """Отмена операции: удаляет временные файлы; в режиме add — последнюю добавленную игру."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer("Операция отменена")

    data = await state.get_data()
    mode = data.get("mode", MODE_ADD)

    paths_to_remove = []
    if data.get("current_game") and data["current_game"].get("photo_path"):
        paths_to_remove.append(data["current_game"]["photo_path"])
    for g in data.get("draft_games", []):
        if g.get("photo_path"):
            paths_to_remove.append(g["photo_path"])

    for photo_path in paths_to_remove:
        try:
            p = Path(photo_path)
            if p.exists():
                p.unlink()
        except Exception:
            pass

    if mode == MODE_ADD and data.get("last_added_game_id"):
        try:
            await container.game_service.delete_game(uuid.UUID(data["last_added_game_id"]))
        except Exception:
            pass

    await state.clear()
    await callback.message.edit_text(
        "Операция отменена.",
        reply_markup=get_back_to_menu_inline_kb()
    )


@router.callback_query(F.data == "games_confirm_replace")
async def confirm_replace_games(callback: CallbackQuery, state: FSMContext, container: Container):
    """Подтверждение полной замены (альтернативный путь через confirm-клавиатуру)."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()

    data = await state.get_data()
    draft_games = data.get("draft_games", [])

    if not draft_games:
        await callback.message.edit_text(
            "Нет игр для добавления. Операция отменена.",
            reply_markup=get_back_to_menu_inline_kb()
        )
        await state.clear()
        return

    new_games = [
        Game(
            id=uuid.uuid4(),
            name=g["name"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            link=None,  # [fix] Ссылка не сохраняется
            photo_path=g["photo_path"],
            deactivated_at=None,
        )
        for g in draft_games
    ]

    try:
        await container.game_service.replace_game_list(new_games)
        await callback.message.edit_text(
            f"Список игр полностью обновлён. Добавлено {len(new_games)} игр.\n\n"
            f"Старые игры деактивированы и будут удалены через 36 часов.",
            reply_markup=get_back_to_menu_inline_kb()
        )
    except Exception as e:
        await callback.message.edit_text(
            f"Ошибка при обновлении: {e}",
            reply_markup=get_back_to_menu_inline_kb()
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

    # [fix] Убран показ ссылки
    text = (
        f"Информация об игре:\n\n"
        f"Название: {game.name}\n"
        f"Активна: {'да' if game.is_active else 'нет'}\n"
        f"Создана: {game.created_at.strftime('%d.%m.%Y %H:%M')}"
    )

    if game.photo_path and Path(game.photo_path).exists():
        photo = FSInputFile(game.photo_path)
        await callback.message.answer_photo(photo, caption=text)
    else:
        await callback.message.answer(text)
