from .tables_class import User, list_tables
from .base_class import Base
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import Any
import os

DB_USER = os.getenv("POSTGRES_USER", "AD")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "TEST")

URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_async_engine(URL)
session_factory = async_sessionmaker(engine)


async def create_db():
    async with engine.begin() as connect:
        await connect.run_sync(Base.metadata.drop_all)
        await connect.run_sync(Base.metadata.create_all)
    print("База данных создана")


async def get_all_from_table(table_name: str) -> list[Any]:
    table = list_tables.get(table_name)

    if table is None:
        raise ValueError(f"Таблица: {table_name} - отсутсвует")

    async with session_factory() as session:
        query = select(table)
        result = await session.execute(query)
        elements = result.scalars().all()
        return elements


async def insert_data(information: Any, table_name: str, username: str | None = None):
    user_table = list_tables.get(table_name)

    if user_table is None:
        raise ValueError(f"Таблица: {table_name} - отсутствует")

    async with session_factory() as session:
        async with session.begin():
            if table_name == "user":
                if not isinstance(information, list):
                    information = [information]

                for info in information:
                    result = user_table(**info)
                    session.add(result)

            elif table_name == "message":
                payload = information.get("payload", {})
                text = payload.get("text")

                if not all([username, text]):
                    raise ValueError("Отсутствуют обязательные поля")

                stmt = select(User).where(User.username == username)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    raise ValueError(f"Пользователь {username} не найден")

                message_data = {
                    "user_id": user.id,
                    "content": text,
                }

                result = user_table(**message_data)
                session.add(result)


async def get_user(login: str) -> Any | None:
    user_table = list_tables.get("user")

    if user_table is None:
        return None

    async with session_factory() as session:
        query = select(user_table).where(user_table.username == login)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        return user
