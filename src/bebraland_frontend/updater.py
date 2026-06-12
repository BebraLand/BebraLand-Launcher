from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import requests

from .config import launcher_data_dir


Status = Callable[[str], None]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_release(release: dict[str, Any], status: Status) -> Path:
    updates_dir = launcher_data_dir() / "updates"
    updates_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(release["url"].split("?")[0]).name or "BebraLandLauncher.exe"
    target = updates_dir / filename
    tmp = target.with_suffix(target.suffix + ".part")
    status(f"Download launcher {release['version']}")
    with requests.get(release["url"], stream=True, timeout=120) as response:
        response.raise_for_status()
        with tmp.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 512):
                if chunk:
                    handle.write(chunk)
    expected = release.get("sha256")
    if expected:
        actual = sha256_file(tmp)
        if actual.lower() != expected.lower():
            tmp.unlink(missing_ok=True)
            raise ValueError(f"Update hash mismatch: {actual} != {expected}")
    tmp.replace(target)
    return target


def can_self_replace() -> bool:
    return bool(getattr(sys, "frozen", False)) and os.name == "nt"


def replace_current_exe(downloaded: Path) -> None:
    current = Path(sys.executable)
    script = Path(tempfile.gettempdir()) / "bebraland_update.cmd"
    script.write_text(
        "\r\n".join(
            [
                "@echo off",
                "ping 127.0.0.1 -n 3 > nul",
                f'copy /Y "{downloaded}" "{current}"',
                f'start "" "{current}"',
                f'del "{script}"',
            ]
        ),
        encoding="utf-8",
    )
    subprocess.Popen(["cmd", "/c", str(script)], close_fds=True)
    raise SystemExit(0)
