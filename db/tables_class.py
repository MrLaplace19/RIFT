from .base_class import Base
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from typing import Annotated


class statuss(Enum):
    online = "online"
    offline = "offline"


int_id = Annotated[int, mapped_column(primary_key=True)]


class User(Base):
    __tablename__ = "user"
    id: Mapped[int_id]
    username: Mapped[str]
    password: Mapped[str]
    friend_list: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[statuss]


list_tables = {
    "user": User,
}
