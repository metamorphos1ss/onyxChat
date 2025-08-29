from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from states import AdminChat
from utils import render_messages
from sql import reqs
from keyboards import back
from keyboards.messages_keyboard import session_view

import logging

async def refresh_session_view(bot, storage, pool, operator_id: int, state: FSMContext | None = None):
    if state is None:
        key = StorageKey(bot_id=bot.id, chat_id=operator_id, user_id=operator_id)
        fsm = FSMContext(storage=storage, key=key)
    else:
        fsm = state
    current = await fsm.get_state()
    
    if current != "AdminChat:active":
        return

    data = await fsm.get_data()
    panel = data.get("panel_msg")
    session_id = int(data.get("session_id") or 0)
    if not panel or not session_id:
        return

    chat_id = panel["chat_id"]
    message_id = panel["message_id"]

    info = await reqs.get_session_view(pool, session_id)
    if not info:
        return

    msgs = await reqs.fetch_session_messages(pool, info["tgid"], session_id)
    text, attachments = render_messages.render_session_text(info["username"], info["assigned_agent"], msgs)

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=session_view.session_view_kb(session_id, taken=bool(info["assigned_agent"]), opened=bool(current), attachments=attachments),
        disable_web_page_preview=True
    )
