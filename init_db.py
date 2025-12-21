import asyncio
from passlib.context import CryptContext
from db.service_db import create_db, insert_data

pwd_context = CryptContext(schemes=["argon2"], deprecated = "auto")

async def main():
    await create_db()

    test_vvod = [
        {"username": "NIKITA", "password": "qwert123", "status": "online"},
        {"username": "ANTON", "password": "qwert", "status": "online"},
    ]

    for user in test_vvod:
        user["password"] = pwd_context.hash(user["password"])
    
    await insert_data(test_vvod, "user")
    print("БД создана, данные загружены")


if __name__ == "__main__":
    asyncio.run(main())
