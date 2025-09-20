from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import texts
from handlers.messages import start
from keyboards import att_kb, back
from keyboards.messages_keyboard import session_view
from sql import reqs
from states import AdminChat
from utils import render_messages
from utils.logger import get_logger

logger = get_logger(__name__)




async def open_session_view(callback_query: CallbackQuery, is_admin: bool, pool, state: FSMContext):
    """Открывает просмотр сессии"""
    agent_id = callback_query.from_user.id
    logger.info(f"Открытие просмотра сессии агентом {agent_id}")
    
    if not is_admin:
        logger.warning(f"Не-админ {agent_id} пытается открыть просмотр сессии")
        return

    session_id = callback_query.data.removeprefix("session:")
    logger.debug(f"ID сессии для просмотра: {session_id}")
    
    info = await reqs.get_session_view(pool, session_id)
    if not info:
        logger.error(f"Сессия {session_id} не найдена для агента {agent_id}")
        return await callback_query.message.edit_text(texts.SESSION_NOT_FOUND, reply_markup=back.keyboard())

    # Получаем сообщения и рендерим текст
    msgs = await reqs.fetch_session_messages(pool, info["tgid"], session_id)
    text, attachments = render_messages.render_session_text(info["username"], info["assigned_agent"], msgs)
    logger.debug(f"Рендеринг сессии: {len(msgs)} сообщений, {len(attachments)} вложений")

    # Обновляем сообщение
    await callback_query.message.edit_text(
        text,
        reply_markup=session_view.session_view_kb(
            session_id, 
            taken=bool(info["assigned_agent"]), 
            opened=bool(await state.get_state()), 
            attachments=attachments
        ),
        disable_web_page_preview=True
    )

    # Сохраняем данные панели в состоянии
    await state.update_data(panel_msg={
        "chat_id": callback_query.message.chat.id,
        "message_id": callback_query.message.message_id,
        "session_id": session_id,
    })
    await callback_query.answer()
    logger.info(f"Просмотр сессии {session_id} открыт агентом {agent_id}")

async def take_session(callback_query: CallbackQuery, is_admin: bool, pool, state: FSMContext):
    agent_id = callback_query.from_user.id
    logger.info(f"Попытка взять сессию агентом {agent_id}")
    
    if not is_admin:
        logger.warning(f"Не-админ {agent_id} пытается взять сессию")
        return
    
    session_id = callback_query.data.removeprefix("take:")
    logger.debug(f"ID сессии для взятия: {session_id}")

    ok = await reqs.assign_session(pool, session_id, agent_id)
    if not ok:
        logger.warning(f"Попытка взять уже занятую сессию {session_id} оператором {agent_id}")
        return await callback_query.answer(texts.TAKEN_SESSION, show_alert=True)
    
    logger.info(f"Оператор {agent_id} взял сессию {session_id}")
    
    logger.debug(f"Установка состояния AdminChat.active для агента {agent_id}")
    await state.set_state(AdminChat.active)
    await state.update_data(session_id=session_id)

    info = await reqs.get_session_view(pool, session_id)
    if not info:
        logger.error(f"Сессия {session_id} не найдена после взятия агентом {agent_id}")
        await state.clear()
        return await callback_query.answer(texts.SESSION_NOT_FOUND, show_alert=True)
    
    logger.info(f"Получение сообщений сессии {session_id} для пользователя {info['tgid']}")
    msgs = await reqs.fetch_session_messages(pool, info["tgid"], session_id)
    text, attachments = render_messages.render_session_text(info["username"], info["assigned_agent"], msgs)
    logger.debug(f"Рендеринг сессии: {len(msgs)} сообщений, {len(attachments)} вложений")

    await callback_query.message.edit_text(
        text,
        reply_markup=session_view.session_view_kb(
            session_id, 
            taken=bool(info["assigned_agent"]), 
            opened=bool(await state.get_state()), 
            attachments=attachments
        ),
        disable_web_page_preview=True
    )

    # Сохраняем данные панели
    await state.update_data(panel_msg={
        "chat_id": callback_query.message.chat.id,
        "message_id": callback_query.message.message_id,
        "session_id": session_id,
    })
    await callback_query.answer(texts.CHAT_ASSIGNED_TO_YOU)
    logger.info(f"Сессия {session_id} успешно взята агентом {agent_id}")

async def open_chat(callback_query: CallbackQuery, is_admin: bool, pool, state: FSMContext):
    """Открывает чат для работы"""
    agent_id = callback_query.from_user.id
    logger.info(f"Открытие чата агентом {agent_id}")
    
    if not is_admin:
        logger.warning(f"Не-админ {agent_id} пытается открыть чат")
        return
    
    session_id = callback_query.data.removeprefix("open:")
    logger.debug(f"ID сессии для открытия чата: {session_id}")
    
    # Устанавливаем состояние
    await state.set_state(AdminChat.active)
    await state.update_data(session_id=session_id)

    # Получаем информацию о сессии
    info = await reqs.get_session_view(pool, session_id)
    if not info:
        logger.error(f"Сессия {session_id} не найдена для открытия чата агентом {agent_id}")
        await state.clear()
        return await callback_query.answer(texts.SESSION_NOT_FOUND, show_alert=True)
    
    # Получаем сообщения и рендерим
    msgs = await reqs.fetch_session_messages(pool, info["tgid"], session_id)
    text, attachments = render_messages.render_session_text(info["username"], info["assigned_agent"], msgs)
    logger.debug(f"Рендеринг сессии: {len(msgs)} сообщений, {len(attachments)} вложений")

    # Обновляем сообщение
    await callback_query.message.edit_text(
        text,
        reply_markup=session_view.session_view_kb(
            session_id, 
            taken=bool(info["assigned_agent"]), 
            opened=bool(await state.get_state()), 
            attachments=attachments
        ),
        disable_web_page_preview=True
    )

    # Сохраняем данные панели
    await state.update_data(panel_msg={
        "chat_id": callback_query.message.chat.id,
        "message_id": callback_query.message.message_id,
        "session_id": session_id,
    })
    await callback_query.answer()
    logger.info(f"Чат сессии {session_id} открыт агентом {agent_id}")
    
async def close_session(callback_query: CallbackQuery, is_admin: bool, pool, state: FSMContext):
    """Закрывает сессию"""
    agent_id = callback_query.from_user.id
    logger.info(f"Попытка закрыть сессию агентом {agent_id}")
    
    if not is_admin:
        logger.warning(f"Не-админ {agent_id} пытается закрыть сессию")
        return
    
    session_id = callback_query.data.removeprefix("close:")
    logger.debug(f"ID сессии для закрытия: {session_id}")
    
    # Закрываем сессию
    ok = await reqs.close_session(pool, session_id=session_id, assigned_agent=agent_id)
    if not ok:
        logger.warning(f"Не удалось закрыть сессию {session_id} оператором {agent_id}")
        return await callback_query.answer(texts.FAILED_TO_CLOSE_SESSION, show_alert=True)
    
    logger.info(f"Оператор {agent_id} закрыл сессию {session_id}")
    
    # Очищаем состояние и возвращаемся на главную
    await state.clear()
    await start.welcome(callback_query.message, state, is_admin, pool, from_callback=True)
    await callback_query.answer(texts.SESSION_CLOSED_SUCCESSFUL)
    logger.info(f"Сессия {session_id} успешно закрыта агентом {agent_id}")

async def open_attachment(callback_query: CallbackQuery, pool):
    """Открывает вложение из сообщения"""
    user_id = callback_query.from_user.id
    logger.info(f"Открытие вложения пользователем {user_id}")
    
    _, sid_str, mid_str = callback_query.data.split(":")
    mid = int(mid_str)
    logger.debug(f"Параметры вложения: session_id={sid_str}, message_id={mid}")

    # Получаем информацию о файле
    file_id, sess_id_of_msg = await reqs.get_message_file(pool, mid)
    if not file_id or int(sid_str) != int(sess_id_of_msg or 0):
        logger.warning(f"Вложение {mid} не найдено или не принадлежит сессии {sid_str}")
        return await callback_query.answer(texts.ATTACHMENT_NOT_FOUND, show_alert=True)
    
    # Отправляем вложение
    await _send_attachment(callback_query, file_id, mid, user_id)
    await callback_query.answer()


async def _send_attachment(callback_query: CallbackQuery, file_id: str, mid: int, user_id: int):
    """Отправляет вложение пользователю"""
    logger.debug(f"Отправка вложения {file_id} пользователю {user_id}")
    
    # Пробуем отправить как фото
    try:
        await callback_query.message.answer_photo(file_id, reply_markup=att_kb.attclose(mid))
        logger.info(f"Фото вложение {mid} отправлено пользователю {user_id}")
        return
    except Exception as e:
        logger.debug(f"Не удалось отправить как фото, пробуем как документ: {e}")
    
    # Пробуем отправить как документ
    try:
        await callback_query.message.answer_document(file_id, reply_markup=att_kb.attclose(mid))
        logger.info(f"Документ вложение {mid} отправлено пользователю {user_id}")
    except Exception as e2:
        logger.error(f"Не удалось отправить вложение {mid}: {e2}")

async def close_attachment(callback_query: CallbackQuery, is_admin: bool):
    """Закрывает вложение"""
    agent_id = callback_query.from_user.id
    logger.info(f"Закрытие вложения агентом {agent_id}")
    
    if not is_admin:
        logger.warning(f"Не-админ {agent_id} пытается закрыть вложение")
        return
    
    try:
        await callback_query.message.delete()
        logger.info(f"Вложение закрыто агентом {agent_id}")
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение с вложением: {e}")
    await callback_query.answer()