from typing import Any, Awaitable, Callable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message

from sql import reqs

class DbAdd(BaseMiddleware):
    def __init__(self, pool):
        self.pool = pool

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and not data.get("is_admin", False):
            tgid = event.from_user.id
            username = event.from_user.username
            await reqs.addUser(self.pool, tgid, username)
        return await handler(event, data)