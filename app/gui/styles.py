"""Shared Qt stylesheet for Genesis Artvision Engine — dark studio."""

APP_STYLE = """
QWidget {
    font-family: "Segoe UI", "Bahnschrift", sans-serif;
    font-size: 13px;
    color: #e8eef4;
}

QMainWindow, QDialog {
    background: #0f1c24;
}

QLabel#BrandTitle {
    font-family: "Bahnschrift", "Segoe UI Semibold", sans-serif;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 1.6px;
    color: #e8eef4;
    padding: 0;
}

QLabel#BrandSub {
    font-size: 10px;
    letter-spacing: 1.8px;
    color: #8aa0ad;
    padding: 0;
}

QLabel#HintLabel {
    font-size: 12px;
    color: #8aa0ad;
    padding: 2px 0 4px 0;
}

QLabel#ChannelPill {
    font-size: 11px;
    color: #9fd4cc;
    background: #143038;
    border: 1px solid #2a4450;
    border-radius: 8px;
    padding: 6px 8px;
}

QLabel#DialogTitle {
    font-size: 16px;
    font-weight: 700;
    color: #e8eef4;
}

QLabel#PathLabel {
    font-size: 12px;
    color: #9bb0bc;
}

QGroupBox {
    background: #162530;
    border: 1px solid #2a4450;
    border-radius: 12px;
    margin-top: 12px;
    padding: 10px 10px 8px 10px;
    font-weight: 600;
    color: #d5e4ec;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #8fd4c8;
}

QComboBox, QSpinBox, QLineEdit, QPlainTextEdit {
    background: #0f1c24;
    border: 1px solid #2a4450;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 22px;
    color: #e8eef4;
    selection-background-color: #1f7a88;
}

QComboBox:hover, QSpinBox:hover, QPlainTextEdit:hover {
    border-color: #2aa89a;
}

QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus {
    border-color: #2aa89a;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background: #162530;
    color: #e8eef4;
    border: 1px solid #2a4450;
    selection-background-color: #1f7a88;
}

QCheckBox, QRadioButton {
    spacing: 8px;
    padding: 4px 2px;
    color: #d5e4ec;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #4a6570;
    background: #0f1c24;
}

QCheckBox::indicator {
    border-radius: 4px;
}

QRadioButton::indicator {
    border-radius: 8px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: #1f7a88;
    border-color: #2aa89a;
}

QPushButton {
    background: #1a2c38;
    border: 1px solid #2a4450;
    border-radius: 8px;
    padding: 8px 14px;
    min-height: 28px;
    color: #e8eef4;
}

QPushButton:hover {
    background: #203844;
    border-color: #2aa89a;
}

QPushButton:pressed {
    background: #152830;
}

QPushButton:disabled {
    color: #5a7180;
    background: #14222c;
    border-color: #243844;
}

QPushButton#GenerateButton {
    background: #1f7a88;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1px;
    min-height: 40px;
    padding: 8px 20px;
}

QPushButton#GenerateButton:hover {
    background: #2494a4;
}

QPushButton#GenerateButton:pressed {
    background: #186874;
}

QPushButton#GenerateButton:disabled {
    background: #35565c;
    color: #9bb8be;
}

QPushButton#DangerButton {
    background: #2a1c1c;
    border-color: #8a3e3e;
    color: #f0c8c8;
}

QPushButton#DangerButton:hover {
    background: #3a2424;
    border-color: #c06060;
}

QPushButton#SecondaryButton {
    background: #0b3d4a;
    color: #ffffff;
    border: none;
}

QPushButton#SecondaryButton:hover {
    background: #156070;
}

QPushButton#SecondaryButton:disabled {
    background: #2a4048;
    color: #7a9098;
}

QPushButton#ChipButton {
    background: #143038;
    border: 1px solid #2a4450;
    border-radius: 16px;
    padding: 4px 12px;
    min-height: 22px;
    font-size: 12px;
    color: #c5e8e2;
}

QPushButton#ChipButton:hover {
    background: #1a4048;
    border-color: #2aa89a;
}

QPushButton#GhostButton {
    background: transparent;
    border: 1px solid #2a4450;
    color: #b8ccd6;
}

QProgressBar {
    border: 1px solid #2a4450;
    border-radius: 8px;
    background: #0f1c24;
    text-align: center;
    min-height: 22px;
    font-weight: 600;
    color: #e8eef4;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #1f7a88, stop:1 #2aa89a);
    border-radius: 7px;
}

QLabel#PreviewCanvas {
    background: #0a141c;
    color: #8aa0ad;
    border-radius: 10px;
    padding: 12px;
    font-size: 13px;
    border: 1px solid #2a4450;
}

QLabel#StatValue {
    font-size: 14px;
    font-weight: 600;
    color: #e8eef4;
}

QLabel#StatKey {
    color: #8aa0ad;
}

QPlainTextEdit#AiLog, QPlainTextEdit#PromptBox {
    background: #0f1c24;
    border: 1px solid #2a4450;
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 13px;
    color: #e8eef4;
}

QPlainTextEdit#PromptBox:focus {
    border-color: #2aa89a;
}

QFrame#PromptRule, QFrame#HeaderRule {
    color: #2a4450;
    background: #2a4450;
    max-height: 1px;
}

QFrame#HeaderBar {
    background: #121f28;
    border: 1px solid #2a4450;
    border-radius: 12px;
}

QFrame#StudioCard {
    background: #162530;
    border: 1px solid #2a4450;
    border-radius: 12px;
}

QMenuBar {
    background: transparent;
    color: #d5e4ec;
    padding: 2px 4px;
    border: none;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 6px;
}

QMenuBar::item:selected {
    background: #1a3440;
    color: #e8eef4;
}

QMenu {
    background: #162530;
    color: #e8eef4;
    border: 1px solid #2a4450;
    padding: 4px;
}

QMenu::item {
    padding: 8px 22px 8px 16px;
    border-radius: 4px;
}

QMenu::item:selected {
    background: #1f7a88;
}

QMenu::separator {
    height: 1px;
    background: #2a4450;
    margin: 4px 8px;
}

QStatusBar {
    background: #121f28;
    color: #8aa0ad;
    border-top: 1px solid #2a4450;
}

QToolTip {
    background: #0b3d4a;
    color: #ffffff;
    border: 1px solid #2aa89a;
    padding: 6px 8px;
}

QHeaderView::section {
    background: #121f28;
    color: #8fd4c8;
    border: none;
    border-bottom: 1px solid #2a4450;
    padding: 8px;
    font-weight: 600;
}

QTableWidget {
    background: #0f1c24;
    alternate-background-color: #142430;
    gridline-color: #2a4450;
    color: #e8eef4;
    border: 1px solid #2a4450;
    border-radius: 8px;
}

QTableWidget::item:selected {
    background: #1f7a88;
}

QScrollBar:vertical {
    background: #0f1c24;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #2a4450;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #0f1c24;
    height: 10px;
}

QScrollBar::handle:horizontal {
    background: #2a4450;
    border-radius: 5px;
}
"""
