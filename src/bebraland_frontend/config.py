from __future__ import annotations

import os
from pathlib import Path

try:
    from . import build_info
except Exception:
    build_info = None


DEFAULT_SERVER_URL = os.environ.get("BEBRALAND_SERVER_URL", "http://127.0.0.1:8765")
DEFAULT_UPDATE_MANIFEST_URL = (
    os.environ.get("BEBRALAND_UPDATE_MANIFEST_URL")
    or getattr(build_info, "UPDATE_MANIFEST_URL", "")
).strip()


def update_manifest_url() -> str:
    return (os.environ.get("BEBRALAND_UPDATE_MANIFEST_URL") or DEFAULT_UPDATE_MANIFEST_URL).strip()


def launcher_data_dir() -> Path:
    override = os.environ.get("BEBRALAND_LAUNCHER_DIR")
    if override:
        return Path(override).expanduser().resolve()
    appdata = os.environ.get("APPDATA")
    if appdata:
        return (Path(appdata) / "BebraLandLauncher").resolve()
    return (Path.home() / ".bebraland-launcher").resolve()
