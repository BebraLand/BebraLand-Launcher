from __future__ import annotations

import sys
import threading
from typing import Any, Callable

from PySide6.QtCore import QObject, Signal
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .api import ApiClient
from .config import DEFAULT_SERVER_URL
from .runtime import launch_minecraft, sync_manifest
from .settings import load_settings, save_settings
from .updater import can_self_replace, download_release, replace_current_exe


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
        self.profiles: list[dict[str, Any]] = []
        self.current_manifest: dict[str, Any] | None = None
        self.auto_sync_done = False

        self.bridge = Bridge()
        self.bridge.log.connect(self.log_line)
        self.bridge.error.connect(self.show_error)
        self.bridge.profiles.connect(self.set_profiles)
        self.bridge.auth.connect(self.set_auth)
        self.bridge.ask_update.connect(self.ask_update)
        self.bridge.replace_update.connect(replace_current_exe)
        self.bridge.progress.connect(self.set_progress)

        self.build_ui()
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
        self.sync_button = QPushButton("Sync")
        self.sync_button.clicked.connect(self.sync_selected)
        pack_row.addWidget(self.sync_button)
        self.launch_button = QPushButton("Launch")
        self.launch_button.clicked.connect(self.launch_selected)
        pack_row.addWidget(self.launch_button)
        root.addLayout(pack_row)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        root.addWidget(self.log_output, 1)

        self.status = QLabel(f"BebraLand Launcher {__version__}")
        root.addWidget(self.status)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

    def log_line(self, text: str) -> None:
        self.log_output.append(text)
        self.status.setText(text)

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
            self.status.setText(label)

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

    def reset_client(self) -> None:
        self.client = ApiClient(self.server_input.text().strip(), self.client.token)
        self.settings["server_url"] = self.client.server_url
        save_settings(self.settings)

    def selected_slug(self) -> str | None:
        selected = self.profile_combo.currentText()
        for profile in self.profiles:
            label = f"{profile['name']} ({profile['slug']})"
            if label == selected:
                return profile["slug"]
        return None

    def profile_changed(self) -> None:
        slug = self.selected_slug()
        if slug:
            self.settings["selected_profile"] = slug
            save_settings(self.settings)

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
            self.profile_combo.addItem(f"{profile['name']} ({profile['slug']})")
        if current_slug:
            for index, profile in enumerate(profiles):
                if profile["slug"] == current_slug:
                    self.profile_combo.setCurrentIndex(index)
                    break
        elif current:
            index = self.profile_combo.findText(current)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
        self.log_line(f"Profiles: {len(profiles)}")
        if profiles and not self.auto_sync_done:
            self.auto_sync_done = True
            self.sync_selected(auto=True)

    def set_auth(self, payload: dict[str, Any]) -> None:
        self.auth_user = payload["user"]
        if payload.get("access_token"):
            self.client.token = payload["access_token"]
            self.settings["access_token"] = payload["access_token"]
        self.settings["user"] = self.auth_user
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
                response = getattr(exc, "response", None)
                if response is not None and response.status_code in {401, 403}:
                    self.settings.pop("access_token", None)
                    self.settings.pop("user", None)
                    save_settings(self.settings)
                    self.client.token = None
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

    def sync_selected(self, auto: bool = False) -> None:
        slug = self.selected_slug()
        if not slug:
            if not auto:
                QMessageBox.warning(self, "BebraLand", "Choose pack first")
            return
        self.reset_client()

        def task() -> None:
            self.bridge.log.emit(f"Fetch manifest {slug}")
            manifest = self.client.latest_manifest(slug)
            sync_manifest(manifest, self.client.server_url, self.bridge.log.emit, self.bridge.progress.emit)
            self.current_manifest = manifest

        self.run_bg(task, popup=not auto)

    def launch_selected(self) -> None:
        slug = self.selected_slug()
        if not slug:
            QMessageBox.warning(self, "BebraLand", "Choose pack first")
            return
        self.reset_client()

        def task() -> None:
            manifest = self.current_manifest
            if not manifest or manifest["profile"]["slug"] != slug:
                manifest = self.client.latest_manifest(slug)
            game_dir = sync_manifest(manifest, self.client.server_url, self.bridge.log.emit, self.bridge.progress.emit)
            username = (self.auth_user or {}).get("display_name") or "BebraPlayer"
            launch_minecraft(manifest, game_dir, username, self.bridge.log.emit, self.bridge.progress.emit)
            self.current_manifest = manifest

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


def main() -> None:
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())
