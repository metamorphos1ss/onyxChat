from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import re
from config import ADMINS_ID

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from keyboards import back

from keyboards.messages_keyboard import session_view

import logging
from sql import reqs
from utils import render_messages

import texts

async def admin_reply(message: Message, state: FSMContext, pool):
    data = await state.get_data()
    session_id = data.get("session_id")
    if not session_id:
        await state.clear()
        return await message.answer(texts.SESSION_NOT_FOUND)
    
    if message.text and message.text.strip() == "/start":
        try:
            await message.delete()
        finally:
            return
    
    view = await reqs.get_session_view(pool, session_id)
    if not view or not view["tgid"]:
        await message.answer(texts.CLIENT_NOT_FOUND)
        return
    
    user_id = view['tgid']
    sent_text = message.text or message.caption
    file_id = None

    try:
        await message.send_copy(chat_id=user_id)
    except Exception as e:
        return await message.answer(texts.FAILED_TO_SEND_MESSAGE.format(exception=e))
    
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.voice:
        file_id = message.voice.file_id

    await reqs.log_message(
        pool,
        tgid=user_id,
        current_session_id=session_id,
        direction="fromAgent",
        text=sent_text,
        file_id=file_id
    )

    panel = data.get("panel_msg")
    if panel:
        info = await reqs.get_session_view(pool, int(session_id))
        msgs = await reqs.fetch_session_messages(pool, user_id, int(session_id))
        text, attachments = render_messages.render_session_text(info["username"], info["assigned_agent"], msgs)
        try:
            await message.bot.edit_message_text(
                chat_id=panel["chat_id"],
                message_id=panel["message_id"],
                text=text,
                reply_markup=session_view.session_view_kb(session_id, taken=bool(info["assigned_agent"]), opened=bool(await state.get_state()), attachments=attachments),
                disable_web_page_preview=True
            )
        except Exception:
            pass
    await message.delete()

async def admin_notify(message: Message, pool):
    bot = message.bot
    tgid = message.from_user.id
    username = message.from_user.username
    
    session_id = await reqs.get_session_id(pool, tgid)
    if not session_id:
        logging.warning("admin_notify: нет открытой сессии для tgid=%s", tgid)
        return
    uline = f"@{username}" if username else "(без username)"
    header = "Новая сессия"
    body = f"Клиент: #{tgid} {uline}"
    text = f"{header}\n{body}"

    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Открыть", callback_data=f"session:{session_id}"),
        InlineKeyboardButton(text="Взять чат", callback_data=f"take:{session_id}")
    )

    admins: set[int] = {int(x) for x in re.findall(r"\d+", str(ADMINS_ID))}

    for admin_id in admins:
        try:
            await bot.send_message(admin_id, text, reply_markup=kb.as_markup())
            pass
        except Exception as e:
            logging.exception("admin_notify: не удалось отправить админу %s: %s", admin_id, e)