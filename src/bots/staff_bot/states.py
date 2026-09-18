from aiogram.fsm.state import State, StatesGroup


class GameManagement(StatesGroup):
    """Состояния для сценария добавления новой игры."""
    waiting_for_name = State()
    waiting_for_link = State()
    waiting_for_photo = State()
    confirming_save = State()


class GameReplaceMode(StatesGroup):
    """Состояния для сценария полной замены списка игр."""
    active = State()


class InstructionManagement(StatesGroup):
    """Состояния для сценария редактирования инструкции."""
    waiting_for_count = State()
    waiting_for_block = State()
    previewing = State()


class SettingsManagement(StatesGroup):
    """Состояния для сценария изменения цены скриншота."""
    waiting_for_price = State()


class TopupManagement(StatesGroup):
    """Состояния для сценария пополнения баланса бота."""
    waiting_for_amount = State()