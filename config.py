import os
import re
from typing import Optional, Set

import aiomysql
from dotenv import load_dotenv

from constants import DB_MAX_POOL_SIZE, DB_MIN_POOL_SIZE, DB_PORT
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# Загрузка конфигурации с проверкой
TOKEN: Optional[str] = os.getenv("TOKEN")
ADMINS_ID: str = os.getenv("ADMINS_ID", "")

DB_HOST: Optional[str] = os.getenv("DB_HOST")
DB_USER: Optional[str] = os.getenv("DB_USER")
DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
DB_DATABASE: Optional[str] = os.getenv("DB_DATABASE")

# Проверка обязательных переменных
required_vars = {
    "TOKEN": TOKEN,
    "ADMINS_ID": ADMINS_ID if ADMINS_ID else None,
    "DB_HOST": DB_HOST,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_DATABASE": DB_DATABASE
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    logger.error(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
    raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")


def get_admin_ids() -> Set[int]:
    """Возвращает множество ID админов, извлеченных из строки ADMINS_ID"""
    return {int(x) for x in re.findall(r"\d+", ADMINS_ID)}


async def create_pool():
    """Создание пула соединений с базой данных"""
    try:
        pool = await aiomysql.create_pool(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_DATABASE,
            port=DB_PORT,
            minsize=DB_MIN_POOL_SIZE,
            maxsize=DB_MAX_POOL_SIZE,
            autocommit=True
        )
        logger.info("Пул соединений с базой данных создан успешно")
        return pool
    except Exception as e:
        logger.error(f"Ошибка создания пула соединений с БД: {e}")
        raise
