"""
Сервис для работы с сообщениями
"""
from typing import Optional, Sequence, Any
from datetime import datetime
from .base_service import BaseService
from sql import message_sql
from constants import MESSAGE_DIRECTIONS


class MessageService(BaseService):
    """Сервис для управления сообщениями"""
    
    async def log_message(self, tgid: int, session_id: int, direction: str, text: Optional[str], file_id: Optional[str]) -> None:
        """
        Логирует сообщение в БД
        
        Args:
            tgid: Telegram ID пользователя
            session_id: ID сессии
            direction: Направление сообщения (fromUser/fromAgent)
            text: Текст сообщения
            file_id: ID файла (если есть)
        """
        self.logger.debug(f"Логирование сообщения: tgid={tgid}, session_id={session_id}, direction={direction}")
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(message_sql.log_message, (tgid, session_id, direction, text, file_id))
                    await conn.commit()
            self.logger.debug(f"Сообщение залогировано в БД")
        except Exception as e:
            self.logger.error(f"Ошибка логирования сообщения: {e}")
            raise
    
    async def get_session_messages(self, tgid: int, session_id: int) -> Sequence[tuple[Any, ...]]:
        """
        Получает сообщения сессии
        
        Args:
            tgid: Telegram ID пользователя
            session_id: ID сессии
            
        Returns:
            Список сообщений
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(message_sql.fetch_session_messages, (tgid, session_id))
                    return await cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Ошибка получения сообщений сессии {session_id}: {e}")
            raise
    
    async def get_message_file(self, message_id: int) -> tuple[Optional[str], Optional[int]]:
        """
        Получает file_id и session_id сообщения
        
        Args:
            message_id: ID сообщения
            
        Returns:
            Кортеж (file_id, session_id)
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(message_sql.get_message_file, (message_id,))
                    row = await cursor.fetchone()
                    return (row[0], row[1]) if row else (None, None)
        except Exception as e:
            self.logger.error(f"Ошибка получения файла сообщения {message_id}: {e}")
            raise
    
    async def log_user_message(self, tgid: int, session_id: int, text: Optional[str], file_id: Optional[str]) -> None:
        """
        Логирует сообщение от пользователя
        
        Args:
            tgid: Telegram ID пользователя
            session_id: ID сессии
            text: Текст сообщения
            file_id: ID файла
        """
        await self.log_message(
            tgid=tgid,
            session_id=session_id,
            direction=MESSAGE_DIRECTIONS["FROM_USER"],
            text=text,
            file_id=file_id
        )
    
    async def log_agent_message(self, tgid: int, session_id: int, text: Optional[str], file_id: Optional[str]) -> None:
        """
        Логирует сообщение от агента
        
        Args:
            tgid: Telegram ID пользователя
            session_id: ID сессии
            text: Текст сообщения
            file_id: ID файла
        """
        await self.log_message(
            tgid=tgid,
            session_id=session_id,
            direction=MESSAGE_DIRECTIONS["FROM_AGENT"],
            text=text,
            file_id=file_id
        )
