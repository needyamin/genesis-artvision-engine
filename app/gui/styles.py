"""Shared Qt stylesheet for Genesis Artvision Engine."""

APP_STYLE = """
QWidget {
    font-family: "Segoe UI", "Bahnschrift", sans-serif;
    font-size: 13px;
    color: #1a2332;
}

QMainWindow, QDialog {
    background: #e8eef4;
}

QLabel#BrandTitle {
    font-family: "Bahnschrift", "Segoe UI Semibold", sans-serif;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #0b3d4a;
    padding: 0;
}

QLabel#BrandSub {
    font-size: 11px;
    letter-spacing: 1.5px;
    color: #3d6b78;
    padding: 0 0 2px 0;
}

QLabel#HintLabel {
    font-size: 12px;
    color: #3a5160;
    padding: 2px 4px 4px 4px;
}

QGroupBox {
    background: #f7fafc;
    border: 1px solid #c5d4de;
    border-radius: 10px;
    margin-top: 10px;
    padding: 8px 8px 6px 8px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #0b3d4a;
}

QComboBox, QSpinBox {
    background: #ffffff;
    border: 1px solid #b7c9d4;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 22px;
}

QComboBox:hover, QSpinBox:hover {
    border-color: #2a8f9e;
}

QComboBox:focus, QSpinBox:focus {
    border-color: #1f7a88;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QCheckBox {
    spacing: 8px;
    padding: 4px 2px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #8aa3b0;
    background: #fff;
}

QCheckBox::indicator:checked {
    background: #1f7a88;
    border-color: #1f7a88;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #b7c9d4;
    border-radius: 8px;
    padding: 8px 14px;
    min-height: 28px;
}

QPushButton:hover {
    background: #eef6f8;
    border-color: #2a8f9e;
}

QPushButton:pressed {
    background: #d9ecef;
}

QPushButton:disabled {
    color: #9aabb5;
    background: #eef2f5;
    border-color: #d0dae1;
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
    background: #186874;
}

QPushButton#GenerateButton:pressed {
    background: #13545e;
}

QPushButton#GenerateButton:disabled {
    background: #9bb8be;
    color: #eef6f8;
}

QPushButton#DangerButton {
    background: #fff5f4;
    border-color: #d98989;
    color: #8a2e2e;
}

QPushButton#DangerButton:hover {
    background: #ffe8e6;
}

QPushButton#SecondaryButton {
    background: #0b3d4a;
    color: #ffffff;
    border: none;
}

QPushButton#SecondaryButton:hover {
    background: #0e4d5c;
}

QPushButton#SecondaryButton:disabled {
    background: #9bb0b6;
    color: #e8eef4;
}

QProgressBar {
    border: 1px solid #b7c9d4;
    border-radius: 8px;
    background: #e4ebf0;
    text-align: center;
    min-height: 22px;
    font-weight: 600;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #1f7a88, stop:1 #2aa89a);
    border-radius: 7px;
}

QLabel#PreviewCanvas {
    background: #0f1c24;
    color: #8aa0ad;
    border-radius: 10px;
    padding: 12px;
    font-size: 13px;
}

QLabel#StatValue {
    font-size: 14px;
    font-weight: 600;
    color: #0b3d4a;
}

QLabel#StatKey {
    color: #5a7180;
}

QStatusBar {
    background: #dfe8ee;
    color: #3a5160;
}

QToolTip {
    background: #0b3d4a;
    color: #ffffff;
    border: none;
    padding: 6px 8px;
}
"""
