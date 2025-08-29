import aiomysql
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN=os.getenv("TOKEN")
ADMINS_ID=os.getenv("ADMINS_ID")

DB_HOST=os.getenv("DB_HOST")
DB_USER=os.getenv("DB_USER")
DB_PASSWORD=os.getenv("DB_PASSWORD")
DB_DATABASE=os.getenv("DB_DATABASE")


async def create_pool():
    pool = await aiomysql.create_pool(
        host=DB_HOST,
        user=DB_USER,
        password =DB_PASSWORD,
        db=DB_DATABASE,
        port=3306,
        minsize=5,
        maxsize=10,
        autocommit=True
    )
    return pool
