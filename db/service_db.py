from .tables_class import list_tables
from .base_class import Base
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


URL = "postgresql://AD:123@127.0.0.1:5432/TEST"
engine = create_engine(URL)
session_factory = sessionmaker(engine)


def create_db():
    engine.echo = False
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    engine.echo = True


def print_db(table_name: str):
    table = list_tables.get(table_name)

    if table is None:
        raise ValueError(f"Таблица: {table_name} - отсутсвует")

    with session_factory() as session:
        query = select(table)
        result = session.execute(query)
        elements = result.scalars().all()

    return elements


def insert_data(information: list[dict], table_name: str):
    table = list_tables.get(table_name)

    if table is None:
        raise ValueError(f"Таблица: {table_name} - отсутсвует")

    with session_factory() as session:
        for info in information:
            result = table(**info)
            session.add(result)
        session.commit()
