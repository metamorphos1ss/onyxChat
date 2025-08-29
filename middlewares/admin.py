import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminCheck(BaseMiddleware):
    def __init__(self, admins: set[int]):
        super().__init__()
        self.admins = admins
        logger.info(f"IDs are loaded and are: {self.admins}")

    async def __call__(
            self,
            handler,
            event: Message, 
            data: Dict[str, Any]
            ):
        from_user = getattr(event, "from_user", None)
        data["is_admin"] = bool(from_user and str(from_user.id) in self.admins)
        return await handler(event, data)