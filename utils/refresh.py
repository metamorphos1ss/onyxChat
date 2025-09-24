from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from keyboards import back
from keyboards.messages_keyboard import session_view
from services import ServiceContainer
from states import AdminChat
from utils import render_messages
from utils.logger import get_logger

logger = get_logger(__name__)

async def refresh_session_view(bot, storage, services: ServiceContainer, operator_id: int, state: FSMContext | None = None):
    """Обновляет просмотр сессии для оператора"""
    logger.debug(f"Обновление просмотра сессии для оператора {operator_id}")
    
    # Получаем FSM контекст
    fsm = state or _create_fsm_context(bot, storage, operator_id)
    
    # Проверяем состояние оператора
    current_state = await fsm.get_state()
    if current_state != "AdminChat:active":
        logger.debug(f"Оператор {operator_id} не в активном состоянии, пропускаем обновление")
        return

    # Получаем данные панели
    data = await fsm.get_data()
    panel = data.get("panel_msg")
    session_id = int(data.get("session_id") or 0)
    
    if not panel or not session_id:
        logger.debug(f"Нет панели или session_id для оператора {operator_id}")
        return

    # Обновляем панель
    await _update_panel(bot, services, session_id, panel, current_state, operator_id)


def _create_fsm_context(bot, storage, operator_id: int) -> FSMContext:
    """Создает FSM контекст для оператора"""
    key = StorageKey(bot_id=bot.id, chat_id=operator_id, user_id=operator_id)
    fsm = FSMContext(storage=storage, key=key)
    logger.debug(f"Создан новый FSM контекст для оператора {operator_id}")
    return fsm


async def _update_panel(bot, services: ServiceContainer, session_id: int, panel: dict, current_state: str, operator_id: int):
    """Обновляет панель сессии"""
    chat_id = panel["chat_id"]
    message_id = panel["message_id"]
    logger.debug(f"Обновление панели: chat_id={chat_id}, message_id={message_id}")

    session_service = services.session_service
    message_service = services.message_service

    # Получаем информацию о сессии
    info = await session_service.get_session_info(session_id)
    if not info:
        logger.warning(f"Сессия {session_id} не найдена для обновления панели оператора {operator_id}")
        return

    # Получаем сообщения и рендерим
    msgs = await message_service.get_session_messages(info["tgid"], session_id)
    text, attachments = render_messages.render_session_text(
        info["username"], 
        info["assigned_agent"], 
        msgs
    )
    logger.debug(f"Рендеринг панели: {len(msgs)} сообщений, {len(attachments)} вложений")

    # Обновляем сообщение
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=session_view.session_view_kb(
                session_id, 
                taken=bool(info["assigned_agent"]), 
                opened=bool(current_state), 
                attachments=attachments
            ),
            disable_web_page_preview=True
        )
        logger.info(f"Панель сессии {session_id} обновлена для оператора {operator_id}")
    except Exception as e:
        logger.warning(f"Не удалось обновить панель сессии {session_id} для оператора {operator_id}: {e}")
