"""Live preview panel."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QGroupBox, QLabel, QSizePolicy, QVBoxLayout, QWidget


class PreviewPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        box = QGroupBox("Live preview")
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inner = QVBoxLayout(box)
        inner.setContentsMargins(10, 8, 10, 10)
        self.label = QLabel("Your art preview will appear here\nwhile a video is generating")
        self.label.setObjectName("PreviewCanvas")
        self.label.setMinimumHeight(160)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setScaledContents(False)
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inner.addWidget(self.label, 1)
        layout.addWidget(box)

    def clear(self) -> None:
        self.label.setText("Your art preview will appear here\nwhile a video is generating")
        self.label.setPixmap(QPixmap())

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        pix = self.label.pixmap()
        if pix and not pix.isNull():
            self.label.setPixmap(
                pix.scaled(
                    self.label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def show_frame(self, frame: np.ndarray | None) -> None:
        if frame is None:
            return
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        h, w = frame.shape[:2]
        if frame.ndim == 2:
            fmt = QImage.Format.Format_Grayscale8
            bytes_per_line = w
            data = frame.tobytes()
        else:
            fmt = QImage.Format.Format_RGB888
            bytes_per_line = 3 * w
            data = np.ascontiguousarray(frame).tobytes()
        image = QImage(data, w, h, bytes_per_line, fmt).copy()
        self._source = QPixmap.fromImage(image)
        self.label.setPixmap(
            self._source.scaled(
                self.label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
