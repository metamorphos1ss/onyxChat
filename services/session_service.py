"""
Сервис для управления сессиями
"""
from typing import Optional, Sequence, Any
from .base_service import BaseService
from sql import texts
from constants import SESSION_TYPES, SESSION_STATUS, CLOSED_PER_PAGE


class SessionService(BaseService):
    """Сервис для управления сессиями чатов"""
    
    async def create_session(self, tgid: int) -> int:
        """
        Создает новую сессию для пользователя
        
        Args:
            tgid: Telegram ID пользователя
            
        Returns:
            ID созданной сессии
        """
        self.logger.debug(f"Создание новой сессии для пользователя {tgid}")
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(texts.openCreate_session, (tgid,))
                    session_id = int(cursor.lastrowid)
                    await conn.commit()
            self.logger.info(f"Создана новая сессия {session_id} для пользователя {tgid}")
            return session_id
        except Exception as e:
            self.logger.error(f"Ошибка создания сессии для пользователя {tgid}: {e}")
            raise
    
    async def ensure_open_session(self, tgid: int) -> int:
        """
        Обеспечивает наличие открытой сессии для пользователя
        
        Args:
            tgid: Telegram ID пользователя
            
        Returns:
            ID открытой сессии
        """
        self.logger.debug(f"Обеспечение открытой сессии для пользователя {tgid}")
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Проверяем существующую сессию
                    await cursor.execute(texts.find_open_session, (tgid,))
                    row = await cursor.fetchone()
                    
                    if row and row[0]:
                        session_id = int(row[0])
                        self.logger.debug(f"Найдена существующая сессия {session_id} для пользователя {tgid}")
                    else:
                        # Создаем новую сессию
                        await cursor.execute(texts.openCreate_session, (tgid,))
                        session_id = int(cursor.lastrowid)
                        self.logger.info(f"Создана новая сессия {session_id} для пользователя {tgid}")
                    
                    # Привязываем сессию к пользователю
                    await cursor.execute(texts.bind_current_session_to_user, (session_id, tgid))
                    await conn.commit()
            
            self.logger.debug(f"Сессия {session_id} привязана к пользователю {tgid}")
            return session_id
        except Exception as e:
            self.logger.error(f"Ошибка обеспечения сессии для пользователя {tgid}: {e}")
            raise
    
    async def get_session_info(self, session_id: int) -> Optional[dict]:
        """
        Получает информацию о сессии
        
        Args:
            session_id: ID сессии
            
        Returns:
            Словарь с информацией о сессии или None
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(texts.get_session_view, (session_id,))
                    row = await cursor.fetchone()
            
            if not row:
                return None
            
            return {
                "session_id": int(row[0]),
                "tgid": int(row[1]),
                "username": row[2],
                "assigned_agent": (int(row[3]) if row[3] is not None else None),
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о сессии {session_id}: {e}")
            raise
    
    async def assign_session(self, session_id: int, agent_id: int) -> bool:
        """
        Назначает сессию оператору
        
        Args:
            session_id: ID сессии
            agent_id: ID оператора
            
        Returns:
            True если назначение успешно, False иначе
        """
        self.logger.info(f"Назначение сессии {session_id} оператору {agent_id}")
        
        try:
            changed = await self._execute_update(
                texts.assign_session, 
                (agent_id, session_id, agent_id)
            )
            success = changed == 1
            self.logger.info(f"Назначение сессии {session_id} оператору {agent_id}: {'успешно' if success else 'неудачно'}")
            return success
        except Exception as e:
            self.logger.error(f"Ошибка назначения сессии {session_id} оператору {agent_id}: {e}")
            raise
    
    async def close_session(self, session_id: int, agent_id: int) -> bool:
        """
        Закрывает сессию агентом
        
        Args:
            session_id: ID сессии
            agent_id: ID агента
            
        Returns:
            True если закрытие успешно, False иначе
        """
        self.logger.info(f"Закрытие сессии {session_id} агентом {agent_id}")
        
        try:
            changed = await self._execute_update(
                texts.close_session, 
                (session_id, agent_id)
            )
            success = changed == 1
            if success:
                self.logger.info(f"Сессия {session_id} закрыта агентом {agent_id}")
            else:
                self.logger.warning(f"Не удалось закрыть сессию {session_id} агентом {agent_id}")
            return success
        except Exception as e:
            self.logger.error(f"Ошибка закрытия сессии {session_id} агентом {agent_id}: {e}")
            raise
    
    async def count_sessions(self, kind: str, agent_id: Optional[int] = None) -> int:
        """
        Подсчитывает количество сессий определенного типа
        
        Args:
            kind: Тип сессии (toServe, processing_mine, processing)
            agent_id: ID агента (для processing_mine и processing)
            
        Returns:
            Количество сессий
        """
        if kind == SESSION_TYPES["TO_SERVE"]:
            # Оптимизированный запрос для ожидающих сессий
            sql = "SELECT COUNT(*) FROM sessions s WHERE s.status = %s AND s.assigned_agent IS NULL"
            params = (SESSION_STATUS['OPEN'],)
        elif kind == SESSION_TYPES["PROCESSING_MINE"]:
            # Оптимизированный запрос для моих сессий
            sql = "SELECT COUNT(*) FROM sessions s WHERE s.status = %s AND s.assigned_agent = %s"
            params = (SESSION_STATUS['OPEN'], agent_id)
        elif kind == SESSION_TYPES["PROCESSING"]:
            # Оптимизированный запрос для сессий других агентов
            sql = "SELECT COUNT(*) FROM sessions s WHERE s.status = %s AND s.assigned_agent IS NOT NULL AND s.assigned_agent != %s"
            params = (SESSION_STATUS['OPEN'], agent_id)
        else:
            raise ValueError(f"kind must be one of: {list(SESSION_TYPES.values())}")
        
        try:
            rows = await self._execute_query(sql, params)
            return int(rows[0][0]) if rows else 0
        except Exception as e:
            self.logger.error(f"Ошибка подсчета сессий типа {kind}: {e}")
            raise
    
    async def fetch_sessions(self, kind: str, agent_id: Optional[int] = None) -> Sequence[tuple[Any, ...]]:
        """
        Получает список сессий определенного типа
        
        Args:
            kind: Тип сессии
            agent_id: ID агента
            
        Returns:
            Список сессий
        """
        if kind == SESSION_TYPES["TO_SERVE"]:
            # Оптимизированный запрос для ожидающих сессий
            sql = """
                SELECT s.id AS session_id,
                       s.tgid AS tgid,
                       u.username
                FROM sessions s
                INNER JOIN users u ON u.tgid = s.tgid
                WHERE s.status = %s AND s.assigned_agent IS NULL
                ORDER BY COALESCE(u.last_message_at, s.opened_at) DESC, s.id DESC
            """
            params = (SESSION_STATUS['OPEN'],)
        elif kind == SESSION_TYPES["PROCESSING_MINE"]:
            # Оптимизированный запрос для моих сессий
            sql = """
                SELECT s.id AS session_id,
                       s.tgid AS tgid,
                       u.username
                FROM sessions s
                INNER JOIN users u ON u.tgid = s.tgid
                WHERE s.status = %s AND s.assigned_agent = %s
                ORDER BY COALESCE(u.last_message_at, s.opened_at) DESC, s.id DESC
            """
            params = (SESSION_STATUS['OPEN'], agent_id)
        elif kind == SESSION_TYPES["PROCESSING"]:
            # Оптимизированный запрос для сессий других агентов
            sql = """
                SELECT s.id AS session_id,
                       s.tgid AS tgid,
                       u.username
                FROM sessions s
                INNER JOIN users u ON u.tgid = s.tgid
                WHERE s.status = %s AND s.assigned_agent IS NOT NULL AND s.assigned_agent != %s
                ORDER BY COALESCE(u.last_message_at, s.opened_at) DESC, s.id DESC
            """
            params = (SESSION_STATUS['OPEN'], agent_id)
        else:
            raise ValueError(f"kind must be one of: {list(SESSION_TYPES.values())}")
        
        try:
            return await self._execute_query(sql, params)
        except Exception as e:
            self.logger.error(f"Ошибка получения сессий типа {kind}: {e}")
            raise
    
    async def count_closed_sessions(self, only_mine: bool, agent_id: Optional[int]) -> int:
        """
        Подсчитывает количество закрытых сессий
        
        Args:
            only_mine: Только мои сессии
            agent_id: ID агента
            
        Returns:
            Количество закрытых сессий
        """
        try:
            if only_mine:
                rows = await self._execute_query(texts.count_closed_mine, (agent_id,))
            else:
                rows = await self._execute_query(texts.count_closed_all)
            return int(rows[0][0]) if rows else 0
        except Exception as e:
            self.logger.error(f"Ошибка подсчета закрытых сессий: {e}")
            raise
    
    async def fetch_closed_sessions(self, page: int, only_mine: bool, agent_id: Optional[int]) -> Sequence[tuple[Any, ...]]:
        """
        Получает список закрытых сессий с пагинацией
        
        Args:
            page: Номер страницы
            only_mine: Только мои сессии
            agent_id: ID агента
            
        Returns:
            Список закрытых сессий
        """
        offset = (page - 1) * CLOSED_PER_PAGE
        
        try:
            if only_mine:
                return await self._execute_query(texts.fetch_closed_mine, (agent_id, CLOSED_PER_PAGE, offset))
            else:
                return await self._execute_query(texts.fetch_closed_all, (CLOSED_PER_PAGE, offset))
        except Exception as e:
            self.logger.error(f"Ошибка получения закрытых сессий: {e}")
            raise
