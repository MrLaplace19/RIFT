import json
from websockets.client import WebSocketClientProtocol

class User():

    def __init__(self, websocket: WebSocketClientProtocol, username: str | None = None, password: str | None = None, role: str | None = None) -> None:
        self.username: str | None = username
        self.websocket: WebSocketClientProtocol = websocket
        self.password: str | None = password
        self.role: str | None = role
    

    async def message_in_general_chat(self, message: str)-> None:
        message_to_send = json.dumps(
                {"type": "message", "payload": {"text": message}}
            )
        await self.websocket.send(message_to_send)
    
    async def private_message(self, recipient: str, text: str) -> None:
        message_to_send = json.dumps(
            {
                "type": "private_message",
                "payload": {
                    "to": recipient,
                    "text": text,
                },
            }
        )
        await self.websocket.send(message_to_send)
        
    async def get_list_online_users(self)->None:
        message_to_send = json.dumps(
            {"type": "get_online_users", "payload": {}}
        )
        await self.websocket.send(message_to_send)
    
    async def registration(self, username: str, password: str) -> tuple[bool,str]:
        register_data = json.dumps(
            {
                "type": "register",
                "payload": {
                    "username": username,
                    "password": password,
                },
            }
        )
        await self.websocket.send(register_data)
        response_str = await self.websocket.recv()
        response = json.loads(response_str)
        if response.get("type") == "register_success":
            return True,"Регистрация успешна. Теперь вы можете войти"
        else:
            
            return False,"Ошибка регистрации" 
    
    async def sign_in(self, username: str, password: str) -> tuple[bool,str]:
        auth_data = json.dumps(
            {
                "type": "auth",
                "payload": {
                    "username": username,
                    "password": password,
                },
            }
        )
        await self.websocket.send(auth_data)
        server_str = await self.websocket.recv()
        response = json.loads(server_str)

        if response.get("type") == "auth_success":
            self.username = username
            self.password = password
            return True, "Авторизация успешна"
        else:
            return False, "Неверный логин или пароль"
