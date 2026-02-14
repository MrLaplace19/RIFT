import json
from pathlib import Path
from passlib.context import CryptContext

settings_save = {
    "type": "settings",
    "payload": {
        "username": "",
        "password": "", # Пароль сразу hash
    }
}
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

settings_file = Path.home() / ".settings.json"

def create_settings(username: str, password: str) -> None:
    hashed_password = pwd_context.hash(password)
    settings_save["payload"]["username"] = username
    settings_save["payload"]["password"] = hashed_password
    with open(settings_file, "w", encoding='utf-8') as f:
        json.dump(settings_save, f)
    

def config():
        with open(settings_file, 'r') as f:
            settings_load = json.load(f)
            return settings_load
