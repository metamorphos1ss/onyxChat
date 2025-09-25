"""
Сервис для работы с базой данных
"""
from .base_service import BaseService
from sql import database_sql
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseService(BaseService):
    """Сервис для управления базой данных"""
    
    async def create_tables(self) -> None:
        """
        Создает все необходимые таблицы в БД
        """
        logger.info("Создание таблиц в БД...")
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Выполняем все запросы в одной транзакции
                    tables = [
                        ("users", database_sql.create_users_table),
                        ("statistics", database_sql.create_statistics_table),
                        ("messages", database_sql.create_messages_table),
                        ("sessions", database_sql.create_sessions_table)
                    ]
                    
                    for table_name, create_sql in tables:
                        logger.debug(f"Создание таблицы {table_name}")
                        try:
                            await cursor.execute(create_sql)
                            logger.info(f"Таблица {table_name} создана успешно")
                        except Exception as e:
                            # Если таблица уже существует, это нормально
                            if "already exists" in str(e).lower():
                                logger.info(f"Таблица {table_name} уже существует")
                            else:
                                logger.error(f"Ошибка создания таблицы {table_name}: {e}")
                                raise
                    
                    await conn.commit()
            logger.info("Все таблицы созданы/проверены в БД")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise
    
    async def check_database_connection(self) -> bool:
        """
        Проверяет подключение к базе данных
        
        Returns:
            True если подключение успешно, False иначе
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    return result is not None
        except Exception as e:
            logger.error(f"Ошибка проверки подключения к БД: {e}")
            return False
    
    async def get_database_info(self) -> dict:
        """
        Получает информацию о базе данных
        
        Returns:
            Словарь с информацией о БД
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Получаем версию MySQL
                    await cursor.execute("SELECT VERSION()")
                    version = await cursor.fetchone()
                    
                    # Получаем размер базы данных
                    await cursor.execute("""
                        SELECT 
                            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size in MB'
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE()
                    """)
                    size = await cursor.fetchone()
                    
                    return {
                        "version": version[0] if version else "Unknown",
                        "size_mb": size[0] if size else 0
                    }
        except Exception as e:
            logger.error(f"Ошибка получения информации о БД: {e}")
            return {"version": "Unknown", "size_mb": 0}
