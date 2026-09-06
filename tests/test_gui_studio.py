"""Headless regression coverage for the Genesis two-pane studio."""

from __future__ import annotations

import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QGroupBox, QScrollArea

from app.gui.main_window import HistoryDialog, MainWindow
from app.gui.preview_panel import PreviewPanel
from app.gui.progress_panel import ProgressPanel
from app.gui.prompt_window import PromptWindow
from app.gui.settings_panel import SettingsPanel
from app.gui.styles import APP_STYLE
from app.utils.validation import load_config


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_main_window_is_a_persistent_two_pane_studio(qapp, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("app.gui.main_window.check_ffmpeg", lambda: (True, "test ffmpeg"))
    settings_path = str(tmp_path / "studio-test.ini")
    monkeypatch.setattr(
        "app.gui.main_window.QSettings",
        lambda *_args: QSettings(settings_path, QSettings.Format.IniFormat),
    )
    window = MainWindow(load_config())
    assert window.studio_splitter.count() == 2
    assert [window.studio_splitter.widget(i).objectName() for i in range(2)] == [
        "ActivityPane",
        "PreviewPane",
    ]
    assert window.studio_splitter.childrenCollapsible() is False
    assert window.findChild(QScrollArea) is None
    assert window.preview.accessibleName()
    assert window.progress.accessibleName()
    assert {"Ctrl+Return", "Esc", "Ctrl+H"}.issubset(
        {shortcut.key().toString() for shortcut in window._shortcuts}
    )
    window.resize(window.minimumSize())
    window.show()
    qapp.processEvents()
    sections = window.settings.findChildren(QGroupBox)
    assert len(sections) == 6
    assert max(section.geometry().bottom() for section in sections) <= window.settings.height()
    window.studio_splitter.setSizes([480, 500])
    saved_sizes = window.studio_splitter.sizes()
    window.close()
    restored = MainWindow(load_config())
    restored.show()
    qapp.processEvents()
    assert restored.studio_splitter.sizes() == saved_sizes
    restored.close()


def test_settings_values_signal_and_preset_sync(qapp) -> None:
    panel = SettingsPanel(load_config())
    changes: list[bool] = []
    panel.settings_changed.connect(lambda: changes.append(True))
    panel.count.setValue(panel.count.value() + 1)
    assert changes
    assert panel.values()["count"] == panel.count.value()

    editing = panel.config.get("editing") or {}
    for name, preset in (editing.get("presets") or {}).items():
        index = panel.edit_preset.findData(name)
        panel.edit_preset.setCurrentIndex(index)
        assert panel.edit_intensity.value() == pytest.approx(
            float(preset.get("motion_scale", 1.0))
        )
        assert panel.caption_mode.currentData() == preset.get("caption_mode", "sidecar")


def test_activity_states_are_explicit_and_reset_cleanly(qapp) -> None:
    panel = ProgressPanel()
    panel.update_progress(percent=35, status="Rendering frames", phase="Rendering")
    assert panel.bar.value() == 35
    assert panel.phase.text() == "RENDERING"
    panel.set_paused(True)
    assert panel.phase.text() == "PAUSED"
    assert panel.bar.format() == "Paused"
    panel.set_upload_progress(62, "Uploading 62%")
    assert panel.bar.value() == 62
    panel.set_qc_summary({"passed": True, "warnings": []})
    assert "QC PASSED" in panel.qc_summary.text()
    panel.reset()
    assert panel.phase.text() == "READY"
    assert not panel.qc_summary.isVisible()


def test_preview_has_idle_state_badge_and_aspect_source(qapp) -> None:
    panel = PreviewPanel()
    assert "PREVIEW MONITOR" in panel.label.text()
    panel.set_resolution_badge((1920, 1080))
    assert "16:9" in panel.format_badge.text()
    panel.show_frame(np.zeros((90, 160, 3), dtype=np.uint8))
    assert panel.label.text() == ""
    assert panel.label._source.size().width() == 160
    panel.clear()
    assert "Choose your settings" in panel.label.text()


def test_history_empty_state_disables_direct_actions(qapp) -> None:
    class EmptyDatabase:
        @staticmethod
        def list_videos(_limit):
            return []

    class EmptyFactory:
        db = EmptyDatabase()

    dialog = HistoryDialog(EmptyFactory())
    assert not dialog.empty_state.isHidden()
    assert not dialog.open_btn.isEnabled()
    assert not dialog.youtube_btn.isEnabled()
    assert dialog.table.isHidden()


def test_prompt_has_accessible_ctrl_enter_submission(qapp) -> None:
    dialog = PromptWindow(load_config())
    sequences = {shortcut.key().toString() for shortcut in dialog._submit_shortcuts}
    assert {"Ctrl+Return", "Ctrl+Enter"} <= sequences
    assert dialog.editor.accessibleName()
    assert dialog.submit_btn.accessibleDescription()


def test_theme_contains_studio_and_accessibility_state_hooks() -> None:
    for selector in (
        "QSplitter#StudioSplitter::handle",
        "QFrame#SettingsDeck",
        "QFrame#ActivityPane",
        "QFrame#PreviewPane",
        "QLabel#HeaderStatePill",
        "QDoubleSpinBox",
        "QToolTip",
        "QTableWidget",
    ):
        assert selector in APP_STYLE
