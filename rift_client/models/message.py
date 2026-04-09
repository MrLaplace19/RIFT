from dataclasses import dataclass
from typing import Any,Dict
import json

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
