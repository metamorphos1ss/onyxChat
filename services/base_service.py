"""
Базовый класс для всех сервисов
"""
from abc import ABC
from typing import Any, Optional
import aiomysql
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseService(ABC):
    """Базовый класс для всех сервисов"""
    
    def __init__(self, pool: aiomysql.Pool):
        """
        Инициализация сервиса с пулом соединений БД
        
        Args:
            pool: Пул соединений с базой данных
        """
        self.pool = pool
        self.logger = get_logger(self.__class__.__name__)
    
    async def _execute_query(self, query: str, params: tuple = ()) -> Any:
        """
        Выполняет SQL запрос с обработкой ошибок
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            
        Returns:
            Результат выполнения запроса
            
        Raises:
            Exception: При ошибке выполнения запроса
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params)
                    return await cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Ошибка выполнения запроса: {query}, params: {params}, error: {e}")
            # Добавляем контекстную информацию об ошибке
            if "connection" in str(e).lower():
                self.logger.error("Проблема с подключением к базе данных")
            elif "syntax" in str(e).lower():
                self.logger.error("Синтаксическая ошибка в SQL запросе")
            elif "duplicate" in str(e).lower():
                self.logger.error("Попытка создать дублирующуюся запись")
            raise
    
    async def _execute_insert(self, query: str, params: tuple = ()) -> int:
        """
        Выполняет INSERT запрос и возвращает ID вставленной записи
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            
        Returns:
            ID вставленной записи
            
        Raises:
            Exception: При ошибке выполнения запроса
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params)
                    await conn.commit()
                    return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Ошибка выполнения INSERT: {query}, params: {params}, error: {e}")
            # Добавляем контекстную информацию об ошибке
            if "duplicate" in str(e).lower():
                self.logger.error("Попытка создать дублирующуюся запись")
            elif "foreign key" in str(e).lower():
                self.logger.error("Нарушение внешнего ключа")
            elif "not null" in str(e).lower():
                self.logger.error("Попытка вставить NULL в поле, которое не может быть NULL")
            raise
    
    async def _execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Выполняет UPDATE запрос и возвращает количество измененных строк
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            
        Returns:
            Количество измененных строк
            
        Raises:
            Exception: При ошибке выполнения запроса
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params)
                    await conn.commit()
                    return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Ошибка выполнения UPDATE: {query}, params: {params}, error: {e}")
            # Добавляем контекстную информацию об ошибке
            if "foreign key" in str(e).lower():
                self.logger.error("Нарушение внешнего ключа при обновлении")
            elif "not null" in str(e).lower():
                self.logger.error("Попытка установить NULL в поле, которое не может быть NULL")
            raise
