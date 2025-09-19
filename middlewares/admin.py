from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from utils.logger import get_logger

logger = get_logger(__name__)

class AdminCheck(BaseMiddleware):
    def __init__(self, admins: set[int]):
        super().__init__()
        self.admins = admins
        logger.info(f"Загружены ID админов: {self.admins}")

    async def __call__(
            self,
            handler,
            event: Message, 
            data: Dict[str, Any]
            ):
        from_user = getattr(event, "from_user", None)
        user_id = from_user.id if from_user else None
        is_admin = bool(from_user and str(from_user.id) in self.admins)
        data["is_admin"] = is_admin
        
        if user_id:
            logger.debug(f"Проверка прав пользователя {user_id}: is_admin={is_admin}")
        
        return await handler(event, data)