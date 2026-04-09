import argparse
import asyncio
import websockets
import getpass

# -------------------------------------------
from .api.chatfabric import ChatFabric
from .config import config, create_settings, settings_file
from .view.tui import ChatApp


def used_settings():
    if not settings_file.exists():
        print(
            "Отсутсвует файл настроек, авторизмруйтесь и создайте файл в главном меню"
        )

    settings = config()
    return settings


async def register_user(url: str, username: str, password: str):
    """Асинхронная функция для регистрации нового пользователя."""
    try:
        async with websockets.connect(url) as websocket:
            chat_manager = ChatFabric(websocket)
            print(f"Попытка регистрации на {url}...")
            success, message = await chat_manager.register(username, password)
            if success:
                print(message)
            else:
                print("Ошибка регистрации:", message)
    except websockets.exceptions.ConnectionClosed:
        print("Соединение с сервером закрыто.")
    except ConnectionRefusedError:
        print("Не удалось подключиться к серверу.")


def interactive_login_or_register(url: str):
    """Интерактивный вход или регистрация пользователя."""
    username = input("Введите свой логин: ")
    password = getpass.getpass("Введите свой пароль: ")

    action = input("Вы хотите (l)og in или (r)egister? ").lower()

    if action == "r":
        asyncio.run(register_user(url, username, password))
        return

    elif action == "l":
        app = ChatApp(username=username, password=password, url=url)
        result = app.run()
        if result in ("auth_failed", "connection_failed"):
            print("Не удалось войти. Попробуйте еще раз.")
    else:
        print(
            "Неверный выбор. Пожалуйста, выберите 'l' для входа или 'r' для регистрации."
        )


def main():
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
        print(f"Подключение к чату {url}")
        username = settings["payload"]["username"]
        password = settings["payload"]["password"]
        app = ChatApp(username=username, password=password, url=url)
        result = app.run()

        if result in ("auth_failed", "connection_failed"):
            print("Не удалось войти с сохраненными настройками.")
            interactive_login_or_register(url)

    else:
        interactive_login_or_register(url)