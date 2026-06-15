from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    platform = str(payload.get("platform") or "").strip().lower()
    if not platform:
        raise ValueError(f"{path} has no platform")
    if not payload.get("url"):
        raise ValueError(f"{path} has no url")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("manifests", nargs="+")
    args = parser.parse_args()

    manifests = [read_manifest(Path(item)) for item in args.manifests]
    first = manifests[0]
    payload: dict[str, Any] = {
        "version": first.get("version"),
        "display_version": first.get("display_version") or first.get("version"),
        "tag": first.get("tag"),
        "releases": {},
    }
    if first.get("update_id"):
        payload["update_id"] = str(first["update_id"])
    if first.get("notes"):
        payload["notes"] = str(first["notes"])

    for manifest in manifests:
        platform = str(manifest["platform"]).strip().lower()
        payload["releases"][platform] = {
            "platform": platform,
            "url": manifest["url"],
            "sha256": manifest.get("sha256", ""),
        }

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
