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

Local `.env` is supported in the frontend folder:

```env
BEBRALAND_SERVER_URL=http://192.168.0.116:8765
```

OS env still wins over `.env`. Release builds bake the value into the launcher from a GitHub Actions repository secret named `BEBRALAND_SERVER_URL`. The release workflow stops before packaging if that secret is empty, malformed, or points to localhost.

## Play flow

When user clicks `Launch`:

1. Frontend requests latest manifest from backend over WebSocket.
2. Backend rebuilds manifest from server profile folder.
3. Frontend uses shared Minecraft/modloader cache if present; otherwise installs it once from profile metadata.
4. Frontend checks pack files by SHA256.
5. Missing/changed pack files download from backend `/files/...`.
6. Launcher downloads/caches authlib-injector, fetches backend Yggdrasil metadata, and starts installed Minecraft/modloader profile with selected RAM and Azuriom credentials.

Launcher keeps `/api/v1/ws` open while running. If backend shell/CLI creates, deletes, clones, edits RAM, or builds pack while server is running, backend pushes `profiles.changed` and the pack combo updates live.

If backend changes a profile runtime with `profile runtime` / `profile hotswap` / `profile loader`, the launcher keeps the same local instance slug, installs the new Minecraft/modloader version from the next manifest, syncs changed pack files, and launches that new installed version.

Pack controls:

- `Reinstall`: keeps shared Minecraft/authlib cache, downloads managed pack files again, and keeps local user data like `saves`, `screenshots`, `resourcepacks`, `shaderpacks`, options, and server list.
- `Delete`: removes the whole local instance folder for the selected pack from this computer.

Sync modes:

- default: enforce exact server hash
- whitelist: download once if missing, then keep user edits and do not delete matching extra local files
- blacklist: enforce exact server hash even inside whitelist folders

Frontend always protects local user data folders/files from pack cleanup: saves, screenshots, resource packs, shader packs, logs/crash reports, replay recordings, options, and server list.

Launcher saves settings, per-profile RAM overrides, Azuriom token, instances, and shared Minecraft/authlib cache in the native user data folder:

- Windows: `%APPDATA%\BebraLandLauncher`
- macOS: `~/Library/Application Support/BebraLandLauncher`
- Linux: `$XDG_DATA_HOME/BebraLandLauncher` or `~/.local/share/BebraLandLauncher`

Each profile still has its own instance folder for mods, config, saves, screenshots, and options. Minecraft assets, libraries, versions, Java runtime, modloader installs, and authlib-injector live once under the install folder's `.shared` directory and are reused by every matching profile.

If a matching 64-bit system Java is already installed, launcher finds it automatically, uses it, and skips downloading Mojang Java runtime. Matching means exact required major version from Minecraft metadata, for example Java 21 for Minecraft 1.21.1. If no safe match is found, launcher falls back to shared Mojang Java runtime. `BEBRALAND_JAVA_PATH` / `BEBRALAND_JAVA_HOME` are optional admin/debug hints, not required for normal users; set `BEBRALAND_USE_SYSTEM_JAVA=0` to disable auto-detect.

Backend sends `recommended_ram_mb` for each profile. Launcher uses that value by default, lets player change it with the RAM slider, and warns before launch if selected RAM is below recommended.

Backend can send `icon_url` and `background_url` for each profile. Launcher uses those assets for the profile rail, hero logo, and main background. If a profile has no background, launcher falls back to bundled `background_for_launcher.jpg`, also used by Settings and Account pages.

Backend can also send `optional_mods` for each profile. Launcher shows them as checkboxes, saves choices per profile in settings, applies defaults for new players, auto-enables `requires`, disables dependents when a required mod is turned off, and syncs only selected optional files. Disabled optional files are removed on next sync unless that optional mod has `keep_on_disable: true`.

## Build launcher

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

Output:

- Windows: `dist\BebraLandLauncher.exe`, `dist\BebraLandUpdater.exe`
- macOS/Linux: `dist/BebraLandLauncher`, `dist/BebraLandUpdater`

PyInstaller builds for the OS and CPU it runs on. Build Windows on Windows, macOS on macOS, and Linux on Linux.

Windows 32-bit note: current PySide6 wheels in this project support Windows x64/ARM64, not win32. A single Windows x64 EXE will not run on 32-bit Windows, and building a 32-bit fallback would require changing the GUI stack or pinning old dependencies. For the launcher and modern modded Minecraft, Windows x64 is the practical target.

## Build Windows installer

Install [Inno Setup 6](https://jrsoftware.org/isinfo.php), then run:

```powershell
.\build_setup.bat
```

Output: `dist\BebraLand-Launcher-Setup.exe`.

The installer defaults to `%LOCALAPPDATA%\Programs\BebraLand Launcher`, lets the user choose another folder, installs `BebraLandLauncher.exe` and `BebraLandUpdater.exe`, creates Desktop and Start Menu shortcuts, and adds an uninstaller.

## Update flow

Release builds ship one launcher and one updater per platform. Windows also ships an Inno Setup installer.

On start launcher downloads the shared update manifest from GitHub Releases:

```json
{
  "version": "9999.123",
  "display_version": "0.0.0.4",
  "update_id": "123",
  "releases": {
    "windows-x64": {
      "platform": "windows-x64",
      "url": "https://github.com/OWNER/REPO/releases/download/launcher-123/BebraLandLauncher-windows-x64.exe",
      "sha256": "..."
    }
  }
}
```

Platform IDs are `windows-x64`, `linux-x64`, `macos-arm64`, and `macos-x64` in the default GitHub workflow.

Update fields:

- `display_version`: the pretty version shown to players. It can go backward, repeat, or be changed for cosmetic reasons.
- `update_id`: the hidden monotonic release number. The launcher uses this to decide whether a release is newer.
- `version`: compatibility value for old launchers that still compare versions. The workflow writes this as `9999.<update_id>` so old `0.1.0` builds still update once.
- GitHub tag: only the GitHub Release identifier. It does not need to match `display_version`.

If `update_id` is newer than the bundled launcher update id, the launcher updates automatically, downloads the new binary into the user data `updates` folder, verifies `sha256`, then starts the installed updater from the install folder:

```text
BebraLandUpdater[.exe] --install-update --source <downloaded-binary> --target <old-binary> --pid <old-pid>
```

The updater waits for the old launcher to exit, copies the downloaded launcher over the old path through a temporary `.new` file, removes that temporary file on failure, and starts the updated launcher. It does not leave a `.bak` file. If the updater is missing, the downloaded launcher can still run the old `--apply-update` helper mode as fallback. The normal launcher cleans the user data `updates` folder on startup and before downloading another update.

Dev builds have no update channel unless `BEBRALAND_UPDATE_MANIFEST_URL` is set. In dev mode, launcher downloads the update but does not replace itself.

## GitHub release

This repo includes `.github/workflows/release.yml`.

Preferred release flow:

1. Open GitHub Actions.
2. Run `Release launcher`.
3. Enter the pretty display version, for example `0.0.0.4`.
4. Leave `release_tag` empty unless you need a custom unique tag.

Manual workflow releases use a safe tag like `launcher-123` by default, where `123` is GitHub's run number. This means the displayed launcher version can be `0.0.0.1` even if tag `v0.0.0.1` already exists.

Tag push still works for advanced/manual releases:

```powershell
git tag v0.2.0
git push origin v0.2.0
```

GitHub Actions should:

1. install uv-managed Python 3.13;
2. build Windows x64, Linux x64, macOS arm64, and macOS x64 launchers;
3. create one `latest.json` with `display_version`, `update_id`, compatibility `version`, and SHA256 for each platform launcher;
4. build `BebraLand-Launcher-Setup-windows-x64.exe` for Windows;
5. publish all launchers, updaters, `latest.json`, and the Windows installer to GitHub Release.

Players on Windows download `BebraLand-Launcher-Setup-windows-x64.exe` from the latest release. macOS/Linux players download their platform binary and keep the updater next to it. Future release builds auto-check:

```text
https://github.com/<owner>/<repo>/releases/latest/download/latest.json
```

Local test build with update channel:

```powershell
$env:BEBRALAND_BUILD_VERSION = "0.1.0"
$env:BEBRALAND_UPDATE_ID = "123"
$env:BEBRALAND_UPDATE_MANIFEST_URL = "https://github.com/OWNER/REPO/releases/latest/download/latest.json"
.\build_frontend.bat
```

Rollback flow:

1. Run the workflow again from a branch/commit that contains the older code you want.
2. Enter the old pretty `display_version` if you want players to see that number.
3. Let the workflow create a new tag like `launcher-124`.

Do not just mark an old GitHub Release as latest for rollback. Its `update_id` is older, so installed launchers may correctly ignore it. A rollback should be a new release with a new `update_id` and old code/artifacts.

## Auth

Azuriom auth works through backend. Backend Azuriom URL lives in backend `.env` as `AZURIOM_URL=...`.

Account page supports Azuriom Skin API:

- `Refresh`: loads current body preview from `/api/skin-api/avatars/body/<username>.png`.
- `Upload skin`: sends a PNG skin through backend websocket to Azuriom Skin API.
- `Upload cape`: sends a PNG cape through backend websocket to Azuriom Skin API, if capes are enabled in Azuriom.

Minecraft launch uses the verified Azuriom access token as the auth token and the backend-provided Minecraft profile as `username`/`uuid`. The launcher adds:

```text
-javaagent:<install-dir>/.shared/authlib-injector/authlib-injector-<version>.jar=<server>/api/yggdrasil/
-Dauthlibinjector.yggdrasil.prefetched=<metadata>
```

Set `AUTHLIB_INJECTOR_JAR` if you want to force a local jar instead of downloading from `https://authlib-injector.yushi.moe/artifact/latest.json`. Set `BEBRALAND_AUTHLIB_CACHE_DIR` or `BEBRALAND_SHARED_MINECRAFT_DIR` only for custom cache layouts.
