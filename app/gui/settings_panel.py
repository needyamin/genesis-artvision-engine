"""Settings panel widgets — compact two-column layout."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

RESOLUTION_LABELS: dict[str, str] = {
    "1920x1080": "Full HD — 1920×1080",
    "3840x2160": "4K UHD — 3840×2160",
    "1080x1920": "Full HD Vertical — 1080×1920",
    "2160x3840": "4K Vertical — 2160×3840",
    "1080x1080": "Full HD Square — 1080×1080",
    "2160x2160": "4K Square — 2160×2160",
}

ENGINE_LABELS: dict[str, str] = {
    "kids_storybook": "Kids Storybook",
    "how_it_works": "How It Works",
    "trend_brief": "Trending Brief",
}

STYLE_LABELS: dict[str, str] = {
    "storybook": "Storybook",
    "classroom": "Classroom",
    "pulse": "Pulse",
}


def resolution_label(value: str) -> str:
    return RESOLUTION_LABELS.get(value, value)


def engine_label(value: str) -> str:
    return ENGINE_LABELS.get(value, value.replace("_", " ").title())


def style_label(value: str) -> str:
    return STYLE_LABELS.get(value, value.replace("_", " ").title())


class SettingsPanel(QWidget):
    """Primary generation settings arranged so all sections stay visible."""

    settings_changed = Signal()

    def __init__(self, config: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self._build()

    def _build(self) -> None:
        root = QGridLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setHorizontalSpacing(12)
        root.setVerticalSpacing(10)

        # ---- Video (top-left) ----
        video_box = QGroupBox("Video")
        vg = QGridLayout(video_box)
        vg.setContentsMargins(12, 10, 12, 10)
        vg.setHorizontalSpacing(10)
        vg.setVerticalSpacing(8)

        self.resolution = QComboBox()
        res_values = list(
            self.config.get(
                "resolutions",
                ["1920x1080", "3840x2160", "1080x1920", "2160x3840", "1080x1080", "2160x2160"],
            )
        )
        self.resolution.addItem("Random", userData=None)
        for value in res_values:
            self.resolution.addItem(resolution_label(str(value)), userData=str(value))
        default_res = str(self.config.get("resolution", "1920x1080"))
        idx = self.resolution.findData(default_res)
        if idx < 0:
            idx = self.resolution.findData("1920x1080")
        if idx >= 0:
            self.resolution.setCurrentIndex(idx)
        self.resolution.setToolTip("Full HD is the default. Choose 4K for higher quality (slower).")
        self.resolution.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.duration = QComboBox()
        dur_opts = ["Random"] + [
            str(x) for x in self.config.get("duration", {}).get("options", [10, 15, 30, 60])
        ]
        self.duration.addItems(dur_opts)
        default_dur = str(self.config.get("duration", {}).get("default", 30))
        if default_dur in dur_opts:
            self.duration.setCurrentText(default_dur)
        self.duration.setToolTip("Length of each generated video in seconds.")

        self.fps = QComboBox()
        fps_opts = ["Random"] + [str(x) for x in self.config.get("fps_options", [24, 30, 60])]
        self.fps.addItems(fps_opts)
        cur_fps = str(self.config.get("fps", 30))
        if cur_fps in fps_opts:
            self.fps.setCurrentText(cur_fps)
        self.fps.setToolTip("Frames per second. 30 is a good balance of smoothness and speed.")

        vg.addWidget(QLabel("Resolution"), 0, 0)
        vg.addWidget(self.resolution, 0, 1, 1, 3)
        vg.addWidget(QLabel("Duration"), 1, 0)
        vg.addWidget(self.duration, 1, 1)
        vg.addWidget(QLabel("FPS"), 1, 2)
        vg.addWidget(self.fps, 1, 3)
        vg.setColumnStretch(1, 1)
        vg.setColumnStretch(3, 1)

        # ---- Art (top-right) ----
        art_box = QGroupBox("Art")
        ag = QGridLayout(art_box)
        ag.setContentsMargins(12, 10, 12, 10)
        ag.setHorizontalSpacing(10)
        ag.setVerticalSpacing(8)

        self.art_mode = QComboBox()
        self.art_mode.addItem("Random", userData=None)
        for eng in self.config.get("engines", []):
            self.art_mode.addItem(engine_label(str(eng)), userData=str(eng))
        self.art_mode.setToolTip(
            "What to generate. Random picks among Kids Storybook, How It Works, and Trending Brief."
        )
        self.art_mode.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.style = QComboBox()
        self.style.addItem("Random", userData=None)
        for st in self.config.get("styles", []):
            self.style.addItem(style_label(str(st)), userData=str(st))
        self.style.setToolTip("Look and colors. Leave on Random unless you want a specific mood.")
        self.style.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        ag.addWidget(QLabel("Engine"), 0, 0)
        ag.addWidget(self.art_mode, 0, 1)
        ag.addWidget(QLabel("Style"), 1, 0)
        ag.addWidget(self.style, 1, 1)
        ag.setColumnStretch(1, 1)

        # ---- Batch (bottom-left) ----
        batch_box = QGroupBox("Batch")
        bg = QVBoxLayout(batch_box)
        bg.setContentsMargins(12, 10, 12, 10)
        bg.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.count = QSpinBox()
        self.count.setRange(1, 100000)
        self.count.setValue(1)
        self.count.setSuffix(" video(s)")
        self.count.setToolTip("How many videos to create in this run.")
        self.count.setMinimumWidth(120)
        row.addWidget(QLabel("Count"))
        row.addWidget(self.count, 1)

        for label, n in (("1", 1), ("5", 5), ("10", 10), ("100", 100)):
            btn = QPushButton(label)
            btn.setFixedWidth(44)
            btn.setToolTip(f"Set count to {n}")
            btn.clicked.connect(lambda _=False, val=n: self._set_count(val))
            row.addWidget(btn)
        bg.addLayout(row)

        self.unlimited = QCheckBox("Keep generating until Stop")
        self.unlimited.setToolTip("Creates videos continuously until you stop.")
        self.unlimited.toggled.connect(self._on_unlimited)
        bg.addWidget(self.unlimited)

        # ---- Output (bottom-right) ----
        extras = QGroupBox("Output")
        eg = QVBoxLayout(extras)
        eg.setContentsMargins(12, 10, 12, 10)
        eg.setSpacing(8)
        self.proc_audio = QCheckBox("Soundtrack")
        self.proc_audio.setChecked(bool(self.config.get("audio", {}).get("enabled", True)))
        self.proc_audio.setToolTip("Mix audio into the MP4.")
        self.gen_thumb = QCheckBox("Thumbnail")
        self.gen_thumb.setChecked(bool(self.config.get("output", {}).get("thumbnail", True)))
        self.gen_thumb.setToolTip("Save a JPG preview next to each video.")
        self.random_colors = QCheckBox()
        self.random_colors.setChecked(True)
        self.random_colors.hide()
        self.random_anim = QCheckBox()
        self.random_anim.setChecked(True)
        self.random_anim.hide()

        ai_cfg = self.config.get("ai") or {}
        self.ai_advisor = QCheckBox("AI advisor")
        self.ai_advisor.setChecked(bool(ai_cfg.get("enabled") and ai_cfg.get("per_video")))
        self.ai_advisor.setToolTip("Optional OpenRouter suggestions. Needs OPENROUTER_API_KEY in .env.")
        self.ai_status = QLabel("")
        self.ai_status.hide()

        yt_cfg = self.config.get("youtube") or {}
        self.youtube_upload = QCheckBox("Upload to YouTube")
        self.youtube_upload.setChecked(bool(yt_cfg.get("enabled")))
        self.youtube_upload.setToolTip(
            "After each video is saved, upload it with an SEO title, hashtags, and thumbnail. "
            "Connect your channel first (YouTube menu). Default privacy is Unlisted."
        )
        self.youtube_privacy = QComboBox()
        self.youtube_privacy.addItem("Unlisted", userData="unlisted")
        self.youtube_privacy.addItem("Public", userData="public")
        self.youtube_privacy.addItem("Private", userData="private")
        priv = str(yt_cfg.get("privacy") or "unlisted")
        idx = self.youtube_privacy.findData(priv)
        if idx >= 0:
            self.youtube_privacy.setCurrentIndex(idx)
        self.youtube_privacy.setToolTip("Unlisted is safest while you review. Public goes live on the channel.")
        self.youtube_channel = QLabel("Channel: not connected")
        self.youtube_channel.setObjectName("ChannelPill")
        self.youtube_channel.setWordWrap(True)

        eg.addWidget(self.proc_audio)
        eg.addWidget(self.gen_thumb)
        eg.addWidget(self.ai_advisor)
        eg.addWidget(self.youtube_upload)
        priv_row = QHBoxLayout()
        priv_row.addWidget(QLabel("YouTube"))
        priv_row.addWidget(self.youtube_privacy, 1)
        eg.addLayout(priv_row)
        eg.addWidget(self.youtube_channel)
        eg.addStretch(1)

        root.addWidget(video_box, 0, 0)
        root.addWidget(art_box, 0, 1)
        root.addWidget(batch_box, 1, 0)
        root.addWidget(extras, 1, 1)
        root.setColumnStretch(0, 1)
        root.setColumnStretch(1, 1)
        root.setRowStretch(0, 0)
        root.setRowStretch(1, 0)

    def _set_count(self, n: int) -> None:
        self.unlimited.setChecked(False)
        self.count.setEnabled(True)
        self.count.setValue(n)

    def _on_unlimited(self, on: bool) -> None:
        self.count.setEnabled(not on)

    def values(self) -> dict[str, Any]:
        eng_val = self.art_mode.currentData()
        style_val = self.style.currentData()

        dur = self.duration.currentText()
        res_data = self.resolution.currentData()
        res = None if res_data is None else str(res_data)
        fps = self.fps.currentText()
        return {
            "engine": None if eng_val is None else str(eng_val),
            "style": None if style_val is None else str(style_val),
            "duration": None if dur == "Random" else int(dur),
            "random_duration": dur == "Random",
            "resolution": res,
            "random_resolution": res is None,
            "fps": None if fps == "Random" else int(fps),
            "random_fps": fps == "Random",
            "count": int(self.count.value()),
            "unlimited": self.unlimited.isChecked(),
            "audio_enabled": self.proc_audio.isChecked(),
            "thumbnail": self.gen_thumb.isChecked(),
            "ai_enabled": self.ai_advisor.isChecked(),
            "ai_per_video": self.ai_advisor.isChecked(),
            "youtube_upload": self.youtube_upload.isChecked(),
            "youtube_privacy": str(self.youtube_privacy.currentData() or "unlisted"),
        }

    def set_youtube_channel(self, label: str) -> None:
        text = (label or "").strip() or "not connected"
        self.youtube_channel.setText(f"Uploads go to: {text}")
