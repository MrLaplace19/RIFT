import json
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ReceivedMessage:

    type: str
    payload: Dict[str, Any]

    @classmethod
    def from_json(cls, json_str: str) -> "ReceivedMessage":
        data = json.loads(json_str)
        return cls(type=data.get("type", ""), payload=data.get("payload", {}))


@dataclass
class Message:
    type: str
    payload: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps({"type": self.type, "payload": self.payload})


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
