"""
Сервис для работы с пользователями
"""
from typing import Optional
from .base_service import BaseService
from sql import texts


class UserService(BaseService):
    """Сервис для управления пользователями"""
    
    async def add_user(self, tgid: int, username: Optional[str]) -> None:
        """
        Добавляет пользователя в БД с обновлением last_message_at
        
        Args:
            tgid: Telegram ID пользователя
            username: Имя пользователя в Telegram
        """
        self.logger.debug(f"Добавление пользователя в БД: tgid={tgid}, username=@{username}")
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(texts.add_user, (tgid, username))
                    await conn.commit()
            self.logger.debug(f"Пользователь {tgid} добавлен в БД")
        except Exception as e:
            self.logger.error(f"Ошибка добавления пользователя {tgid}: {e}")
            raise
    
    async def get_user_session_id(self, tgid: int) -> Optional[int]:
        """
        Получает ID открытой сессии пользователя
        
        Args:
            tgid: Telegram ID пользователя
            
        Returns:
            ID открытой сессии или None
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(texts.find_open_session, (tgid,))
                    row = await cursor.fetchone()
                    return int(row[0]) if row and row[0] is not None else None
        except Exception as e:
            self.logger.error(f"Ошибка получения сессии пользователя {tgid}: {e}")
            raise
    
    async def has_open_session(self, tgid: int) -> bool:
        """
        Проверяет, есть ли у пользователя открытая сессия
        
        Args:
            tgid: Telegram ID пользователя
            
        Returns:
            True если есть открытая сессия, False иначе
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(texts.find_open_session, (tgid,))
                    row = await cursor.fetchone()
                    return bool(row)
        except Exception as e:
            self.logger.error(f"Ошибка проверки открытой сессии для пользователя {tgid}: {e}")
            raise
    
    async def update_user_session(self, tgid: int, session_id: int) -> None:
        """
        Обновляет текущую сессию пользователя
        
        Args:
            tgid: Telegram ID пользователя
            session_id: ID сессии
        """
        self.logger.debug(f"Обновление сессии пользователя {tgid} на {session_id}")
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(texts.bind_current_session_to_user, (session_id, tgid))
                    await conn.commit()
            self.logger.debug(f"Сессия {session_id} привязана к пользователю {tgid}")
        except Exception as e:
            self.logger.error(f"Ошибка обновления сессии пользователя {tgid}: {e}")
            raise
