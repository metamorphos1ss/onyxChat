import texts

from aiogram import BaseMiddleware
from aiogram.types import Message

from constants import MESSAGE_DIRECTIONS
from sql import reqs
from utils import refresh
from utils.logger import get_logger

logger = get_logger(__name__)

class LogMiddleware(BaseMiddleware):
    def __init__(self, pool, storage):
        super().__init__()
        self.pool = pool
        self.storage = storage
    async def __call__(self, handler, event: Message, data: dict):
        if isinstance(event, Message) and not data.get("is_admin", False):
            tgid = event.from_user.id
            session_id = await reqs.get_session_id(self.pool, tgid)
            if session_id:
                logger.debug(f"Сообщение от пользователя {tgid} в сессии {session_id}")
                text = event.text or event.caption
                file_id = None
                if event.photo:
                    file_id = event.photo[-1].file_id
                elif event.document:
                    file_id = event.document.file_id
                elif event.voice:
                    file_id = event.voice.file_id

                await reqs.log_message(
                    self.pool,
                    tgid=tgid,
                    current_session_id=session_id,
                    direction=MESSAGE_DIRECTIONS["FROM_USER"],
                    text=text,
                    file_id=file_id
                )
                view = await reqs.get_session_view(self.pool, session_id)
                assigned = view.get("assigned_agent") if view else None
                if assigned:
                    await refresh.refresh_session_view(
                        bot=event.bot,
                        storage=self.storage,
                        pool=self.pool,
                        operator_id=assigned
                    )
            elif event.text == "/start":
                pass
            else:
                await event.answer(texts.TEXT_BEFORE_START)
        return await handler(event, data)