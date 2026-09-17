from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from src.infrastructure.container import Container
from src.config.settings import settings
from src.bots.staff_bot.keyboards.report_kb import get_report_period_kb
from src.bots.staff_bot.keyboards.menu_kb import get_main_menu_kb

router = Router()

PERIOD_LABELS = {
    "today": "Сегодня",
    "30_days": "30 дней",
    "all_time": "Всё время",
}


def is_admin(user_id: int) -> bool:
    return user_id in settings.staff_bot.admin_ids


@router.message(F.text == "Отчет")
async def show_report_menu(message: Message, container: Container, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return
    await state.clear()
    await message.answer(
        "Выберите период для отчёта:",
        reply_markup=get_report_period_kb()
    )


@router.callback_query(F.data.startswith("report:"))
async def show_report(callback: CallbackQuery, container: Container):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer("Формирую отчёт...")

    period = callback.data.split(":")[1]
    period_label = PERIOD_LABELS.get(period, period)

    try:
        report = await container.report_service.get_full_report(period)
    except Exception as e:
        await callback.message.answer(f"Ошибка при формировании отчёта: {str(e)}")
        return

    # Сводка
    text = f"Отчёт за период: {period_label}\n\n"
    text += f"Уникальных пользователей: {report['unique_users']}\n"
    text += f"Прислано скриншотов: {report['sent_screenshots']}\n"
    text += f"Награждено скриншотов: {report['approved_screenshots']}\n\n"

    # Топ-30 пользователей
    top_users = report.get("top_users", [])
    if top_users:
        text += f"Топ пользователей по скриншотам (всего {len(top_users)}):\n"
        for i, user in enumerate(top_users[:30], 1):
            username = user.get("username") or user.get("first_name") or f"ID {user['user_id']}"
            sent = user.get("sent_count", 0)
            approved = user.get("approved_count", 0)
            text += f"  {i}. {username}: прислал {sent}, награждено {approved}\n"
    else:
        text += "Нет данных по пользователям.\n"

    text += "\n"

    # Разбивка по играм
    by_game = report.get("by_game", [])
    if by_game:
        text += "Статистика по играм:\n"
        for game in by_game:
            game_name = game.get("game_name", "Неизвестно")
            user_count = game.get("user_count", 0)
            sent = game.get("sent_count", 0)
            approved = game.get("approved_count", 0)
            text += f"  {game_name}: {user_count} польз., {sent} скрин., {approved} нагр.\n"
    else:
        text += "Нет данных по играм.\n"

    # Разбиваем на части, если текст длинный
    if len(text) > 3800:
        parts = []
        while text:
            parts.append(text[:3800])
            text = text[3800:]
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                await callback.message.answer(part, reply_markup=get_report_period_kb())
            else:
                await callback.message.answer(part)
    else:
        await callback.message.answer(text, reply_markup=get_report_period_kb())