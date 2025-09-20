from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from handlers.messages import start
from keyboards import back, messages_page_keyboard
from utils.logger import get_logger

logger = get_logger(__name__)

async def mainPageCallback(callback_query: CallbackQuery, state: FSMContext, is_admin: bool, pool):
    user_id = callback_query.from_user.id
    callback_data = callback_query.data
    logger.info(f"Обработка callback от пользователя {user_id}: {callback_data}")

    if callback_data == "home":
        logger.info(f"Переход на главную страницу пользователем {user_id}")
        if is_admin:
            logger.debug(f"Очистка состояния для админа {user_id}")
            await state.clear()
        await start.welcome(callback_query.message, state, is_admin, pool, from_callback=True)
        await callback_query.answer()
        logger.info(f"Главная страница показана пользователю {user_id}")

    elif callback_data == "onyxStats":
        logger.info(f"Запрос статистики onyx от пользователя {user_id}")
        await callback_query.message.edit_text("здесь будет onyx stats", reply_markup=back.keyboard())
        await callback_query.answer()
        logger.info(f"Страница статистики показана пользователю {user_id}")

    elif callback_data == "messages":
        logger.info(f"Запрос страницы сообщений от пользователя {user_id}")
        await callback_query.message.edit_text("Чаты:", reply_markup=messages_page_keyboard.keyboard())
        await callback_query.answer()
        logger.info(f"Страница сообщений показана пользователю {user_id}")