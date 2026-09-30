import json
import os
import shutil
from typing import Dict, Any, List

CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "config.json"))
EXAMPLE_CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "config.example.json"))

TMP_CONFIG_FILE = "/tmp/config.json"

def load_config() -> Dict[str, Any]:
    cfg = {}
    if os.path.exists(TMP_CONFIG_FILE):
        try:
            with open(TMP_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
    elif os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
    elif os.path.exists(EXAMPLE_CONFIG_FILE):
        try:
            with open(EXAMPLE_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass

    if not cfg:
        cfg = {"telegram": {}, "translation": {}, "topics": [], "schedules": []}

    # 优先支持从 Vercel Environment Variables 环境变量读取
    env_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    env_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if env_token:
        cfg.setdefault("telegram", {})["bot_token"] = env_token.strip()
    if env_chat_id:
        cfg.setdefault("telegram", {})["chat_id"] = env_chat_id.strip()

    # Twitter / X (x.com) 环境变量支持
    env_tw_key = os.environ.get("TWITTER_API_KEY")
    env_tw_secret = os.environ.get("TWITTER_API_SECRET")
    env_tw_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    env_tw_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    env_tw_bearer = os.environ.get("TWITTER_BEARER_TOKEN")
    if env_tw_key:
        cfg.setdefault("twitter", {})["api_key"] = env_tw_key.strip()
    if env_tw_secret:
        cfg.setdefault("twitter", {})["api_secret"] = env_tw_secret.strip()
    if env_tw_token:
        cfg.setdefault("twitter", {})["access_token"] = env_tw_token.strip()
    if env_tw_token_secret:
        cfg.setdefault("twitter", {})["access_token_secret"] = env_tw_token_secret.strip()
    if env_tw_bearer:
        cfg.setdefault("twitter", {})["bearer_token"] = env_tw_bearer.strip()

    cfg.setdefault("twitter", {
        "enabled": False,
        "api_key": "",
        "api_secret": "",
        "access_token": "",
        "access_token_secret": "",
        "bearer_token": "",
        "account_info": {}
    })

    return cfg

def save_config(config_data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    except (OSError, PermissionError):
        # Vercel 只读环境自动写入 /tmp
        with open(TMP_CONFIG_FILE, "w", encoding="utf-8") as f:
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

def update_twitter_settings(
    api_key: str, 
    api_secret: str, 
    access_token: str, 
    access_token_secret: str, 
    bearer_token: str = "", 
    enabled: bool = True,
    account_info: Dict[str, Any] = None
) -> Dict[str, Any]:
    cfg = load_config()
    cfg.setdefault("twitter", {})
    cfg["twitter"]["api_key"] = api_key.strip()
    cfg["twitter"]["api_secret"] = api_secret.strip()
    cfg["twitter"]["access_token"] = access_token.strip()
    cfg["twitter"]["access_token_secret"] = access_token_secret.strip()
    if bearer_token is not None:
        cfg["twitter"]["bearer_token"] = bearer_token.strip()
    cfg["twitter"]["enabled"] = enabled
    if account_info is not None:
        cfg["twitter"]["account_info"] = account_info
    save_config(cfg)
    return cfg
