"""Prompt window — type a brief, generate a video from it."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from app.ai.client import has_api_key
from app.gui.branding import apply_app_icon
from app.gui.styles import APP_STYLE

EXAMPLES = (
    ("Kids story", "A bedtime story about a brave orange cat named Luna who finds the moon behind a rain cloud."),
    ("Classroom", "Explain how rain is made, step by step, as a clear classroom lesson with a calm voice."),
    ("Trending", "Why everyone is talking about AI agents this week — a punchy internet brief with facts."),
)


class PromptWindow(QDialog):
    """New window: write a prompt, choose offline or AI, generate one video."""

    def __init__(self, config: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.payload: dict[str, Any] | None = None
        self.setWindowTitle("Prompt a video — Genesis Artvision Engine")
        apply_app_icon(self)
        self.setStyleSheet(APP_STYLE)
        self.setAccessibleName("Prompt a video")
        self.setAccessibleDescription(
            "Describe a film, choose how it is planned, and generate it locally."
        )
        self.resize(760, 640)
        self.setMinimumSize(640, 540)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(12)

        heading = QLabel("Prompt a video")
        heading.setObjectName("DialogTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignLeft)
        root.addWidget(heading)

        hint = QLabel(
            "Write what the film should be. Offline builds it on this machine. "
            "AI suggestion asks OpenRouter for a plan, then the engine still paints locally."
        )
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.editor = QPlainTextEdit()
        self.editor.setObjectName("PromptBox")
        self.editor.setPlaceholderText(
            "Example: A picture-book about a small boat that follows the stars home…"
        )
        self.editor.setAccessibleName("Video prompt")
        self.editor.setAccessibleDescription(
            "Describe the video to create. Press Control+Enter to generate."
        )
        self.editor.setTabChangesFocus(True)
        self.editor.setMinimumHeight(180)
        font = QFont(self.editor.font())
        font.setPointSize(12)
        self.editor.setFont(font)
        root.addWidget(self.editor, 1)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        chips.addWidget(QLabel("Try:"))
        self.example_buttons: list[QPushButton] = []
        for label, text in EXAMPLES:
            btn = QPushButton(label)
            btn.setObjectName("ChipButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setAccessibleName(f"Use {label} example")
            btn.setAccessibleDescription(f"Replace the prompt with the {label.lower()} example.")
            btn.clicked.connect(lambda _=False, t=text: self.editor.setPlainText(t))
            self.example_buttons.append(btn)
            chips.addWidget(btn)
        chips.addStretch(1)
        root.addLayout(chips)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("PromptRule")
        root.addWidget(line)

        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Source"))
        self.source_group = QButtonGroup(self)
        self.offline_radio = QRadioButton("Offline (no internet)")
        self.ai_radio = QRadioButton("AI suggestion")
        self.offline_radio.setAccessibleName("Offline planning")
        self.offline_radio.setAccessibleDescription(
            "Plan and create the video entirely on this machine."
        )
        self.ai_radio.setAccessibleName("AI-assisted planning")
        self.ai_radio.setAccessibleDescription(
            "Ask OpenRouter for a plan, then create the video locally."
        )
        self.offline_radio.setChecked(True)
        self.source_group.addButton(self.offline_radio)
        self.source_group.addButton(self.ai_radio)
        source_row.addWidget(self.offline_radio)
        source_row.addWidget(self.ai_radio)
        source_row.addStretch(1)
        root.addLayout(source_row)

        key_ok = has_api_key(self.config)
        self.key_hint = QLabel(
            "OpenRouter key found — AI suggestion will plan title, beats, and voice."
            if key_ok
            else "No OPENROUTER_API_KEY in .env — AI suggestion will fall back to offline."
        )
        self.key_hint.setObjectName("HintLabel")
        self.key_hint.setWordWrap(True)
        self.key_hint.setAccessibleName("OpenRouter availability")
        self.key_hint.setAccessibleDescription(self.key_hint.text())
        root.addWidget(self.key_hint)
        if not key_ok:
            self.key_hint.setObjectName("WarningText")
            self.ai_radio.setToolTip("Add OPENROUTER_API_KEY to .env for a richer plan. Offline still works.")

        opts = QHBoxLayout()
        opts.setSpacing(12)
        self.engine = QComboBox()
        self.engine.addItem("Auto-detect from prompt", userData=None)
        self.engine.addItem("Kids Storybook", userData="kids_storybook")
        self.engine.addItem("How It Works", userData="how_it_works")
        self.engine.addItem("Trending Brief", userData="trend_brief")
        self.engine.setToolTip("Leave on Auto unless you want a specific engine.")
        self.engine.setAccessibleName("Video engine")
        self.engine.setAccessibleDescription(
            "Choose a specific visual format, or let the prompt select one."
        )

        self.quality = QComboBox()
        self.quality.addItem("Full HD — 1920×1080", userData="1080")
        self.quality.addItem("4K UHD — 3840×2160", userData="4k")
        self.quality.setToolTip("Full HD is sharp and faster. 4K is the highest quality (slower).")
        self.quality.setAccessibleName("Output quality")
        self.quality.setAccessibleDescription("Choose Full HD or 4K video resolution.")

        self.length = QComboBox()
        self.length.addItem("Auto (fits the voice)", userData=None)
        self.length.addItem("30 seconds", userData=30)
        self.length.addItem("60 seconds", userData=60)
        self.length.setToolTip("Pictures still hold until each spoken line finishes.")
        self.length.setAccessibleName("Video length")
        self.length.setAccessibleDescription("Choose automatic, 30-second, or 60-second timing.")

        for label, widget in (("Engine", self.engine), ("Quality", self.quality), ("Length", self.length)):
            col = QVBoxLayout()
            col.setSpacing(4)
            lab = QLabel(label)
            lab.setObjectName("StatKey")
            lab.setBuddy(widget)
            col.addWidget(lab)
            col.addWidget(widget)
            opts.addLayout(col, 1)
        root.addLayout(opts)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("GhostButton")
        self.cancel_btn.setAccessibleName("Cancel prompt")
        self.cancel_btn.setAccessibleDescription("Close without generating a video.")
        self.submit_btn = QPushButton("GENERATE FROM PROMPT")
        self.submit_btn.setObjectName("GenerateButton")
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.setDefault(True)
        self.submit_btn.setAccessibleName("Generate from prompt")
        self.submit_btn.setAccessibleDescription(
            "Generate the video. Keyboard shortcut: Control+Enter."
        )
        buttons.addWidget(self.cancel_btn)
        buttons.addWidget(self.submit_btn)
        root.addLayout(buttons)

        self.cancel_btn.clicked.connect(self.reject)
        self.submit_btn.clicked.connect(self._submit)
        self.editor.textChanged.connect(self._sync_submit)
        for sequence in ("Ctrl+Return", "Ctrl+Enter"):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(self._submit)
            if not hasattr(self, "_submit_shortcuts"):
                self._submit_shortcuts: list[QShortcut] = []
            self._submit_shortcuts.append(shortcut)

        tab_widgets: list[QWidget] = [
            self.editor,
            *self.example_buttons,
            self.offline_radio,
            self.ai_radio,
            self.engine,
            self.quality,
            self.length,
            self.cancel_btn,
            self.submit_btn,
        ]
        for current, following in zip(tab_widgets, tab_widgets[1:]):
            self.setTabOrder(current, following)

        self._sync_submit()

    def _sync_submit(self) -> None:
        self.submit_btn.setEnabled(bool(self.editor.toPlainText().strip()))

    def _submit(self) -> None:
        text = self.editor.toPlainText().strip()
        if not text:
            return
        self.payload = {
            "user_prompt": text,
            "prompt_mode": "ai" if self.ai_radio.isChecked() else "offline",
            "engine": self.engine.currentData(),
            "prompt_quality": str(self.quality.currentData() or "1080"),
            "duration": self.length.currentData(),
        }
        self.accept()
