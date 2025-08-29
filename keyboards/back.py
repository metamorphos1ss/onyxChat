from aiogram.utils.keyboard import InlineKeyboardBuilder
import texts

def keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text=texts.BACK_KB_TEXT, callback_data="home")
    return builder.as_markup()