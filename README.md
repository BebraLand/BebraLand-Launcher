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

Backend can also send `optional_mods` for each profile. Launcher shows them as checkboxes, saves choices per profile in settings, applies defaults for new players, auto-enables `requires`, disables dependents when a required mod is turned off, and syncs only selected optional files. Disabled optional files are removed on next sync unless that optional mod has `keep_on_disable: true`.

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

Release builds are one-file Windows EXEs. No separate updater is shipped.

On start launcher downloads `latest.json` from GitHub Releases:

```json
{
  "version": "0.2.0",
  "platform": "windows",
  "url": "https://github.com/OWNER/REPO/releases/download/v0.2.0/BebraLandLauncher.exe",
  "sha256": "..."
}
```

If `version` is newer than the bundled launcher version, the launcher asks user to update, downloads the new EXE into `%APPDATA%\BebraLandLauncher\updates`, verifies `sha256`, then starts that downloaded EXE in updater mode:

```text
BebraLandLauncher.exe --apply-update --target <old-exe> --pid <old-pid>
```

The downloaded EXE waits for the old launcher to exit, moves old launcher to `BebraLandLauncher.exe.bak`, copies itself over the old path, and starts the updated launcher.

Dev builds have no update channel unless `BEBRALAND_UPDATE_MANIFEST_URL` is set. In dev mode, launcher downloads the update but does not replace itself.

## GitHub release

This repo includes `.github/workflows/release.yml`.

Release by tag:

```powershell
git tag v0.2.0
git push origin v0.2.0
```

Or run the `Release launcher` workflow manually and enter version like `0.2.0`.

GitHub Actions will:

1. install uv-managed Python 3.13;
2. build `dist\BebraLandLauncher.exe`;
3. create `dist\latest.json` with SHA256;
4. publish both files to GitHub Release.

Players download only `BebraLandLauncher.exe` from the latest release. Future release builds auto-check:

```text
https://github.com/<owner>/<repo>/releases/latest/download/latest.json
```

Local test build with update channel:

```powershell
$env:BEBRALAND_BUILD_VERSION = "0.1.0"
$env:BEBRALAND_UPDATE_MANIFEST_URL = "https://github.com/OWNER/REPO/releases/latest/download/latest.json"
.\build_frontend.bat
```

## Auth

Azuriom auth works through backend. Backend Azuriom URL lives in backend `.env` as `AZURIOM_URL=...`.

Minecraft launch uses the verified Azuriom access token as the auth token and the backend-provided Minecraft profile as `username`/`uuid`. The launcher adds:

```text
-javaagent:%APPDATA%\BebraLandLauncher\authlib-injector\authlib-injector-<version>.jar=<server>/api/yggdrasil/
-Dauthlibinjector.yggdrasil.prefetched=<metadata>
```

Set `AUTHLIB_INJECTOR_JAR` if you want to force a local jar instead of downloading from `https://authlib-injector.yushi.moe/artifact/latest.json`.
