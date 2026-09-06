"""Shared dark-studio dialogs: info/warning and the video-ready result card."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.gui.branding import apply_app_icon, app_logo_path
from app.gui.styles import APP_STYLE


def _short_youtube_url(url: str) -> str:
    text = (url or "").strip()
    if "watch?v=" in text:
        vid = text.split("watch?v=", 1)[1].split("&", 1)[0]
        return f"https://youtu.be/{vid}"
    return text


def _fade_in(widget: QWidget) -> None:
    """120ms fade when the dialog is shown."""
    if getattr(widget, "_fade_started", False):
        return
    widget._fade_started = True
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(120)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    widget._fade_anim = anim
    anim.start()


class StudioDialog(QDialog):
    """Dark card dialog with a title, body, and action row."""

    def __init__(
        self,
        parent: QWidget | None,
        *,
        title: str,
        body: str,
        buttons: list[tuple[str, str]] | None = None,
        window_title: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.clicked = "close"
        apply_app_icon(self)
        self.setStyleSheet(APP_STYLE)
        self.setWindowTitle(window_title or title)
        self.setMinimumWidth(460)
        self._build(title, body, buttons or [("OK", "close")])

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        _fade_in(self)

    def _build(self, title: str, body: str, buttons: list[tuple[str, str]]) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 16)
        root.setSpacing(12)

        heading = QLabel(title)
        heading.setObjectName("DialogTitle")
        heading.setWordWrap(True)
        root.addWidget(heading)

        text = QLabel(body)
        text.setObjectName("HintLabel")
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(text)

        row = QHBoxLayout()
        row.addStretch(1)
        for i, (label, key) in enumerate(buttons):
            btn = QPushButton(label)
            if key in {"generate", "open_video"}:
                btn.setObjectName("GenerateButton")
            elif key in {"ok", "secondary", "open_folder", "connect", "open_youtube"}:
                btn.setObjectName("SecondaryButton")
            elif key == "danger":
                btn.setObjectName("DangerButton")
            else:
                btn.setObjectName("GhostButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self._finish(k))
            if i == len(buttons) - 1:
                btn.setDefault(True)
            row.addWidget(btn)
        root.addLayout(row)

    def _finish(self, key: str) -> None:
        self.clicked = key
        if key in {"close", "cancel"}:
            self.reject()
        else:
            self.accept()


def studio_info(parent: QWidget | None, title: str, body: str, ok: str = "OK") -> str:
    dlg = StudioDialog(parent, title=title, body=body, buttons=[(ok, "ok")])
    dlg.exec()
    return dlg.clicked


def studio_warn(parent: QWidget | None, title: str, body: str) -> str:
    dlg = StudioDialog(parent, title=title, body=body, buttons=[("OK", "ok")])
    dlg.exec()
    return dlg.clicked


class ResultDialog(QDialog):
    """Video-ready card with thumbnail and YouTube success or short error."""

    def __init__(
        self,
        parent: QWidget | None,
        *,
        ok_count: int,
        total: int,
        engine: str,
        style: str,
        seed: Any,
        output_path: Path,
        thumbnail_path: Path | None,
        youtube_url: str | None,
        youtube_error: str | None,
        youtube_urls: list[str],
        channel_label: str = "",
    ) -> None:
        super().__init__(parent)
        self.clicked = "close"
        apply_app_icon(self)
        self.setStyleSheet(APP_STYLE)
        self.setWindowTitle("Video ready")
        self.setMinimumWidth(640)
        self._build(
            ok_count,
            total,
            engine,
            style,
            seed,
            output_path,
            thumbnail_path,
            youtube_url,
            youtube_error,
            youtube_urls,
            channel_label,
        )

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        _fade_in(self)

    def _build(
        self,
        ok_count: int,
        total: int,
        engine: str,
        style: str,
        seed: Any,
        output_path: Path,
        thumbnail_path: Path | None,
        youtube_url: str | None,
        youtube_error: str | None,
        youtube_urls: list[str],
        channel_label: str,
    ) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(14)

        title = QLabel("Video ready" if ok_count else "Render finished")
        title.setObjectName("DialogTitle")
        root.addWidget(title)
        sub = QLabel(f"Created {ok_count} of {total} video(s).")
        sub.setObjectName("HintLabel")
        root.addWidget(sub)

        card = QFrame()
        card.setObjectName("StudioCard")
        body = QHBoxLayout(card)
        body.setContentsMargins(12, 12, 12, 12)
        body.setSpacing(16)

        thumb = QLabel()
        thumb.setObjectName("PreviewCanvas")
        thumb.setFixedSize(220, 124)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix_src = thumbnail_path if thumbnail_path and Path(thumbnail_path).is_file() else None
        if pix_src is None:
            sibling = output_path.with_suffix(".jpg")
            if sibling.is_file():
                pix_src = sibling
        if pix_src:
            pix = QPixmap(str(pix_src)).scaled(
                220,
                124,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = max(0, (pix.width() - 220) // 2)
            y = max(0, (pix.height() - 124) // 2)
            thumb.setPixmap(pix.copy(x, y, 220, 124))
        else:
            thumb.setText("No thumbnail")
        body.addWidget(thumb, 0)

        meta = QVBoxLayout()
        meta.setSpacing(6)
        line = QLabel(f"{engine}  ·  {style}  ·  seed {seed}")
        line.setObjectName("StatValue")
        line.setWordWrap(True)
        meta.addWidget(line)
        path_lbl = QLabel(str(output_path))
        path_lbl.setObjectName("PathLabel")
        path_lbl.setWordWrap(True)
        path_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        meta.addWidget(path_lbl)
        meta.addStretch(1)
        body.addLayout(meta, 1)
        root.addWidget(card)

        yt = QFrame()
        yt.setObjectName("StudioCard")
        yt_l = QVBoxLayout(yt)
        yt_l.setContentsMargins(12, 10, 12, 10)
        yt_l.setSpacing(4)
        if youtube_urls or youtube_url:
            head = QLabel("Uploaded to YouTube")
            head.setObjectName("StatValue")
            yt_l.addWidget(head)
            if channel_label:
                ch = QLabel(channel_label)
                ch.setObjectName("ChannelPill")
                yt_l.addWidget(ch)
            for url in (youtube_urls or ([youtube_url] if youtube_url else []))[:5]:
                link = QLabel(_short_youtube_url(str(url)))
                link.setObjectName("HintLabel")
                link.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                yt_l.addWidget(link)
        elif youtube_error:
            head = QLabel("YouTube upload did not finish")
            head.setObjectName("StatValue")
            yt_l.addWidget(head)
            err = QLabel(str(youtube_error)[:700])
            err.setObjectName("HintLabel")
            err.setWordWrap(True)
            err.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            yt_l.addWidget(err)
        else:
            head = QLabel("Saved locally")
            head.setObjectName("StatValue")
            yt_l.addWidget(head)
            hint = QLabel("Turn on Upload to YouTube to send the next film to your channel.")
            hint.setObjectName("HintLabel")
            hint.setWordWrap(True)
            yt_l.addWidget(hint)
        root.addWidget(yt)

        row = QHBoxLayout()
        row.addStretch(1)

        def add(label: str, key: str, name: str) -> None:
            btn = QPushButton(label)
            btn.setObjectName(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self._finish(k))
            row.addWidget(btn)

        add("Open video", "open_video", "GenerateButton")
        add("Open folder", "open_folder", "SecondaryButton")
        if youtube_url:
            add("Open YouTube", "open_youtube", "SecondaryButton")
        add("Close", "close", "GhostButton")
        root.addLayout(row)

    def _finish(self, key: str) -> None:
        self.clicked = key
        if key == "close":
            self.reject()
        else:
            self.accept()


class _AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)
        apply_app_icon(self)
        self.setStyleSheet(APP_STYLE)
        self.setWindowTitle("About")
        self.setMinimumWidth(420)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(10)
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(str(app_logo_path()))
        if not pix.isNull():
            logo.setPixmap(
                pix.scaled(
                    88,
                    88,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        root.addWidget(logo)
        title = QLabel("Genesis Artvision Engine")
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        body = QLabel(
            "by ANSNEW TECH\n\n"
            "Offline procedural art video generator.\n"
            "Optional OpenRouter advisor suggests creative direction only.\n"
            "Frames, audio, and FFmpeg stay local.\n\n"
            "File menu for history and output. Prompt to type a brief. "
            "YouTube to connect a channel."
        )
        body.setObjectName("HintLabel")
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(body)
        row = QHBoxLayout()
        row.addStretch(1)
        ok = QPushButton("Close")
        ok.setObjectName("GhostButton")
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        root.addLayout(row)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        _fade_in(self)


def about_dialog(parent: QWidget | None) -> None:
    _AboutDialog(parent).exec()
