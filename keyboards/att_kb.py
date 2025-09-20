import texts

from aiogram.utils.keyboard import InlineKeyboardBuilder

def attclose(mid) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text=texts.CLOSE_ATTACHMENT, callback_data=f"attclose:{mid}")
    return builder.as_markup()