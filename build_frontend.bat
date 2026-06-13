@echo off
setlocal

cd /d "%~dp0"

set "UV_CACHE_DIR=%CD%\.uv-cache"
set "UV_PYTHON_INSTALL_DIR=%CD%\.uv-python"

where uv >nul 2>nul
if errorlevel 1 (
    echo ERROR: uv not found in PATH.
    echo Install uv first: https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

echo Install Python runtime...
uv python install 3.13
if errorlevel 1 exit /b %ERRORLEVEL%

echo Sync build dependencies...
uv sync --extra build
if errorlevel 1 exit /b %ERRORLEVEL%

echo Write build metadata...
uv run python scripts\write_build_info.py
if errorlevel 1 exit /b %ERRORLEVEL%

echo Build BebraLandLauncher.exe...
uv run pyinstaller --noconfirm BebraLandLauncher.spec
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo Done: %CD%\dist\BebraLandLauncher.exe
