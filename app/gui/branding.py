"""Application icon for the window, taskbar, and dialogs."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

from app.utils.paths import project_root

APP_USER_MODEL_ID = "ANSNEWTECH.GenesisArtvisionEngine"


def app_logo_path() -> Path:
    """Original square logo used in the header and About dialog."""
    return project_root() / "assets" / "app_icon.jpg"


def app_icon_path() -> Path:
    """Prefer a Windows .ico, then the original logo JPEG."""
    assets = project_root() / "assets"
    ico = assets / "app_icon.ico"
    if ico.is_file():
        return ico
    return assets / "app_icon.jpg"


def load_app_icon() -> QIcon:
    path = app_icon_path()
    icon = QIcon()
    if not path.is_file():
        return icon
    if path.suffix.lower() == ".ico":
        return QIcon(str(path))
    pix = QPixmap(str(path))
    if pix.isNull():
        return icon
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(
            pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )
    return icon


def apply_windows_app_id() -> None:
    """Tell Windows this is Genesis, not python.exe, so the taskbar uses our icon."""
    if sys.platform != "win32":
        return
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)


def apply_app_icon(target) -> QIcon:
    """Set the Genesis icon on a QApplication or QWidget."""
    icon = load_app_icon()
    if not icon.isNull():
        target.setWindowIcon(icon)
    return icon
