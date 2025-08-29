from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import texts

def kb(users: list[tuple[int, str | None]]):
    builder = InlineKeyboardBuilder()

    for session_id, tgid, username in users:
        text = f"#{tgid} @{username}" if username else f"#{tgid}"
        builder.add(
            InlineKeyboardButton(
                text=text,
                callback_data=f"session:{session_id}"
            )
        )

    builder.add(InlineKeyboardButton(text=texts.BACK_KB_TEXT, callback_data="home"))
    builder.adjust(1)
    return builder.as_markup()
