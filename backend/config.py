import json
import os
import shutil
from typing import Dict, Any, List

CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "config.json"))
EXAMPLE_CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "config.example.json"))

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE):
        if os.path.exists(EXAMPLE_CONFIG_FILE):
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            shutil.copy(EXAMPLE_CONFIG_FILE, CONFIG_FILE)
        else:
            return {"telegram": {}, "translation": {}, "topics": [], "schedules": []}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config_data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

def update_telegram_settings(bot_token: str, chat_id: str) -> Dict[str, Any]:
    cfg = load_config()
    cfg["telegram"]["bot_token"] = bot_token.strip()
    cfg["telegram"]["chat_id"] = chat_id.strip()
    save_config(cfg)
    return cfg

def update_translation_settings(engine: str, api_key: str, model: str = "") -> Dict[str, Any]:
    cfg = load_config()
    cfg["translation"]["engine"] = engine.strip()
    cfg["translation"]["api_key"] = api_key.strip()
    if model:
        cfg["translation"]["model"] = model.strip()
    save_config(cfg)
    return cfg

def update_topics(topics: List[Dict[str, Any]]) -> Dict[str, Any]:
    cfg = load_config()
    cfg["topics"] = topics
    save_config(cfg)
    return cfg

def update_schedules(schedules: List[Dict[str, Any]]) -> Dict[str, Any]:
    cfg = load_config()
    cfg["schedules"] = schedules
    save_config(cfg)
    return cfg
