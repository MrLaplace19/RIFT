import asyncio
from websockets.server import serve, WebSocketServerProtocol  # pyright: ignore[reportAttributeAccessIssue]
from db.service_db import create_db, insert_data
import json

CONNECTED_CLIENTS = set()


async def handler(websocket: WebSocketServerProtocol, path: str):
    CONNECTED_CLIENTS.add(websocket)
    print(f"Новый клиент подключен! Всего: {len(CONNECTED_CLIENTS)}")
    try:
        async for message in websocket:
            print(f"Получено сообщение: {message}")
            message_data = [{"content": message, "user_id": 1}]
            await insert_data(message_data, "message")
            asyncio.create_task(broadcast(message, websocket))
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        print(f"Клиент отключился, осталось {len(CONNECTED_CLIENTS)}")


async def broadcast(message: str, sender_websocket: WebSocketServerProtocol):
    if len(CONNECTED_CLIENTS) < 2:
        return

    tasks = []
    for client_websocket in CONNECTED_CLIENTS:
        if client_websocket != sender_websocket:
            task = asyncio.create_task(client_websocket.send(message))
            tasks.append(task)

    if tasks:
        await asyncio.wait(tasks)


async def main():
    test_vvod = [
        {"username": "NIKITA", "password": "qwert123", "status": "online"},
        {"username": "ANTON", "password": "qwert", "status": "online"},
    ]
    await create_db()
    await insert_data(test_vvod, "user")
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
