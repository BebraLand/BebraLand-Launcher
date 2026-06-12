# BebraLand Launcher Frontend

Python GUI launcher. Connects to backend, logs in by Azuriom, asks backend for profile manifest, installs Minecraft/modloader locally through `minecraft-launcher-lib`, checks local pack files by SHA256, downloads missing or changed pack files from backend, then starts Minecraft.

## Run with uv

```powershell
cd "C:\Users\aurum\Desktop\custom bebraland launcher\BebraLand Launcher Frontend"
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
$env:UV_PYTHON_INSTALL_DIR = "$PWD\.uv-python"
uv sync
uv run bebraland-launcher
```

Default backend URL: `http://127.0.0.1:8765`.

## Play flow

When user clicks `Launch`:

1. Frontend requests latest manifest from backend.
2. Backend rebuilds manifest from server profile folder.
3. Frontend uses existing Minecraft/modloader install if present; otherwise installs it locally from profile metadata.
4. Frontend checks pack files by SHA256.
5. Missing/changed pack files download from backend `/files/...`.
6. Launcher starts installed Minecraft/modloader profile with selected RAM.

Sync modes:

- default: enforce exact server hash
- whitelist: download once if missing, then keep user edits and do not delete matching extra local files
- blacklist: enforce exact server hash even inside whitelist folders

Launcher saves settings, per-profile RAM overrides, and Azuriom token in `%APPDATA%\BebraLandLauncher\settings.json`. Instance files live in `%APPDATA%\BebraLandLauncher\instances\<profile-slug>`.

Backend sends `recommended_ram_mb` for each profile. Launcher uses that value by default, lets player change it with the RAM slider, and warns before launch if selected RAM is below recommended.

## Build EXE

```powershell
.\scripts\build_exe.ps1
```

Output: `dist\BebraLandLauncher.exe`.

## Update flow

On start launcher calls backend update endpoint. If backend release metadata has newer version, launcher downloads EXE, verifies SHA256, and if running as frozen Windows EXE replaces itself through small restart script.

## Auth

Azuriom auth works through backend. Backend Azuriom URL lives in backend `.env` as `AZURIOM_URL=...`.

Minecraft launch still uses `minecraft-launcher-lib.utils.generate_test_options()` for prototype mode. Next step: map Azuriom/Microsoft profile data into real `username`, `uuid`, `token` for `minecraft_launcher_lib.command.get_minecraft_command`.
