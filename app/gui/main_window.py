"""Main application window."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.generator import VideoFactory
from app.core.project import clean_all_temp
from app.gui.branding import apply_app_icon, app_logo_path
from app.gui.dialogs import ResultDialog, about_dialog, studio_info, studio_warn
from app.gui.preview_panel import PreviewPanel
from app.gui.progress_panel import ProgressPanel
from app.gui.settings_panel import SettingsPanel, engine_label, style_label
from app.gui.styles import APP_STYLE
from app.utils.paths import resolve_path
from app.video.ffmpeg import check_ffmpeg


class GenerateWorker(QThread):
    progress = Signal(dict)
    finished_batch = Signal(list)
    failed = Signal(str)

    def __init__(self, factory: VideoFactory, options: dict[str, Any]) -> None:
        super().__init__()
        self.factory = factory
        self.options = options

    def run(self) -> None:
        try:
            ai = self.factory.config.setdefault("ai", {})
            if self.options.get("ai_enabled"):
                ai["enabled"] = True
                ai["per_video"] = True
            else:
                # Keep catalogs usable; only disable per-video advisor for this run
                ai["per_video"] = False
            replay_spec = self.options.get("replay_spec")
            if replay_spec is not None:
                result = self.factory.render_spec(
                    replay_spec,
                    on_progress=lambda p: self.progress.emit(p),
                )
                self.finished_batch.emit([result])
                return
            results = self.factory.generate_batch(
                count=self.options.get("count", 1),
                unlimited=self.options.get("unlimited", False),
                on_progress=lambda p: self.progress.emit(p),
                engine=self.options.get("engine"),
                style=self.options.get("style"),
                resolution=self.options.get("resolution"),
                fps=self.options.get("fps"),
                duration=self.options.get("duration"),
                audio_enabled=self.options.get("audio_enabled"),
                thumbnail=self.options.get("thumbnail"),
                random_resolution=self.options.get("random_resolution", False),
                random_fps=self.options.get("random_fps", False),
                random_duration=self.options.get("random_duration", False),
                edit_preset=self.options.get("edit_preset"),
                edit_intensity=self.options.get("edit_intensity"),
                caption_mode=self.options.get("caption_mode"),
                seed=self.options.get("seed"),
                user_prompt=self.options.get("user_prompt"),
                prompt_mode=self.options.get("prompt_mode"),
                prompt_quality=self.options.get("prompt_quality"),
                youtube_upload=bool(self.options.get("youtube_upload")),
                youtube_privacy=self.options.get("youtube_privacy"),
            )
            self.finished_batch.emit(results)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class HistoryDialog(QDialog):
    regenerate = Signal(object)

    def __init__(self, factory: VideoFactory, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.factory = factory
        self.setWindowTitle("Video history — Genesis Artvision Engine")
        apply_app_icon(self)
        self.setStyleSheet(APP_STYLE)
        self.resize(1180, 560)
        self.setMinimumSize(940, 440)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(12)
        heading = QLabel("History")
        heading.setObjectName("DialogTitle")
        layout.addWidget(heading)
        hint = QLabel("Select a video, then open it or recreate it with the same seed.")
        hint.setObjectName("HintLabel")
        layout.addWidget(hint)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Thumb", "Date", "Engine", "Style", "Duration", "Resolution", "Seed", "Path"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setAccessibleName("Generated video history")
        self.table.setAccessibleDescription("Select a completed render to open or recreate it.")
        self.table.verticalHeader().setDefaultSectionSize(48)
        layout.addWidget(self.table)
        self.empty_state = QLabel(
            "No finished videos yet.\nCreate your first video and it will appear here."
        )
        self.empty_state.setObjectName("EmptyState")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setAccessibleName("History is empty")
        layout.addWidget(self.empty_state)

        buttons = QHBoxLayout()
        self.open_btn = QPushButton("Open video")
        self.open_btn.setObjectName("GenerateButton")
        self.folder_btn = QPushButton("Open folder")
        self.folder_btn.setObjectName("SecondaryButton")
        self.regen_btn = QPushButton("Make again from seed")
        self.regen_btn.setObjectName("SecondaryButton")
        self.caption_btn = QPushButton("Open captions")
        self.caption_btn.setObjectName("SecondaryButton")
        self.report_btn = QPushButton("Open manifest / QC")
        self.report_btn.setObjectName("SecondaryButton")
        self.youtube_btn = QPushButton("Open YouTube")
        self.youtube_btn.setObjectName("SecondaryButton")
        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("GhostButton")
        buttons.addWidget(self.open_btn)
        buttons.addWidget(self.folder_btn)
        buttons.addWidget(self.regen_btn)
        buttons.addWidget(self.caption_btn)
        buttons.addWidget(self.report_btn)
        buttons.addWidget(self.youtube_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)

        self.open_btn.clicked.connect(self._open_video)
        self.folder_btn.clicked.connect(self._open_folder)
        self.regen_btn.clicked.connect(self._regen)
        self.caption_btn.clicked.connect(self._open_caption)
        self.report_btn.clicked.connect(self._open_manifest)
        self.youtube_btn.clicked.connect(self._open_youtube)
        self.close_btn.clicked.connect(self.accept)
        self.table.itemDoubleClicked.connect(lambda _item: self._open_video())
        self.table.itemSelectionChanged.connect(self._update_history_actions)
        self._rows: list = []
        self.reload()

    def reload(self) -> None:
        self._rows = self.factory.db.list_videos(200)
        self.table.clearContents()
        self.table.setRowCount(len(self._rows))
        for i, row in enumerate(self._rows):
            thumb_item = QTableWidgetItem("")
            if row.thumbnail_path and Path(row.thumbnail_path).exists():
                pix = QPixmap(row.thumbnail_path).scaled(
                    72,
                    40,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                thumb_item.setData(Qt.ItemDataRole.DecorationRole, pix)
            self.table.setItem(i, 0, thumb_item)
            self.table.setItem(i, 1, QTableWidgetItem(row.created_at))
            self.table.setItem(i, 2, QTableWidgetItem(row.engine))
            self.table.setItem(i, 3, QTableWidgetItem(row.style))
            self.table.setItem(i, 4, QTableWidgetItem(f"{row.duration:.0f}s"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{row.width}x{row.height}"))
            self.table.setItem(i, 6, QTableWidgetItem(str(row.seed)))
            self.table.setItem(i, 7, QTableWidgetItem(row.output_path))
        has_rows = bool(self._rows)
        self.table.setVisible(has_rows)
        self.empty_state.setVisible(not has_rows)
        for button in (
            self.open_btn,
            self.folder_btn,
            self.regen_btn,
            self.caption_btn,
            self.report_btn,
            self.youtube_btn,
        ):
            button.setEnabled(has_rows)
        if has_rows:
            self.table.selectRow(0)
        self._update_history_actions()

    def _update_history_actions(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        has_selection = bool(selected_rows)
        self.youtube_btn.setEnabled(
            has_selection and bool(self._rows[selected_rows[0].row()].youtube_url)
        )

    def _selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            studio_info(self, "Nothing selected", "Click a row in the table first.")
            return None
        return self._rows[rows[0].row()]

    def _open_video(self) -> None:
        row = self._selected()
        if not row:
            return
        path = Path(row.output_path)
        if path.exists():
            self._open_path(path)
        else:
            studio_warn(self, "Missing file", f"File not found:\n{path}")

    def _open_folder(self) -> None:
        row = self._selected()
        if not row:
            return
        self._open_path(Path(row.output_path).parent)

    def _regen(self) -> None:
        row = self._selected()
        if not row:
            return
        self.regenerate.emit(row)
        self.accept()

    def _open_caption(self) -> None:
        row = self._selected()
        if not row:
            return
        path = Path(row.output_path).with_suffix(".srt")
        if path.exists():
            self._open_path(path)
        else:
            studio_warn(self, "No captions", "This render has no SRT sidecar.")

    def _open_manifest(self) -> None:
        row = self._selected()
        if not row:
            return
        path = Path(row.output_path).with_suffix(".json")
        if path.exists():
            self._open_path(path)
        else:
            studio_warn(self, "No report", "This render has no JSON delivery report.")

    def _open_youtube(self) -> None:
        row = self._selected()
        if not row:
            return
        if row.youtube_url:
            self._open_path(row.youtube_url)
        else:
            studio_info(self, "Not uploaded", "This video has not been uploaded to YouTube.")

    @staticmethod
    def _open_path(path: Path | str) -> None:
        target = str(path)
        if sys.platform.startswith("win"):
            os.startfile(target)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target])
        else:
            subprocess.Popen(["xdg-open", target])


class MainWindow(QMainWindow):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.config = config
        self.factory = VideoFactory(config)
        self.worker: GenerateWorker | None = None
        self._batch_started = 0.0
        self._video_index = 0
        self._video_total: int | None = 1
        self._last_output: Path | None = None
        self._ai_wait_started = 0.0
        self._ai_wait_message = ""
        self._ai_timer = QTimer(self)
        self._ai_timer.setInterval(400)
        self._ai_timer.timeout.connect(self._tick_ai_wait)
        self.setWindowTitle("Genesis Artvision Engine — ANSNEW TECH")
        apply_app_icon(self)
        self._ui_settings = QSettings("ANSNEW TECH", "Genesis Artvision Engine")
        self.resize(1440, 860)
        self.setMinimumSize(980, 720)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        geometry = self._ui_settings.value("studio/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        splitter_state = self._ui_settings.value("studio/two_pane_splitter")
        if splitter_state is not None:
            self.studio_splitter.restoreState(splitter_state)
        self._check_ffmpeg()

    def _build_ui(self) -> None:
        native = self.menuBar()
        native.setNativeMenuBar(False)
        native.hide()

        central = QWidget()
        central.setObjectName("StudioRoot")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 8)
        root.setSpacing(10)

        header = QFrame()
        header.setObjectName("HeaderBar")
        bar = QHBoxLayout(header)
        bar.setContentsMargins(14, 9, 12, 9)
        bar.setSpacing(13)

        logo = QLabel()
        logo.setAccessibleName("Genesis Artvision logo")
        pix = QPixmap(str(app_logo_path()))
        if not pix.isNull():
            logo.setPixmap(
                pix.scaled(
                    42,
                    42,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        bar.addWidget(logo)

        brand = QVBoxLayout()
        brand.setSpacing(0)
        title = QLabel("GENESIS ARTVISION")
        title.setObjectName("BrandTitle")
        company = QLabel("ANSNEW TECH")
        company.setObjectName("BrandSub")
        brand.addWidget(title)
        brand.addWidget(company)
        bar.addLayout(brand)
        bar.addStretch(1)

        self.header_state = QLabel("READY")
        self.header_state.setObjectName("HeaderStatePill")
        self.header_state.setAccessibleName("Studio state")
        self.header_state.setAccessibleDescription("The studio is ready.")
        bar.addWidget(self.header_state)

        self._studio_menu = QMenuBar()
        self._studio_menu.setNativeMenuBar(False)
        self._fill_studio_menu(self._studio_menu)
        bar.addWidget(self._studio_menu, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(header)

        self.generate_btn = QPushButton("GENERATE VIDEO")
        self.generate_btn.setObjectName("GenerateButton")
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.setToolTip("Start creating unique procedural art videos.")
        self.generate_btn.setAccessibleName("Generate video")
        self.generate_btn.setAccessibleDescription(self.generate_btn.toolTip())
        self.generate_btn.setDefault(True)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("SecondaryButton")
        self.pause_btn.setToolTip("Temporarily pause rendering.")
        self.pause_btn.setAccessibleName("Pause generation")
        self.pause_btn.setAccessibleDescription(self.pause_btn.toolTip())
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setObjectName("SecondaryButton")
        self.resume_btn.setToolTip("Continue after pause.")
        self.resume_btn.setAccessibleName("Resume generation")
        self.resume_btn.setAccessibleDescription(self.resume_btn.toolTip())
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("DangerButton")
        self.stop_btn.setToolTip("Cancel the current run safely.")
        self.stop_btn.setAccessibleName("Stop generation")
        self.stop_btn.setAccessibleDescription(self.stop_btn.toolTip())

        self.output_btn = QPushButton("Output folder")
        self.output_btn.setObjectName("ChipButton")
        self.output_btn.setToolTip("Open the folder where finished MP4 files are saved.")
        self.history_btn = QPushButton("History")
        self.history_btn.setObjectName("ChipButton")
        self.history_btn.setToolTip("Browse past videos and recreate any seed.")
        self.prompt_btn = QPushButton("New prompt")
        self.prompt_btn.setObjectName("ChipButton")
        self.prompt_btn.setToolTip("Write a creative brief and generate a video.")
        self.clean_btn = QPushButton("Clean temporary files")
        self.clean_btn.setObjectName("ChipButton")
        self.clean_btn.setToolTip("Delete leftover temporary render files.")
        for button in (self.output_btn, self.history_btn, self.prompt_btn, self.clean_btn):
            button.setAccessibleName(button.text())
            button.setAccessibleDescription(button.toolTip())

        # Full-width control deck: compact and visible without scrolling.
        settings_deck = QFrame()
        settings_deck.setObjectName("SettingsDeck")
        settings_layout = QVBoxLayout(settings_deck)
        settings_layout.setContentsMargins(10, 8, 10, 9)
        settings_layout.setSpacing(6)
        settings_title = QLabel("PROJECT SETUP")
        settings_title.setObjectName("PanelEyebrow")
        settings_layout.addWidget(settings_title)
        self.settings = SettingsPanel(self.config)
        settings_layout.addWidget(self.settings)
        root.addWidget(settings_deck)

        # Transport stays directly below the project controls.
        transport = QHBoxLayout()
        transport.setSpacing(8)
        transport.addWidget(self.generate_btn, 3)
        transport.addWidget(self.pause_btn)
        transport.addWidget(self.resume_btn)
        transport.addWidget(self.stop_btn)
        root.addLayout(transport)

        # Balanced two-pane workspace: activity on the left, preview on the right.
        activity_pane = QFrame()
        activity_pane.setObjectName("ActivityPane")
        activity_pane.setMinimumWidth(360)
        activity_layout = QVBoxLayout(activity_pane)
        activity_layout.setContentsMargins(10, 8, 10, 10)
        activity_layout.setSpacing(6)
        activity_title = QLabel("ACTIVITY & DELIVERY")
        activity_title.setObjectName("PanelEyebrow")
        activity_layout.addWidget(activity_title)
        self.progress = ProgressPanel()
        activity_layout.addWidget(self.progress, 1)

        preview_pane = QFrame()
        preview_pane.setObjectName("PreviewPane")
        preview_pane.setMinimumWidth(420)
        preview_layout = QVBoxLayout(preview_pane)
        preview_layout.setContentsMargins(10, 8, 10, 10)
        preview_layout.setSpacing(6)
        preview_title = QLabel("PROGRAM MONITOR")
        preview_title.setObjectName("PanelEyebrow")
        preview_layout.addWidget(preview_title)
        self.preview = PreviewPanel()
        preview_layout.addWidget(self.preview, 1)

        self.studio_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.studio_splitter.setObjectName("StudioSplitter")
        self.studio_splitter.setChildrenCollapsible(False)
        self.studio_splitter.addWidget(activity_pane)
        self.studio_splitter.addWidget(preview_pane)
        self.studio_splitter.setStretchFactor(0, 1)
        self.studio_splitter.setStretchFactor(1, 1)
        self.studio_splitter.setSizes([560, 640])
        root.addWidget(self.studio_splitter, 1)

        # Secondary actions remain visible in one compact footer.
        actions = QFrame()
        actions.setObjectName("QuickActions")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(8, 6, 8, 6)
        actions_layout.setSpacing(7)
        actions_title = QLabel("QUICK ACTIONS")
        actions_title.setObjectName("PanelEyebrow")
        actions_layout.addWidget(actions_title)
        actions_layout.addWidget(self.prompt_btn)
        actions_layout.addWidget(self.history_btn)
        actions_layout.addWidget(self.output_btn)
        actions_layout.addWidget(self.clean_btn)
        actions_layout.addStretch(1)
        root.addWidget(actions)

        self.generate_btn.clicked.connect(self.start_generate)
        self.stop_btn.clicked.connect(self.stop_generate)
        self.pause_btn.clicked.connect(self.pause_generate)
        self.resume_btn.clicked.connect(self.resume_generate)
        self.output_btn.clicked.connect(self.open_output)
        self.history_btn.clicked.connect(self.show_history)
        self.prompt_btn.clicked.connect(self.open_prompt_window)
        self.clean_btn.clicked.connect(self.clean_temp)
        self.settings.settings_changed.connect(self._sync_preview_format)

        self._shortcuts = [
            QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.start_generate),
            QShortcut(QKeySequence("Escape"), self, activated=self.stop_generate),
            QShortcut(QKeySequence("Ctrl+Shift+P"), self, activated=self.pause_generate),
            QShortcut(QKeySequence("Ctrl+Shift+R"), self, activated=self.resume_generate),
            QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_output),
            QShortcut(QKeySequence("Ctrl+H"), self, activated=self.show_history),
        ]
        self.setTabOrder(self.generate_btn, self.pause_btn)
        self.setTabOrder(self.pause_btn, self.resume_btn)
        self.setTabOrder(self.resume_btn, self.stop_btn)
        self.setTabOrder(self.stop_btn, self.prompt_btn)

        self._set_running(False)
        self._sync_preview_format()

        status = QStatusBar()
        status.setAccessibleName("Application status")
        self.setStatusBar(status)
        self.statusBar().showMessage("Ready")
        self._refresh_youtube_channel_label()

    def _sync_preview_format(self) -> None:
        values = self.settings.values()
        resolution = values.get("resolution")
        self.preview.set_resolution_badge(resolution or "Random format")

    def closeEvent(self, event) -> None:  # noqa: N802
        self._ui_settings.setValue("studio/geometry", self.saveGeometry())
        self._ui_settings.setValue("studio/two_pane_splitter", self.studio_splitter.saveState())
        super().closeEvent(event)

    def _fill_studio_menu(self, bar: QMenuBar) -> None:
        file_menu = bar.addMenu("File")
        open_out = QAction("Open output folder", self)
        open_out.triggered.connect(self.open_output)
        file_menu.addAction(open_out)
        history = QAction("History", self)
        history.triggered.connect(self.show_history)
        file_menu.addAction(history)
        clean = QAction("Clean temp files", self)
        clean.triggered.connect(self.clean_temp)
        file_menu.addAction(clean)

        prompt_menu = bar.addMenu("Prompt")
        write_prompt = QAction("Write a prompt…", self)
        write_prompt.setShortcut("Ctrl+P")
        write_prompt.triggered.connect(self.open_prompt_window)
        prompt_menu.addAction(write_prompt)

        yt_menu = bar.addMenu("YouTube")
        connect_yt = QAction("Connect / switch channel…", self)
        connect_yt.setToolTip("Google will ask which account or Brand Account to use.")
        connect_yt.triggered.connect(self.connect_youtube)
        yt_menu.addAction(connect_yt)
        which_yt = QAction("Which channel is connected?", self)
        which_yt.triggered.connect(self.show_youtube_channel)
        yt_menu.addAction(which_yt)
        studio = QAction("Open this channel in Studio", self)
        studio.triggered.connect(self._open_youtube_studio)
        yt_menu.addAction(studio)
        disconnect_yt = QAction("Disconnect", self)
        disconnect_yt.triggered.connect(self.disconnect_youtube)
        yt_menu.addAction(disconnect_yt)

        help_menu = bar.addMenu("Help")
        about = QAction("About", self)
        about.triggered.connect(self._about)
        help_menu.addAction(about)

    def _set_running(self, running: bool) -> None:
        self.generate_btn.setEnabled(not running)
        self.settings.setEnabled(not running)
        self.prompt_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.pause_btn.setEnabled(running)
        self.resume_btn.setEnabled(False)
        state = "GENERATING" if running else "READY"
        self.header_state.setText(state)
        self.header_state.setAccessibleDescription(f"Studio state: {state.lower()}.")
        self.header_state.setProperty("active", running)
        self.header_state.style().unpolish(self.header_state)
        self.header_state.style().polish(self.header_state)
        self.preview.set_rendering_overlay(running, "Rendering preview…" if running else None)
        if not running:
            self.progress.set_paused(False)

    def _check_ffmpeg(self) -> None:
        ok, msg = check_ffmpeg()
        if not ok:
            self.statusBar().showMessage("FFmpeg missing — install FFmpeg before generating videos")
            studio_warn(
                self,
                "FFmpeg required",
                "FFmpeg was not found on this computer.\n\n"
                "Install it, then restart Genesis Artvision Engine.\n\n"
                f"Details:\n{msg}",
            )
        else:
            short = msg.split("(")[0].strip()
            extra = ""
            try:
                from app.publish.youtube import connected_channel, format_channel, is_connected

                if is_connected(self.config):
                    extra = f" · YT: {format_channel(connected_channel(self.config))}"
            except Exception:  # noqa: BLE001
                extra = ""
            self.statusBar().showMessage(f"Ready · FFmpeg found · {short}{extra}")
            self.progress.update_progress(status="Ready")

    @Slot()
    def start_generate(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        opts = self.settings.values()
        if opts.get("youtube_upload"):
            from app.publish.youtube import client_secret_path, connected_channel, format_channel, is_connected

            if not is_connected(self.config):
                studio_warn(
                    self,
                    "YouTube not connected",
                    "Upload to YouTube is on, but this app is not connected to a channel yet.\n\n"
                    "Use YouTube → Connect / switch channel…\n"
                    "On Google's screen pick the Brand Account for THAT channel, not only your Gmail.\n"
                    f"OAuth client file should be:\n{client_secret_path(self.config)}",
                )
                return
            dest = format_channel(connected_channel(self.config))
            self.statusBar().showMessage(f"Generating… then upload to {dest}")
        self._batch_started = time.perf_counter()
        self._video_index = 0
        self._video_total = None if opts["unlimited"] else opts["count"]
        self.progress.reset()
        self.progress.set_ai_visible(bool(opts.get("ai_enabled")))
        count_txt = "unlimited" if opts["unlimited"] else str(opts["count"])
        self.progress.update_progress(status=f"Starting… ({count_txt})")
        self.preview.clear()
        self._set_running(True)
        if opts.get("youtube_upload"):
            from app.publish.youtube import connected_channel, format_channel

            dest = format_channel(connected_channel(self.config))
            self.statusBar().showMessage(f"Generating… then upload to {dest}")
        else:
            self.statusBar().showMessage("Generating…")

        self._start_worker(opts)

    def _start_worker(self, options: dict[str, Any]) -> None:
        """Create and bind the generation worker through one stable signal path."""
        self.worker = GenerateWorker(self.factory, options)
        self.worker.progress.connect(self.on_progress, Qt.ConnectionType.QueuedConnection)
        self.worker.finished_batch.connect(self.on_finished, Qt.ConnectionType.QueuedConnection)
        self.worker.failed.connect(self.on_failed, Qt.ConnectionType.QueuedConnection)
        self.worker.start()

    @Slot()
    def stop_generate(self) -> None:
        if not (self.worker and self.worker.isRunning()):
            return
        self.factory.scheduler.stop()
        self._stop_ai_wait()
        self.progress.update_progress(status="Stopping… finishing safely", phase="Stopping", indeterminate=True)
        self.header_state.setText("STOPPING")
        self.preview.set_rendering_status("Stopping safely…", active=True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.statusBar().showMessage("Stopping…")

    @Slot()
    def pause_generate(self) -> None:
        if not (self.worker and self.worker.isRunning()):
            return
        self.factory.scheduler.pause()
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)
        self.progress.set_paused(True)
        self.header_state.setText("PAUSED")
        self.preview.set_rendering_status("Paused", active=True)
        self.statusBar().showMessage("Paused")

    @Slot()
    def resume_generate(self) -> None:
        if not (self.worker and self.worker.isRunning()):
            return
        self.factory.scheduler.resume()
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.progress.set_paused(False)
        self.progress.update_progress(status="Generating…", phase="Rendering")
        self.header_state.setText("GENERATING")
        self.preview.set_rendering_status("Rendering preview…", active=True)
        self.statusBar().showMessage("Generating…")

    @Slot(dict)
    def on_progress(self, payload: dict) -> None:
        phase = payload.get("phase")
        if phase == "batch":
            self._video_index = int(payload.get("video_index") or 1)
            self._video_total = payload.get("video_total")
            total_txt = "∞" if self._video_total is None else str(self._video_total)
            self.progress.set_batch_stats(batch=f"{self._video_index} of {total_txt}")
            return
        if phase == "ai":
            self._on_ai_progress(payload)
            return
        if phase in {"start", "render", "audio", "voice", "youtube", "qc"}:
            engine = payload.get("engine", "?")
            style = payload.get("style", "?")
            seed = payload.get("seed", "?")
            frame = int(payload.get("frame") or 0)
            total = int(payload.get("total_frames") or 1)
            pct = int(100 * frame / max(1, total))
            elapsed = time.perf_counter() - self._batch_started
            mins, secs = divmod(int(elapsed), 60)
            phase_status = {
                "start": "Preparing…",
                "voice": str(payload.get("message") or "Timing kids voice…"),
                "audio": "Creating soundtrack…",
                "render": f"Rendering frames ({frame}/{total})",
                "youtube": str(payload.get("message") or "Uploading to YouTube…"),
                "qc": str(payload.get("message") or "Checking export quality…"),
            }.get(str(phase), str(phase))
            self.progress.update_progress(
                percent=pct,
                current=f"{engine}  ·  {style}",
                seed=str(seed),
                time_text=f"{mins:02d}:{secs:02d}",
                status=phase_status,
                phase={
                    "start": "Preparing",
                    "voice": "Voice",
                    "audio": "Audio",
                    "render": "Rendering",
                    "youtube": "Upload",
                    "qc": "Quality control",
                }.get(str(phase), str(phase)),
                indeterminate=phase not in {"render", "youtube"},
                upload_percent=payload.get("percent") if phase == "youtube" else None,
            )
            self.preview.set_rendering_status(phase_status, active=phase != "qc")
            preview = payload.get("preview")
            if preview is not None:
                self.preview.show_frame(preview)

    def _on_ai_progress(self, payload: dict) -> None:
        status = str(payload.get("ai_status") or "")
        message = str(payload.get("message") or "")
        detail = str(payload.get("detail") or "")
        engine = payload.get("engine", "?")
        style = payload.get("style", "?")
        seed = payload.get("seed", "?")
        self.progress.update_progress(current=f"{engine}  ·  {style}", seed=str(seed))
        if status == "off":
            return
        if status == "asking":
            self._start_ai_wait(message)
            self.progress.set_ai_log(message)
            self.progress.update_progress(status="AI thinking…")
            self.statusBar().showMessage("AI advisor working…")
            return
        self._stop_ai_wait()
        if status in {"realize", "image", "text"}:
            self.progress.append_ai_log(detail or message)
            self.progress.update_progress(status=(message or "Building images & text…")[:90])
            self.statusBar().showMessage((message or "Building images & text…")[:90])
            return
        if status == "cache":
            self.progress.set_ai_log(detail or message)
            self.progress.update_progress(status="AI applied (cached)")
            self.statusBar().showMessage("AI applied (cached)")
        elif status == "applied":
            self.progress.set_ai_log(detail or message)
            self.progress.update_progress(status="AI applied")
            self.statusBar().showMessage("AI applied")
        else:
            self.progress.set_ai_log(message or "AI skipped.")
            short = (message.split("\n")[0] if message else "AI skipped")[:90]
            self.progress.update_progress(status=short)
            self.statusBar().showMessage(short)

    def _start_ai_wait(self, message: str) -> None:
        self._ai_wait_message = message
        self._ai_wait_started = time.perf_counter()
        if not self._ai_timer.isActive():
            self._ai_timer.start()

    def _stop_ai_wait(self) -> None:
        if self._ai_timer.isActive():
            self._ai_timer.stop()

    def _tick_ai_wait(self) -> None:
        elapsed = time.perf_counter() - self._ai_wait_started
        dots = "." * (1 + int(elapsed) % 3)
        self.progress.update_progress(status=f"AI thinking{dots} {elapsed:.0f}s")
        self.statusBar().showMessage(f"AI advisor working… {elapsed:.0f}s")
        self.progress.set_ai_log(f"{self._ai_wait_message}\nWaiting {elapsed:.0f}s")

    @Slot(list)
    def on_finished(self, results: list) -> None:
        self._stop_ai_wait()
        self._set_running(False)
        ok = sum(1 for r in results if r.success)
        ai_note = ""
        if results:
            last_spec = results[-1].spec
            if last_spec is not None and last_spec.params.get("ai_applied"):
                ai_note = " · AI applied"
                summary = last_spec.params.get("ai_summary")
                if summary:
                    self.progress.set_ai_log(str(summary))
        if not results:
            self.progress.update_progress(status="Stopped — no videos were saved", phase="Ready")
            self.header_state.setText("STOPPED")
            self.statusBar().showMessage("Stopped")
            return
        last = results[-1]
        qc_report = getattr(last, "qc", {}) or {}
        qc_warnings = list(qc_report.get("warnings") or [])
        qc_note = " · QC passed" if last.success and not qc_warnings else (
            f" · QC: {len(qc_warnings)} warning(s)" if qc_warnings else ""
        )
        yt_ok = [getattr(r, "youtube_url", None) for r in results if getattr(r, "youtube_url", None)]
        yt_err = [getattr(r, "youtube_error", None) for r in results if getattr(r, "youtube_error", None)]
        yt_note = ""
        if yt_ok:
            yt_note = f" · {len(yt_ok)} uploaded to YouTube"
        elif yt_err:
            yt_note = " · YouTube upload failed"
        self.progress.update_progress(
            percent=100 if ok else self.progress.bar.value(),
            status=f"Finished — {ok} of {len(results)} video(s) saved{ai_note}{yt_note}{qc_note}",
            phase="Complete",
            indeterminate=False,
        )
        self.progress.set_qc_summary(qc_report, passed=bool(last.success))
        self.header_state.setText("COMPLETE" if ok else "ATTENTION")
        self.statusBar().showMessage(f"Done · {ok}/{len(results)} succeeded{ai_note}{yt_note}{qc_note}")
        if last.success and last.output_path:
            self._last_output = Path(last.output_path)
            spec = last.spec
            engine = engine_label(str(last.engine or (spec.engine if spec else "?")))
            style = style_label(str(last.style or (spec.style if spec else "?")))
            seed = last.seed if last.seed is not None else (spec.seed if spec else "?")
            channel_label = ""
            try:
                from app.publish.youtube import connected_channel, format_channel, is_connected

                if is_connected(self.config):
                    channel_label = format_channel(connected_channel(self.config))
            except Exception:  # noqa: BLE001
                channel_label = ""
            dlg = ResultDialog(
                self,
                ok_count=ok,
                total=len(results),
                engine=engine,
                style=style,
                seed=seed,
                output_path=Path(last.output_path),
                thumbnail_path=Path(last.thumbnail_path) if last.thumbnail_path else None,
                youtube_url=getattr(last, "youtube_url", None),
                youtube_error=str(yt_err[0]) if yt_err else None,
                youtube_urls=[str(u) for u in yt_ok],
                channel_label=channel_label,
                caption_path=getattr(last, "caption_path", None),
                manifest_path=getattr(last, "manifest_path", None),
                qc=getattr(last, "qc", {}),
            )
            dlg.exec()
            clicked = dlg.clicked
            if clicked == "open_video":
                HistoryDialog._open_path(Path(last.output_path))
            elif clicked == "open_folder":
                HistoryDialog._open_path(Path(last.output_path).parent)
            elif clicked == "open_youtube" and last.youtube_url:
                HistoryDialog._open_path(last.youtube_url)
            elif clicked == "open_captions" and last.caption_path:
                HistoryDialog._open_path(last.caption_path)
            elif clicked == "open_manifest" and last.manifest_path:
                HistoryDialog._open_path(last.manifest_path)
        elif any(not r.success for r in results):
            errs = [r.error for r in results if r.error][:3]
            studio_warn(
                self,
                "Some videos failed",
                f"Succeeded: {ok}/{len(results)}\n\n" + "\n".join(str(e) for e in errs),
            )

    @Slot(str)
    def on_failed(self, message: str) -> None:
        self._stop_ai_wait()
        self._set_running(False)
        self.progress.update_progress(status="Something went wrong", phase="Failed", indeterminate=False)
        self.header_state.setText("FAILED")
        self.statusBar().showMessage("Failed")
        studio_warn(self, "Generation failed", message)

    def _refresh_youtube_channel_label(self) -> None:
        from app.publish.youtube import connected_channel, format_channel, is_connected

        if not is_connected(self.config):
            self.settings.set_youtube_channel("not connected")
            return
        info = connected_channel(self.config)
        self.settings.set_youtube_channel(format_channel(info) if info else "connected (name unknown — use YouTube menu)")

    @Slot()
    def connect_youtube(self) -> None:
        from app.gui.dialogs import StudioDialog
        from app.publish.youtube import YouTubePublishError, connect_youtube, format_channel

        if self.worker and self.worker.isRunning():
            studio_warn(self, "Busy", "Stop the current batch before connecting YouTube.")
            return
        hint = StudioDialog(
            self,
            title="Connect a YouTube channel",
            body=(
                "Google will open a browser. If you have many channels, do not stop at your Gmail — "
                "choose the Brand Account whose name matches the channel you want.\n\n"
                "This app uploads to that one channel until you switch."
            ),
            buttons=[("Cancel", "cancel"), ("Connect in browser", "connect")],
            window_title="YouTube",
        )
        if hint.exec() != QDialog.DialogCode.Accepted or hint.clicked != "connect":
            return
        try:
            info = connect_youtube(self.config, force=True)
        except YouTubePublishError as exc:
            studio_warn(self, "YouTube connect", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            studio_warn(self, "YouTube connect failed", str(exc))
            return
        label = format_channel(info)
        self._refresh_youtube_channel_label()
        studio_info(
            self,
            "Uploads go here",
            f"{label}\n\n"
            f"Channel ID: {info.get('id') or '?'}\n"
            f"{info.get('url') or ''}\n\n"
            "Wrong one? YouTube → Connect / switch channel… and pick a different Brand Account.",
        )
        self.statusBar().showMessage(f"YouTube uploads → {label}")

    @Slot()
    def show_youtube_channel(self) -> None:
        from app.publish.youtube import connected_channel, format_channel, is_connected

        if not is_connected(self.config):
            studio_info(
                self,
                "No channel yet",
                "Nothing is connected. Use YouTube → Connect / switch channel…",
            )
            return
        info = connected_channel(self.config) or {}
        studio_info(
            self,
            "Uploads go here",
            f"{format_channel(info)}\n\n"
            f"Channel ID: {info.get('id') or '?'}\n"
            f"{info.get('url') or ''}\n\n"
            "Wrong channel? YouTube → Connect / switch channel… and pick the Brand Account you want.",
        )

    @Slot()
    def disconnect_youtube(self) -> None:
        from app.publish.youtube import disconnect_youtube

        disconnect_youtube(self.config)
        self._refresh_youtube_channel_label()
        self.statusBar().showMessage("YouTube disconnected")
        studio_info(self, "YouTube", "Disconnected. Connect again to pick a channel.")

    @Slot()
    def _open_youtube_studio(self) -> None:
        from app.publish.youtube import connected_channel

        info = connected_channel(self.config) or {}
        HistoryDialog._open_path(info.get("studio") or info.get("url") or "https://studio.youtube.com/")

    @Slot()
    def open_output(self) -> None:
        path = resolve_path(self.config.get("output", {}).get("directory", "./output"))
        path.mkdir(parents=True, exist_ok=True)
        HistoryDialog._open_path(path)

    @Slot()
    def show_history(self) -> None:
        dlg = HistoryDialog(self.factory, self)
        dlg.regenerate.connect(self._regen_seed)
        dlg.exec()

    @Slot()
    def open_prompt_window(self) -> None:
        if self.worker and self.worker.isRunning():
            studio_warn(self, "Busy", "Stop the current batch before prompting a new video.")
            return
        from app.gui.prompt_window import PromptWindow

        dlg = PromptWindow(self.config, self)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.payload:
            return
        self._start_prompt_generate(dlg.payload)

    def _start_prompt_generate(self, payload: dict[str, Any]) -> None:
        opts = self.settings.values()
        opts["count"] = 1
        opts["unlimited"] = False
        opts["seed"] = None
        opts["engine"] = payload.get("engine")
        opts["style"] = None
        opts["user_prompt"] = payload.get("user_prompt")
        opts["prompt_mode"] = payload.get("prompt_mode") or "offline"
        opts["prompt_quality"] = payload.get("prompt_quality") or "1080"
        opts["duration"] = payload.get("duration")
        opts["random_duration"] = payload.get("duration") is None
        opts["random_resolution"] = False
        opts["random_fps"] = False
        opts["fps"] = 30
        opts["audio_enabled"] = True
        opts["thumbnail"] = True
        opts["ai_enabled"] = payload.get("prompt_mode") == "ai"
        quality = str(payload.get("prompt_quality") or "1080")
        prompt_text = str(payload.get("user_prompt") or "")
        from app.ai.prompt_brief import detect_resolution

        opts["resolution"] = detect_resolution(prompt_text, quality)

        self._batch_started = time.perf_counter()
        self._video_index = 0
        self._video_total = 1
        self.progress.reset()
        self.progress.set_ai_visible(True)
        self.progress.update_progress(status="Reading your prompt…")
        self.preview.clear()
        self._set_running(True)
        self.statusBar().showMessage("Generating from prompt…")

        self._start_worker(opts)

    @Slot(object)
    def _regen_seed(self, row: object) -> None:
        if self.worker and self.worker.isRunning():
            studio_warn(self, "Busy", "Stop the current batch before regenerating.")
            return
        seed = int(getattr(row, "seed"))
        try:
            from app.core.randomizer import ProjectSpec

            stored = json.loads(str(getattr(row, "params_json")))
            spec = ProjectSpec.from_dict(stored)
            spec.params["_replay_locked"] = True
        except Exception as exc:  # noqa: BLE001
            studio_warn(self, "Cannot replay", f"The stored project specification is invalid:\n{exc}")
            return
        opts = self.settings.values()
        opts["replay_spec"] = spec
        opts["count"] = 1
        opts["unlimited"] = False
        self._batch_started = time.perf_counter()
        self._set_running(True)
        self.progress.update_progress(status=f"Recreating seed {seed}…")
        self.progress.set_ai_visible(bool(opts.get("ai_enabled")))
        self._start_worker(opts)

    @Slot()
    def clean_temp(self) -> None:
        n = clean_all_temp(self.config)
        self.statusBar().showMessage(f"Cleaned {n} temporary item(s)")
        studio_info(self, "Temp files cleaned", f"Removed {n} temporary item(s).")

    def _about(self) -> None:
        about_dialog(self)
