from aiogram.types import CallbackQuery
from sql import reqs
from utils.logger import get_logger
from constants import SESSION_TYPES, CLOSED_PER_PAGE
import texts
from keyboards import back
from keyboards.messages_keyboard import waiting_keyboard, closed_kb
import math

logger = get_logger(__name__)


def _format_count_text(count: int, mine_texts: tuple[str, str, str], other_texts: tuple[str, str, str]) -> str:
    """Форматирование текста с количеством в зависимости от числа"""
    if count == 1:
        return mine_texts[0].format(count=count)
    elif count in [2, 3, 4]:
        return mine_texts[1].format(count=count)
    else:
        return mine_texts[2].format(count=count)


async def done_list_page(callback_query: CallbackQuery, pool):
    agent_id = callback_query.from_user.id
    logger.info(f"Обработка пагинации закрытых чатов для агента {agent_id}")
    
    _, _, page_str, mine_str = callback_query.data.split(":")
    page = int(page_str)
    only_mine = bool(int(mine_str))
    logger.debug(f"Параметры пагинации: page={page}, only_mine={only_mine}")
    
    await _render_done_page(callback_query, pool, page=page, only_mine=only_mine, agent_id=agent_id)
    await callback_query.answer()
    logger.info(f"Пагинация закрытых чатов обработана для агента {agent_id}")

async def done_toggle(callback_query: CallbackQuery, pool):
    agent_id = callback_query.from_user.id
    logger.info(f"Переключение режима просмотра закрытых чатов для агента {agent_id}")
    
    _, _, page_str, mine_str = callback_query.data.split(":")
    page = int(page_str)
    only_mine = not bool(int(mine_str))
    logger.debug(f"Переключение режима: page={page}, only_mine={only_mine}")
    
    await _render_done_page(callback_query, pool, page=page, only_mine=only_mine, agent_id=agent_id)
    await callback_query.answer()
    logger.info(f"Режим просмотра переключен для агента {agent_id}")



async def _render_done_page(callback_query, pool, page: int, only_mine: bool, agent_id: int):
    logger.debug(f"Рендеринг страницы закрытых чатов: page={page}, only_mine={only_mine}, agent_id={agent_id}")
    
    total = await reqs.count_closed(pool, only_mine=only_mine, agent_id=agent_id)
    total_pages = max(1, math.ceil(total / CLOSED_PER_PAGE))
    page = max(1, min(page, total_pages))
    logger.debug(f"Статистика: total={total}, total_pages={total_pages}, corrected_page={page}")

    rows = await reqs.fetch_closed(pool, page=page, only_mine=only_mine, agent_id=agent_id)
    logger.debug(f"Получено {len(rows)} закрытых чатов")
    
    title = "Закрытые чаты - Мои" if only_mine else "Закрытые чаты - Все"
    if not rows:
        title += "\n\nПока нет закрытых чатов в этом режиме."
        logger.info(f"Нет закрытых чатов для агента {agent_id} в режиме {'только мои' if only_mine else 'все'}")
        
    kb = closed_kb.closed_list_kb(rows, page=page, total_pages=total_pages, only_mine=only_mine)
    await callback_query.message.edit_text(title, reply_markup=kb)
    logger.info(f"Страница закрытых чатов отрендерена для агента {agent_id}")

async def messages(callback_query: CallbackQuery, is_admin: bool, pool):
    agent_id = callback_query.from_user.id
    logger.info(f"Обработка запроса сообщений от агента {agent_id}")
    
    if not is_admin:
        logger.warning(f"Не-админ {agent_id} пытается получить доступ к сообщениям")
        return

    callback_data = callback_query.data.removeprefix("msg:")
    logger.debug(f"Тип запроса: {callback_data}")

    if callback_data == "toServe":
        logger.info(f"Запрос ожидающих сессий от агента {agent_id}")
        items = await reqs.fetch_sessions(pool, SESSION_TYPES["TO_SERVE"])
        count = await reqs.count_sessions(pool, SESSION_TYPES["TO_SERVE"])
        logger.debug(f"Найдено {count} ожидающих сессий")
        
        if not items:
            logger.info(f"Нет ожидающих сессий для агента {agent_id}")
            await callback_query.message.edit_text(texts.NONE_TO_SERVE, reply_markup=back.keyboard())
            return

        await callback_query.message.edit_text(texts.COUNT_TO_SERVE.format(count=count), reply_markup=waiting_keyboard.kb(items))
        await callback_query.answer()
        logger.info(f"Список ожидающих сессий показан агенту {agent_id}")

    elif callback_data == "processing_mine":
        logger.info(f"Запрос моих активных сессий от агента {agent_id}")
        items = await reqs.fetch_sessions(pool, SESSION_TYPES["PROCESSING_MINE"], agent_id=agent_id)
        count = await reqs.count_sessions(pool, SESSION_TYPES["PROCESSING_MINE"], agent_id=agent_id)
        logger.debug(f"Найдено {count} моих активных сессий")
        
        if not items:
            logger.info(f"Нет активных сессий у агента {agent_id}")
            await callback_query.message.edit_text(texts.NO_ONE_ASSIGNED_TO_ADMIN, reply_markup=back.keyboard())
            return
        text = _format_count_text(
            count, 
            (texts.MINE_ASSIGNED_1, texts.MINE_ASSIGNED_2_3_4, texts.MINE_ASSIGNED_OTHER),
            (texts.OTHER_ASSIGNED_1, texts.OTHER_ASSIGNED_2_3_4, texts.OTHER_ASSIGNED_OTHER)
        )
        await callback_query.message.edit_text(text=text, reply_markup=waiting_keyboard.kb(items))
        await callback_query.answer()
        logger.info(f"Список моих активных сессий показан агенту {agent_id}")

    elif callback_data == "processing":
        logger.info(f"Запрос активных сессий других агентов от агента {agent_id}")
        items = await reqs.fetch_sessions(pool, SESSION_TYPES["PROCESSING"], agent_id=agent_id)
        count = await reqs.count_sessions(pool, SESSION_TYPES["PROCESSING"], agent_id=agent_id)
        logger.debug(f"Найдено {count} активных сессий других агентов")
        
        if not items:
            logger.info(f"Нет активных сессий других агентов для агента {agent_id}")
            await callback_query.message.edit_text(texts.NO_ONE_ASSGINED, reply_markup=back.keyboard())
            return
        text = _format_count_text(
            count,
            (texts.OTHER_ASSIGNED_1, texts.OTHER_ASSIGNED_2_3_4, texts.OTHER_ASSIGNED_OTHER),
            (texts.OTHER_ASSIGNED_1, texts.OTHER_ASSIGNED_2_3_4, texts.OTHER_ASSIGNED_OTHER)
        )
        await callback_query.message.edit_text(text=text, reply_markup=waiting_keyboard.kb(items))
        await callback_query.answer()
        logger.info(f"Список активных сессий других агентов показан агенту {agent_id}")
    
    elif callback_data == "done":
        logger.info(f"Запрос закрытых чатов от агента {agent_id}")
        await _render_done_page(callback_query, pool, page=1, only_mine=False, agent_id=agent_id)
        await callback_query.answer()
        logger.info(f"Список закрытых чатов показан агенту {agent_id}")