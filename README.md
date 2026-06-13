# BebraLand Launcher Frontend

Python GUI launcher. Connects to backend through WebSocket, logs in by Azuriom, asks backend for profile manifest, installs Minecraft/modloader locally through `minecraft-launcher-lib`, checks local pack files by SHA256, downloads missing or changed pack files from backend, then starts Minecraft.

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

1. Frontend requests latest manifest from backend over WebSocket.
2. Backend rebuilds manifest from server profile folder.
3. Frontend uses existing Minecraft/modloader install if present; otherwise installs it locally from profile metadata.
4. Frontend checks pack files by SHA256.
5. Missing/changed pack files download from backend `/files/...`.
6. Launcher downloads/caches authlib-injector, fetches backend Yggdrasil metadata, and starts installed Minecraft/modloader profile with selected RAM and Azuriom credentials.

Launcher keeps `/api/v1/ws` open while running. If backend shell/CLI creates, deletes, clones, edits RAM, or builds pack while server is running, backend pushes `profiles.changed` and the pack combo updates live.

If backend changes a profile runtime with `profile runtime` / `profile hotswap` / `profile loader`, the launcher keeps the same local instance slug, installs the new Minecraft/modloader version from the next manifest, syncs changed pack files, and launches that new installed version.

Pack controls:

- `Reinstall`: downloads Minecraft runtime and managed pack files again, while keeping local user data like `saves`, `screenshots`, `resourcepacks`, `shaderpacks`, options, and server list.
- `Delete`: removes the whole local instance folder for the selected pack from this computer.

Sync modes:

- default: enforce exact server hash
- whitelist: download once if missing, then keep user edits and do not delete matching extra local files
- blacklist: enforce exact server hash even inside whitelist folders

Frontend always protects local user data folders/files from pack cleanup: saves, screenshots, resource packs, shader packs, logs/crash reports, replay recordings, options, and server list.

Launcher saves settings, per-profile RAM overrides, and Azuriom token in `%APPDATA%\BebraLandLauncher\settings.json`. Instance files live in `%APPDATA%\BebraLandLauncher\instances\<profile-slug>`.

Backend sends `recommended_ram_mb` for each profile. Launcher uses that value by default, lets player change it with the RAM slider, and warns before launch if selected RAM is below recommended.

## Build EXE

Windows:

```powershell
.\build_frontend.bat
```

Git Bash/Linux/macOS:

```sh
./build_frontend.sh
```

Old PowerShell helper still works:

```powershell
.\scripts\build_exe.ps1
```

Output: `dist\BebraLandLauncher.exe`.

## Update flow

On start launcher asks backend for update metadata over WebSocket. If backend release metadata has newer version, launcher downloads EXE, verifies SHA256, and if running as frozen Windows EXE replaces itself through small restart script.

## Auth

Azuriom auth works through backend. Backend Azuriom URL lives in backend `.env` as `AZURIOM_URL=...`.

Minecraft launch uses the verified Azuriom access token as the auth token and the backend-provided Minecraft profile as `username`/`uuid`. The launcher adds:

```text
-javaagent:%APPDATA%\BebraLandLauncher\authlib-injector\authlib-injector-<version>.jar=<server>/api/yggdrasil/
-Dauthlibinjector.yggdrasil.prefetched=<metadata>
```

Set `AUTHLIB_INJECTOR_JAR` if you want to force a local jar instead of downloading from `https://authlib-injector.yushi.moe/artifact/latest.json`.
