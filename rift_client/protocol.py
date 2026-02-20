import json


def create_json(number: int, username: str | None, password: str | None, message: str | None,room: str | None = "general"):
    payload = ""
    if number == 1:  # Json авториризация
        payload = json.dumps(
            {
                "type": "auth",
                "payload": {
                    "username": username,
                    "password": password,
                },
            }
        )
    if number == 2:  # Json сообщзения в общий чат
        payload = json.dumps({"type": "room_message", "payload": {"room": room, "text": message}})

    if number == 3:  # Json сообщение приватное
        if message != None:
            parts = message[4:].split(" ", 1)
            if len(parts) == 2:
                recipient, text = parts
                payload = json.dumps(
                    {
                        "type": "private_message",
                        "payload": {
                            "to": recipient,
                            "text": text,
                        },
                    }
                )
            else:
                print("Неверный формат")
                return

    if number == 4:  # Json получения списка пользователей
        payload = json.dumps({"type": "get_online_users", "payload": {}})

    if number == 5:  # Json регистрация
        payload = json.dumps(
            {
                "type": "register",
                "payload": {
                    "username": username,
                    "password": password,
                },
            }
        )

    return payload
