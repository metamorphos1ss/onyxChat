from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards import back, att_kb
from keyboards.messages_keyboard import session_view
from utils import render_messages

from handlers.messages import start

from states import AdminChat

import texts
from sql import reqs




async def open_session_view(callback_query: CallbackQuery, is_admin: bool, pool, state: FSMContext):
    if not is_admin:
        return

    session_id = callback_query.data.removeprefix("session:")
    info = await reqs.get_session_view(pool, session_id)
    if not info:
        return await callback_query.message.edit_text(texts.SESSION_NOT_FOUND, reply_markup=back.keyboard())

    msgs = await reqs.fetch_session_messages(pool, info["tgid"], session_id)
    text, attachments = render_messages.render_session_text(info["username"], info["assigned_agent"], msgs)

    await callback_query.message.edit_text(
        text,
        reply_markup=session_view.session_view_kb(session_id, taken=bool(info["assigned_agent"]), opened=bool(await state.get_state()), attachments=attachments),
        disable_web_page_preview=True
    )

    await state.update_data(panel_msg={
        "chat_id": callback_query.message.chat.id,
        "message_id": callback_query.message.message_id,
        "session_id": session_id,
    })
    await callback_query.answer()

async def take_session(callback_query: CallbackQuery, is_admin: bool, pool, state: FSMContext):
    if not is_admin:
        return
    session_id = callback_query.data.removeprefix("take:")

    operator_id = callback_query.from_user.id

    ok = await reqs.assign_session(pool, session_id, callback_query.from_user.id)
    if not ok:
        return await callback_query.answer(texts.TAKEN_SESSION, show_alert=True)
    
    await state.set_state(AdminChat.active)
    await state.update_data(session_id=session_id)

    info = await reqs.get_session_view(pool, session_id)
    if not info:
        await state.clear()
        return await callback_query.answer(texts.SESSION_NOT_FOUND, show_alert=True)
    msgs = await reqs.fetch_session_messages(pool, info["tgid"], session_id)
    text, attachments = render_messages.render_session_text(info["username"], info["assigned_agent"], msgs)

    await callback_query.message.edit_text(
        text,
        reply_markup=session_view.session_view_kb(session_id, taken=bool(info["assigned_agent"]), opened=bool(await state.get_state()), attachments=attachments),
        disable_web_page_preview=True
    )

    await state.update_data(panel_msg={
        "chat_id": callback_query.message.chat.id,
        "message_id": callback_query.message.message_id,
        "session_id": session_id,
    })
    await callback_query.answer(texts.CHAT_ASSIGNED_TO_YOU)

async def open_chat(callback_query: CallbackQuery, is_admin: bool, pool, state: FSMContext):
    if not is_admin:
        return
    session_id = callback_query.data.removeprefix("open:")
    await state.set_state(AdminChat.active)
    await state.update_data(session_id=session_id)

    info = await reqs.get_session_view(pool, session_id)
    if not info:
        await state.clear()
        return await callback_query.answer(texts.SESSION_NOT_FOUND, show_alert=True)
    msgs = await reqs.fetch_session_messages(pool, info["tgid"], session_id)
    text, attachments = render_messages.render_session_text(info["username"], info["assigned_agent"], msgs)

    await callback_query.message.edit_text(
        text,
        reply_markup=session_view.session_view_kb(session_id, taken=bool(info["assigned_agent"]), opened=bool(await state.get_state()), attachments=attachments),
        disable_web_page_preview=True
    )

    await state.update_data(panel_msg={
    "chat_id": callback_query.message.chat.id,
    "message_id": callback_query.message.message_id,
    "session_id": session_id,
    })
    await callback_query.answer()
    
async def close_session(callback_query: CallbackQuery, is_admin: bool, pool, state: FSMContext):
    if not is_admin:
        return
    session_id = callback_query.data.removeprefix("close:")
    ok = await reqs.close_session(pool, session_id=session_id, assigned_agent=callback_query.from_user.id)
    if not ok:
        return await callback_query.answer(texts.FAILED_TO_CLOSE_SESSION, show_alert=True)
    await state.clear()
    await start.welcome(callback_query.message, state, is_admin, pool, from_callback=True)
    await callback_query.answer(texts.SESSION_CLOSED_SUCCESSFUL)

async def open_attachment(callback_query: CallbackQuery, pool):
    _, sid_str, mid_str = callback_query.data.split(":")
    mid = int(mid_str)

    file_id, sess_id_of_msg = await reqs.get_message_file(pool, mid)
    if not file_id or int(sid_str) != int(sess_id_of_msg or 0):
        return await callback_query.answer(texts.ATTACHMENT_NOT_FOUND, show_alert=True)
    
    try:
        await callback_query.message.answer_photo(file_id, reply_markup=att_kb.attclose(mid))
    except:
        await callback_query.message.answer_document(file_id, reply_markup=att_kb.attclose(mid))
    await callback_query.answer()

async def close_attachment(callback_query: CallbackQuery, is_admin: bool):
    if not is_admin:
        return
    try:
        await callback_query.message.delete()
    except:
        pass
    await callback_query.answer()