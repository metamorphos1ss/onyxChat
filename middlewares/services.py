"""
Middleware для передачи сервисов в обработчики
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from services import ServiceContainer
from utils.logger import get_logger

logger = get_logger(__name__)


class ServicesMiddleware(BaseMiddleware):
    """Middleware для передачи сервисов в обработчики"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """
        Добавляет сервисы в контекст обработчика
        
        Args:
            handler: Обработчик события
            event: Событие (Message или CallbackQuery)
            data: Данные контекста
            
        Returns:
            Результат выполнения обработчика
        """
        # Получаем контейнер сервисов из диспетчера
        services = data.get("services")
        if not services:
            logger.warning("Контейнер сервисов не найден в контексте")
            return await handler(event, data)
        
        # Добавляем сервисы в контекст
        data["services"] = services
        logger.debug("Сервисы добавлены в контекст обработчика")
        
        return await handler(event, data)
