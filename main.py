import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram import F
from aiogram.filters import Command, CommandStart

from sql import reqs

from middlewares import admin, databaseAdd, log
from handlers.messages import start, admin_reply_handlers
from handlers.callbacks import adminPage, messages_handler, users_handler, catch

from states import AdminChat
from config import TOKEN, ADMINS_ID, create_pool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher(storage=MemoryStorage())
router = Router()
bot = Bot(TOKEN, DefaultBotProperties=ParseMode.HTML)



async def bot_init():
    pool = await create_pool()
    dp["pool"] = pool
    dp.message.middleware(admin.AdminCheck(ADMINS_ID))
    dp.callback_query.middleware(admin.AdminCheck(ADMINS_ID))
    dp.message.middleware(log.LogMiddleware(pool, dp.storage))
    dp.message.middleware(databaseAdd.DbAdd(pool))


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

    router.message.register(admin_reply_handlers.admin_reply, AdminChat.active)
    router.message.register(start.welcome, CommandStart())
    router.message.register(catch.catch_all)
    dp.include_router(router)
    
    return pool

async def main() -> None:
    pool = await bot_init()
    await reqs.createTables(pool)

    logger.info("Бот запущен и ожидает сообщений")
    
    try:
        await dp.start_polling(bot)
    finally:
        pool.close()
        await pool.wait_closed()
if __name__ == "__main__":
    logger.info("Запуск основного потока...")
    asyncio.run(main())
