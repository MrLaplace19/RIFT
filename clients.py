import asyncio
import websockets


async def receive_message(websocket):
    try:
        async for message in websocket:
            print(f"{message}")
    except websockets.exceptions.ConnectionClosed:
        print("Соединение разорвано")


async def send_message(websocket):
    while True:
        try:
            message = await asyncio.to_thread(input, "> ")
            if message.lower() == "exit":
                print("Выход из чата")
                break
            await websocket.send(message)
        except (KeyboardInterrupt, EOFError):
            print("Выход из чата")
            break


async def main():
    url = "ws://localhost:8765"

    try:
        async with websockets.connect(url) as websocket:
            print(f"Подключение к чату{url}")

            receive_task = asyncio.create_task(receive_message(websocket))
            send_task = asyncio.create_task(send_message(websocket))

            done, pending = await asyncio.wait(
                [receive_task, send_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
    except ConnectionRefusedError:
        print("Не удалось подключиться")


if __name__ == "__main__":
    asyncio.run(main())
