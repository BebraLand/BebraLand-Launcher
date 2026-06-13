from __future__ import annotations

import os
import platform
import sys
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
APP_DIR_NAME = "BebraLandLauncher"


def update_manifest_url() -> str:
    return (os.environ.get("BEBRALAND_UPDATE_MANIFEST_URL") or DEFAULT_UPDATE_MANIFEST_URL).strip()


def build_update_id() -> str:
    return str(os.environ.get("BEBRALAND_UPDATE_ID") or getattr(build_info, "UPDATE_ID", "")).strip()


def normalized_machine() -> str:
    machine = platform.machine().lower().replace(" ", "")
    aliases = {
        "amd64": "x64",
        "x86_64": "x64",
        "i386": "x86",
        "i686": "x86",
        "x86": "x86",
        "aarch64": "arm64",
        "arm64": "arm64",
    }
    return aliases.get(machine, machine or "unknown")


def platform_id() -> str:
    arch = normalized_machine()
    if sys.platform.startswith("win"):
        return f"windows-{arch}"
    if sys.platform == "darwin":
        return f"macos-{arch}"
    if sys.platform.startswith("linux"):
        return f"linux-{arch}"
    return f"{sys.platform}-{arch}"


def executable_suffix() -> str:
    return ".exe" if os.name == "nt" else ""


def launcher_binary_name() -> str:
    return f"BebraLandLauncher{executable_suffix()}"


def updater_binary_name() -> str:
    return f"BebraLandUpdater{executable_suffix()}"


def launcher_data_dir() -> Path:
    override = os.environ.get("BEBRALAND_LAUNCHER_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if appdata:
            return (Path(appdata) / APP_DIR_NAME).resolve()
    if sys.platform == "darwin":
        return (Path.home() / "Library" / "Application Support" / APP_DIR_NAME).resolve()
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return (Path(xdg_data_home).expanduser() / APP_DIR_NAME).resolve()
    return (Path.home() / ".local" / "share" / APP_DIR_NAME).resolve()
