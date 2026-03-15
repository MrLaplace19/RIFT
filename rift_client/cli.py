import argparse
import asyncio
import websockets
import json
import getpass

# -------------------------------------------
from .api.user import ChatManager
from .api.message import ReceivedMessage
from .config import config, create_settings, settings_file


async def receive_message(websocket):
    """
    Функция приёма websocket`а

    :param websocket: The websocket connection object.
    """
    try:
        async for message_str in websocket:
            message = ReceivedMessage.from_json(message_str)
            if message.type == "new_message":
                username = message.payload.get("username", "unknown")
                text = message.payload.get("text", "")
                print(f"<{username}> : {text}")
            elif message.type == "private_message":
                sender = message.payload.get("from", "unknown")
                text = message.payload.get("text", "")
                print(f"[PM от {sender}> : {text}")
            elif message.type == "private_message_sent":
                recipient = message.payload.get("to", "unknown")
                text = message.payload.get("text", "")
                print(f"[PM для {recipient}> : {text}")
            elif message.type == "online_users":
                users = message.payload.get("users", [])
                print("--- Online Users ---")
                for user_online in users:
                    print(f"- {user_online}")
                print("--------------------")
            else:
                print(f"[SERVER] : {message.payload}")
    except websockets.exceptions.ConnectionClosed:
        print("Соединение разорвано")


async def send_message(chat_manager: ChatManager):
    """
    Функция отправки websocket

    :param chat_manager: The ChatManager object.
    """
    current_room = "general"
    while True:
        try:
            message = await asyncio.to_thread(input, "")
            if message.lower() == "exit":
                print("Выход из чата")
                break
            elif message.lower() == "/users":
                await chat_manager.get_list_online_users()
                continue
            elif message.startswith("/pm "):
                parts = message.split(" ", 2)
                if len(parts) == 3:
                    recipient, text = parts[1], parts[2]
                    await chat_manager.private_message(recipient, text)
                else:
                    print("Неверный формат. Используйте: /pm <получатель> <сообщение>")
                continue
            else:
                await chat_manager.send_message_room(message, current_room)
                continue
        except (KeyboardInterrupt, EOFError):
            print("Выход из чата")
            break


async def connect(chat_manager: ChatManager):
    """
    Функция подключения и отправки сообщений

    :param chat_manager: The ChatManager object.
    """
    print("Аутентификация успешна. Подключение к чату.")

    receive_task = asyncio.create_task(receive_message(chat_manager.websocket))
    send_task = asyncio.create_task(send_message(chat_manager))

    done, pending = await asyncio.wait(
        [receive_task, send_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


def used_settings():
    if not settings_file.exists():
        print(
            "Отсутсвует файл настроек, авторизмруйтесь и создайте файл в главном меню"
        )

    settings = config()
    return settings


async def interactive_login_or_register(url: str):
    username = input("Введите свой логин: ")
    password = getpass.getpass("Введите свой пароль: ")

    action = input("Вы хотите (l)og in или (r)egister? ").lower()

    if action == "r":
        try:
            async with websockets.connect(url) as websocket:
                chat_manager = ChatManager(websocket)
                print(f"Попытка регистрации на {url}...")
                success, message = await chat_manager.register(username, password)
                if success:
                    print(message)
                else:
                    print("Ошибка регистрации:", message)
            return
        except websockets.exceptions.ConnectionClosed:
            print("Соединение с сервером закрыто.")
        except ConnectionRefusedError:
            print("Не удалось подключиться к серверу.")
        return

    elif action == "l":
        try:
            async with websockets.connect(url) as websocket:
                chat_manager = ChatManager(websocket)
                print(f"Подключение к чату {url}")
                success, message = await chat_manager.sign_in(username, password)

                if success:
                    if not settings_file.exists():
                        set_choice = input(
                            "Хотите сохранить данные для автоматического входа (Y) или (N)"
                        )
                        if set_choice.lower() == "y":
                            create_settings(username, password)
                    await connect(chat_manager)
                else:
                    print("Не удалось войти: ", message)
                    # Removed recursive call to avoid potential infinite loop
        except websockets.exceptions.ConnectionClosed:
            print("Соединение с сервером закрыто.")
        except ConnectionRefusedError:
            print("Не удалось подключиться к серверу.")
    else:
        print(
            "Неверный выбор. Пожалуйста, выберите 'l' для входа или 'r' для регистрации."
        )


async def main():
    """
    Основная функция - точка входа
    """
    parser = argparse.ArgumentParser(description="WebSocket Chat Client")
    parser.add_argument("--host", default="localhost", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    args = parser.parse_args()

    url = f"ws://{args.host}:{args.port}"
    if settings_file.exists():
        settings = used_settings()
        try:
            async with websockets.connect(url) as websocket:
                chat_manager = ChatManager(websocket)
                print(f"Подключение к чату {url}")
                username = settings["payload"]["username"]
                password = settings["payload"]["password"]
                success, message = await chat_manager.sign_in(username, password)

                if success:
                    await connect(chat_manager)
                else:
                    print(f"Не удалось войти автоматически: {message}")
                    settings_file.unlink()
                    print("Файл с неверными настройками удален.")
                    await interactive_login_or_register(url)

        except websockets.exceptions.ConnectionClosed:
            print("Соединение с сервером закрыто.")
            await interactive_login_or_register(url)
        except ConnectionRefusedError:
            print("Не удалось подключиться к серверу.")
            await interactive_login_or_register(url)
    else:
        await interactive_login_or_register(url)