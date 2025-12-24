import asyncio
import websockets
import json
import getpass


async def receive_message(websocket):
    """
    Функция приёма websocket`а

    :param websocket: Websocket
    :type websocket: WebSocketServerProtocol
    """
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
            else:
                print(f"[SERVER] : {data}")
    except websockets.exceptions.ConnectionClosed:
        print("Соединение разорвано")


async def send_message(websocket, username: str):
    """
    Функция отправки websocket

    :param websocket: Websocket
    :type websocket: WebSocketServerProtocol
    :param username: Login
    :type username: str
    """
    while True:
        try:
            message = await asyncio.to_thread(input, "")
            if message.lower() == "exit":
                print("Выход из чата")
                break
            elif message.startswith("/pm "):
                parts = message[4:].split(" ",1)
                if (len(parts) == 2):
                    recipient, text = parts
                    message_to_send = json.dumps({
                        "type": "private_message",
                        "payload":
                        {
                            "to": recipient,
                            "text": text,
                        }
                    })
                    await websocket.send(message_to_send)
                else:
                    print("Неверный формат")
                    continue
            message_to_send = json.dumps(
                {"type": "message", "payload": {"text": message, "username": username}}
            )
            await websocket.send(message_to_send)
        except (KeyboardInterrupt, EOFError):
            print("\nВыход из чата")
            break


async def connect(url: str, username: str, password: str):
    """
    Функция подлючения и отправкии сообщений

    :param url: Ссылка на websocket server
    :type url: str
    :param username: Login
    :type username: str
    :param password: password
    :type password: str
    """

    auth_data = json.dumps(
        {
            "type": "auth",
            "payload": {
                "username": username,
                "password": password,
            },
        }
    )
    async with websockets.connect(url) as websocket:
        print(f"Подключение к чату {url}")

        await websocket.send(
            auth_data
        )  # Отправляем json пакет с логиным и паролем для аутентификации
        server_str = await websocket.recv()
        response = json.loads(server_str)

        if response.get("type") == "auth_success":
            print("Аутентификация успешна")

            receive_task = asyncio.create_task(receive_message(websocket))
            send_task = asyncio.create_task(send_message(websocket, username))

            done, pending = await asyncio.wait(
                [receive_task, send_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()

        else:
            error_message = response.get("payload", {}).get(
                "error", "Неверный логин или пароль"
            )
            print("Не удалось войти: ", error_message)
            return


async def main():
    """
    Основная функция - точка входа
    inputs: Принимает login и password
    const: URL сервера websocket
    """
    url = "ws://localhost:8765"

    username = input("Введите свой логин ")
    password = getpass.getpass("Введите свой пароль ")

    try:
        await connect(url, username, password)
    except ConnectionRefusedError:
        print("Не удалось подключиться")


if __name__ == "__main__":
    asyncio.run(main())
