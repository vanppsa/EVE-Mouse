import json
import os
import socket
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "EVE-Mouse"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "password_hash": "",
    "port": 10101,
    "session_mode": "persistent",
    "session_timeout_minutes": 0,
    "trackpad_sensitivity": 1.5,
    "keep_background": False,
}


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def load_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = {**DEFAULTS, **data}
        return merged
    save_config(DEFAULTS)
    return dict(DEFAULTS)


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    merged = {**DEFAULTS, **data}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)


def get_url(port: int = 10101) -> str:
    return f"http://{get_local_ip()}:{port}"
