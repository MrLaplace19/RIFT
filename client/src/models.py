from abc import ABC, abstractclassmethod
import json
from pydantic import BaseModel
from enum import Enum

class type_message(str,Enum):
    AUTH = "auth"
    MESSAGE = "message"
    PRIVATE_MESSAGE = "private_message"
    LIST_FRIENDS = "friends_list"

class User(BaseModel):
    username: str
    password: str

    def __init__(self, _username, _password) -> None:
        super().__init__(username = _username, password = _password)
    
class BaseMessage(ABC):
    type: type_message

    @abstractclassmethod
    def create_dict(self) -> dict:
        pass
    
    def create_json(self) -> str:
        return json.dumps(self.create_dict())

    @classmethod
    @abstractclassmethod
    def from_dict(cls, data: dict) -> 'BaseMessage':
        """Создание объекта из словаря"""
        pass
    pass

class AuthMessage(BaseMessage):
    type: type_message.AUTH

    def