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

from .config import launcher_binary_name, launcher_data_dir, platform_id, updater_binary_name


Status = Callable[[str], None]
UPDATE_HELPER_FLAG = "--apply-update"
INSTALLED_UPDATER_FLAG = "--install-update"
UPDATER_EXE_NAME = updater_binary_name()
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


def platform_aliases(value: str | None = None) -> set[str]:
    current = str(value or platform_id()).strip().lower()
    aliases = {current}
    if current == "windows":
        aliases.add("windows-x64")
    elif current == "linux":
        aliases.add("linux-x64")
    elif current == "macos":
        aliases.update({"macos-arm64", "macos-x64", "darwin"})
    elif current.startswith("windows-"):
        aliases.add("windows")
    elif current.startswith("macos-"):
        aliases.update({"macos", "darwin"})
    elif current.startswith("linux-"):
        aliases.add("linux")
    return aliases


def release_matches_platform(release: dict[str, Any], current_platform: str) -> bool:
    release_platform = str(release.get("platform") or "").strip().lower()
    return not release_platform or release_platform in platform_aliases(current_platform)


def select_platform_release(manifest: dict[str, Any], current_platform: str) -> dict[str, Any] | None:
    releases = manifest.get("releases")
    if isinstance(releases, dict):
        aliases = [current_platform, *sorted(platform_aliases(current_platform) - {current_platform})]
        for alias in aliases:
            release = releases.get(alias)
            if isinstance(release, dict):
                selected = dict(release)
                selected.setdefault("platform", alias)
                return selected
        return None
    if isinstance(releases, list):
        for release in releases:
            if isinstance(release, dict) and release_matches_platform(release, current_platform):
                return release
        return None
    if release_matches_platform(manifest, current_platform):
        return manifest
    return None


def normalize_release(manifest: dict[str, Any], current_platform: str | None = None) -> dict[str, Any] | None:
    current_platform = str(current_platform or platform_id()).strip().lower()
    selected = select_platform_release(manifest, current_platform)
    if selected is None:
        return None

    version = str(manifest.get("version") or "").strip().lstrip("vV")
    version = str(selected.get("version") or version).strip().lstrip("vV")
    url = str(selected.get("url") or selected.get("download_url") or "").strip()
    if not version:
        raise ValueError("Update manifest has no version")
    if not url:
        raise ValueError("Update manifest has no download url")
    release: dict[str, Any] = {
        "version": version,
        "platform": str(selected.get("platform") or current_platform).strip().lower() or current_platform,
        "url": url,
    }
    sha256 = str(selected.get("sha256") or "").strip()
    if sha256:
        release["sha256"] = sha256
    notes = str(selected.get("notes") or manifest.get("notes") or "").strip()
    if notes:
        release["notes"] = notes
    return release


def get_update_release(
    current_version: str,
    manifest_url: str,
    status: Status,
    current_platform: str | None = None,
) -> dict[str, Any] | None:
    manifest_url = manifest_url.strip()
    if not manifest_url:
        return None
    current_platform = str(current_platform or platform_id()).strip().lower()
    status("Check launcher update")
    response = requests.get(manifest_url, timeout=20)
    response.raise_for_status()
    manifest = response.json()
    if not isinstance(manifest, dict):
        raise ValueError("Update manifest must be a JSON object")
    release = normalize_release(manifest, current_platform)
    if release is None:
        status(f"No launcher update for {current_platform}")
        return None
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
    filename = Path(str(release["url"]).split("?")[0]).name
    if not filename:
        base = Path(launcher_binary_name())
        filename = f"{base.stem}-{release['version']}-{release.get('platform') or platform_id()}{base.suffix}"
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
    if os.name != "nt":
        tmp.chmod(tmp.stat().st_mode | 0o755)
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
    return bool(getattr(sys, "frozen", False))


def detached_creationflags() -> int:
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    return creationflags


def launch_detached(command: list[str], cwd: Path) -> None:
    subprocess.Popen(
        command,
        cwd=str(cwd),
        close_fds=True,
        creationflags=detached_creationflags(),
    )


def installed_updater_path(current: Path) -> Path | None:
    updater = current.with_name(UPDATER_EXE_NAME)
    if updater.exists() and updater.resolve() != current:
        return updater.resolve()
    return None


def replace_current_exe(downloaded: Path) -> None:
    if not can_self_replace():
        raise RuntimeError("Self-update works only for frozen launcher builds")

    current = Path(sys.executable).resolve()
    downloaded = downloaded.resolve()
    if downloaded == current:
        raise RuntimeError("Downloaded update cannot replace itself")

    updater = installed_updater_path(current)
    if updater:
        launch_detached(
            [
                str(updater),
                INSTALLED_UPDATER_FLAG,
                "--source",
                str(downloaded),
                "--target",
                str(current),
                "--pid",
                str(os.getpid()),
            ],
            current.parent,
        )
    else:
        launch_detached(
            [
                str(downloaded),
                UPDATE_HELPER_FLAG,
                "--target",
                str(current),
                "--pid",
                str(os.getpid()),
            ],
            current.parent,
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


def apply_update_file(source: Path, target: Path, old_pid: int, relaunch: bool = True) -> None:
    source = source.resolve()
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
        launch_detached([str(target)], target.parent)


def apply_downloaded_update(target: Path, old_pid: int, relaunch: bool = True) -> None:
    apply_update_file(Path(sys.executable), target, old_pid, relaunch=relaunch)


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


def run_installed_updater_from_cli(argv: list[str] | None = None) -> bool:
    argv = list(sys.argv[1:] if argv is None else argv)
    if INSTALLED_UPDATER_FLAG not in argv:
        return False

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(INSTALLED_UPDATER_FLAG, action="store_true")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--pid", type=int, default=0)
    parser.add_argument("--no-relaunch", action="store_true")
    args, _unknown = parser.parse_known_args(argv)
    apply_update_file(Path(args.source), Path(args.target), args.pid, relaunch=not args.no_relaunch)
    return True


def updater_main() -> None:
    run_installed_updater_from_cli()
