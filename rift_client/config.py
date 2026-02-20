import json
from pathlib import Path

settings_save = {
    "type": "settings",
    "payload": {
        "username": "",
        "password": "", 
    }
}

settings_file = Path.home() / ".settings.json"

def create_settings(username: str, password: str) -> None:
    settings_save["payload"]["username"] = username
    settings_save["payload"]["password"] = password
    with open(settings_file, "w", encoding='utf-8') as f:
        json.dump(settings_save, f)
    

def config():
        with open(settings_file, 'r') as f:
            settings_load = json.load(f)
            return settings_load
