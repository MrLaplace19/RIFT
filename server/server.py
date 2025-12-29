import asyncio
from websockets.server import serve, WebSocketServerProtocol  # pyright: ignore[reportAttributeAccessIssue]
import json
from passlib.context import CryptContext
from db.service_db import get_user, insert_data
from db.tables_class import User

ACTIVE_USERS = {}
WEBSOCKET_TO_USER = {}
USER_TO_WEBSOCKET = {}
error_login_or_password = {
    "type": "auth_fail",
    "payload": {"error": "Неверный логин или пароль"},
}
error_first_non_auth = {
    "type": "auth_fail",
    "payload": {"error": "Сначала пройдите авторизацию"},
}
error_user_offline = {
    "type": "error",
    "payload": {
        "error": "Пользователь не в сети"
    }
}
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verificated_pass(password: str, hash_password: str) -> bool:
    return pwd_context.verify(password, hash_password)


async def broadcast(message: str, sender_websocket: WebSocketServerProtocol):
    """
    Функция отправки сообщений всем

    :param message: Сообщение из json
    :type message: str
    :param sender_websocket: sender_websocket
    :type sender_websocket: WebSocketServerProtocol
    """
    sender_user = ACTIVE_USERS.get(sender_websocket)

    if not sender_user:
        return

    message_to_send = json.dumps(
        {
            "type": "new_message",
            "payload": {
                "username": sender_user.username,
                "text": message,
            },
        }
    )
    tasks = []

    for client_websocket in ACTIVE_USERS:
        if client_websocket != sender_websocket:
            task = asyncio.create_task(client_websocket.send(message_to_send))
            tasks.append(task)
    if tasks:
        await asyncio.wait(tasks)


async def send_private_message(message: str, sender_websocket: WebSocketServerProtocol, recipient_username: str):
    sender_username = WEBSOCKET_TO_USER.get(sender_websocket)
    if not sender_username:
        return False
    
    recipient_websocket = USER_TO_WEBSOCKET.get(recipient_username)
    if not recipient_websocket:
        error_msg = json.dumps(error_user_offline)
        await sender_websocket.send(error_msg)
        return False
    
    private_message_to_recipient = json.dumps({
        "type": "private_message",
        "payload":
        {
            "from": sender_username,
            "text": message,
            "is_private": True,
        }
    })
    
    private_message_to_sender = json.dumps({
        "type": "priavate_message_sent",
        "payload":
        {
            "to": recipient_username,
            "text": message,
            "is_private": True,
        }
    })

    await recipient_websocket.send(private_message_to_recipient)
    await sender_websocket.send(private_message_to_sender)

    print(f"[PRIVATE] {sender_username} -> {recipient_username}: {message}")
    

async def authentication(data, websocket: WebSocketServerProtocol) -> bool:
    """
    Функция аутетификации

    :param data: Словарь от пользователя с тегом auth
    :type data: Any
    :param websocket: websocket
    :type websocket: WebSocketServerProtocol
    """
    if data.get("type") == "auth":
        user = await get_user(data["payload"]["username"])
        if user != None and verificated_pass(
            data["payload"]["password"], user.password
        ):
            WEBSOCKET_TO_USER[websocket] = user.username
            USER_TO_WEBSOCKET[user.username] = websocket
            print(
                f"Пользователь {user.username} подключился всего пользователей {len(ACTIVE_USERS)}"
            )
            await websocket.send(json.dumps({"type": "auth_success"}))
            return True
        else:
            await websocket.send(json.dumps(error_login_or_password))
            return False
    else:
        await websocket.send(json.dumps(error_first_non_auth))
        return False


async def shipping(websocket: WebSocketServerProtocol):
    async for message in websocket:
        data = json.loads(message)
        if data.get("type") == "message":
            await insert_data(data, "message")
            await broadcast(message=data["payload"]["text"], sender_websocket=websocket)
        if data.get("type") == "private_message":
            #await insert_data(data,"message")
            message = data["payload"]["text"]
            recipient = data["payload"]["to"]
            await send_private_message(message,websocket,recipient)

async def handler(websocket: WebSocketServerProtocol, path: str):
    """
    Функция handler

    :param websocket: Websocket
    :type websocket: WebSocketServerProtocol
    :param path: Путь?
    :type path: str
    """
    user: User | None = None
    message = await websocket.recv()
    data = json.loads(message)
    try:
        if await authentication(data, websocket) == True:
            await shipping(websocket)
        else:
            count_auth = 0
            print("Ошибка авторизации повторите попытку")
            while count_auth != 3:
                await authentication(data, websocket)

    finally:
        if websocket in ACTIVE_USERS:
            user = ACTIVE_USERS.pop(websocket)
            print(f"Клиент {user.username} отключился осталось {len(ACTIVE_USERS)}")  # type: ignore


async def main():
    """
    Основная функция - точка входа в сервеной части
    """
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
