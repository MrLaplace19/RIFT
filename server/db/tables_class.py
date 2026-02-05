from sqlalchemy import String, func, ForeignKey, UUID
import uuid
from .base_class import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from typing import Annotated
from datetime import datetime


class statuss(Enum):
    online = "online"
    offline = "offline"


int_id = Annotated[
    uuid.UUID, mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
]
date_create = Annotated[datetime, mapped_column(server_default=func.now())]


class User(Base):
    __tablename__ = "user"
    id: Mapped[int_id]
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    friend_list: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[statuss]
    date: Mapped[date_create]
    messages: Mapped[list["Message"]] = relationship(
        back_populates="author"
    )


class Message(Base):
    __tablename__ = "message"
    id: Mapped[int_id]
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[date_create]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    author: Mapped["User"] = relationship(
        back_populates="messages"
    )


list_tables = {
    "user": User,
    "message": Message,
}
