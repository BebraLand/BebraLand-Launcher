from __future__ import annotations

import argparse
from datetime import date
import os
from pathlib import Path
import re
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
BUILD_INFO = ROOT / "src" / "bebraland_frontend" / "build_info.py"
PYPROJECT = ROOT / "pyproject.toml"
WINDOWS_VERSION_INFO_DIR = ROOT / "build"


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


def windows_file_version(version: str) -> tuple[int, int, int, int]:
    """Convert a display version to the four numeric fields Windows requires."""
    numbers = [int(value) for value in re.findall(r"\d+", version)[:4]]
    return tuple((numbers + [0, 0, 0, 0])[:4])  # type: ignore[return-value]


def write_windows_version_info(version: str) -> None:
    WINDOWS_VERSION_INFO_DIR.mkdir(parents=True, exist_ok=True)
    numeric_version = windows_file_version(version)
    file_version = ".".join(map(str, numeric_version))
    copyright_year = str(date.today().year)

    products = {
        "launcher": ("BebraLand Launcher", "BebraLandLauncher.exe"),
        "updater": ("BebraLand Launcher Updater", "BebraLandUpdater.exe"),
    }
    for resource_name, (description, original_filename) in products.items():
        content = f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={numeric_version},
    prodvers={numeric_version},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0),
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [
          StringStruct(u'CompanyName', u'BebraLand Team'),
          StringStruct(u'FileDescription', u'{description}'),
          StringStruct(u'FileVersion', u'{file_version}'),
          StringStruct(u'InternalName', u'{original_filename.removesuffix(".exe")}'),
          StringStruct(u'LegalCopyright', u'© {copyright_year} BebraLand Team'),
          StringStruct(u'OriginalFilename', u'{original_filename}'),
          StringStruct(u'ProductName', u'BebraLand Launcher'),
          StringStruct(u'ProductVersion', u'{version}'),
        ]),
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])]),
  ],
)
'''
        (WINDOWS_VERSION_INFO_DIR / f"{resource_name}_version_info.txt").write_text(
            content, encoding="utf-8"
        )


def validate_required_server_url(server_url: str) -> None:
    if not server_url:
        raise RuntimeError(
            "BEBRALAND_SERVER_URL is required for release builds. "
            "Configure the GitHub Actions repository secret before publishing a release."
        )

    parsed = urlparse(server_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise RuntimeError("BEBRALAND_SERVER_URL must be an absolute http(s) URL for release builds.")
    if parsed.hostname.lower() in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("BEBRALAND_SERVER_URL must not point to localhost for release builds.")


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
    if os.environ.get("BEBRALAND_REQUIRE_SERVER_URL", "").strip().lower() in {"1", "true", "yes"}:
        validate_required_server_url(server_url)
    write_build_info(version, manifest_url, update_id, server_url)
    write_windows_version_info(version)
    print(
        f"Wrote {BUILD_INFO.relative_to(ROOT)}: "
        f"version={version}, update_id={update_id or '<none>'}, "
        f"manifest_url={manifest_url or '<disabled>'}, server_url={server_url or '<default>'}"
    )


if __name__ == "__main__":
    main()
