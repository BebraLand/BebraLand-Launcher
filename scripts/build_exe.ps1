$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot "..\.uv-cache"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot "..\.uv-python"
uv python install 3.13
uv sync --extra build
uv run python scripts\write_build_info.py
uv run pyinstaller --noconfirm BebraLandLauncher.spec
