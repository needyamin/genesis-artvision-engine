"""AI used to paste title cards onto procedural art. Engines paint the whole frame now."""

from __future__ import annotations

from typing import Any

import numpy as np


def apply_ai_overlays(frame: np.ndarray, spec: Any, frame_number: int, total_frames: int) -> np.ndarray:
    """No-op: Particle / Galaxy / Waves / Tunnel / Explainer already own the frame."""
    return frame
