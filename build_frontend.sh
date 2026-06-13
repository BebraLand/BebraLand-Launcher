#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

export UV_CACHE_DIR="$PWD/.uv-cache"
export UV_PYTHON_INSTALL_DIR="$PWD/.uv-python"

if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: uv not found in PATH."
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "Install Python runtime..."
uv python install 3.13

echo "Sync build dependencies..."
uv sync --extra build

echo "Write build metadata..."
uv run python scripts/write_build_info.py

echo "Build launcher..."
uv run pyinstaller --noconfirm BebraLandLauncher.spec

echo
echo "Done: $PWD/dist"
