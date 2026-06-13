from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def current_platform_id() -> str:
    arch = normalized_machine()
    if sys.platform.startswith("win"):
        return f"windows-{arch}"
    if sys.platform == "darwin":
        return f"macos-{arch}"
    if sys.platform.startswith("linux"):
        return f"linux-{arch}"
    return f"{sys.platform}-{arch}"


def default_artifact(platform_id: str) -> Path:
    suffix = ".exe" if platform_id.startswith("windows-") else ""
    return ROOT / "dist" / f"BebraLandLauncher{suffix}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=os.environ.get("BEBRALAND_BUILD_VERSION"), required=False)
    parser.add_argument("--display-version", default=os.environ.get("BEBRALAND_DISPLAY_VERSION", ""))
    parser.add_argument("--update-id", default=os.environ.get("BEBRALAND_UPDATE_ID", ""))
    parser.add_argument("--compat-version", default=os.environ.get("BEBRALAND_COMPAT_VERSION", ""))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--tag", default="")
    parser.add_argument("--platform", default=os.environ.get("BEBRALAND_RELEASE_PLATFORM") or current_platform_id())
    parser.add_argument("--artifact", "--exe", dest="artifact", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    release_platform = str(args.platform).strip().lower()
    artifact = Path(args.artifact).resolve() if args.artifact else default_artifact(release_platform).resolve()
    if not artifact.exists():
        raise FileNotFoundError(artifact)

    display_version = (args.display_version or args.version or "").strip().lstrip("vV")
    if not display_version:
        raise RuntimeError("Version required. Pass --version or BEBRALAND_BUILD_VERSION.")

    update_id = str(args.update_id or "").strip()
    compat_version = str(args.compat_version or "").strip().lstrip("vV")
    if not compat_version:
        compat_version = f"9999.{update_id}" if update_id.isdigit() else display_version

    tag = (args.tag or f"v{display_version}").strip()
    url = args.url.strip()
    if not url:
        if not args.repo:
            raise RuntimeError("Repo required. Pass --repo owner/name or --url.")
        url = f"https://github.com/{args.repo}/releases/download/{tag}/{artifact.name}"

    payload = {
        "version": compat_version,
        "display_version": display_version,
        "tag": tag,
        "platform": release_platform,
        "url": url,
        "sha256": sha256_file(artifact),
    }
    if update_id:
        payload["update_id"] = update_id
    if args.notes:
        payload["notes"] = args.notes

    output = Path(args.output or ROOT / "dist" / f"latest-{release_platform}.json").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}: {url}")


if __name__ == "__main__":
    main()
