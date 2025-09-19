from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from states import AdminChat
from utils import render_messages
from sql import reqs
from keyboards import back
from keyboards.messages_keyboard import session_view
from utils.logger import get_logger

logger = get_logger(__name__)

async def refresh_session_view(bot, storage, pool, operator_id: int, state: FSMContext | None = None):
    logger.debug(f"Обновление просмотра сессии для оператора {operator_id}")
    
    if state is None:
        key = StorageKey(bot_id=bot.id, chat_id=operator_id, user_id=operator_id)
        fsm = FSMContext(storage=storage, key=key)
        logger.debug(f"Создан новый FSM контекст для оператора {operator_id}")
    else:
        fsm = state
        logger.debug(f"Используется переданный FSM контекст для оператора {operator_id}")
    
    current = await fsm.get_state()
    logger.debug(f"Текущее состояние оператора {operator_id}: {current}")
    
    if current != "AdminChat:active":
        logger.debug(f"Оператор {operator_id} не в активном состоянии, пропускаем обновление")
        return

    data = await fsm.get_data()
    panel = data.get("panel_msg")
    session_id = int(data.get("session_id") or 0)
    logger.debug(f"Данные состояния оператора {operator_id}: panel={bool(panel)}, session_id={session_id}")
    
    if not panel or not session_id:
        logger.debug(f"Нет панели или session_id для оператора {operator_id}")
        return

    chat_id = panel["chat_id"]
    message_id = panel["message_id"]
    logger.debug(f"Обновление панели: chat_id={chat_id}, message_id={message_id}")

    info = await reqs.get_session_view(pool, session_id)
    if not info:
        logger.warning(f"Сессия {session_id} не найдена для обновления панели оператора {operator_id}")
        return

    logger.debug(f"Получение сообщений сессии {session_id} для пользователя {info['tgid']}")
    msgs = await reqs.fetch_session_messages(pool, info["tgid"], session_id)
    text, attachments = render_messages.render_session_text(info["username"], info["assigned_agent"], msgs)
    logger.debug(f"Рендеринг панели: {len(msgs)} сообщений, {len(attachments)} вложений")

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=session_view.session_view_kb(session_id, taken=bool(info["assigned_agent"]), opened=bool(current), attachments=attachments),
            disable_web_page_preview=True
        )
        logger.info(f"Панель сессии {session_id} обновлена для оператора {operator_id}")
    except Exception as e:
        logger.warning(f"Не удалось обновить панель сессии {session_id} для оператора {operator_id}: {e}")
