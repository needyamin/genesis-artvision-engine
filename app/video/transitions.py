"""Optional transition helpers between scenes (reserved for multi-scene)."""

from __future__ import annotations

import numpy as np


def crossfade(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    """Blend two frames. t in [0, 1]."""
    t = float(np.clip(t, 0.0, 1.0))
    return np.clip(a.astype(np.float32) * (1 - t) + b.astype(np.float32) * t, 0, 255).astype(
        np.uint8
    )
