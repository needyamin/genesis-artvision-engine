"""Main application window."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.generator import VideoFactory
from app.core.project import clean_all_temp
from app.gui.preview_panel import PreviewPanel
from app.gui.progress_panel import ProgressPanel
from app.gui.settings_panel import SettingsPanel
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
                seed=self.options.get("seed"),
            )
            self.finished_batch.emit(results)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class HistoryDialog(QDialog):
    regenerate = Signal(int)

    def __init__(self, factory: VideoFactory, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.factory = factory
        self.setWindowTitle("Video history — Genesis Artvision Engine")
        self.resize(920, 500)
        layout = QVBoxLayout(self)
        hint = QLabel("Select a video, then open it or recreate it with the same seed.")
        hint.setObjectName("HintLabel")
        layout.addWidget(hint)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Thumb", "Date", "Engine", "Style", "Duration", "Resolution", "Seed", "Path"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.open_btn = QPushButton("Open video")
        self.open_btn.setObjectName("SecondaryButton")
        self.folder_btn = QPushButton("Open folder")
        self.regen_btn = QPushButton("Make again from seed")
        self.close_btn = QPushButton("Close")
        buttons.addWidget(self.open_btn)
        buttons.addWidget(self.folder_btn)
        buttons.addWidget(self.regen_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)

        self.open_btn.clicked.connect(self._open_video)
        self.folder_btn.clicked.connect(self._open_folder)
        self.regen_btn.clicked.connect(self._regen)
        self.close_btn.clicked.connect(self.accept)
        self._rows: list = []
        self.reload()

    def reload(self) -> None:
        self._rows = self.factory.db.list_videos(200)
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
        if not self._rows:
            self.open_btn.setEnabled(False)
            self.folder_btn.setEnabled(False)
            self.regen_btn.setEnabled(False)

    def _selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Nothing selected", "Click a row in the table first.")
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
            QMessageBox.warning(self, "Missing file", f"File not found:\n{path}")

    def _open_folder(self) -> None:
        row = self._selected()
        if not row:
            return
        self._open_path(Path(row.output_path).parent)

    def _regen(self) -> None:
        row = self._selected()
        if not row:
            return
        self.regenerate.emit(int(row.seed))
        self.accept()

    @staticmethod
    def _open_path(path: Path) -> None:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])


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
        self.setWindowTitle("Genesis Artvision Engine — ANSNEW TECH")
        self.resize(1200, 820)
        self.setMinimumSize(980, 700)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self._check_ffmpeg()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 10, 16, 10)
        root.setSpacing(8)

        header = QVBoxLayout()
        header.setSpacing(0)
        title = QLabel("GENESIS ARTVISION ENGINE")
        title.setObjectName("BrandTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(title)

        company = QLabel("by ANSNEW TECH")
        company.setObjectName("BrandSub")
        company.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(company)

        hint = QLabel(
            "Click Generate — the app invents the art, colors, motion, and soundtrack for you. "
            "No topic, image, or prompt needed."
        )
        hint.setObjectName("HintLabel")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        header.addWidget(hint)
        root.addLayout(header)

        # Settings: fixed height section (2×2 grid) — always fully visible
        self.settings = SettingsPanel(self.config)
        root.addWidget(self.settings, 0)

        # Primary actions
        primary = QHBoxLayout()
        primary.setSpacing(10)
        self.generate_btn = QPushButton("GENERATE VIDEO")
        self.generate_btn.setObjectName("GenerateButton")
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.setToolTip("Start creating unique procedural art videos.")

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("SecondaryButton")
        self.pause_btn.setToolTip("Temporarily pause rendering.")
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setObjectName("SecondaryButton")
        self.resume_btn.setToolTip("Continue after pause.")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("DangerButton")
        self.stop_btn.setToolTip("Cancel the current run safely.")

        primary.addWidget(self.generate_btn, 3)
        primary.addWidget(self.pause_btn, 1)
        primary.addWidget(self.resume_btn, 1)
        primary.addWidget(self.stop_btn, 1)
        root.addLayout(primary)

        # Progress + preview fill remaining window space
        mid = QHBoxLayout()
        mid.setSpacing(12)
        self.progress = ProgressPanel()
        self.preview = PreviewPanel()
        mid.addWidget(self.progress, 2)
        mid.addWidget(self.preview, 3)
        root.addLayout(mid, 1)

        # Secondary actions always pinned at bottom
        secondary = QHBoxLayout()
        secondary.setSpacing(8)
        self.output_btn = QPushButton("Open output folder")
        self.output_btn.setToolTip("Open the folder where finished MP4 files are saved.")
        self.history_btn = QPushButton("History")
        self.history_btn.setToolTip("Browse past videos and recreate any seed.")
        self.clean_btn = QPushButton("Clean temp files")
        self.clean_btn.setToolTip("Delete leftover temporary render files.")
        secondary.addWidget(self.output_btn)
        secondary.addWidget(self.history_btn)
        secondary.addWidget(self.clean_btn)
        secondary.addStretch(1)
        root.addLayout(secondary)

        # Stretch: header/settings/buttons stay compact; mid expands
        root.setStretch(0, 0)  # header
        root.setStretch(1, 0)  # settings
        root.setStretch(2, 0)  # primary buttons
        root.setStretch(3, 1)  # progress/preview
        root.setStretch(4, 0)  # secondary buttons

        self.generate_btn.clicked.connect(self.start_generate)
        self.stop_btn.clicked.connect(self.stop_generate)
        self.pause_btn.clicked.connect(self.pause_generate)
        self.resume_btn.clicked.connect(self.resume_generate)
        self.output_btn.clicked.connect(self.open_output)
        self.history_btn.clicked.connect(self.show_history)
        self.clean_btn.clicked.connect(self.clean_temp)

        self._set_running(False)

        about = QAction("About", self)
        about.triggered.connect(self._about)
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction(about)

        status = QStatusBar()
        self.setStatusBar(status)
        self.statusBar().showMessage("Ready — pick settings or leave defaults, then press Generate")

    def _set_running(self, running: bool) -> None:
        self.generate_btn.setEnabled(not running)
        self.settings.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.pause_btn.setEnabled(running)
        self.resume_btn.setEnabled(False)

    def _check_ffmpeg(self) -> None:
        ok, msg = check_ffmpeg()
        if not ok:
            self.statusBar().showMessage("FFmpeg missing — install FFmpeg before generating videos")
            QMessageBox.warning(
                self,
                "FFmpeg required",
                "FFmpeg was not found on this computer.\n\n"
                "Install it, then restart Genesis Artvision Engine.\n\n"
                f"Details:\n{msg}",
            )
        else:
            short = msg.split("(")[0].strip()
            self.statusBar().showMessage(f"Ready · FFmpeg found · {short}")
            self.progress.update_progress(status="Ready — press Generate to create a video")

    @Slot()
    def start_generate(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        opts = self.settings.values()
        self._batch_started = time.perf_counter()
        self._video_index = 0
        self._video_total = None if opts["unlimited"] else opts["count"]
        self.progress.reset()
        count_txt = "unlimited" if opts["unlimited"] else str(opts["count"])
        self.progress.update_progress(status=f"Starting… ({count_txt})")
        self.preview.clear()
        self._set_running(True)
        self.statusBar().showMessage("Generating…")

        self.worker = GenerateWorker(self.factory, opts)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_batch.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    @Slot()
    def stop_generate(self) -> None:
        self.factory.scheduler.stop()
        self.progress.update_progress(status="Stopping… finishing safely")
        self.statusBar().showMessage("Stopping…")

    @Slot()
    def pause_generate(self) -> None:
        self.factory.scheduler.pause()
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)
        self.progress.update_progress(status="Paused — press Resume to continue")
        self.statusBar().showMessage("Paused")

    @Slot()
    def resume_generate(self) -> None:
        self.factory.scheduler.resume()
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.progress.update_progress(status="Generating…")
        self.statusBar().showMessage("Generating…")

    @Slot(dict)
    def on_progress(self, payload: dict) -> None:
        phase = payload.get("phase")
        if phase == "batch":
            self._video_index = int(payload.get("video_index") or 1)
            self._video_total = payload.get("video_total")
            total_txt = "∞" if self._video_total is None else str(self._video_total)
            self.progress.update_progress(video=f"{self._video_index} of {total_txt}")
            return
        if phase in {"start", "render", "audio"}:
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
                "audio": "Creating soundtrack…",
                "render": f"Rendering frames ({frame}/{total})",
            }.get(str(phase), str(phase))
            self.progress.update_progress(
                percent=pct,
                current=f"{engine}  ·  {style}",
                seed=str(seed),
                time_text=f"{mins:02d}:{secs:02d}",
                status=phase_status,
            )
            preview = payload.get("preview")
            if preview is not None:
                self.preview.show_frame(preview)

    @Slot(list)
    def on_finished(self, results: list) -> None:
        self._set_running(False)
        ok = sum(1 for r in results if r.success)
        self.progress.update_progress(
            percent=100 if ok else self.progress.bar.value(),
            status=f"Finished — {ok} of {len(results)} video(s) saved",
        )
        self.statusBar().showMessage(f"Done · {ok}/{len(results)} succeeded")
        if not results:
            return
        last = results[-1]
        if last.success and last.output_path:
            self._last_output = Path(last.output_path)
            box = QMessageBox(self)
            box.setWindowTitle("Video ready")
            box.setIcon(QMessageBox.Icon.Information)
            box.setText(f"Created {ok} video(s).")
            box.setInformativeText(f"Saved to:\n{last.output_path}")
            open_btn = box.addButton("Open video", QMessageBox.ButtonRole.AcceptRole)
            folder_btn = box.addButton("Open folder", QMessageBox.ButtonRole.ActionRole)
            box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
            box.exec()
            clicked = box.clickedButton()
            if clicked is open_btn:
                HistoryDialog._open_path(Path(last.output_path))
            elif clicked is folder_btn:
                HistoryDialog._open_path(Path(last.output_path).parent)
        elif any(not r.success for r in results):
            errs = [r.error for r in results if r.error][:3]
            QMessageBox.warning(
                self,
                "Some videos failed",
                f"Succeeded: {ok}/{len(results)}\n\n" + "\n".join(str(e) for e in errs),
            )

    @Slot(str)
    def on_failed(self, message: str) -> None:
        self._set_running(False)
        self.progress.update_progress(status="Something went wrong")
        self.statusBar().showMessage("Failed")
        QMessageBox.critical(self, "Generation failed", message)

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

    @Slot(int)
    def _regen_seed(self, seed: int) -> None:
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Busy", "Stop the current batch before regenerating.")
            return
        opts = self.settings.values()
        opts["seed"] = seed
        opts["count"] = 1
        opts["unlimited"] = False
        self._batch_started = time.perf_counter()
        self._set_running(True)
        self.progress.update_progress(status=f"Recreating seed {seed}…")
        self.worker = GenerateWorker(self.factory, opts)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_batch.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    @Slot()
    def clean_temp(self) -> None:
        n = clean_all_temp(self.config)
        self.statusBar().showMessage(f"Cleaned {n} temporary item(s)")
        QMessageBox.information(self, "Temp files cleaned", f"Removed {n} temporary item(s).")

    def _about(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "Genesis Artvision Engine\n"
            "by ANSNEW TECH\n\n"
            "Offline procedural art video generator.\n"
            "No cloud APIs. No AI models required.\n\n"
            "Just press Generate — the engine decides the rest.",
        )
