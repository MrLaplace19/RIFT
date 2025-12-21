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
            else:
                print(f"[SERVER] : {data}")
    except websockets.exceptions.ConnectionClosed:
        print("Соединение разорвано")


async def send_message(websocket):
    while True:
        try:
            message = await asyncio.to_thread(input, "")
            if message.lower() == "exit":
                print("Выход из чата")
                break

            message_to_send = json.dumps({
                "type": "message",
                "payload": {
                    "text": message
                }
            })
            await websocket.send(message_to_send)
        except (KeyboardInterrupt, EOFError):
            print("\nВыход из чата")
            break


async def main():
    url = "ws://localhost:8765"

    username = input("Введите свой логин ")
    password = getpass.getpass("Введите свой пароль ")
    
    auth_data = json.dumps({
        "type": "auth",
        "payload": {
            "username": username,
            "password": password,
        }
    })
    try:
        async with websockets.connect(url) as websocket:
            print(f"Подключение к чату {url}")
            
            await websocket.send(auth_data)
            server_str = await websocket.recv()
            response = json.loads(server_str)

            if response.get("type") == "auth_success":
                print("Аутентификация успешна") 

                receive_task = asyncio.create_task(receive_message(websocket))
                send_task = asyncio.create_task(send_message(websocket))

                done, pending = await asyncio.wait(
                    [receive_task, send_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
            
            else:
                error_message = response.get("payload", {}).get("error", "Неверный логин или пароль")
                print("Не удалось войти")
                return
    except ConnectionRefusedError:
        print("Не удалось подключиться")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.Future()
