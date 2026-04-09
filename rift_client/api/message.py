from ..models.message import Message

class MessageManager:

    def create_auth_message(self, username: str, password: str) -> str:
        payload = {"username": username, "password": password}
        message = Message(type="auth", payload=payload)
        return message.to_json()

    def create_chat_message(self, room: str, text: str) -> str:
        payload = {"room": room, "text": text}
        message = Message(type="room_message", payload=payload)
        return message.to_json()

    def create_private_message(self, recipient: str, text: str) -> str:
        payload = {"to": recipient, "text": text}
        message = Message(type="private_message", payload=payload)
        return message.to_json()

    def get_online_users(self) -> str:
        payload = {}
        message = Message(type="get_online_users", payload=payload)
        return message.to_json()

    def create_registration(self, username: str, password: str) -> str:
        payload = {"username": username, "password": password}
        message = Message(type="register", payload=payload)
        return message.to_json()
