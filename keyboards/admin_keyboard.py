from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def keyboard():
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="Сообщения", callback_data="messages"),
        InlineKeyboardButton(text="onyxStats", callback_data="onyxStats")
    )
    builder.adjust(1)
    return builder.as_markup()