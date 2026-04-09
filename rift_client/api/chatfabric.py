import json
from websockets.client import WebSocketClientProtocol  # type: ignore
from ..models.user import User
from .message import MessageManager


class ChatFabric:

    def __init__(self, websocket: WebSocketClientProtocol) -> None:
        self.websocket = websocket
        self.current_user: User | None = None
        self.message_manager = MessageManager()

    async def register(self, username: str, password: str) -> tuple[bool, str]:
        register_data = self.message_manager.create_registration(username, password)
        await self.websocket.send(register_data)
        response_str = await self.websocket.recv()
        response = json.loads(response_str)
        if response.get("type") == "register_success":
            return True, "Регистрация успешна. Теперь вы можете войти"
        else:
            return False, "Ошибка регистрации"

    async def sign_in(self, username: str, password: str) -> tuple[bool, str]:
        auth_data = self.message_manager.create_auth_message(username, password)
        await self.websocket.send(auth_data)
        server_str = await self.websocket.recv()
        response = json.loads(server_str)

        if response.get("type") == "auth_success":
            self.current_user = User(username=username, password=password)
            return True, "Авторизация успешна"
        else:
            return False, "Неверный логин или пароль"

    async def send_message_room(self, message: str, room: str) -> None:
        if not self.current_user:
            return
        message_to_send = self.message_manager.create_chat_message(text=message, room=room)
        await self.websocket.send(message_to_send)

    async def send_private_message(self, recipient: str, text: str) -> None:
        if not self.current_user:
            return
        message_to_send = self.message_manager.create_private_message(recipient, text)
        await self.websocket.send(message_to_send)

    async def get_list_online_users(self) -> None:
        if not self.current_user:
            return
        message_to_send = self.message_manager.get_online_users()
        await self.websocket.send(message_to_send)
