from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

import requests

from .config import launcher_data_dir


Status = Callable[[str], None]
UPDATE_HELPER_FLAG = "--apply-update"
UPDATE_WAIT_SECONDS = 60


def numeric_version(value: str) -> tuple[int, ...]:
    parts = [int(part) for part in re.findall(r"\d+", value.lstrip("vV"))]
    return tuple(parts) if parts else (0,)


def is_newer_version(latest: str, current: str) -> bool:
    latest_parts = list(numeric_version(latest))
    current_parts = list(numeric_version(current))
    width = max(len(latest_parts), len(current_parts))
    latest_parts.extend([0] * (width - len(latest_parts)))
    current_parts.extend([0] * (width - len(current_parts)))
    return latest_parts > current_parts


def normalize_release(manifest: dict[str, Any]) -> dict[str, Any]:
    version = str(manifest.get("version") or "").strip().lstrip("vV")
    url = str(manifest.get("url") or manifest.get("download_url") or "").strip()
    if not version:
        raise ValueError("Update manifest has no version")
    if not url:
        raise ValueError("Update manifest has no download url")
    release: dict[str, Any] = {
        "version": version,
        "url": url,
    }
    sha256 = str(manifest.get("sha256") or "").strip()
    if sha256:
        release["sha256"] = sha256
    notes = str(manifest.get("notes") or "").strip()
    if notes:
        release["notes"] = notes
    return release


def get_update_release(current_version: str, manifest_url: str, status: Status) -> dict[str, Any] | None:
    manifest_url = manifest_url.strip()
    if not manifest_url:
        return None
    status("Check launcher update")
    response = requests.get(manifest_url, timeout=20)
    response.raise_for_status()
    manifest = response.json()
    if not isinstance(manifest, dict):
        raise ValueError("Update manifest must be a JSON object")
    release = normalize_release(manifest)
    if not is_newer_version(release["version"], current_version):
        status("Launcher up to date")
        return None
    return release


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_release(release: dict[str, Any], status: Status) -> Path:
    cleanup_update_cache()
    updates_dir = launcher_data_dir() / "updates"
    updates_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(str(release["url"]).split("?")[0]).name or f"BebraLandLauncher-{release['version']}.exe"
    target = updates_dir / filename
    tmp = target.with_suffix(target.suffix + ".part")
    status(f"Download launcher {release['version']}")
    try:
        with requests.get(release["url"], stream=True, timeout=120) as response:
            response.raise_for_status()
            with tmp.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 512):
                    if chunk:
                        handle.write(chunk)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    expected = release.get("sha256")
    if expected:
        actual = sha256_file(tmp)
        if actual.lower() != expected.lower():
            tmp.unlink(missing_ok=True)
            raise ValueError(f"Update hash mismatch: {actual} != {expected}")
    tmp.replace(target)
    return target


def cleanup_update_cache(status: Status | None = None) -> None:
    updates_dir = launcher_data_dir() / "updates"
    if not updates_dir.exists():
        return
    current = Path(sys.executable).resolve()
    removed = 0
    for item in updates_dir.iterdir():
        try:
            if item.resolve() == current:
                continue
            if item.is_file() or item.is_symlink():
                item.unlink()
                removed += 1
            elif item.is_dir():
                shutil.rmtree(item)
                removed += 1
        except OSError:
            continue
    try:
        updates_dir.rmdir()
    except OSError:
        pass
    if removed and status:
        status(f"Cleaned launcher update cache: {removed}")


def can_self_replace() -> bool:
    return bool(getattr(sys, "frozen", False)) and os.name == "nt"


def replace_current_exe(downloaded: Path) -> None:
    if not can_self_replace():
        raise RuntimeError("Self-update works only for frozen Windows EXE")

    current = Path(sys.executable).resolve()
    downloaded = downloaded.resolve()
    if downloaded == current:
        raise RuntimeError("Downloaded update cannot replace itself")

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    subprocess.Popen(
        [
            str(downloaded),
            UPDATE_HELPER_FLAG,
            "--target",
            str(current),
            "--pid",
            str(os.getpid()),
        ],
        cwd=str(current.parent),
        close_fds=True,
        creationflags=creationflags,
    )
    raise SystemExit(0)


def wait_for_process_exit(pid: int, timeout_seconds: int = UPDATE_WAIT_SECONDS) -> None:
    if pid <= 0:
        return
    if os.name == "nt":
        import ctypes

        synchronize = 0x00100000
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(synchronize, False, pid)
        if not handle:
            return
        try:
            result = kernel32.WaitForSingleObject(handle, timeout_seconds * 1000)
            if result == 0x00000102:
                raise TimeoutError("Old launcher did not exit before update timeout")
            return
        finally:
            kernel32.CloseHandle(handle)

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return
        time.sleep(0.25)
    raise TimeoutError("Old launcher did not exit before update timeout")


def apply_downloaded_update(target: Path, old_pid: int, relaunch: bool = True) -> None:
    source = Path(sys.executable).resolve()
    target = target.resolve()
    if source == target:
        raise RuntimeError("Update source and target are the same file")

    wait_for_process_exit(old_pid)
    tmp_target = target.with_name(f"{target.name}.new")

    try:
        tmp_target.unlink(missing_ok=True)
        shutil.copy2(source, tmp_target)
        os.replace(tmp_target, target)
    except Exception:
        tmp_target.unlink(missing_ok=True)
        raise

    if relaunch:
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        subprocess.Popen([str(target)], cwd=str(target.parent), close_fds=True, creationflags=creationflags)


def run_update_helper_from_cli(argv: list[str] | None = None) -> bool:
    argv = list(sys.argv[1:] if argv is None else argv)
    if UPDATE_HELPER_FLAG not in argv:
        return False

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(UPDATE_HELPER_FLAG, action="store_true")
    parser.add_argument("--target", required=True)
    parser.add_argument("--pid", type=int, default=0)
    parser.add_argument("--no-relaunch", action="store_true")
    args, _unknown = parser.parse_known_args(argv)
    apply_downloaded_update(Path(args.target), args.pid, relaunch=not args.no_relaunch)
    return True
