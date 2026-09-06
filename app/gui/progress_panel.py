"""Professional activity and render progress panel."""

from __future__ import annotations

import re
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

_PERCENT_RE = re.compile(r"(?<!\d)(100|\d{1,2})\s*%")


class ProgressPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ActivityPanel")
        self.setAccessibleName("Render activity")
        self.setAccessibleDescription("Current generation phase, progress, statistics, and quality checks.")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._determinate_value = 0
        self._paused = False
        self._phase_before_pause = "Ready"
        self._ai_expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.box = QGroupBox("Activity")
        self.box.setAccessibleName("Activity")
        self.box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inner = QVBoxLayout(self.box)
        inner.setContentsMargins(12, 12, 12, 12)
        inner.setSpacing(8)

        phase_row = QHBoxLayout()
        phase_key = QLabel("CURRENT PHASE")
        phase_key.setObjectName("StatKey")
        self.phase = QLabel("READY")
        self.phase.setObjectName("ActivityPhase")
        self.phase.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phase.setAccessibleName("Current phase")
        phase_row.addWidget(phase_key)
        phase_row.addStretch(1)
        phase_row.addWidget(self.phase)
        inner.addLayout(phase_row)

        self.status = QLabel("Ready")
        self.status.setObjectName("ActivityStatus")
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.status.setAccessibleName("Activity status")
        inner.addWidget(self.status)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFormat("%p%")
        self.bar.setTextVisible(True)
        self.bar.setMinimumHeight(24)
        self.bar.setAccessibleName("Generation progress")
        self.bar.setAccessibleDescription("No generation is currently running.")
        inner.addWidget(self.bar)

        grid = QVBoxLayout()
        grid.setSpacing(6)
        self.current = self._row(grid, "Now creating")
        self.seed = self._row(grid, "Seed")
        self.batch = self._row(grid, "Batch")
        self.video = self.batch  # Backwards-compatible MainWindow attribute.
        self.time = self._row(grid, "Elapsed")
        inner.addLayout(grid)

        self.qc_summary = QLabel("")
        self.qc_summary.setObjectName("QcSummary")
        self.qc_summary.setWordWrap(True)
        self.qc_summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.qc_summary.setAccessibleName("Quality control summary")
        self.qc_summary.hide()
        inner.addWidget(self.qc_summary)

        self.ai_label = QPushButton("AI DETAILS  ›")
        self.ai_label.setObjectName("AiDetailsButton")
        self.ai_label.setCheckable(True)
        self.ai_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ai_label.setAccessibleName("AI details")
        self.ai_label.setToolTip("Show or hide AI activity details.")
        self.ai_label.toggled.connect(self._set_ai_expanded)
        inner.addWidget(self.ai_label)

        self.ai_log = QPlainTextEdit()
        self.ai_log.setObjectName("AiLog")
        self.ai_log.setReadOnly(True)
        self.ai_log.setPlaceholderText("AI activity will appear here.")
        self.ai_log.setMinimumHeight(72)
        self.ai_log.setMaximumHeight(160)
        self.ai_log.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.ai_log.setAccessibleName("AI activity details")
        inner.addWidget(self.ai_log, 1)
        self.set_ai_visible(False)

        inner.addStretch(1)
        layout.addWidget(self.box)
        self.setStyleSheet(
            """
            QLabel#ActivityPhase {
                color: #9fe3d7; background: #12333a;
                border: 1px solid #28606a; border-radius: 9px;
                padding: 3px 9px; font-size: 11px; font-weight: 700;
            }
            QLabel#ActivityStatus {
                color: #edf5f8; font-size: 14px; font-weight: 600;
                padding: 3px 0;
            }
            QLabel#QcSummary {
                color: #c9e9df; background: #102b2c;
                border: 1px solid #2d655f; border-radius: 8px;
                padding: 7px 9px;
            }
            QPushButton#AiDetailsButton {
                background: transparent; border: none; border-top: 1px solid #2a4450;
                border-radius: 0; color: #9bb0bc; text-align: left;
                padding: 8px 2px 4px 2px; min-height: 20px; font-size: 11px;
                font-weight: 700;
            }
            QPushButton#AiDetailsButton:hover { color: #c5e8e2; }
            """
        )

    @staticmethod
    def _row(parent: QVBoxLayout, key: str) -> QLabel:
        row = QHBoxLayout()
        k = QLabel(key)
        k.setObjectName("StatKey")
        v = QLabel("—")
        v.setObjectName("StatValue")
        v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(k)
        row.addWidget(v, 1)
        parent.addLayout(row)
        return v

    def reset(self) -> None:
        self._paused = False
        self._determinate_value = 0
        self.set_indeterminate(False)
        self.bar.setValue(0)
        self.bar.setFormat("%p%")
        self.current.setText("—")
        self.seed.setText("—")
        self.batch.setText("—")
        self.time.setText("—")
        self.status.setText("Ready")
        self.set_phase("Ready")
        self.set_qc_summary(None)
        self.set_ai_log("")
        self.bar.setAccessibleDescription("No generation is currently running.")

    def set_ai_visible(self, visible: bool) -> None:
        self.ai_label.setVisible(visible)
        if visible:
            self._set_ai_expanded(self.ai_label.isChecked())
        else:
            self.ai_log.hide()
        if not visible:
            self.ai_label.setChecked(False)
            self.set_ai_log("")

    def _set_ai_expanded(self, expanded: bool) -> None:
        self._ai_expanded = bool(expanded)
        self.ai_label.setText("AI DETAILS  ⌄" if expanded else "AI DETAILS  ›")
        self.ai_label.setAccessibleDescription("Expanded" if expanded else "Collapsed")
        self.ai_log.setVisible(self.ai_label.isVisible() and expanded)

    def set_ai_log(self, text: str) -> None:
        self.ai_log.setPlainText(text or "")
        cursor = self.ai_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.ai_log.setTextCursor(cursor)

    def append_ai_log(self, text: str) -> None:
        line = (text or "").strip()
        if not line:
            return
        existing = self.ai_log.toPlainText().strip()
        combined = f"{existing}\n{line}".strip() if existing else line
        lines = combined.splitlines()
        self.set_ai_log("\n".join(lines[-40:]))

    def set_phase(self, phase: str | None) -> None:
        """Set the concise phase pill independently of the status message."""
        text = str(phase or "Working").strip()
        self.phase.setText(text.upper())
        self.phase.setAccessibleDescription(text)

    def set_indeterminate(self, indeterminate: bool = True) -> None:
        """Switch between busy animation and percentage progress."""
        if indeterminate:
            if self.bar.maximum() > 0:
                self._determinate_value = self.bar.value()
            self.bar.setRange(0, 0)
            self.bar.setFormat("Working…")
            self.bar.setAccessibleDescription("Work is in progress; completion percentage is not available.")
        else:
            self.bar.setRange(0, 100)
            self.bar.setValue(self._determinate_value)
            self.bar.setFormat("%p%")
            self.bar.setAccessibleDescription(f"Generation is {self._determinate_value} percent complete.")

    def set_paused(self, paused: bool = True, message: str | None = None) -> None:
        """Present or clear the paused state without losing progress."""
        paused = bool(paused)
        if paused == self._paused and message is None:
            return
        self._paused = paused
        if paused:
            self._phase_before_pause = self.phase.text().title()
            self.set_phase("Paused")
            self.status.setText(message or "Paused — press Resume to continue")
            self.bar.setFormat("Paused")
            self.bar.setAccessibleDescription("Generation is paused.")
        else:
            self.set_phase(self._phase_before_pause if self._phase_before_pause != "Paused" else "Working")
            self.bar.setFormat("Working…" if self.bar.maximum() == 0 else "%p%")

    def set_upload_progress(self, percent: int | float | None, status: str | None = None) -> None:
        """Display upload progress; ``None`` means the upload size is unknown."""
        self.set_phase("Upload")
        self.set_paused(False)
        if percent is None:
            self.set_indeterminate(True)
        else:
            self._set_percent(percent)
        if status is not None:
            self.status.setText(status)

    def set_qc_summary(
        self,
        report: dict[str, Any] | str | None,
        *,
        passed: bool | None = None,
    ) -> None:
        """Show a compact QC result from a report dictionary or plain message."""
        if report is None and passed is None:
            self.qc_summary.clear()
            self.qc_summary.hide()
            return
        if isinstance(report, dict):
            if passed is None:
                passed = bool(report.get("passed"))
            problems = list(report.get("errors") or report.get("warnings") or [])
            detail = "; ".join(str(item) for item in problems[:3])
            if not detail:
                metrics = report.get("metrics")
                detail = "Export checks completed" if not metrics else f"{len(metrics)} checks completed"
        else:
            detail = str(report or "").strip()
        prefix = "QC PASSED" if passed is True else "QC NEEDS ATTENTION" if passed is False else "QUALITY CHECK"
        text = f"{prefix}  ·  {detail}" if detail else prefix
        self.qc_summary.setText(text)
        self.qc_summary.setAccessibleDescription(text)
        self.qc_summary.show()

    def set_batch_stats(
        self,
        *,
        batch: str | int | None = None,
        seed: str | int | None = None,
        elapsed: str | None = None,
    ) -> None:
        """Update the stable batch, seed, and elapsed statistics."""
        if batch is not None:
            self.batch.setText(str(batch))
        if seed is not None:
            self.seed.setText(str(seed))
        if elapsed is not None:
            self.time.setText(str(elapsed))

    def _set_percent(self, percent: int | float) -> None:
        value = max(0, min(100, int(round(float(percent)))))
        self._determinate_value = value
        if self.bar.maximum() == 0:
            self.bar.setRange(0, 100)
        self.bar.setValue(value)
        self.bar.setFormat("%p%")
        self.bar.setAccessibleDescription(f"Generation is {value} percent complete.")

    @staticmethod
    def _phase_from_status(status: str) -> str | None:
        lowered = status.lower()
        for needle, phase in (
            ("pause", "Paused"),
            ("upload", "Upload"),
            ("youtube", "Upload"),
            ("quality", "Quality control"),
            ("checking export", "Quality control"),
            ("render", "Rendering"),
            ("soundtrack", "Audio"),
            ("voice", "Voice"),
            ("ai ", "AI"),
            ("prepar", "Preparing"),
            ("start", "Preparing"),
            ("finish", "Complete"),
            ("ready", "Ready"),
            ("stop", "Stopping"),
            ("generat", "Rendering"),
        ):
            if needle in lowered:
                return phase
        return None

    def update_progress(
        self,
        *,
        percent: int | float | None = None,
        current: str | None = None,
        seed: str | None = None,
        video: str | None = None,
        time_text: str | None = None,
        status: str | None = None,
        phase: str | None = None,
        indeterminate: bool | None = None,
        paused: bool | None = None,
        upload_percent: int | float | None = None,
    ) -> None:
        """Backward-compatible aggregate update used by :class:`MainWindow`."""
        status_text = str(status or "")
        inferred_phase = phase or (self._phase_from_status(status_text) if status is not None else None)
        upload_match = _PERCENT_RE.search(status_text) if inferred_phase == "Upload" else None

        if paused is not None:
            self.set_paused(paused, status_text or None)
        elif inferred_phase == "Paused":
            self.set_paused(True, status_text or None)
        elif self._paused and status_text.strip().lower() in {"generating", "generating…", "generating..."}:
            self.set_paused(False)

        if inferred_phase and inferred_phase != "Paused" and not self._paused:
            self.set_phase(inferred_phase)

        effective_upload = upload_percent
        if effective_upload is None and upload_match:
            effective_upload = int(upload_match.group(1))
        if effective_upload is not None:
            self.set_upload_progress(effective_upload)
        elif indeterminate is not None:
            self.set_indeterminate(indeterminate)
        elif inferred_phase in {"Preparing", "Audio", "Voice", "AI", "Quality control", "Stopping", "Upload"}:
            self.set_indeterminate(True)
        elif percent is not None:
            self._set_percent(percent)

        if current is not None:
            self.current.setText(current)
        if seed is not None:
            self.seed.setText(seed)
        if video is not None:
            self.batch.setText(video)
        if time_text is not None:
            self.time.setText(time_text)
        if status is not None:
            self.status.setText(status)
        if self._paused:
            self.set_phase("Paused")
            self.bar.setFormat("Paused")
            self.bar.setAccessibleDescription("Generation is paused.")
