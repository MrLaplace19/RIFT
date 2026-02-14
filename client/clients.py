import argparse
import asyncio
import websockets
import json
import getpass
from src.User import User


async def receive_message(user_websocket):
    """
    Функция приёма websocket`а

    :param user_websocket: Websocket
    :type user_websocket: WebSocketServerProtocol
    """
    try:
        async for message in user_websocket:
            data = json.loads(message)
            if data.get("type") == "new_message":
                username = data["payload"]["username"]
                text = data["payload"]["text"]
                print(f"<{username}> : {text}")
            elif data.get("type") == "private_message":
                sender = data["payload"]["from"]
                text = data["payload"]["text"]
                print(f"[PM от {sender}] : {text}")
            elif data.get("type") == "private_message_sent":
                recipient = data["payload"]["to"]
                text = data["payload"]["text"]
                print(f"[PM для {recipient}] : {text}")
            elif data.get("type") == "online_users":  # New block
                users = data["payload"]["users"]
                print("\n--- Online Users ---")
                for user_online in users:
                    print(f"- {user_online}")
                print("--------------------")
            else:
                print(f"[SERVER] : {data}")
    except websockets.exceptions.ConnectionClosed:
        print("Соединение разорвано")


async def send_message(user: User):
    """
    Функция отправки websocket

    :param user: Объект пользователя
    :type user: User
    """
    while True:
        try:
            message = await asyncio.to_thread(input, "")
            if message.lower() == "exit":
                print("Выход из чата")
                break
            elif message.lower() == "/users":
                await user.get_list_online_users()
                continue
            elif message.startswith("/pm "):
                await user.private_message(message)
            else:
                print("Неверный формат")
                continue
            await user.message_in_general_chat(message)
        except (KeyboardInterrupt, EOFError):
            print("\nВыход из чата")
            break


async def connect(user: User):
    """
    Функция подключения и отправки сообщений

    :param user: Объект пользователя
    :type user: User
    """
    print("Аутентификация успешна. Подключение к чату.")

    receive_task = asyncio.create_task(receive_message(user.websocket))
    send_task = asyncio.create_task(send_message(user))

    done, pending = await asyncio.wait(
        [receive_task, send_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


async def main():
    """
    Основная функция - точка входа
    inputs: Принимает login и password
    const: URL сервера websocket
    """
    parser = argparse.ArgumentParser(description="WebSocket Chat Client")
    parser.add_argument("--host", default="localhost", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    args = parser.parse_args()

    url = f"ws://{args.host}:{args.port}"

    username = input("Введите свой логин: ")
    password = getpass.getpass("Введите свой пароль: ")

    action = input("Вы хотите (l)og in или (r)egister? ").lower()

    if action == "r":
        try:
            async with websockets.connect(url) as websocket:
                user = User(websocket)
                print(f"Попытка регистрации на {url}...")
                success, message = await user.registration(username, password)
                if success:
                    print(message)
                else:
                    print("Ошибка регистрации:", message)
            return  # Exit after registration attempt
        except websockets.exceptions.ConnectionClosed:
            print("Соединение с сервером закрыто.")
        except ConnectionRefusedError:
            print("Не удалось подключиться к серверу.")
        return

    elif action == "l":
        try:
            async with websockets.connect(url) as websocket:
                user = User(websocket)
                print(f"Подключение к чату {url}")
                success, message = await user.sign_in(username, password)

                if success:
                    user.websocket = websocket
                    await connect(user)
                else:
                    print("Не удалось войти: ", message)
        except websockets.exceptions.ConnectionClosed:
            print("Соединение с сервером закрыто.")
        except ConnectionRefusedError:
            print("Не удалось подключиться к серверу.")
    else:
        print(
            "Неверный выбор. Пожалуйста, выберите 'l' для входа или 'r' для регистрации."
        )


if __name__ == "__main__":
    asyncio.run(main())
