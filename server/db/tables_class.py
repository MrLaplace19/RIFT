from email import message

from sqlalchemy import String, Table, Column ,func, ForeignKey, UUID
import uuid
from .base_class import Base
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship
from enum import Enum
from typing import Annotated
from datetime import datetime

room_association_table = Table(
    "room_association",
    Base.metadata,
    Column("user_id", ForeignKey("user.id"), primary_key=True),
    Column("chat_room_id", ForeignKey("chat_room.id"), primary_key = True)
)

class Statuss(Enum):
    online = "online"
    offline = "offline"

class Roles(Enum):
    user = "user"
    admin = "admin"

int_id = Annotated[
    uuid.UUID, mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
]
date_create = Annotated[datetime, mapped_column(server_default=func.now())]


class User(Base):
    __tablename__ = "user"
    id: Mapped[int_id]
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[Roles] = mapped_column(nullable=False, default=Roles.user)
    friend_list: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[Statuss]
    date: Mapped[date_create]
    messages: Mapped[list["Message"]] = relationship(back_populates="author")
    chat_rooms: Mapped[list["ChatRoom"]] = relationship(secondary=room_association_table, back_populates="users")


class Message(Base):
    __tablename__ = "message"
    id: Mapped[int_id]
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[date_create]
    user_id: Mapped[int_id] = mapped_column(ForeignKey("user.id"), nullable=False)
    chat_room_id: Mapped[int_id] = mapped_column(ForeignKey("chat_room.id"), nullable=False)
    author: Mapped["User"] = relationship(back_populates="messages")
    chat: Mapped["ChatRoom"] = relationship(back_populates="messages")


class ChatRoom(Base):
    __tablename__ = "chat_room"
    id: Mapped[int_id]
    name: Mapped[str] = mapped_column(String,nullable=False, unique=True)
    messages: Mapped[list["Message"]] = relationship(back_populates="chat")
    users: Mapped[list["User"]] = relationship(secondary=room_association_table, back_populates="chat_rooms")

list_tables = {
    "user": User,
    "message": Message,
    "chat_room": ChatRoom
}
