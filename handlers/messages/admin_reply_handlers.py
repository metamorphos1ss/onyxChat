import asyncio
import re

from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import texts
from config import ADMINS_ID
from constants import MESSAGE_DIRECTIONS
from keyboards.messages_keyboard import session_view
from sql import reqs
from utils import render_messages
from utils.logger import get_logger

logger = get_logger(__name__)

async def admin_reply(message: Message, state: FSMContext, pool):
    """Обрабатывает ответ админа пользователю"""
    admin_id = message.from_user.id
    logger.info(f"Обработка ответа админа {admin_id}")
    
    data = await state.get_data()
    session_id = data.get("session_id")
    logger.debug(f"Данные состояния: {data}")
    
    if not session_id:
        logger.warning(f"Админ {admin_id} пытается ответить без активной сессии")
        await state.clear()
        return await message.answer(texts.SESSION_NOT_FOUND)
    
    # Обработка команды /start
    if message.text and message.text.strip() == "/start":
        logger.info(f"Админ {admin_id} отправил /start, удаляем сообщение")
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение /start: {e}")
        return
    
    logger.info(f"Получение информации о сессии {session_id}")
    view = await reqs.get_session_view(pool, session_id)
    if not view or not view["tgid"]:
        logger.error(f"Сессия {session_id} не найдена или не имеет tgid")
        await message.answer(texts.CLIENT_NOT_FOUND)
        return
    
    user_id = view["tgid"]
    sent_text = message.text or message.caption
    file_id = _extract_file_id(message)
    
    logger.info(f"Отправка сообщения от админа {admin_id} пользователю {user_id} в сессии {session_id}")
    logger.debug(f"Текст сообщения: {sent_text}")

    # Отправляем сообщение пользователю
    try:
        await message.send_copy(chat_id=user_id)
        logger.info(f"Сообщение успешно отправлено пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
        return await message.answer(texts.FAILED_TO_SEND_MESSAGE.format(exception=e))
    
  # Логируем сообщение в БД
    logger.info(f"Логирование сообщения в БД: user_id={user_id}, session_id={session_id}")
    await reqs.log_message(
        pool,
        tgid=user_id,
        current_session_id=session_id,
        direction=MESSAGE_DIRECTIONS["FROM_AGENT"],
        text=sent_text,
        file_id=file_id
    )
    logger.info(f"Сообщение залогировано в БД")

    # Обновляем панель если есть
    await _update_session_panel(message, state, pool, session_id, user_id, view)
    
    # Удаляем сообщение админа
    logger.debug(f"Удаление сообщения админа {admin_id}")
    await message.delete()
    logger.info(f"Обработка ответа админа {admin_id} завершена")


def _extract_file_id(message: Message) -> str | None:
    """Извлекает file_id из сообщения"""
    if message.photo:
        file_id = message.photo[-1].file_id
        logger.debug(f"Обнаружено фото с file_id: {file_id}")
        return file_id
    elif message.document:
        file_id = message.document.file_id
        logger.debug(f"Обнаружен документ с file_id: {file_id}")
        return file_id
    elif message.voice:
        file_id = message.voice.file_id
        logger.debug(f"Обнаружено голосовое сообщение с file_id: {file_id}")
        return file_id
    return None


async def _update_session_panel(message: Message, state: FSMContext, pool, session_id: int, user_id: int, view: dict):
    """Обновляет панель сессии"""
    data = await state.get_data()
    panel = data.get("panel_msg")
    
    if not panel:
        logger.debug(f"Панель для сессии {session_id} не найдена")
        return
    
    logger.info(f"Обновление панели сессии {session_id}")
    info = await reqs.get_session_view(pool, int(session_id))
    msgs = await reqs.fetch_session_messages(pool, user_id, int(session_id))
    text, attachments = render_messages.render_session_text(
        info["username"], info["assigned_agent"], msgs
    )
    logger.debug(f"Рендеринг панели: {len(msgs)} сообщений, {len(attachments)} вложений")
    
    try:
        await message.bot.edit_message_text(
            chat_id=panel["chat_id"],
            message_id=panel["message_id"],
            text=text,
            reply_markup=session_view.session_view_kb(
                session_id,
                taken=bool(info["assigned_agent"]),
                opened=bool(await state.get_state()),
                attachments=attachments,
            ),
            disable_web_page_preview=True,
        )
        logger.info(f"Панель сессии {session_id} обновлена")
    except Exception as e:
        logger.warning(f"Не удалось обновить панель сессии {session_id}: {e}")

async def admin_notify(message: Message, pool):
    """Отправляет уведомление админам о новой сессии"""
    bot = message.bot
    tgid = message.from_user.id
    username = message.from_user.username
    logger.info(f"Отправка уведомления админам о новой сессии для пользователя {tgid}")
    
    session_id = await reqs.get_session_id(pool, tgid)
    if not session_id:
        logger.warning(f"admin_notify: нет открытой сессии для tgid={tgid}")
        return
    
    # Формируем текст уведомления
    uline = f"@{username}" if username else "(без username)"
    text = f"Новая сессия\nКлиент: #{tgid} {uline}"
    logger.debug(f"Текст уведомления: {text}")

    # Создаем клавиатуру
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Открыть", callback_data=f"session:{session_id}"),
        InlineKeyboardButton(text="Взять чат", callback_data=f"take:{session_id}")
    )
    logger.debug(f"Создана клавиатура для сессии {session_id}")

    # Получаем список админов
    admins: set[int] = {int(x) for x in re.findall(r"\d+", str(ADMINS_ID))}
    logger.info(f"Отправка уведомления {len(admins)} админам: {admins}")

    # Отправляем уведомления параллельно
    await _send_notifications_to_admins(bot, admins, text, kb.as_markup())
    
    logger.info(f"Уведомления о сессии {session_id} отправлены всем админам")


async def _send_notifications_to_admins(bot, admins: set[int], text: str, keyboard):
    """Отправляет уведомления всем админам"""
    tasks = []
    for admin_id in admins:
        task = _send_single_notification(bot, admin_id, text, keyboard)
        tasks.append(task)
    
    # Выполняем все отправки параллельно
    await asyncio.gather(*tasks, return_exceptions=True)


async def _send_single_notification(bot, admin_id: int, text: str, keyboard):
    """Отправляет уведомление одному админу"""
    try:
        await bot.send_message(admin_id, text, reply_markup=keyboard)
        logger.info(f"Уведомление отправлено админу {admin_id}")
    except Exception as e:
        logger.exception(f"admin_notify: не удалось отправить админу {admin_id}: {e}")