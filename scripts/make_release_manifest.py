from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=os.environ.get("BEBRALAND_BUILD_VERSION"), required=False)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--tag", default="")
    parser.add_argument("--exe", default=str(ROOT / "dist" / "BebraLandLauncher.exe"))
    parser.add_argument("--output", default=str(ROOT / "dist" / "latest.json"))
    parser.add_argument("--url", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    if not exe.exists():
        raise FileNotFoundError(exe)

    version = (args.version or "").strip().lstrip("vV")
    if not version:
        raise RuntimeError("Version required. Pass --version or BEBRALAND_BUILD_VERSION.")

    tag = (args.tag or f"v{version}").strip()
    url = args.url.strip()
    if not url:
        if not args.repo:
            raise RuntimeError("Repo required. Pass --repo owner/name or --url.")
        url = f"https://github.com/{args.repo}/releases/download/{tag}/{exe.name}"

    payload = {
        "version": version,
        "platform": "windows",
        "url": url,
        "sha256": sha256_file(exe),
    }
    if args.notes:
        payload["notes"] = args.notes

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}: {url}")


if __name__ == "__main__":
    main()
