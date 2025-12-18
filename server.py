import asyncio

import websockets
from db.service_db import create_db, insert_data
import json


CONNECTED_CLIENTS = set()

async def handler(websocket, path):
    CONNECTED_CLIENTS.add(websocket)
    try:
        async for message in websocket:
            print(f"Получено сообщение: {message}")
            message_data = [{"content": message, "user_id": 1 }]
            await insert_data(message_data, "message")
            asyncio.create_task(broadcast(message, websocket))
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        print(f"Клиент отключился, осталось {len(CONNECTED_CLIENTS)}")

async def broadcast(message: str, send_websocket):
    if len(CONNECTED_CLIENTS) <2:
        return
    
    tasks = []
    for clients_websocket in CONNECTED_CLIENTS:
        if(send_websocket != clients_websocket):
            task = asyncio.create_task(clients_websocket.send(message))
            tasks.append(task)
        if tasks:
            await asyncio.wait(tasks)


async def main():
    await create_db()

    host = "localhost"
    port = 8765

    async with websockets.serve(handler, host, port): # type: ignore
        print("Сервер запущен")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())