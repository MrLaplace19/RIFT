import json
from websockets.client import WebSocketClientProtocol  # type: ignore
from samples.json_samples import create_json


class User:
    def __init__(
        self,
        websocket: WebSocketClientProtocol,
        username: str | None = None,
        password: str | None = None,
        role: str | None = None,
    ) -> None:
        self.username: str | None = username
        self.websocket: WebSocketClientProtocol = websocket
        self.password: str | None = password
        self.role: str | None = role

    async def message_in_general_chat(self, message: str) -> None:
        message_to_send = create_json(2, None, None, message)
        await self.websocket.send(message_to_send)

    async def private_message(self, message: str) -> None:
        message_to_send = create_json(3, self.username, self.password, message)
        await self.websocket.send(message_to_send)

    async def get_list_online_users(self) -> None:
        message_to_send = create_json(4, None, None, None)
        await self.websocket.send(message_to_send)

    async def registration(self, username: str, password: str) -> tuple[bool, str]:
        register_data = create_json(5, username, password, None)
        await self.websocket.send(register_data)
        response_str = await self.websocket.recv()
        response = json.loads(response_str)
        if response.get("type") == "register_success":
            return True, "Регистрация успешна. Теперь вы можете войти"
        else:
            return False, "Ошибка регистрации"

    async def sign_in(self, username: str, password: str) -> tuple[bool, str]:
        auth_data = create_json(1, username, password, None)
        await self.websocket.send(auth_data)
        server_str = await self.websocket.recv()
        response = json.loads(server_str)

        if response.get("type") == "auth_success":
            self.username = username
            self.password = password
            return True, "Авторизация успешна"
        else:
            return False, "Неверный логин или пароль"
