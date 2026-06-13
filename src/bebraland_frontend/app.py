from __future__ import annotations

import ctypes
import os
import sys
import threading
from typing import Any, Callable

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .api import ApiClient
from .config import DEFAULT_SERVER_URL
from .runtime import (
    delete_instance,
    install_mod_loader,
    instance_dir,
    instance_path,
    launch_minecraft,
    prepare_reinstall,
    sync_manifest,
)
from .settings import load_settings, save_settings
from .updater import can_self_replace, download_release, replace_current_exe


DEFAULT_RECOMMENDED_RAM_MB = 2048
MIN_RAM_MB = 512
MAX_RAM_MB = 16384
RESERVED_SYSTEM_RAM_MB = 1024
PROGRESS_DETAIL_WIDTH = 430


def is_progress_detail_part(text: str) -> bool:
    value = text.strip()
    if value.startswith("ETA ") or "/s" in value or value.endswith("files"):
        return True
    return " / " in value and any(unit in value for unit in (" B", " KB", " MB", " GB", " TB"))


def split_progress_label(label: str) -> tuple[str, str]:
    parts = label.split(" - ")
    for index, part in enumerate(parts[1:], start=1):
        if is_progress_detail_part(part):
            return " - ".join(parts[:index]), "    ".join(parts[index:])
    return label, ""


def detect_system_ram_mb() -> int | None:
    if sys.platform.startswith("win"):
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys // (1024 * 1024))
        return None

    if hasattr(os, "sysconf"):
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError):
            return None
        if isinstance(pages, int) and isinstance(page_size, int):
            return int(pages * page_size // (1024 * 1024))
    return None


def launcher_ram_limit_mb() -> int:
    total = detect_system_ram_mb()
    if not total:
        return MAX_RAM_MB
    return max(MIN_RAM_MB, min(MAX_RAM_MB, total - RESERVED_SYSTEM_RAM_MB))


def clamp_ram_mb(value: Any, maximum: int) -> int:
    try:
        ram_mb = int(value)
    except (TypeError, ValueError):
        ram_mb = DEFAULT_RECOMMENDED_RAM_MB
    return max(MIN_RAM_MB, min(ram_mb, maximum))


class Bridge(QObject):
    log = Signal(str)
    error = Signal(str)
    profiles = Signal(list)
    auth = Signal(dict)
    ask_update = Signal(dict)
    replace_update = Signal(object)
    progress = Signal(int, int, str)


class LauncherWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BebraLand Launcher")
        self.resize(860, 540)
        self.setMinimumSize(760, 460)

        self.settings = load_settings()
        self.client = ApiClient(self.settings.get("server_url", DEFAULT_SERVER_URL), self.settings.get("access_token"))
        self.auth_user: dict[str, Any] | None = self.settings.get("user")
        self.minecraft_profile: dict[str, Any] | None = self.settings.get("minecraft_profile")
        self.profiles: list[dict[str, Any]] = []
        self.max_ram_mb = launcher_ram_limit_mb()

        self.bridge = Bridge()
        self.bridge.log.connect(self.log_line)
        self.bridge.error.connect(self.show_error)
        self.bridge.profiles.connect(self.set_profiles)
        self.bridge.auth.connect(self.set_auth)
        self.bridge.ask_update.connect(self.ask_update)
        self.bridge.replace_update.connect(replace_current_exe)
        self.bridge.progress.connect(self.set_progress)

        self.build_ui()
        self.configure_client_events()
        if self.auth_user:
            self.show_logged_user(self.auth_user, prefix="Saved login")
        self.verify_saved_login()
        self.refresh_profiles()
        self.check_update()

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(10)

        server_row = QHBoxLayout()
        server_row.addWidget(QLabel("Server"))
        self.server_input = QLineEdit(self.settings.get("server_url", DEFAULT_SERVER_URL))
        server_row.addWidget(self.server_input, 1)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.refresh_profiles)
        server_row.addWidget(self.connect_button)
        root.addLayout(server_row)

        auth_grid = QGridLayout()
        auth_grid.addWidget(QLabel("Azuriom"), 0, 0)
        self.az_email_input = QLineEdit()
        self.az_email_input.setPlaceholderText("email or username")
        auth_grid.addWidget(self.az_email_input, 0, 1)
        self.az_password_input = QLineEdit()
        self.az_password_input.setPlaceholderText("password")
        self.az_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        auth_grid.addWidget(self.az_password_input, 0, 2)
        self.az_2fa_input = QLineEdit()
        self.az_2fa_input.setPlaceholderText("2FA")
        self.az_2fa_input.setMaximumWidth(120)
        auth_grid.addWidget(self.az_2fa_input, 0, 3, 1, 2)
        self.az_login_button = QPushButton("Login Azuriom")
        self.az_login_button.clicked.connect(self.azuriom_login)
        auth_grid.addWidget(self.az_login_button, 0, 5)
        self.auth_label = QLabel("Not logged in")
        auth_grid.addWidget(self.auth_label, 1, 0, 1, 6)
        auth_grid.setColumnStretch(1, 1)
        root.addLayout(auth_grid)

        pack_row = QHBoxLayout()
        pack_row.addWidget(QLabel("Pack"))
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self.profile_changed)
        pack_row.addWidget(self.profile_combo, 1)
        self.launch_button = QPushButton("Launch")
        self.launch_button.clicked.connect(self.launch_selected)
        pack_row.addWidget(self.launch_button)
        self.reinstall_button = QPushButton("Reinstall")
        self.reinstall_button.clicked.connect(self.reinstall_selected)
        pack_row.addWidget(self.reinstall_button)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_selected)
        self.delete_button.setStyleSheet("color: #b91c1c;")
        pack_row.addWidget(self.delete_button)
        root.addLayout(pack_row)

        ram_row = QHBoxLayout()
        ram_row.addWidget(QLabel("RAM"))
        self.ram_slider = QSlider(Qt.Orientation.Horizontal)
        self.ram_slider.setRange(MIN_RAM_MB, self.max_ram_mb)
        self.ram_slider.setSingleStep(512)
        self.ram_slider.setPageStep(1024)
        self.ram_slider.setTickInterval(1024)
        self.ram_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.ram_slider.valueChanged.connect(self.ram_slider_changed)
        ram_row.addWidget(self.ram_slider, 1)
        self.ram_spin = QSpinBox()
        self.ram_spin.setRange(MIN_RAM_MB, self.max_ram_mb)
        self.ram_spin.setSingleStep(512)
        self.ram_spin.setSuffix(" MB")
        self.ram_spin.valueChanged.connect(self.ram_spin_changed)
        ram_row.addWidget(self.ram_spin)
        self.ram_hint = QLabel("")
        self.ram_hint.setMinimumWidth(220)
        self.ram_hint.setWordWrap(True)
        ram_row.addWidget(self.ram_hint)
        root.addLayout(ram_row)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        root.addWidget(self.log_output, 1)

        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        self.status = QLabel(f"BebraLand Launcher {__version__}")
        self.status.setMinimumWidth(0)
        self.status.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        status_row.addWidget(self.status, 1)
        self.progress_detail = QLabel("")
        self.progress_detail.setFixedWidth(PROGRESS_DETAIL_WIDTH)
        self.progress_detail.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        detail_font = QFont("Consolas")
        detail_font.setStyleHint(QFont.StyleHint.Monospace)
        self.progress_detail.setFont(detail_font)
        status_row.addWidget(self.progress_detail)
        root.addLayout(status_row)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

    def log_line(self, text: str) -> None:
        self.log_output.append(text)
        self.status.setText(text)
        self.progress_detail.clear()

    def show_error(self, text: str) -> None:
        self.log_line(f"Error: {text}")
        QMessageBox.critical(self, "BebraLand", text)

    def set_progress(self, value: int, maximum: int, label: str) -> None:
        if maximum > 0:
            self.progress_bar.setRange(0, maximum)
            self.progress_bar.setValue(max(0, min(value, maximum)))
        elif value > 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(max(0, min(value, 100)))
        if label:
            status_text, detail_text = split_progress_label(label)
            self.status.setText(status_text)
            self.status.setToolTip(label)
            self.progress_detail.setText(detail_text)

    def run_bg(self, fn: Callable[[], Any], popup: bool = True) -> None:
        def worker() -> None:
            try:
                fn()
            except Exception as exc:
                if popup:
                    self.bridge.error.emit(str(exc))
                else:
                    self.bridge.log.emit(f"Error: {exc}")

        threading.Thread(target=worker, daemon=True).start()

    def configure_client_events(self) -> None:
        self.client.set_event_handlers(
            profiles_changed=self.bridge.profiles.emit,
            log=self.bridge.log.emit,
        )
        self.client.start_event_stream()

    def reset_client(self) -> None:
        server_url = self.server_input.text().strip()
        if server_url.rstrip("/") != self.client.server_url:
            token = self.client.token
            self.client.close()
            self.client = ApiClient(server_url, token)
            self.configure_client_events()
        self.settings["server_url"] = self.client.server_url
        save_settings(self.settings)

    def selected_slug(self) -> str | None:
        selected_data = self.profile_combo.currentData()
        if selected_data:
            return str(selected_data)
        selected = self.profile_combo.currentText()
        for profile in self.profiles:
            label = f"{profile['name']} ({profile['slug']})"
            if label == selected:
                return profile["slug"]
        return None

    def selected_profile(self) -> dict[str, Any] | None:
        slug = self.selected_slug()
        if not slug:
            return None
        for profile in self.profiles:
            if profile["slug"] == slug:
                return profile
        return None

    def recommended_ram_mb(self, profile: dict[str, Any] | None = None) -> int:
        profile = profile or self.selected_profile()
        if not profile:
            return DEFAULT_RECOMMENDED_RAM_MB
        return clamp_ram_mb(profile.get("recommended_ram_mb", DEFAULT_RECOMMENDED_RAM_MB), self.max_ram_mb)

    def raw_recommended_ram_mb(self, profile: dict[str, Any] | None = None) -> int:
        profile = profile or self.selected_profile()
        if not profile:
            return DEFAULT_RECOMMENDED_RAM_MB
        try:
            return int(profile.get("recommended_ram_mb", DEFAULT_RECOMMENDED_RAM_MB))
        except (TypeError, ValueError):
            return DEFAULT_RECOMMENDED_RAM_MB

    def selected_ram_mb(self) -> int:
        return clamp_ram_mb(self.ram_spin.value(), self.max_ram_mb)

    def ram_overrides(self) -> dict[str, Any]:
        overrides = self.settings.get("profile_ram_mb")
        if not isinstance(overrides, dict):
            overrides = {}
            self.settings["profile_ram_mb"] = overrides
        return overrides

    def profile_ram_value(self, profile: dict[str, Any]) -> int:
        overrides = self.ram_overrides()
        return clamp_ram_mb(overrides.get(profile["slug"], profile.get("recommended_ram_mb")), self.max_ram_mb)

    def set_ram_controls(self, ram_mb: int, save: bool = False) -> None:
        ram_mb = clamp_ram_mb(ram_mb, self.max_ram_mb)
        self.ram_slider.blockSignals(True)
        self.ram_spin.blockSignals(True)
        self.ram_slider.setValue(ram_mb)
        self.ram_spin.setValue(ram_mb)
        self.ram_slider.blockSignals(False)
        self.ram_spin.blockSignals(False)
        self.update_ram_hint()
        if save:
            profile = self.selected_profile()
            if profile:
                overrides = self.ram_overrides()
                overrides[profile["slug"]] = ram_mb
                save_settings(self.settings)

    def update_ram_controls(self) -> None:
        profile = self.selected_profile()
        if profile:
            self.set_ram_controls(self.profile_ram_value(profile), save=False)
        else:
            self.set_ram_controls(DEFAULT_RECOMMENDED_RAM_MB, save=False)

    def update_ram_hint(self) -> None:
        profile = self.selected_profile()
        recommended = self.recommended_ram_mb(profile)
        value = self.selected_ram_mb()
        raw_recommended = self.raw_recommended_ram_mb(profile)
        if raw_recommended > self.max_ram_mb:
            self.ram_hint.setText(f"Recommended {raw_recommended} MB, capped at {self.max_ram_mb} MB")
            self.ram_hint.setStyleSheet("color: #b45309;")
        elif value < recommended:
            self.ram_hint.setText(f"Below recommended: {recommended} MB")
            self.ram_hint.setStyleSheet("color: #b91c1c;")
        else:
            self.ram_hint.setText(f"Recommended: {recommended} MB")
            self.ram_hint.setStyleSheet("color: #4b5563;")

    def ram_slider_changed(self, value: int) -> None:
        self.set_ram_controls(value, save=True)

    def ram_spin_changed(self, value: int) -> None:
        self.set_ram_controls(value, save=True)

    def profile_changed(self) -> None:
        slug = self.selected_slug()
        if slug:
            self.settings["selected_profile"] = slug
            save_settings(self.settings)
        self.update_ram_controls()

    def refresh_profiles(self) -> None:
        self.reset_client()

        def task() -> None:
            self.bridge.log.emit("Load profiles")
            self.bridge.profiles.emit(self.client.get_profiles())

        self.run_bg(task)

    def set_profiles(self, profiles: list[dict[str, Any]]) -> None:
        current_slug = self.settings.get("selected_profile")
        current = self.profile_combo.currentText()
        self.profiles = profiles
        self.profile_combo.clear()
        for profile in profiles:
            self.profile_combo.addItem(f"{profile['name']} ({profile['slug']})", profile["slug"])
        if current_slug:
            for index, profile in enumerate(profiles):
                if profile["slug"] == current_slug:
                    self.profile_combo.setCurrentIndex(index)
                    break
        elif current:
            index = self.profile_combo.findText(current)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
        self.update_ram_controls()
        self.log_line(f"Profiles: {len(profiles)}")

    def set_auth(self, payload: dict[str, Any]) -> None:
        self.auth_user = payload["user"]
        self.minecraft_profile = payload.get("minecraft_profile") or self.minecraft_profile
        if payload.get("access_token"):
            self.client.token = payload["access_token"]
            self.settings["access_token"] = payload["access_token"]
        self.settings["user"] = self.auth_user
        if self.minecraft_profile:
            self.settings["minecraft_profile"] = self.minecraft_profile
        save_settings(self.settings)
        self.show_logged_user(self.auth_user, prefix="Logged in")

    def show_logged_user(self, user: dict[str, Any], prefix: str = "Logged in") -> None:
        name = user.get("display_name") or user.get("username") or "AzuriomUser"
        user_id = user.get("id") or user.get("azuriom_id") or "unknown"
        text = f"{prefix}: {name} ({user_id})"
        self.auth_label.setText(text)
        self.log_line(text)

    def verify_saved_login(self) -> None:
        token = self.client.token
        if not token:
            return

        def task() -> None:
            try:
                payload = self.client.azuriom_verify(token)
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                response = getattr(exc, "response", None)
                if status_code in {401, 403} or (response is not None and response.status_code in {401, 403}):
                    self.settings.pop("access_token", None)
                    self.settings.pop("user", None)
                    self.settings.pop("minecraft_profile", None)
                    save_settings(self.settings)
                    self.client.token = None
                    self.minecraft_profile = None
                    self.bridge.log.emit("Saved login expired")
                else:
                    self.bridge.log.emit("Saved login not verified")
                return
            payload["access_token"] = token
            self.bridge.auth.emit(payload)

        threading.Thread(target=task, daemon=True).start()

    def azuriom_login(self) -> None:
        email = self.az_email_input.text().strip()
        password = self.az_password_input.text()
        code = self.az_2fa_input.text().strip() or None
        self.reset_client()

        def task() -> None:
            payload = self.client.azuriom_login(email, password, code)
            if payload.get("status") == "pending":
                self.bridge.log.emit(payload.get("message") or "Azuriom 2FA code required")
                return
            self.bridge.auth.emit(payload)

        self.run_bg(task)

    def launch_selected(self) -> None:
        slug = self.selected_slug()
        if not slug:
            QMessageBox.warning(self, "BebraLand", "Choose pack first")
            return
        if not self.client.token or not self.auth_user:
            QMessageBox.warning(self, "BebraLand", "Login Azuriom first")
            return
        if not self.minecraft_profile:
            QMessageBox.warning(self, "BebraLand", "Saved login is not verified yet")
            return
        profile = self.selected_profile()
        recommended_ram_mb = self.recommended_ram_mb(profile)
        ram_mb = self.selected_ram_mb()
        if ram_mb < recommended_ram_mb:
            answer = QMessageBox.question(
                self,
                "BebraLand RAM",
                f"Selected RAM ({ram_mb} MB) is below recommended ({recommended_ram_mb} MB). Launch anyway?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.reset_client()

        def task() -> None:
            self.bridge.log.emit(f"Fetch manifest {slug}")
            manifest = self.client.latest_manifest(slug)
            game_dir = instance_dir(manifest["profile"]["slug"])
            installed_version = install_mod_loader(manifest, game_dir, self.bridge.log.emit, self.bridge.progress.emit)
            game_dir = sync_manifest(manifest, self.client.server_url, self.bridge.log.emit, self.bridge.progress.emit)
            username = (self.auth_user or {}).get("display_name") or "BebraPlayer"
            launch_minecraft(
                manifest,
                game_dir,
                username,
                self.bridge.log.emit,
                self.bridge.progress.emit,
                installed_version=installed_version,
                ram_mb=ram_mb,
                server_url=self.client.server_url,
                access_token=self.client.token,
                minecraft_profile=self.minecraft_profile,
            )

        self.run_bg(task)

    def reinstall_selected(self) -> None:
        slug = self.selected_slug()
        if not slug:
            QMessageBox.warning(self, "BebraLand", "Choose pack first")
            return
        profile = self.selected_profile() or {}
        name = profile.get("name") or slug
        answer = QMessageBox.question(
            self,
            "BebraLand reinstall",
            (
                f"Reinstall local pack '{name}'?\n\n"
                "Saves, screenshots, resource packs, shader packs, options, and server list stay. "
                "Minecraft runtime and managed pack files download again."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.reset_client()

        def task() -> None:
            self.bridge.log.emit(f"Fetch manifest {slug}")
            manifest = self.client.latest_manifest(slug)
            game_dir = prepare_reinstall(manifest, self.bridge.log.emit)
            install_mod_loader(manifest, game_dir, self.bridge.log.emit, self.bridge.progress.emit)
            sync_manifest(manifest, self.client.server_url, self.bridge.log.emit, self.bridge.progress.emit)
            self.bridge.log.emit(f"Reinstalled {slug}")

        self.run_bg(task)

    def delete_selected(self) -> None:
        slug = self.selected_slug()
        if not slug:
            QMessageBox.warning(self, "BebraLand", "Choose pack first")
            return
        profile = self.selected_profile() or {}
        name = profile.get("name") or slug
        path = instance_path(slug)
        answer = QMessageBox.question(
            self,
            "BebraLand delete",
            (
                f"Delete local pack '{name}' from this computer?\n\n"
                f"This removes everything in:\n{path}\n\n"
                "This cannot be undone."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        def task() -> None:
            delete_instance(slug, self.bridge.log.emit)

        self.run_bg(task)

    def check_update(self) -> None:
        self.reset_client()

        def task() -> None:
            payload = self.client.check_update(__version__)
            if not payload.get("update_available"):
                self.bridge.log.emit("Launcher up to date")
                return
            release = payload["release"]
            self.bridge.log.emit(f"Update available: {release['version']}")
            self.bridge.ask_update.emit(release)

        self.run_bg(task)

    def ask_update(self, release: dict[str, Any]) -> None:
        answer = QMessageBox.question(
            self,
            "BebraLand update",
            f"Install launcher {release['version']}?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        def task() -> None:
            downloaded = download_release(release, self.bridge.log.emit)
            self.bridge.log.emit(f"Downloaded: {downloaded}")
            if can_self_replace():
                self.bridge.log.emit("Restart launcher to apply update")
                self.bridge.replace_update.emit(downloaded)
            else:
                self.bridge.log.emit("Run downloaded EXE manually in dev mode")

        self.run_bg(task)

    def closeEvent(self, event: Any) -> None:
        self.client.close()
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())
