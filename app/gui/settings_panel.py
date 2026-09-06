"""Settings panel widgets for the compact studio inspector."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
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
    """Primary generation settings in a compact, no-scroll control deck."""

    settings_changed = Signal()

    def __init__(self, config: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.setAccessibleName("Professional Studio settings")
        self.setAccessibleDescription(
            "Video generation, creative, editing, batch, delivery, and YouTube settings."
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._build()

    def _build(self) -> None:
        root = QGridLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setHorizontalSpacing(8)
        root.setVerticalSpacing(6)

        # ---- Video ----
        video_box = QGroupBox("Video")
        video_box.setAccessibleName("Video settings")
        vg = self._section_layout(video_box)

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
        self._prepare_combo(
            self.resolution,
            "Video resolution",
            "Select the output dimensions, or Random to choose for each video.",
        )

        self.duration = QComboBox()
        dur_opts = ["Random"] + [
            str(x) for x in self.config.get("duration", {}).get("options", [10, 15, 30, 60])
        ]
        self.duration.addItems(dur_opts)
        default_dur = str(self.config.get("duration", {}).get("default", 30))
        if default_dur in dur_opts:
            self.duration.setCurrentText(default_dur)
        self.duration.setToolTip("Length of each generated video in seconds.")
        self._prepare_combo(
            self.duration,
            "Video duration",
            "Select the video length in seconds, or Random to vary each video.",
        )

        self.fps = QComboBox()
        fps_opts = ["Random"] + [str(x) for x in self.config.get("fps_options", [24, 30, 60])]
        self.fps.addItems(fps_opts)
        cur_fps = str(self.config.get("fps", 30))
        if cur_fps in fps_opts:
            self.fps.setCurrentText(cur_fps)
        self.fps.setToolTip("Frames per second. 30 is a good balance of smoothness and speed.")
        self._prepare_combo(
            self.fps,
            "Video frame rate",
            "Select frames per second, or Random to vary each video.",
        )

        vg.addLayout(self._field_row("Resolution", self.resolution))
        vg.addLayout(self._field_row("Duration", self.duration))
        vg.addLayout(self._field_row("FPS", self.fps))

        # ---- Creative ----
        creative_box = QGroupBox("Creative")
        creative_box.setAccessibleName("Creative settings")
        cg = self._section_layout(creative_box)

        self.art_mode = QComboBox()
        self.art_mode.addItem("Random", userData=None)
        for eng in self.config.get("engines", []):
            self.art_mode.addItem(engine_label(str(eng)), userData=str(eng))
        self.art_mode.setToolTip(
            "What to generate. Random picks among Kids Storybook, How It Works, and Trending Brief."
        )
        self._prepare_combo(
            self.art_mode,
            "Creative engine",
            "Select the kind of artwork to generate, or Random to vary each video.",
        )

        self.style = QComboBox()
        self.style.addItem("Random", userData=None)
        for st in self.config.get("styles", []):
            self.style.addItem(style_label(str(st)), userData=str(st))
        self.style.setToolTip("Look and colors. Leave on Random unless you want a specific mood.")
        self._prepare_combo(
            self.style,
            "Creative style",
            "Select the visual style, or Random to vary each video.",
        )

        ai_cfg = self.config.get("ai") or {}
        self.ai_advisor = QCheckBox("AI advisor")
        self.ai_advisor.setChecked(bool(ai_cfg.get("enabled") and ai_cfg.get("per_video")))
        self.ai_advisor.setToolTip("Optional OpenRouter suggestions. Needs OPENROUTER_API_KEY in .env.")
        self._prepare_control(
            self.ai_advisor,
            "Use AI advisor",
            "Request optional OpenRouter creative suggestions for each video.",
        )

        cg.addLayout(self._field_row("Engine", self.art_mode))
        cg.addLayout(self._field_row("Style", self.style))
        cg.addWidget(self.ai_advisor)

        # ---- Editing ----
        editing_box = QGroupBox("Editing")
        editing_box.setAccessibleName("Editing settings")
        eg = self._section_layout(editing_box)

        self.edit_preset = QComboBox()
        editing = self.config.get("editing") or {}
        for name in (editing.get("presets") or {"standard": {}}):
            self.edit_preset.addItem(str(name).replace("_", " ").title(), userData=str(name))
        preset_idx = self.edit_preset.findData(str(editing.get("default_preset") or "standard"))
        if preset_idx >= 0:
            self.edit_preset.setCurrentIndex(preset_idx)
        self.edit_preset.setToolTip("Draft is fastest; Master uses stronger finishing and higher bitrate.")
        self._prepare_combo(
            self.edit_preset,
            "Editing preset",
            "Select a finishing preset for motion, captions, and output quality.",
        )
        selected_preset = dict(
            (editing.get("presets") or {}).get(str(self.edit_preset.currentData() or "standard")) or {}
        )
        self.edit_intensity = QDoubleSpinBox()
        self.edit_intensity.setRange(0.25, 2.0)
        self.edit_intensity.setSingleStep(0.05)
        self.edit_intensity.setDecimals(2)
        self.edit_intensity.setValue(float(selected_preset.get("motion_scale", 1.0)))
        self.edit_intensity.setToolTip("Controls transition, camera, and procedural motion intensity.")
        self._prepare_control(
            self.edit_intensity,
            "Editing intensity",
            "Adjust transition, camera, and procedural motion intensity.",
        )
        self.caption_mode = QComboBox()
        self.caption_mode.addItem("SRT sidecar", userData="sidecar")
        self.caption_mode.addItem("Burned + SRT", userData="both")
        self.caption_mode.addItem("Burned only", userData="burn")
        self.caption_mode.addItem("Off", userData="off")
        cap_idx = self.caption_mode.findData(str(selected_preset.get("caption_mode") or "sidecar"))
        if cap_idx >= 0:
            self.caption_mode.setCurrentIndex(cap_idx)
        self.caption_mode.setToolTip("Choose how captions are delivered with the video.")
        self._prepare_combo(
            self.caption_mode,
            "Caption delivery",
            "Choose a caption sidecar, burned captions, both, or no captions.",
        )
        self.edit_preset.currentIndexChanged.connect(self._apply_edit_preset_defaults)

        eg.addLayout(self._field_row("Preset", self.edit_preset))
        eg.addLayout(self._field_row("Intensity", self.edit_intensity))
        eg.addLayout(self._field_row("Captions", self.caption_mode))

        # ---- Batch ----
        batch_box = QGroupBox("Batch")
        batch_box.setAccessibleName("Batch settings")
        bg = self._section_layout(batch_box)

        self.count = QSpinBox()
        self.count.setRange(1, 100000)
        self.count.setValue(1)
        self.count.setSuffix(" video(s)")
        self.count.setToolTip("How many videos to create in this run.")
        self._prepare_control(
            self.count,
            "Batch video count",
            "Set how many videos to create in this run.",
        )
        bg.addLayout(self._field_row("Count", self.count))

        presets = QHBoxLayout()
        presets.setSpacing(6)
        preset_label = QLabel("Presets")
        preset_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        presets.addWidget(preset_label)
        for label, n in (("1", 1), ("5", 5), ("10", 10), ("100", 100)):
            btn = QPushButton(label)
            btn.setObjectName("ChipButton")
            btn.setToolTip(f"Set count to {n}")
            btn.setAccessibleName(f"Set batch count to {n}")
            btn.setAccessibleDescription(f"Sets the number of videos in this run to {n}.")
            btn.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda _=False, val=n: self._set_count(val))
            presets.addWidget(btn, 1)
        bg.addLayout(presets)

        self.unlimited = QCheckBox("Generate until stopped")
        self.unlimited.setToolTip("Creates videos continuously until you stop.")
        self._prepare_control(
            self.unlimited,
            "Unlimited generation",
            "Continue creating videos until the Stop action is used.",
        )
        self.unlimited.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.unlimited.toggled.connect(self._on_unlimited)
        bg.addWidget(self.unlimited)

        # ---- Delivery ----
        delivery_box = QGroupBox("Delivery")
        delivery_box.setAccessibleName("Delivery settings")
        dg = self._section_layout(delivery_box)

        self.proc_audio = QCheckBox("Soundtrack")
        self.proc_audio.setChecked(bool(self.config.get("audio", {}).get("enabled", True)))
        self.proc_audio.setToolTip("Mix audio into the MP4.")
        self._prepare_control(
            self.proc_audio,
            "Include soundtrack",
            "Mix the generated soundtrack into the MP4 video.",
        )
        self.gen_thumb = QCheckBox("Thumbnail")
        self.gen_thumb.setChecked(bool(self.config.get("output", {}).get("thumbnail", True)))
        self.gen_thumb.setToolTip("Save a JPG preview next to each video.")
        self._prepare_control(
            self.gen_thumb,
            "Generate thumbnail",
            "Save a JPG preview beside each generated video.",
        )
        dg.addWidget(self.proc_audio)
        dg.addWidget(self.gen_thumb)

        # ---- YouTube ----
        youtube_box = QGroupBox("YouTube")
        youtube_box.setAccessibleName("YouTube delivery settings")
        yg = self._section_layout(youtube_box)
        yt_cfg = self.config.get("youtube") or {}
        self.youtube_upload = QCheckBox("Upload to YouTube")
        self.youtube_upload.setChecked(bool(yt_cfg.get("enabled")))
        self.youtube_upload.setToolTip(
            "After each video is saved, upload it with an SEO title, hashtags, and thumbnail. "
            "Connect your channel first (YouTube menu). Default privacy is Unlisted."
        )
        self._prepare_control(
            self.youtube_upload,
            "Upload videos to YouTube",
            "Upload each completed video to the connected YouTube channel.",
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
        self._prepare_combo(
            self.youtube_privacy,
            "YouTube privacy",
            "Choose whether uploaded videos are unlisted, public, or private.",
        )
        self.youtube_channel = QLabel("Channel: not connected")
        self.youtube_channel.setObjectName("ChannelPill")
        self.youtube_channel.setWordWrap(True)
        self.youtube_channel.setAccessibleName("Connected YouTube channel")
        self.youtube_channel.setAccessibleDescription(
            "Shows which YouTube channel will receive uploaded videos."
        )
        self.youtube_channel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        yg.addWidget(self.youtube_upload)
        yg.addLayout(self._field_row("Privacy", self.youtube_privacy))
        yg.addWidget(self.youtube_channel)

        sections = (
            (video_box, 0, 0),
            (creative_box, 0, 1),
            (editing_box, 0, 2),
            (batch_box, 1, 0),
            (delivery_box, 1, 1),
            (youtube_box, 1, 2),
        )
        for section, row, column in sections:
            section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            root.addWidget(section, row, column)
        root.setColumnStretch(0, 1)
        root.setColumnStretch(1, 1)
        root.setColumnStretch(2, 1)
        root.setRowStretch(2, 1)

        self._connect_change_signals()

    @staticmethod
    def _section_layout(section: QGroupBox) -> QVBoxLayout:
        layout = QVBoxLayout(section)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        return layout

    @staticmethod
    def _field_row(label_text: str, control: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        label = QLabel(label_text)
        label.setMinimumWidth(68)
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        label.setBuddy(control)
        row.addWidget(label)
        row.addWidget(control, 1)
        return row

    @staticmethod
    def _prepare_control(control: QWidget, name: str, description: str) -> None:
        control.setAccessibleName(name)
        control.setAccessibleDescription(description)
        control.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _prepare_combo(self, combo: QComboBox, name: str, description: str) -> None:
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(8)
        self._prepare_control(combo, name, description)

    def _connect_change_signals(self) -> None:
        for combo in (
            self.resolution,
            self.duration,
            self.fps,
            self.art_mode,
            self.style,
            self.edit_preset,
            self.caption_mode,
            self.youtube_privacy,
        ):
            combo.currentIndexChanged.connect(lambda _index: self.settings_changed.emit())
        for spin in (self.count, self.edit_intensity):
            spin.valueChanged.connect(lambda _value: self.settings_changed.emit())
        for checkbox in (
            self.unlimited,
            self.proc_audio,
            self.gen_thumb,
            self.ai_advisor,
            self.youtube_upload,
        ):
            checkbox.toggled.connect(lambda _checked: self.settings_changed.emit())

    def _set_count(self, n: int) -> None:
        changed = self.unlimited.isChecked() or self.count.value() != n
        with QSignalBlocker(self.unlimited), QSignalBlocker(self.count):
            self.unlimited.setChecked(False)
            self.count.setEnabled(True)
            self.count.setValue(n)
        if changed:
            self.settings_changed.emit()

    def _on_unlimited(self, on: bool) -> None:
        self.count.setEnabled(not on)

    def _apply_edit_preset_defaults(self, _index: int = -1) -> None:
        editing = self.config.get("editing") or {}
        name = str(self.edit_preset.currentData() or "standard")
        preset = dict((editing.get("presets") or {}).get(name) or {})
        with QSignalBlocker(self.edit_intensity), QSignalBlocker(self.caption_mode):
            self.edit_intensity.setValue(float(preset.get("motion_scale", 1.0)))
            idx = self.caption_mode.findData(str(preset.get("caption_mode") or "sidecar"))
            if idx >= 0:
                self.caption_mode.setCurrentIndex(idx)

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
            "edit_preset": str(self.edit_preset.currentData() or "standard"),
            "edit_intensity": float(self.edit_intensity.value()),
            "caption_mode": str(self.caption_mode.currentData() or "sidecar"),
            "thumbnail": self.gen_thumb.isChecked(),
            "ai_enabled": self.ai_advisor.isChecked(),
            "ai_per_video": self.ai_advisor.isChecked(),
            "youtube_upload": self.youtube_upload.isChecked(),
            "youtube_privacy": str(self.youtube_privacy.currentData() or "unlisted"),
        }

    def set_youtube_channel(self, label: str) -> None:
        text = (label or "").strip() or "not connected"
        self.youtube_channel.setText(f"Uploads go to: {text}")
