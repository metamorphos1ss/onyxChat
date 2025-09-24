from typing import Any, Awaitable, Callable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message

from services import ServiceContainer
from utils.logger import get_logger

logger = get_logger(__name__)

class DbAdd(BaseMiddleware):
    def __init__(self, services: ServiceContainer):
        self.services = services

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and not data.get("is_admin", False):
            tgid = event.from_user.id
            username = event.from_user.username
            logger.debug(f"Добавление пользователя в БД: tgid={tgid}, username=@{username}")
            
            user_service = self.services.user_service
            await user_service.add_user(tgid, username)
            logger.debug(f"Пользователь {tgid} добавлен в БД")
        return await handler(event, data)