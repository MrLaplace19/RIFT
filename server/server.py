import asyncio
from websockets.server import serve, WebSocketServerProtocol  # type: ignore
from websockets.exceptions import ConnectionClosed
import json
from passlib.context import CryptContext

# ---------------------------------------------
from db.service_db import get_user, insert_data
from db.tables_class import User, Statuss
from erorrs_messages.erorrs import (
    error_user_exists,
    register_success,
    error_user_offline,
    error_login_or_password,
    error_first_non_auth,
)

ROOMS = {
    "general": set()
}
WEBSOCKET_TO_USER_OBJ = {}
WEBSOCKET_TO_USER = {}
USER_TO_WEBSOCKET = {}

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verificated_pass(password: str, hash_password: str) -> bool:
    return pwd_context.verify(password, hash_password)


async def register_new_user(data: dict, websocket: WebSocketServerProtocol):
    username = data["payload"]["username"]
    password = data["payload"]["password"]

    user_exists = await get_user(username)
    if user_exists:
        await websocket.send(json.dumps(error_user_exists))
        return

    hashed_password = pwd_context.hash(password)
    await insert_data(
        [{"username": username, "password": hashed_password, "status": Statuss.online}],
        "user",
    )
    await websocket.send(json.dumps(register_success))
    print(f"Новый пользователь {username} зарегистрирован.")


async def broadcast_to_room(room_name: str,message: str, sender_websocket: WebSocketServerProtocol):
    

    sender_user = WEBSOCKET_TO_USER_OBJ[sender_websocket]

    if not sender_user:
        return
    
    if room_name not in ROOMS:
        return
    message_to_send = json.dumps(
        {
            "type": "new_message",
            "payload": {
                "room": room_name,
                "username": sender_user.username,
                "text": message,
            },
        }
    )

    for client_websocket in ROOMS[room_name]:
        if client_websocket != sender_websocket:
            await client_websocket.send(message)
            


async def send_private_message(
    message: str, sender_websocket: WebSocketServerProtocol, recipient_username: str
):
    sender_user = WEBSOCKET_TO_USER_OBJ.get(sender_websocket)
    if not sender_user:
        return False

    recipient_websocket = USER_TO_WEBSOCKET.get(recipient_username)
    if not recipient_websocket:
        error_msg = json.dumps(error_user_offline)
        await sender_websocket.send(error_msg)
        return False

    private_message_to_recipient = json.dumps(
        {
            "type": "private_message",
            "payload": {
                "from": sender_user.username,
                "text": message,
                "is_private": True,
            },
        }
    )

    private_message_to_sender = json.dumps(
        {
            "type": "priavate_message_sent",
            "payload": {
                "to": recipient_username,
                "text": message,
                "is_private": True,
            },
        }
    )

    await recipient_websocket.send(private_message_to_recipient)
    await sender_websocket.send(private_message_to_sender)

    print(f"[PRIVATE] {sender_user.username} -> {recipient_username}: {message}")


async def send_online_users_list(websocket: WebSocketServerProtocol):
    online_users = list(USER_TO_WEBSOCKET.keys())
    response = {"type": "online_users", "payload": {"users": online_users}}
    await websocket.send(json.dumps(response))


async def authentication(data: dict, websocket: WebSocketServerProtocol) -> User | None:
    if data.get("type") == "auth":
        user = await get_user(data["payload"]["username"])
        if user is not None and verificated_pass(
            data["payload"]["password"], user.password
        ):
            print(f"Пользователь {user.username} подключился")
            await websocket.send(json.dumps({"type": "auth_success"}))
            return user
        else:
            await websocket.send(json.dumps(error_login_or_password))
            return None
    else:
        await websocket.send(json.dumps(error_first_non_auth))
        return None


async def shipping(websocket: WebSocketServerProtocol):

    async for message in websocket:
        data = json.loads(message)
        if data.get("type") == "room_message":
            sender_user = WEBSOCKET_TO_USER_OBJ.get(websocket)
            if sender_user:
                #await insert_data(data, "message", username=sender_user.username)
                await broadcast_to_room(
                    message=data["payload"]["text"], 
                    sender_websocket=websocket,
                    room_name=data["payload"]["room"]
                )
            else:
                print("Ошибка: Неизвестный пользователь пытается отправить сообщение.")
        elif data.get("type") == "private_message":
            message = data["payload"]["text"]
            recipient = data["payload"]["to"]
            await send_private_message(message, websocket, recipient)
        elif data.get("type") == "get_online_users":
            await send_online_users_list(websocket)


async def handler(websocket: WebSocketServerProtocol, path: str):
    user: User | None = None
    try:
        message = await websocket.recv()
        data: dict = json.loads(message)

        if data.get("type") == "auth":
            user = await authentication(data, websocket)
            if user:
                WEBSOCKET_TO_USER_OBJ[websocket] = user
                WEBSOCKET_TO_USER[websocket] = user.username
                USER_TO_WEBSOCKET[user.username] = websocket
                ROOMS["general"].add(websocket) 
                print(
                    f"Пользователь {user.username} подключился. Всего пользователей: {len(ROOMS['general'])}"
                )
                await shipping(websocket)
            else:
                await websocket.close()
                return
        elif data.get("type") == "register":
            await register_new_user(data, websocket)
        else:
            await websocket.send(json.dumps(error_first_non_auth))

    except ConnectionClosed:
        pass
    finally:
        if user:
            if user.username in USER_TO_WEBSOCKET:
                USER_TO_WEBSOCKET.pop(user.username)
            if websocket in WEBSOCKET_TO_USER:
                WEBSOCKET_TO_USER.pop(websocket)
            if websocket in WEBSOCKET_TO_USER_OBJ:
                WEBSOCKET_TO_USER_OBJ.pop(websocket)
            for room_set in ROOMS.values():
                room_set.discard(websocket)
            print(f"Клиент {user.username} отключился. Осталось: {len(ROOMS['general'])}")


async def main():
    host = "0.0.0.0"
    port = 8765

    async with serve(handler, host, port):
        print(f"Основной сервер запущен на ws://{host}:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
