from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QWidget


FRONTEND_ROOT = Path(__file__).resolve().parents[2]
BUNDLED_ROOT = Path(getattr(sys, "_MEIPASS", FRONTEND_ROOT))
DEFAULT_BACKGROUND_PATH = BUNDLED_ROOT / "background_for_launcher.jpg"
GML_ASSETS_DIR = BUNDLED_ROOT / "resources" / "gml"
GML_IMAGES_DIR = GML_ASSETS_DIR / "Images"
GML_FONTS_DIR = GML_ASSETS_DIR / "Fonts"
NEWS_API_URL = os.environ.get("BEBRALAND_NEWS_API_URL", "https://bebraland.auuruum.me/api/posts")


def register_fonts(widget: QWidget) -> None:
    if GML_FONTS_DIR.exists():
        for font_path in GML_FONTS_DIR.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_path))
    widget.setFont(QFont("Manrope", 10))
