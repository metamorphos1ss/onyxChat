import asyncio

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

from config import get_admin_ids, TOKEN, create_pool
from handlers.callbacks import adminPage, messages_handler, users_handler
from handlers.messages import admin_reply_handlers, start
from middlewares import admin, databaseAdd, log
from sql import reqs
from states import AdminChat
from utils.logger import get_logger

logger = get_logger(__name__)

dp = Dispatcher(storage=MemoryStorage())
router = Router()
bot = Bot(TOKEN, DefaultBotProperties=ParseMode.HTML)



async def bot_init():
    """Инициализирует бота и все его компоненты"""
    logger.info("Инициализация бота...")
    
    # Создаем пул соединений с БД
    pool = await create_pool()
    dp["pool"] = pool
    logger.info("Пул БД добавлен в диспетчер")
    
    # Настраиваем middleware
    await _setup_middleware(pool)
    
    # Регистрируем обработчики
    await _register_handlers()
    
    # Подключаем роутер
    dp.include_router(router)
    logger.info("Роутер добавлен в диспетчер")
    
    return pool


async def _setup_middleware(pool):
    """Настраивает middleware для бота"""
    # Middleware для проверки админов
    admin_ids = get_admin_ids()
    dp.message.middleware(admin.AdminCheck(admin_ids))
    dp.callback_query.middleware(admin.AdminCheck(admin_ids))
    logger.info("Middleware для проверки админов добавлен")
    
    # Middleware для логгирования
    dp.message.middleware(log.LogMiddleware(pool, dp.storage))
    logger.info("Middleware для логгирования добавлен")
    
    # Middleware для добавления пользователей в БД
    dp.message.middleware(databaseAdd.DbAdd(pool))
    logger.info("Middleware для добавления пользователей в БД добавлен")


async def _register_handlers():
    """Регистрирует все обработчики"""
    logger.info("Регистрация обработчиков callback_query...")
    
    # Обработчики callback_query
    callback_handlers = [
        (messages_handler.done_list_page, F.data.startswith("done:list:")),
        (messages_handler.done_toggle, F.data.startswith("done:toggle:")),
        (users_handler.open_attachment, F.data.startswith("att:")),
        (users_handler.close_attachment, F.data.startswith("attclose:")),
        (users_handler.open_session_view, F.data.startswith("session:")),
        (users_handler.take_session, F.data.startswith("take:")),
        (users_handler.open_chat, F.data.startswith("open:")),
        (users_handler.close_session, F.data.startswith("close:")),
        (messages_handler.messages, F.data.startswith("msg:")),
        (adminPage.mainPageCallback, None),  # Без фильтра
    ]
    
    for handler, filter_condition in callback_handlers:
        if filter_condition:
            router.callback_query.register(handler, filter_condition)
        else:
            router.callback_query.register(handler)
    
    logger.info("Обработчики callback_query зарегистрированы")

    logger.info("Регистрация обработчиков сообщений...")
    router.message.register(admin_reply_handlers.admin_reply, AdminChat.active)
    router.message.register(start.welcome, CommandStart())
    logger.info("Обработчики сообщений зарегистрированы")

async def main() -> None:
    """Основная функция запуска бота"""
    logger.info("Запуск основного процесса...")
    
    # Инициализируем бота
    pool = await bot_init()
    logger.info("Инициализация бота завершена")
    
    # Создаем таблицы в БД
    logger.info("Создание таблиц в БД...")
    await reqs.createTables(pool)
    logger.info("Таблицы в БД созданы/проверены")

    # Запускаем бота
    logger.info("Бот запущен и ожидает сообщений")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
        raise
    finally:
        # Закрываем соединения с БД
        await _cleanup_database(pool)


async def _cleanup_database(pool):
    """Закрывает соединения с базой данных"""
    logger.info("Закрытие пула соединений с БД...")
    pool.close()
    await pool.wait_closed()
    logger.info("Пул соединений закрыт")
if __name__ == "__main__":
    logger.info("Запуск основного потока...")
    asyncio.run(main())
