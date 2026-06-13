from __future__ import annotations

import argparse
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_INFO = ROOT / "src" / "bebraland_frontend" / "build_info.py"
PYPROJECT = ROOT / "pyproject.toml"


def read_project_version() -> str:
    in_project = False
    for raw_line in PYPROJECT.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "[project]":
            in_project = True
            continue
        if in_project and line.startswith("["):
            break
        if in_project and line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError("No [project].version found in pyproject.toml")


def write_build_info(version: str, manifest_url: str, update_id: str) -> None:
    BUILD_INFO.write_text(
        "\n".join(
            [
                f'VERSION = "{version}"',
                f'UPDATE_ID = "{update_id}"',
                f'UPDATE_MANIFEST_URL = "{manifest_url}"',
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=os.environ.get("BEBRALAND_BUILD_VERSION"))
    parser.add_argument("--update-id", default=os.environ.get("BEBRALAND_UPDATE_ID", ""))
    parser.add_argument("--manifest-url", default=os.environ.get("BEBRALAND_UPDATE_MANIFEST_URL", ""))
    args = parser.parse_args()

    version = (args.version or read_project_version()).strip().lstrip("vV")
    update_id = str(args.update_id or "").strip()
    manifest_url = args.manifest_url.strip()
    write_build_info(version, manifest_url, update_id)
    print(
        f"Wrote {BUILD_INFO.relative_to(ROOT)}: "
        f"version={version}, update_id={update_id or '<none>'}, manifest_url={manifest_url or '<disabled>'}"
    )


if __name__ == "__main__":
    main()
