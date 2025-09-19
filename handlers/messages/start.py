from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from handlers.messages.admin_reply_handlers import admin_notify
from sql import reqs
from utils.logger import get_logger
import texts
from keyboards import admin_keyboard

logger = get_logger(__name__)


async def welcome(message: Message, state: FSMContext, is_admin: bool, pool, from_callback=False):
    tgid = message.from_user.id
    username = message.from_user.username
    logger.info(f"Обработка команды /start: tgid={tgid}, username=@{username}, is_admin={is_admin}, from_callback={from_callback}")
    
    if is_admin:
        logger.info(f"Админ {tgid} запустил бота")
        first_name = message.chat.first_name or message.chat.title
        logger.debug(f"Имя админа: {first_name}")
        
        if first_name == "Father":
            text = texts.WELCOME_TEXT_ONYX
            logger.info(f"Специальное приветствие для Father")
        else:
            text = texts.WELCOME_TEXT_ADMIN.format(first_name=first_name)
            logger.info(f"Обычное приветствие для админа {first_name}")
            
        if from_callback:
            logger.debug(f"Редактирование сообщения для админа {tgid}")
            await message.edit_text(text, reply_markup=admin_keyboard.keyboard())
        else:
            logger.debug(f"Отправка нового сообщения админу {tgid}")
            await message.answer(text, reply_markup=admin_keyboard.keyboard())
        logger.info(f"Приветствие админу {tgid} отправлено")
    else:
        logger.info(f"Пользователь {tgid} запустил бота")
        session_opened = await reqs.find_open_session(pool, tgid)
        logger.debug(f"Проверка открытой сессии для {tgid}: {session_opened}")
        text = texts.WELCOME_TEXT_USER
        
        if session_opened:
            logger.info(f"У клиента {tgid} уже была открыта сессия")
        else:
            logger.info(f"Создание новой сессии для пользователя {tgid}")
            session_id = await reqs.ensure_open_session(pool, tgid)
            logger.info(f"Создана новая сессия {session_id} для пользователя {tgid}")
            await admin_notify(message, pool)
            logger.info(f"Уведомление админам о новой сессии {session_id} отправлено")
        
        logger.debug(f"Отправка приветствия пользователю {tgid}")
        await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)
        logger.info(f"Приветствие пользователю {tgid} отправлено")
