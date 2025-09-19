import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram import F
from aiogram.filters import Command, CommandStart

from sql import reqs
from middlewares import admin, databaseAdd, log
from handlers.messages import start, admin_reply_handlers
from handlers.callbacks import adminPage, messages_handler, users_handler
from states import AdminChat
from config import TOKEN, ADMINS_ID, create_pool
from utils.logger import get_logger

logger = get_logger(__name__)

dp = Dispatcher(storage=MemoryStorage())
router = Router()
bot = Bot(TOKEN, DefaultBotProperties=ParseMode.HTML)



async def bot_init():
    logger.info("Инициализация бота...")
    pool = await create_pool()
    dp["pool"] = pool
    logger.info("Пул БД добавлен в диспетчер")
    
    dp.message.middleware(admin.AdminCheck(ADMINS_ID))
    dp.callback_query.middleware(admin.AdminCheck(ADMINS_ID))
    logger.info("Middleware для проверки админов добавлен")
    
    dp.message.middleware(log.LogMiddleware(pool, dp.storage))
    logger.info("Middleware для логгирования добавлен")
    
    dp.message.middleware(databaseAdd.DbAdd(pool))
    logger.info("Middleware для добавления пользователей в БД добавлен")


    logger.info("Регистрация обработчиков callback_query...")
    router.callback_query.register(messages_handler.done_list_page, F.data.startswith("done:list:"))
    router.callback_query.register(messages_handler.done_toggle, F.data.startswith("done:toggle:"))
    router.callback_query.register(users_handler.open_attachment, F.data.startswith("att:"))
    router.callback_query.register(users_handler.close_attachment, F.data.startswith("attclose:"))
    router.callback_query.register(users_handler.open_session_view, F.data.startswith("session:"))
    router.callback_query.register(users_handler.take_session, F.data.startswith("take:"))
    router.callback_query.register(users_handler.open_chat, F.data.startswith("open:"))
    router.callback_query.register(users_handler.close_session, F.data.startswith("close:"))
    router.callback_query.register(messages_handler.messages, F.data.startswith("msg:"))
    router.callback_query.register(adminPage.mainPageCallback)
    logger.info("Обработчики callback_query зарегистрированы")

    logger.info("Регистрация обработчиков сообщений...")
    router.message.register(admin_reply_handlers.admin_reply, AdminChat.active)
    router.message.register(start.welcome, CommandStart())
    logger.info("Обработчики сообщений зарегистрированы")
    
    dp.include_router(router)
    logger.info("Роутер добавлен в диспетчер")
    
    return pool

async def main() -> None:
    logger.info("Запуск основного процесса...")
    pool = await bot_init()
    logger.info("Инициализация бота завершена")
    
    logger.info("Создание таблиц в БД...")
    await reqs.createTables(pool)
    logger.info("Таблицы в БД созданы/проверены")

    logger.info("Бот запущен и ожидает сообщений")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
        raise
    finally:
        logger.info("Закрытие пула соединений с БД...")
        pool.close()
        await pool.wait_closed()
        logger.info("Пул соединений закрыт")
if __name__ == "__main__":
    logger.info("Запуск основного потока...")
    asyncio.run(main())
