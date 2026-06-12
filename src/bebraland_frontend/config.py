from __future__ import annotations

import os
from pathlib import Path


DEFAULT_SERVER_URL = os.environ.get("BEBRALAND_SERVER_URL", "http://127.0.0.1:8765")


def launcher_data_dir() -> Path:
    override = os.environ.get("BEBRALAND_LAUNCHER_DIR")
    if override:
        return Path(override).expanduser().resolve()
    appdata = os.environ.get("APPDATA")
    if appdata:
        return (Path(appdata) / "BebraLandLauncher").resolve()
    return (Path.home() / ".bebraland-launcher").resolve()
