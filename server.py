import asyncio
from websockets.server import serve, WebSocketServerProtocol  # pyright: ignore[reportAttributeAccessIssue]
import json
from passlib.context import CryptContext
from db.service_db import get_user
from db.tables_class import User

ACTIVE_USERS = {}
error_login_or_password = {"type": "auth_fail", "payload": {"error": "Неверный логин или пароль"}}
error_first_non_auth = {"type": "auth_fail", "payload": {"error": "Сначала пройдите авторизацию"}}
pwd_context = CryptContext(schemes=["argon2"], deprecated = "auto")



def verificated_pass(password: str, hash_password: str) -> bool:
    return pwd_context.verify(password, hash_password)


async def handler(websocket: WebSocketServerProtocol, path: str):
    user: User | None = None

    try:
        message = await websocket.recv()
        data = json.loads(message)

        if data.get("type") == "auth":
            user = await get_user(data["payload"]["username"])
            if user != None and verificated_pass(data["payload"]["password"], user.password):
                ACTIVE_USERS[websocket] = user
                print(f"Пользователь {user.username} подключился всего пользователей {len(ACTIVE_USERS)}")
                await websocket.send(json.dumps({"type": "auth_success"}))
            else:
                await websocket.send(json.dumps(error_login_or_password))
                return
        else:
            await websocket.send(json.dumps(error_first_non_auth))
            return
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "message":
                await broadcast(message=data["payload"]["text"], sender_websocket=websocket) 
    except Exception as e:
        print("Ошибка", e)
    
    finally:
        if websocket in ACTIVE_USERS:
            user = ACTIVE_USERS.pop(websocket)
            print(f"Клиент {user.username} отключился осталось {len(ACTIVE_USERS)}")


async def broadcast(message: str, sender_websocket: WebSocketServerProtocol):
    sender_user = ACTIVE_USERS.get(sender_websocket)

    if not sender_user:
        return
    
    message_to_send = json.dumps({
        "type": "new_message",
        "payload": {
            "username": sender_user.username,
            "text": message,
        }   
    })
    tasks = []

    for client_websocket in ACTIVE_USERS:
        if client_websocket != sender_websocket:
            task = asyncio.create_task(client_websocket.send(message_to_send))
            tasks.append(task)
    if tasks:
        await asyncio.wait(tasks)


async def main():
    
    host = "localhost"
    port = 8765

    async with serve(handler, host, port):
        print(f"Основной сервер запущен на ws://{host}:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
