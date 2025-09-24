import texts

from aiogram import BaseMiddleware
from aiogram.types import Message

from constants import MESSAGE_DIRECTIONS
from services import ServiceContainer
from utils import refresh
from utils.logger import get_logger

logger = get_logger(__name__)

class LogMiddleware(BaseMiddleware):
    def __init__(self, services: ServiceContainer, storage):
        super().__init__()
        self.services = services
        self.storage = storage
    async def __call__(self, handler, event: Message, data: dict):
        if isinstance(event, Message) and not data.get("is_admin", False):
            tgid = event.from_user.id
            
            user_service = self.services.user_service
            message_service = self.services.message_service
            session_service = self.services.session_service
            
            session_id = await user_service.get_user_session_id(tgid)
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

                await message_service.log_user_message(
                    tgid=tgid,
                    session_id=session_id,
                    text=text,
                    file_id=file_id
                )
                view = await session_service.get_session_info(session_id)
                assigned = view.get("assigned_agent") if view else None
                if assigned:
                    await refresh.refresh_session_view(
                        bot=event.bot,
                        storage=self.storage,
                        services=self.services,
                        operator_id=assigned
                    )
            elif event.text == "/start":
                pass
            else:
                await event.answer(texts.TEXT_BEFORE_START)
        return await handler(event, data)