"""
Устаревшие функции для работы с БД.
Большинство функций перенесены в сервисы.
Оставлены только функции, которые еще используются напрямую.
"""
from typing import Any, Optional, Sequence

from constants import CLOSED_PER_PAGE, MESSAGE_DIRECTIONS, SESSION_STATUS, SESSION_TYPES
from sql import texts
from utils.logger import get_logger

logger = get_logger(__name__)

async def createTables(pool):
    """Создает все необходимые таблицы в БД"""
    logger.info("Создание таблиц в БД...")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Выполняем все запросы в одной транзакции
            tables = [
                ("users", texts.create_users_table),
                ("orders", texts.create_orders_table),
                ("messages", texts.create_messages_table),
                ("sessions", texts.create_sessions_table)
            ]
            
            for table_name, create_sql in tables:
                logger.debug(f"Создание таблицы {table_name}")
                await cursor.execute(create_sql)
            
            await conn.commit()
    logger.info("Все таблицы созданы/проверены в БД")

# УСТАРЕВШИЕ ФУНКЦИИ - НЕ ИСПОЛЬЗУЙТЕ В НОВОМ КОДЕ
# Используйте соответствующие сервисы вместо этих функций

async def addUser(pool, tgid, username):
    """УСТАРЕЛО: Используйте UserService.add_user()"""
    logger.warning("Использование устаревшей функции addUser. Используйте UserService.add_user()")
    logger.debug(f"Добавление пользователя в БД: tgid={tgid}, username=@{username}")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.add_user, (tgid, username))
            await conn.commit()
    logger.debug(f"Пользователь {tgid} добавлен в БД")

async def count_sessions(pool, kind: str, agent_id: Optional[int] = None) -> int:
    """УСТАРЕЛО: Используйте SessionService.count_sessions()"""
    logger.warning("Использование устаревшей функции count_sessions. Используйте SessionService.count_sessions()")
    if kind == SESSION_TYPES["TO_SERVE"]:
        where_sql, params = f"s.status='{SESSION_STATUS['OPEN']}' AND s.assigned_agent IS NULL", ()
    elif kind == SESSION_TYPES["PROCESSING_MINE"]:
        where_sql, params = f"s.status='{SESSION_STATUS['OPEN']}' AND s.assigned_agent = %s", (agent_id,)
    elif kind == SESSION_TYPES["PROCESSING"]:
        where_sql, params = f"s.status='{SESSION_STATUS['OPEN']}' AND s.assigned_agent IS NOT NULL AND s.assigned_agent <> %s", (agent_id,)
    else:
        raise ValueError(f"kind must be one of: {list(SESSION_TYPES.values())}")

    sql = f"SELECT COUNT(*) FROM sessions s WHERE {where_sql}"
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, params)
            row = await cursor.fetchone()
            return int(row[0]) if row else 0

async def fetch_sessions(pool, kind: str, agent_id: Optional[int] = None) -> Sequence[tuple[Any, ...]]:
    """УСТАРЕЛО: Используйте SessionService.fetch_sessions()"""
    logger.warning("Использование устаревшей функции fetch_sessions. Используйте SessionService.fetch_sessions()")
    if kind == SESSION_TYPES["TO_SERVE"]:
        where_sql, params = f"s.status='{SESSION_STATUS['OPEN']}' AND s.assigned_agent IS NULL", ()
    elif kind == SESSION_TYPES["PROCESSING_MINE"]:
        where_sql, params = f"s.status='{SESSION_STATUS['OPEN']}' AND s.assigned_agent = %s", (agent_id,)
    elif kind == SESSION_TYPES["PROCESSING"]:
        where_sql, params = f"s.status='{SESSION_STATUS['OPEN']}' AND s.assigned_agent IS NOT NULL AND s.assigned_agent <> %s", (agent_id,)
    else:
        raise ValueError(f"kind must be one of: {list(SESSION_TYPES.values())}")

    sql = f"""
        SELECT s.id AS session_id,
               s.tgid AS tgid,
               u.username
        FROM sessions s
        JOIN users u ON u.tgid = s.tgid
        WHERE {where_sql}
        ORDER BY COALESCE(u.last_message_at, s.opened_at) DESC, s.id DESC
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, params)
            return await cursor.fetchall()

async def count_closed(pool, only_mine: bool, agent_id: int | None) -> int:
    """УСТАРЕЛО: Используйте SessionService.count_closed_sessions()"""
    logger.warning("Использование устаревшей функции count_closed. Используйте SessionService.count_closed_sessions()")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if only_mine:
                await cursor.execute(texts.count_closed_mine, (agent_id,))
            else:
                await cursor.execute(texts.count_closed_all)
            row = await cursor.fetchone()
            return int(row[0]) if row else 0
        
async def fetch_closed(pool, page: int, only_mine: bool, agent_id: int | None):
    """УСТАРЕЛО: Используйте SessionService.fetch_closed_sessions()"""
    logger.warning("Использование устаревшей функции fetch_closed. Используйте SessionService.fetch_closed_sessions()")
    offset = (page - 1) * CLOSED_PER_PAGE
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if only_mine:
                await cursor.execute(texts.fetch_closed_mine, (agent_id, CLOSED_PER_PAGE, offset))
            else:
                await cursor.execute(texts.fetch_closed_all, (CLOSED_PER_PAGE, offset))
            return await cursor.fetchall()

async def log_message(pool, tgid, current_session_id, direction, text, file_id):
    """УСТАРЕЛО: Используйте MessageService.log_message()"""
    logger.warning("Использование устаревшей функции log_message. Используйте MessageService.log_message()")
    logger.debug(f"Логирование сообщения: tgid={tgid}, session_id={current_session_id}, direction={direction}")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.log_message, (tgid, current_session_id, direction, text, file_id))
            await conn.commit()
    logger.debug(f"Сообщение залогировано в БД")

async def find_open_session(pool, tgid: int) -> bool:
    """УСТАРЕЛО: Используйте UserService.has_open_session()"""
    logger.warning("Использование устаревшей функции find_open_session. Используйте UserService.has_open_session()")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.find_open_session, (tgid,))
            row = await cursor.fetchone()
            return bool(row)

async def ensure_open_session(pool, tgid) -> int:
    """УСТАРЕЛО: Используйте SessionService.ensure_open_session()"""
    logger.warning("Использование устаревшей функции ensure_open_session. Используйте SessionService.ensure_open_session()")
    logger.debug(f"Обеспечение открытой сессии для пользователя {tgid}")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.find_open_session, (tgid,))
            row = await cursor.fetchone()
            
            if row and row[0]:
                session_id = int(row[0])
                logger.debug(f"Найдена существующая сессия {session_id} для пользователя {tgid}")
            else:
                await cursor.execute(texts.openCreate_session, (tgid,))
                session_id = int(cursor.lastrowid)
                logger.info(f"Создана новая сессия {session_id} для пользователя {tgid}")
            await cursor.execute(texts.bind_current_session_to_user, (session_id, tgid))
        await conn.commit()
    logger.debug(f"Сессия {session_id} привязана к пользователю {tgid}")
    return session_id

async def close_session(pool, session_id, assigned_agent) -> bool:
    """УСТАРЕЛО: Используйте SessionService.close_session()"""
    logger.warning("Использование устаревшей функции close_session. Используйте SessionService.close_session()")
    logger.info(f"Закрытие сессии {session_id} агентом {assigned_agent}")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.close_session, (session_id, assigned_agent))
            await conn.commit()
            logger.info(f"Сессия {session_id} закрыта агентом {assigned_agent}")
            return True

async def get_session_id(pool, tgid) -> Optional[int]:
    """УСТАРЕЛО: Используйте UserService.get_user_session_id()"""
    logger.warning("Использование устаревшей функции get_session_id. Используйте UserService.get_user_session_id()")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.find_open_session, (tgid,))
            row = await cursor.fetchone()
            await conn.commit()
            return int(row[0]) if row and row[0] is not None else None
        
async def get_session_view(pool, session_id: int) -> Optional[dict]:
    """УСТАРЕЛО: Используйте SessionService.get_session_info()"""
    logger.warning("Использование устаревшей функции get_session_view. Используйте SessionService.get_session_info()")
    async with pool.acquire() as conn:
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

async def fetch_session_messages(pool, tgid, session_id: int):
    """УСТАРЕЛО: Используйте MessageService.get_session_messages()"""
    logger.warning("Использование устаревшей функции fetch_session_messages. Используйте MessageService.get_session_messages()")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.fetch_session_messages, (tgid, session_id))
            rows = await cursor.fetchall()
    return rows

async def get_message_file(pool, msg_id: int) -> tuple[str | None, int | None]:
    """УСТАРЕЛО: Используйте MessageService.get_message_file()"""
    logger.warning("Использование устаревшей функции get_message_file. Используйте MessageService.get_message_file()")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.get_message_file, (msg_id,))
            row = await cursor.fetchone()
            return (row[0], row[1]) if row else (None, None)

async def assign_session(pool, session_id: int, operator_id: int) -> bool:
    """УСТАРЕЛО: Используйте SessionService.assign_session()"""
    logger.warning("Использование устаревшей функции assign_session. Используйте SessionService.assign_session()")
    logger.info(f"Назначение сессии {session_id} оператору {operator_id}")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.assign_session, (operator_id, session_id, operator_id))
            changed = cursor.rowcount
        await conn.commit()
    success = changed == 1
    logger.info(f"Назначение сессии {session_id} оператору {operator_id}: {'успешно' if success else 'неудачно'}")
    return success