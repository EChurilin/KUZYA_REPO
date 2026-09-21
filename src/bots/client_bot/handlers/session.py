from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.context import FSMContext
from src.infrastructure.container import Container
from src.core.exceptions import (
    SessionAlreadyActiveError,
    ScreenshotIntervalTooShortError,
    ScreenshotLimitReachedError,
)
import uuid


router = Router()


@router.callback_query(F.data == "session_start")
async def cb_session_start(callback: CallbackQuery, container: Container, state: FSMContext):
    """Запускает новую сессию для выбранной игры"""
    await callback.answer()

    data = await state.get_data()
    game_id_str = data.get("selected_game_id")

    if not game_id_str:
        await callback.message.answer("Сначала выберите игру.")
        return

    try:
        game_id = uuid.UUID(game_id_str)
    except ValueError:
        await callback.message.answer("Ошибка: некорректный идентификатор игры.")
        return

    user_id = callback.from_user.id

    # [fix] Гейт: новый пользователь должен сначала посмотреть инструкцию
    user = await container.user_service.get_user(user_id)
    if user is None or not user.instruction_passed:
        await callback.message.answer(
            "Сначала необходимо просмотреть инструкцию.\n\n"
            "Используйте кнопку «Посмотреть инструкцию» в главном меню."
        )
        return

    try:
        # Создаём сессию
        session = await container.session_service.start_session(user_id, game_id)

        # Сохраняем session_id в состоянии FSM
        await state.update_data(session_id=str(session.id))

        await callback.message.answer(
            "Сессия открыта! Теперь вы можете отправлять скриншоты.\n\n"
            "Важно: между скриншотами должно проходить не менее 10 минут.\n"
            "После каждого скриншота вам будет предложено продолжить или забрать награду."
        )

    except SessionAlreadyActiveError:
        await callback.message.answer(
            "У вас уже есть активная сессия. Завершите её или дождитесь истечения."
        )


@router.message(F.photo)
async def handle_screenshot(message: Message, container: Container, state: FSMContext, bot):
    """Обрабатывает полученный скриншот"""
    data = await state.get_data()
    session_id_str = data.get("session_id")

    if not session_id_str:
        await message.answer("Сначала начните сессию через меню.")
        return

    try:
        session_id = uuid.UUID(session_id_str)
    except ValueError:
        await message.answer("Ошибка: некорректный идентификатор сессии.")
        return

    # Получаем фото (берём самое большое разрешение)
    photo = message.photo[-1]
    file_id = photo.file_id

    # Скачиваем файл
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)
    file_data = file_bytes.read()

    user_id = message.from_user.id

    try:
        # Добавляем скриншот в сессию
        screenshot, count = await container.session_service.add_screenshot(
            session_id=session_id,
            file_bytes=file_data,
            extension="jpg",
            client_file_id=file_id,
        )

        # Показываем кнопки "Продолжить" / "Забрать награду"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Продолжить", callback_data="session_continue"),
                InlineKeyboardButton(text="Забрать награду", callback_data="session_finish")
            ]
        ])

        await message.answer(
            f"Скриншот принят! Это скриншот #{count} в текущей сессии.\n\n"
            "Что вы хотите сделать?",
            reply_markup=kb
        )

    except ScreenshotIntervalTooShortError as e:
        await message.answer(str(e))

    except ScreenshotLimitReachedError as e:
        await message.answer(
            f"{e}\n\nНажмите 'Забрать награду', чтобы завершить сессию.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Забрать награду", callback_data="session_finish")]
            ])
        )


@router.callback_query(F.data == "session_continue")
async def cb_session_continue(callback: CallbackQuery, state: FSMContext):
    """Пользователь хочет продолжить сессию"""
    await callback.answer()
    await callback.message.answer(
        "Продолжаем! Отправьте следующий скриншот через 10 минут или позже."
    )


@router.callback_query(F.data == "session_finish")
async def cb_session_finish(callback: CallbackQuery, container: Container, state: FSMContext):
    """Завершает сессию и создаёт заявку"""
    await callback.answer()

    data = await state.get_data()
    session_id_str = data.get("session_id")

    if not session_id_str:
        await callback.message.answer("У вас нет активной сессии.")
        return

    try:
        session_id = uuid.UUID(session_id_str)
    except ValueError:
        await callback.message.answer("Ошибка: некорректный идентификатор сессии.")
        return

    user_id = callback.from_user.id

    try:
        # Создаём заявку из сессии
        application = await container.application_service.create_from_session(
            session_id=session_id,
            user_id=user_id,
            campaign_id=None  # Кампании пока не используются
        )

        # Очищаем состояние FSM
        await state.clear()

        await callback.message.answer(
            "Сессия завершена! Ваша заявка отправлена на проверку администратору.\n\n"
            "Вы получите уведомление о результате проверки."
        )

    except Exception as e:
        await callback.message.answer(f"Ошибка при создании заявки: {str(e)}")
