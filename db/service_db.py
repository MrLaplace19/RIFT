from .tables_class import list_tables
from .base_class import Base
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import Any

URL = "postgresql+asyncpg://AD:123@127.0.0.1:5432/TEST"
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
        return elements  # type: ignore


async def insert_data(information: list[dict], table_name: str):
    table = list_tables.get(table_name)

    if table is None:
        raise ValueError(f"Таблица: {table_name} - отсутсвует")

    async with session_factory() as session:
        for info in information:
            result = table(**info)
            session.add(result)
        await session.commit()


async def get_user(login: str) -> Any | None :
    user_table = list_tables.get("user")

    if user_table is None:
        return None
    
    async with session_factory() as session:
        query = select(user_table).where(user_table.username == login)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        return user
