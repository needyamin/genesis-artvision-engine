"""Progress display panel."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ProgressPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        box = QGroupBox("Progress")
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inner = QVBoxLayout(box)
        inner.setContentsMargins(12, 10, 12, 10)
        inner.setSpacing(8)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFormat("%p%")
        self.bar.setTextVisible(True)
        self.bar.setMinimumHeight(24)
        inner.addWidget(self.bar)

        self.status = QLabel("Ready when you are")
        self.status.setObjectName("StatValue")
        self.status.setWordWrap(True)
        inner.addWidget(self.status)

        grid = QVBoxLayout()
        grid.setSpacing(6)
        self.current = self._row(grid, "Now creating")
        self.seed = self._row(grid, "Seed")
        self.video = self._row(grid, "Video")
        self.time = self._row(grid, "Elapsed")
        inner.addLayout(grid)

        ai_label = QLabel("AI creative director")
        ai_label.setObjectName("StatKey")
        inner.addWidget(ai_label)
        self.ai_log = QPlainTextEdit()
        self.ai_log.setObjectName("AiLog")
        self.ai_log.setReadOnly(True)
        self.ai_log.setPlaceholderText(
            "When the AI advisor is on, suggestions appear here while they load — "
            "the rest of the window stays responsive."
        )
        self.ai_log.setMinimumHeight(72)
        self.ai_log.setMaximumHeight(160)
        self.ai_log.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        inner.addWidget(self.ai_log, 1)

        layout.addWidget(box)

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
        self.bar.setValue(0)
        self.current.setText("—")
        self.seed.setText("—")
        self.video.setText("—")
        self.time.setText("—")
        self.status.setText("Ready when you are")
        self.set_ai_log("AI idle — turn on AI creative advisor in Extras to see suggestions here.")

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

    def update_progress(
        self,
        *,
        percent: int | None = None,
        current: str | None = None,
        seed: str | None = None,
        video: str | None = None,
        time_text: str | None = None,
        status: str | None = None,
    ) -> None:
        if percent is not None:
            self.bar.setValue(max(0, min(100, percent)))
        if current is not None:
            self.current.setText(current)
        if seed is not None:
            self.seed.setText(seed)
        if video is not None:
            self.video.setText(video)
        if time_text is not None:
            self.time.setText(time_text)
        if status is not None:
            self.status.setText(status)
