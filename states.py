from aiogram.fsm.state import State, StatesGroup

class AdminChat(StatesGroup):
    active = State()