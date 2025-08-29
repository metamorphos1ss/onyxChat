from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import texts

def session_view_kb(session_id: int, taken: bool, opened: bool | None, attachments: list[tuple[int, int]] | None = None):
    builder = InlineKeyboardBuilder()
    

    if attachments:
        row: list[InlineKeyboardButton] = []
        for i, (n, mid) in enumerate(attachments, start=1):
            row.append(InlineKeyboardButton(text=f"Вложение {n}", callback_data=f"att:{session_id}:{mid}"))
            if i%3 == 0:
                builder.row(*row)
                row = []
        if row:
            builder.row(*row)

    action_btns: list[InlineKeyboardButton] = []
    if not taken:
        action_btns.append(
            InlineKeyboardButton(text=texts.TAKE_CLIENT, callback_data=f"take:{session_id}")
        )
    if not opened:
        action_btns.append(
            InlineKeyboardButton(text=texts.AGENT_OPEN_CHAT, callback_data=f"open:{session_id}")
        )
    else:
        if taken:
            action_btns.append(
                InlineKeyboardButton(text=texts.CLOSE_SESSION, callback_data=f"close:{session_id}")
            )
    if action_btns:
        builder.row(*action_btns)

    builder.row(InlineKeyboardButton(text=texts.BACK_KB_TEXT, callback_data="home"))
    return builder.as_markup()