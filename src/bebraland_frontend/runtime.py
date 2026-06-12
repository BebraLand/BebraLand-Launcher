from __future__ import annotations

import fnmatch
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

import minecraft_launcher_lib
import requests

from .api import absolute_url
from .config import launcher_data_dir


Status = Callable[[str], None]
Progress = Callable[[int, int, str], None]
PROTECTED_LOCAL_PATTERNS = [
    ".bebraland/**",
    "assets/**",
    "libraries/**",
    "versions/**",
    "runtime/**",
    "runtimes/**",
    "saves/**",
    "screenshots/**",
    "logs/**",
    "crash-reports/**",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_protected(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in PROTECTED_LOCAL_PATTERNS)


def matches_pattern(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/")
    normalized_pattern = pattern.replace("\\", "/").strip("/")
    if normalized_pattern in {"*", "**", "**/*"}:
        return True
    if not any(char in normalized_pattern for char in "*?[]"):
        return normalized == normalized_pattern or normalized.startswith(f"{normalized_pattern}/")
    return fnmatch.fnmatch(normalized, normalized_pattern)


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(matches_pattern(path, pattern) for pattern in patterns)


def sync_mode_for(path: str, rules: dict[str, Any]) -> str:
    blacklist = rules.get("blacklist") or []
    whitelist = rules.get("whitelist") or []
    if matches_any(path, blacklist):
        return "enforce"
    if matches_any(path, whitelist):
        return "seed"
    return "enforce"


def instance_dir(slug: str) -> Path:
    path = launcher_data_dir() / "instances" / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_dir(game_dir: Path) -> Path:
    path = game_dir / ".bebraland"
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_old_manifest(game_dir: Path) -> dict[str, Any] | None:
    path = state_dir(game_dir) / "manifest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(game_dir: Path, manifest: dict[str, Any]) -> None:
    path = state_dir(game_dir) / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def download_file(
    url: str,
    dest: Path,
    expected_sha256: str,
    status: Status,
    progress: Progress | None = None,
) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    dest.parent.mkdir(parents=True, exist_ok=True)
    status(f"Download {dest.name}")
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length") or 0)
        done = 0
        with tmp.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 512):
                if chunk:
                    handle.write(chunk)
                    done += len(chunk)
                    if progress and total:
                        progress(done, total, f"Download {dest.name}")
    actual = sha256_file(tmp)
    if actual != expected_sha256:
        tmp.unlink(missing_ok=True)
        raise ValueError(f"Hash mismatch for {dest}: {actual} != {expected_sha256}")
    tmp.replace(dest)


def cleanup_extra_files(
    game_dir: Path,
    wanted: set[str],
    rules: dict[str, Any],
    status: Status,
) -> int:
    removed = 0
    for item in sorted(game_dir.rglob("*")):
        if item.is_dir():
            continue
        rel = item.relative_to(game_dir).as_posix()
        if rel in wanted or is_protected(rel):
            continue
        if sync_mode_for(rel, rules) == "seed":
            continue
        status(f"Remove extra {rel}")
        item.unlink()
        removed += 1
    return removed


def sync_manifest(
    manifest: dict[str, Any],
    server_url: str,
    status: Status,
    progress: Progress | None = None,
) -> Path:
    profile = manifest["profile"]
    game_dir = instance_dir(profile["slug"])
    wanted = {item["path"]: item for item in manifest["files"]}
    rules = manifest.get("rules") or {}
    stats = {"checked": len(wanted), "downloaded": 0, "updated": 0, "seeded": 0, "kept": 0, "removed": 0}

    for rel, item in wanted.items():
        target = game_dir / rel
        mode = item.get("mode") or sync_mode_for(rel, rules)
        if target.exists():
            if mode == "seed":
                stats["kept"] += 1
                continue
            if sha256_file(target) == item["sha256"]:
                continue
            url = absolute_url(server_url, item["url"])
            download_file(url, target, item["sha256"], status, progress)
            stats["updated"] += 1
            continue
        url = absolute_url(server_url, item["url"])
        download_file(url, target, item["sha256"], status, progress)
        if mode == "seed":
            stats["seeded"] += 1
        else:
            stats["downloaded"] += 1

    stats["removed"] = cleanup_extra_files(game_dir, set(wanted), rules, status)

    write_manifest(game_dir, manifest)
    status(
        "Sync done: "
        f"checked={stats['checked']} downloaded={stats['downloaded']} updated={stats['updated']} "
        f"seeded={stats['seeded']} kept_user={stats['kept']} removed={stats['removed']}"
    )
    return game_dir


def install_mod_loader(
    manifest: dict[str, Any],
    game_dir: Path,
    status: Status,
    progress: Progress | None = None,
) -> str:
    profile = manifest["profile"]
    loader_id = profile["mod_loader"].lower()
    minecraft_version = profile["minecraft_version"]
    loader_version = profile["loader_version"]
    current_status = {"text": "", "max": 0}

    def set_status(text: str) -> None:
        current_status["text"] = text
        status(text)

    def set_max(value: int) -> None:
        current_status["max"] = value
        if progress:
            progress(0, value, current_status["text"])

    def set_progress(value: int) -> None:
        if progress:
            progress(value, int(current_status["max"] or 0), current_status["text"])

    callback = {"setStatus": set_status, "setMax": set_max, "setProgress": set_progress}
    if loader_id in {"vanilla", "minecraft", "none"}:
        status(f"Install Minecraft {minecraft_version}")
        minecraft_launcher_lib.install.install_minecraft_version(minecraft_version, str(game_dir), callback=callback)
        return minecraft_version

    status(f"Install {loader_id} {loader_version} for Minecraft {minecraft_version}")
    mod_loader = minecraft_launcher_lib.mod_loader.get_mod_loader(loader_id)
    return mod_loader.install(
        minecraft_version,
        str(game_dir),
        loader_version=loader_version,
        callback=callback,
    )


def launch_minecraft(
    manifest: dict[str, Any],
    game_dir: Path,
    username: str,
    status: Status,
    progress: Progress | None = None,
) -> subprocess.Popen:
    installed_version = install_mod_loader(manifest, game_dir, status, progress)
    options = minecraft_launcher_lib.utils.generate_test_options()
    options.update(
        {
            "username": username or "BebraPlayer",
            "gameDirectory": str(game_dir),
            "launcherName": "BebraLand Launcher",
            "launcherVersion": "0.1.0",
        }
    )
    command = minecraft_launcher_lib.command.get_minecraft_command(
        installed_version,
        str(game_dir),
        options,
    )
    status("Start Minecraft")
    return subprocess.Popen(command, cwd=str(game_dir))
