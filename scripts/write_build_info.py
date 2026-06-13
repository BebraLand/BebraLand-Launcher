from __future__ import annotations

import argparse
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_INFO = ROOT / "src" / "bebraland_frontend" / "build_info.py"
PYPROJECT = ROOT / "pyproject.toml"


def load_dotenv() -> None:
    dotenv_path = ROOT / ".env"
    if not dotenv_path.is_file():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = value


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


def write_build_info(version: str, manifest_url: str, update_id: str, server_url: str) -> None:
    BUILD_INFO.write_text(
        "\n".join(
            [
                f'VERSION = "{version}"',
                f'UPDATE_ID = "{update_id}"',
                f'UPDATE_MANIFEST_URL = "{manifest_url}"',
                f'SERVER_URL = "{server_url}"',
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=os.environ.get("BEBRALAND_BUILD_VERSION"))
    parser.add_argument("--update-id", default=os.environ.get("BEBRALAND_UPDATE_ID", ""))
    parser.add_argument("--manifest-url", default=os.environ.get("BEBRALAND_UPDATE_MANIFEST_URL", ""))
    parser.add_argument("--server-url", default=os.environ.get("BEBRALAND_SERVER_URL", ""))
    args = parser.parse_args()

    version = (args.version or read_project_version()).strip().lstrip("vV")
    update_id = str(args.update_id or "").strip()
    manifest_url = args.manifest_url.strip()
    server_url = args.server_url.strip()
    write_build_info(version, manifest_url, update_id, server_url)
    print(
        f"Wrote {BUILD_INFO.relative_to(ROOT)}: "
        f"version={version}, update_id={update_id or '<none>'}, "
        f"manifest_url={manifest_url or '<disabled>'}, server_url={server_url or '<default>'}"
    )


if __name__ == "__main__":
    main()
