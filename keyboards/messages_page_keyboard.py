from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import texts

def keyboard():
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text=texts.WAITING_KB_TEXT, callback_data="msg:toServe"),
        InlineKeyboardButton(text=texts.MY_CHATS_KB_TEXT, callback_data="msg:processing_mine"),
        InlineKeyboardButton(text=texts.PROCESSING_CHATS_KB_TEXT, callback_data="msg:processing"),
        InlineKeyboardButton(text=texts.DONE_CHATS_KB_TEXT, callback_data="msg:done"),
        InlineKeyboardButton(text=texts.BACK_KB_TEXT, callback_data="home")
    )
    builder.adjust(1)
    return builder.as_markup()