"""Lightweight post-processing effects."""

from __future__ import annotations

import cv2
import numpy as np


def apply_contrast(frame: np.ndarray, amount: float) -> np.ndarray:
    """Adjust contrast around mid-gray. amount ~0.5-1.5."""
    f = frame.astype(np.float32)
    mid = 127.5
    f = (f - mid) * amount + mid
    return np.clip(f, 0, 255).astype(np.uint8)


def apply_glow(frame: np.ndarray, amount: float) -> np.ndarray:
    """Soft bloom based on bright areas."""
    if amount <= 0.05:
        return frame
    blur = cv2.GaussianBlur(frame, (0, 0), sigmaX=2 + amount * 6)
    return cv2.addWeighted(frame, 1.0, blur, amount * 0.45, 0)


def apply_effects(frame: np.ndarray, params: dict) -> np.ndarray:
    """Apply configured post effects."""
    out = frame
    contrast = float(params.get("contrast", 1.0))
    if abs(contrast - 1.0) > 0.05:
        out = apply_contrast(out, contrast)
    glow = float(params.get("glow", 0.0))
    if glow > 0.05:
        out = apply_glow(out, glow)
    blur = float(params.get("blur", 0.0))
    if blur > 0.15:
        out = cv2.GaussianBlur(out, (0, 0), sigmaX=blur * 2)
    return out
