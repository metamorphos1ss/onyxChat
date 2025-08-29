from typing import Optional, Sequence, Any
from sql import texts
import logging

CLOSED_PER_PAGE = 10

async def addUser(pool, tgid, username):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.add_user, (tgid, username))
            await conn.commit()

async def createTables(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.create_users_table)
            await cursor.execute(texts.create_orders_table)
            await cursor.execute(texts.create_messages_table)
            await cursor.execute(texts.create_sessions_table)
            await conn.commit()

async def count_sessions(pool, kind: str, agent_id: Optional[int] = None) -> int:
    if kind == "toServe":
        where_sql, params = "s.status='open' AND s.assigned_agent IS NULL", ()
    elif kind == "processing_mine":
        where_sql, params = "s.status='open' AND s.assigned_agent = %s", (agent_id,)
    elif kind == "processing":
        where_sql, params = "s.status='open' AND s.assigned_agent IS NOT NULL AND s.assigned_agent <> %s", (agent_id,)
    else:
        raise ValueError("kind must be one of: toServe, processing_mine, processing")

    sql = f"SELECT COUNT(*) FROM sessions s WHERE {where_sql}"
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, params)
            row = await cursor.fetchone()
            return int(row[0]) if row else 0

async def fetch_sessions(pool, kind: str, agent_id: Optional[int] = None) -> Sequence[tuple[Any, ...]]:
    if kind == "toServe":
        where_sql, params = "s.status='open' AND s.assigned_agent IS NULL", ()
    elif kind == "processing_mine":
        where_sql, params = "s.status='open' AND s.assigned_agent = %s", (agent_id,)
    elif kind == "processing":
        where_sql, params = "s.status='open' AND s.assigned_agent IS NOT NULL AND s.assigned_agent <> %s", (agent_id,)
    else:
        raise ValueError("kind must be one of: toServe, processing_mine, processing")

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
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if only_mine:
                await cursor.execute(texts.count_closed_mine, (agent_id,))
            else:
                await cursor.execute(texts.count_closed_all)
            row = await cursor.fetchone()
            return int(row[0]) if row else 0
        
async def fetch_closed(pool, page: int, only_mine: bool, agent_id: int | None):
    limit = 10
    offset = (page - 1) * CLOSED_PER_PAGE
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if only_mine:
                await cursor.execute(texts.fetch_closed_mine, (agent_id, limit, offset))
            else:
                await cursor.execute(texts.fetch_closed_all, (limit, offset))
            return await cursor.fetchall()

async def log_message(pool, tgid, current_session_id, direction, text, file_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.log_message, (tgid, current_session_id, direction, text, file_id))
            await conn.commit()

async def find_open_session(pool, tgid: int) -> bool:
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.find_open_session, (tgid,))
            row = await cursor.fetchone()
            return bool(row)

async def ensure_open_session(pool, tgid) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.find_open_session, (tgid,))
            row = await cursor.fetchone()
            if row and row[0]:
                session_id = int(row[0])
            else:
                await cursor.execute(texts.openCreate_session, (tgid,))
                session_id = int(cursor.lastrowid)
            await cursor.execute(texts.bind_current_session_to_user, (session_id, tgid))
        await conn.commit()
    return session_id

async def close_session(pool, session_id, assigned_agent) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.close_session, (session_id, assigned_agent))
            await conn.commit()
            return True

async def get_session_id(pool, tgid) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.find_open_session, (tgid,))
            row = await cursor.fetchone()
            await conn.commit()
            return int(row[0]) if row and row[0] is not None else None
        
async def get_session_view(pool, session_id: int) -> Optional[dict]:
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
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.fetch_session_messages, (tgid, session_id))
            rows = await cursor.fetchall()
    return rows

async def get_message_file(pool, msg_id: int) -> tuple[str | None, int | None]:
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.get_message_file, (msg_id,))
            row = await cursor.fetchone()
            return (row[0], row[1]) if row else (None, None)

async def assign_session(pool, session_id: int, operator_id: int) -> bool:
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(texts.assign_session, (operator_id, session_id, operator_id))
            changed = cursor.rowcount
        await conn.commit()
    return changed == 1