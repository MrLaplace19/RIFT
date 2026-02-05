import argparse
import asyncio
import websockets
import json
import getpass


async def receive_message(websocket):
    try:
        async for message in websocket:
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
            elif data.get("type") == "online_users":
                users = data["payload"]["users"]
                print("\n--- Online Users ---")
                for user_online in users:
                    print(f"- {user_online}")
                print("--------------------")
            else:
                print(f"[SERVER] : {data}")
    except websockets.exceptions.ConnectionClosed:
        print("Соединение разорвано")


async def send_message(websocket, username: str):
    while True:
        try:
            message = await asyncio.to_thread(input, "")
            if message.lower() == "exit":
                print("Выход из чата")
                break
            elif message.lower() == "/users":
                message_to_send = json.dumps(
                    {"type": "get_online_users", "payload": {}}
                )
                await websocket.send(message_to_send)
                continue
            elif message.startswith("/pm "):
                parts = message[4:].split(" ", 1)
                if len(parts) == 2:
                    recipient, text = parts
                    message_to_send = json.dumps(
                        {
                            "type": "private_message",
                            "payload": {
                                "to": recipient,
                                "text": text,
                            },
                        }
                    )
                    await websocket.send(message_to_send)
                else:
                    print("Неверный формат")
                    continue
            message_to_send = json.dumps(
                {"type": "message", "payload": {"text": message}}
            )
            await websocket.send(message_to_send)
        except (KeyboardInterrupt, EOFError):
            print("\nВыход из чата")
            break


async def connect(websocket, username: str):
    print("Аутентификация успешна. Подключение к чату.")

    receive_task = asyncio.create_task(receive_message(websocket))
    send_task = asyncio.create_task(send_message(websocket, username))

    done, pending = await asyncio.wait(
        [receive_task, send_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


async def main():
    parser = argparse.ArgumentParser(description="WebSocket Chat Client")
    parser.add_argument("--host", default="localhost", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    args = parser.parse_args()

    url = f"ws://{args.host}:{args.port}"

    username = input("Введите свой логин: ")
    password = getpass.getpass("Введите свой пароль: ")

    action = input("Вы хотите (l)og in или (r)egister? ").lower()

    if action == "r":
        register_data = json.dumps(
            {
                "type": "register",
                "payload": {
                    "username": username,
                    "password": password,
                },
            }
        )
        try:
            async with websockets.connect(url) as websocket:
                print(f"Попытка регистрации на {url}...")
                await websocket.send(register_data)
                response_str = await websocket.recv()
                response = json.loads(response_str)
                if response.get("type") == "register_success":
                    print("Регистрация успешна. Теперь вы можете войти.")
                else:
                    error_message = response.get("payload", {}).get(
                        "error", "Ошибка регистрации"
                    )
                    print("Ошибка регистрации:", error_message)
            return
        except websockets.exceptions.ConnectionClosed:
            print("Соединение с сервером закрыто.")
        except ConnectionRefusedError:
            print("Не удалось подключиться к серверу.")
        return

    elif action == "l":
        auth_data = json.dumps(
            {
                "type": "auth",
                "payload": {
                    "username": username,
                    "password": password,
                },
            }
        )
        try:
            async with websockets.connect(url) as websocket:
                print(f"Подключение к чату {url}")
                await websocket.send(auth_data)
                server_str = await websocket.recv()
                response = json.loads(server_str)

                if response.get("type") == "auth_success":
                    await connect(websocket, username)
                else:
                    error_message = response.get("payload", {}).get(
                        "error", "Неверный логин или пароль"
                    )
                    print("Не удалось войти: ", error_message)
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