$ErrorActionPreference = "Stop"
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot "..\.uv-cache"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot "..\.uv-python"
uv sync --extra build
uv run pyinstaller --noconfirm BebraLandLauncher.spec
