"""Cinematic, aspect-correct live preview panel."""

from __future__ import annotations

from math import gcd

import numpy as np
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QSizePolicy, QVBoxLayout, QWidget


class _AspectPreviewLabel(QLabel):
    """A QLabel that always scales from the original frame, never a scaled copy."""

    def __init__(self, idle_text: str, parent: QWidget | None = None) -> None:
        super().__init__(idle_text, parent)
        self._idle_text = idle_text
        self._source = QPixmap()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(640, 360)

    def set_source(self, pixmap: QPixmap) -> None:
        self._source = pixmap
        self.setText("")
        self._fit_source()

    def clear_source(self) -> None:
        self._source = QPixmap()
        super().setPixmap(QPixmap())
        self.setText(self._idle_text)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._fit_source()

    def _fit_source(self) -> None:
        if self._source.isNull():
            return
        target = self.contentsRect().size()
        if target.width() < 1 or target.height() < 1:
            return
        super().setPixmap(
            self._source.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class PreviewPanel(QWidget):
    """Central preview canvas with unobtrusive render and format overlays."""

    _IDLE_TEXT = (
        "PREVIEW MONITOR\n\n"
        "Choose your settings, then select Generate Video.\n"
        "Frames will appear here while your film renders."
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PreviewPanel")
        self.setAccessibleName("Video preview monitor")
        self.setAccessibleDescription("Displays generated frames at their original aspect ratio.")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.box = QGroupBox("Preview monitor")
        self.box.setAccessibleName("Preview monitor")
        self.box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inner = QVBoxLayout(self.box)
        inner.setContentsMargins(12, 12, 12, 12)

        canvas = QWidget()
        canvas.setObjectName("PreviewStage")
        stage = QGridLayout(canvas)
        stage.setContentsMargins(0, 0, 0, 0)
        self.label = _AspectPreviewLabel(self._IDLE_TEXT)
        self.label.setObjectName("PreviewCanvas")
        self.label.setMinimumHeight(160)
        self.label.setAccessibleName("Rendered frame preview")
        self.label.setAccessibleDescription(self._IDLE_TEXT.replace("\n", " "))
        stage.addWidget(self.label, 0, 0)

        self.render_status = QLabel("")
        self.render_status.setObjectName("PreviewStatusBadge")
        self.render_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.render_status.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.render_status.setAccessibleName("Preview rendering status")
        self.render_status.hide()
        stage.addWidget(
            self.render_status,
            0,
            0,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )

        self.format_badge = QLabel("")
        self.format_badge.setObjectName("PreviewFormatBadge")
        self.format_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.format_badge.setAccessibleName("Preview resolution and aspect ratio")
        self.format_badge.hide()
        stage.addWidget(
            self.format_badge,
            0,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
        )

        inner.addWidget(canvas, 1)
        layout.addWidget(self.box)
        self.setStyleSheet(
            """
            QWidget#PreviewStage { background: #070e14; border-radius: 10px; }
            QLabel#PreviewStatusBadge {
                color: #d7f4ef; background: rgba(10, 24, 32, 215);
                border: 1px solid #2aa89a; border-radius: 10px;
                padding: 5px 11px; margin: 10px; font-weight: 600;
            }
            QLabel#PreviewFormatBadge {
                color: #c7d8e1; background: rgba(10, 20, 28, 220);
                border: 1px solid #36515e; border-radius: 8px;
                padding: 4px 8px; margin: 10px; font-size: 11px;
            }
            """
        )

    def clear(self) -> None:
        """Restore the instructional idle canvas and clear render status."""
        self.label.clear_source()
        self.set_rendering_status("", active=False)

    def show_frame(self, frame: np.ndarray | None) -> None:
        """Display a grayscale, RGB, or RGBA numpy frame."""
        if frame is None:
            return
        frame = np.asarray(frame)
        if frame.ndim not in (2, 3) or frame.size == 0:
            raise ValueError("Preview frame must be a non-empty grayscale, RGB, or RGBA array")
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        frame = np.ascontiguousarray(frame)
        h, w = frame.shape[:2]
        if frame.ndim == 2:
            fmt = QImage.Format.Format_Grayscale8
            bytes_per_line = frame.strides[0]
        else:
            channels = frame.shape[2]
            if channels == 3:
                fmt = QImage.Format.Format_RGB888
            elif channels == 4:
                fmt = QImage.Format.Format_RGBA8888
            else:
                raise ValueError("Preview color frames must have 3 (RGB) or 4 (RGBA) channels")
            bytes_per_line = frame.strides[0]
        data = frame.tobytes()
        image = QImage(data, w, h, bytes_per_line, fmt).copy()
        self.label.set_source(QPixmap.fromImage(image))
        self.label.setAccessibleDescription(f"Rendered frame, {w} by {h} pixels.")

    def set_resolution_badge(
        self,
        resolution: str | tuple[int, int] | None,
        aspect_ratio: str | None = None,
    ) -> None:
        """Set the lower-right format badge, for example ``1920×1080 · 16:9``."""
        dimensions: tuple[int, int] | None = None
        if isinstance(resolution, tuple):
            width, height = resolution
            dimensions = (int(width), int(height))
            resolution_text = f"{width}×{height}"
        else:
            resolution_text = str(resolution or "").strip().lower().replace("x", "×")
            try:
                width_text, height_text = resolution_text.split("×", 1)
                dimensions = (int(width_text), int(height_text))
            except (TypeError, ValueError):
                dimensions = None
        if not aspect_ratio and dimensions and all(value > 0 for value in dimensions):
            divisor = gcd(*dimensions)
            aspect_ratio = f"{dimensions[0] // divisor}:{dimensions[1] // divisor}"
        parts = [part for part in (resolution_text, str(aspect_ratio or "").strip()) if part]
        text = "  ·  ".join(parts)
        self.format_badge.setText(text)
        self.format_badge.setAccessibleDescription(text)
        self.format_badge.setVisible(bool(text))

    def set_rendering_status(self, status: str | None, *, active: bool = True) -> None:
        """Show or hide the top rendering-state overlay."""
        text = str(status or "").strip()
        if active and not text:
            text = "Rendering preview…"
        self.render_status.setText(text)
        self.render_status.setAccessibleDescription(text)
        self.render_status.setVisible(bool(active and text))

    def set_rendering_overlay(self, active: bool, status: str | None = None) -> None:
        """Convenience API for toggling the rendering overlay."""
        self.set_rendering_status(status, active=active)
