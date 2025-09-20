from typing import Any, Optional, Sequence

from constants import CLOSED_PER_PAGE, MESSAGE_DIRECTIONS, SESSION_STATUS, SESSION_TYPES
from sql import texts
from utils.logger import get_logger

logger = get_logger(__name__)

async def addUser(pool, tgid, username):
    """Добавляет пользователя в БД с обновлением last_message_at"""
    logger.debug(f"Добавление пользователя в БД: tgid={tgid}, username=@{username}")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.add_user, (tgid, username))
            await conn.commit()
    logger.debug(f"Пользователь {tgid} добавлен в БД")

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

async def count_sessions(pool, kind: str, agent_id: Optional[int] = None) -> int:
    """Подсчитывает количество сессий определенного типа"""
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
    """Получает список сессий определенного типа с информацией о пользователях"""
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
    """Подсчитывает количество закрытых сессий"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if only_mine:
                await cursor.execute(texts.count_closed_mine, (agent_id,))
            else:
                await cursor.execute(texts.count_closed_all)
            row = await cursor.fetchone()
            return int(row[0]) if row else 0
        
async def fetch_closed(pool, page: int, only_mine: bool, agent_id: int | None):
    """Получает список закрытых сессий с пагинацией"""
    offset = (page - 1) * CLOSED_PER_PAGE
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if only_mine:
                await cursor.execute(texts.fetch_closed_mine, (agent_id, CLOSED_PER_PAGE, offset))
            else:
                await cursor.execute(texts.fetch_closed_all, (CLOSED_PER_PAGE, offset))
            return await cursor.fetchall()

async def log_message(pool, tgid, current_session_id, direction, text, file_id):
    """Логирует сообщение в БД"""
    logger.debug(f"Логирование сообщения: tgid={tgid}, session_id={current_session_id}, direction={direction}")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.log_message, (tgid, current_session_id, direction, text, file_id))
            await conn.commit()
    logger.debug(f"Сообщение залогировано в БД")

async def find_open_session(pool, tgid: int) -> bool:
    """Проверяет, есть ли у пользователя открытая сессия"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.find_open_session, (tgid,))
            row = await cursor.fetchone()
            return bool(row)

async def ensure_open_session(pool, tgid) -> int:
    """Обеспечивает наличие открытой сессии для пользователя"""
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
    """Закрывает сессию агентом"""
    logger.info(f"Закрытие сессии {session_id} агентом {assigned_agent}")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.close_session, (session_id, assigned_agent))
            await conn.commit()
            logger.info(f"Сессия {session_id} закрыта агентом {assigned_agent}")
            return True

async def get_session_id(pool, tgid) -> Optional[int]:
    """Получает ID открытой сессии пользователя"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.find_open_session, (tgid,))
            row = await cursor.fetchone()
            await conn.commit()
            return int(row[0]) if row and row[0] is not None else None
        
async def get_session_view(pool, session_id: int) -> Optional[dict]:
    """Получает информацию о сессии"""
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
    """Получает сообщения сессии"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.fetch_session_messages, (tgid, session_id))
            rows = await cursor.fetchall()
    return rows

async def get_message_file(pool, msg_id: int) -> tuple[str | None, int | None]:
    """Получает file_id и session_id сообщения"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.get_message_file, (msg_id,))
            row = await cursor.fetchone()
            return (row[0], row[1]) if row else (None, None)

async def assign_session(pool, session_id: int, operator_id: int) -> bool:
    """Назначает сессию оператору"""
    logger.info(f"Назначение сессии {session_id} оператору {operator_id}")
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.assign_session, (operator_id, session_id, operator_id))
            changed = cursor.rowcount
        await conn.commit()
    success = changed == 1
    logger.info(f"Назначение сессии {session_id} оператору {operator_id}: {'успешно' if success else 'неудачно'}")
    return success