from sqlalchemy import func, ForeignKey
from .base_class import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from typing import Annotated
from datetime import datetime


class statuss(Enum):
    online = "online"
    offline = "offline"


int_id = Annotated[int, mapped_column(primary_key=True)]
date_create = Annotated[datetime, mapped_column(server_default=func.now())]


class User(Base):
    __tablename__ = "user"
    id: Mapped[int_id]
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    friend_list: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[statuss]
    date: Mapped[date_create]
    messages: Mapped[list["Message"]] = relationship(
        back_populates="author"
    )  # Узнать что это за связь


class Message(Base):
    __tablename__ = "message"
    id: Mapped[int_id]
    content: Mapped[str]
    created_at: Mapped[date_create]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    author: Mapped["User"] = relationship(
        back_populates="messages"
    )  # Узнать что это за связь


list_tables = {
    "user": User,
    "message": Message,
}
