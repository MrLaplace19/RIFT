from db.tables_class import statuss
from pydantic import BaseModel


class user(BaseModel):
    username: str
    password: str
    list_friends: str
    status: statuss

    @classmethod
    def user_registartion(cls, db_data):
        if db_data is None:
            raise ValueError("Пустой массив")
        return cls(
            db_data["username"],  # type: ignore
            db_data["password"],
            db_data["list_friend"],
            db_data["status"],
        )

    def my_info(self):
        print(
            f"Имя пользователя: {self.username}\
              Ваш пароль: {self.password}\
                Статус: {self.status}"
        )
        print(f"Ваши друзья: {self.list_friends}")
