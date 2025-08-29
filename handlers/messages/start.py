from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from handlers.messages.admin_reply_handlers import admin_notify

import logging
from sql import reqs

import texts

from keyboards import admin_keyboard


async def welcome(message: Message, state: FSMContext, is_admin: bool, pool, from_callback=False):
    tgid = message.from_user.id
    if is_admin:
        logging.info("Пользователь является админом")
        first_name = message.chat.first_name or message.chat.title
        if first_name == "Father":
            text = texts.WELCOME_TEXT_ONYX
        else:
            text = texts.WELCOME_TEXT_ADMIN.format(first_name=first_name)
        if from_callback:
            await message.edit_text(text, reply_markup=admin_keyboard.keyboard())
        else:
            await message.answer(text, reply_markup=admin_keyboard.keyboard())
    else:
        logging.info("Пользователь не является админом")
        session_opened = await reqs.find_open_session(pool, tgid)
        print(session_opened)
        if session_opened:
            logging.info("У клиента уже была открыта сессия")
            text = texts.SESSION_WAS_OPENED
        else:
            text = texts.WELCOME_TEXT_USER
            session_id = await reqs.ensure_open_session(pool, tgid)
            await admin_notify(message, pool)
        await message.answer(text)
