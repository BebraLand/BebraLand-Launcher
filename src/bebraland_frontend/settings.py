from __future__ import annotations

import json
import os
from typing import Any

from .config import DEFAULT_SERVER_URL, launcher_data_dir


LEGACY_DEFAULT_SERVER_URL = "http://127.0.0.1:8765"


def settings_path():
    return launcher_data_dir() / "settings.json"


def load_settings() -> dict[str, Any]:
    env_server_url = os.environ.get("BEBRALAND_SERVER_URL", "").strip()
    path = settings_path()
    if not path.exists():
        return {"server_url": DEFAULT_SERVER_URL}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"server_url": DEFAULT_SERVER_URL}
    if not isinstance(data, dict):
        return {"server_url": DEFAULT_SERVER_URL}
    server_url = str(data.get("server_url") or "").strip()
    if env_server_url or not server_url or server_url.rstrip("/") == LEGACY_DEFAULT_SERVER_URL:
        data["server_url"] = DEFAULT_SERVER_URL
    return data


def save_settings(data: dict[str, Any]) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
