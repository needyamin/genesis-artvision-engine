"""Small offline mastering chain for consistent delivery loudness."""

from __future__ import annotations

import numpy as np


def master_audio(samples: np.ndarray, *, target_lufs: float = -14.0, ceiling_dbfs: float = -1.0) -> np.ndarray:
    """Apply RMS-based loudness targeting and a transparent soft limiter.

    This is an offline approximation suitable for generated mono content; final
    QC reports measured RMS/peak so a distributor can apply strict EBU R128.
    """
    audio = np.asarray(samples, dtype=np.float32)
    if not len(audio):
        return audio
    active = audio[np.abs(audio) > 1e-4]
    if not len(active):
        return audio
    rms = float(np.sqrt(np.mean(active * active)) + 1e-9)
    current_db = 20.0 * np.log10(rms)
    gain_db = float(np.clip(target_lufs - current_db, -12.0, 12.0))
    mastered = audio * (10.0 ** (gain_db / 20.0))
    ceiling = 10.0 ** (float(ceiling_dbfs) / 20.0)
    mastered = np.tanh(mastered / max(ceiling, 1e-6)) * ceiling
    peak = float(np.max(np.abs(mastered)) + 1e-9)
    if peak > ceiling:
        mastered *= ceiling / peak
    return mastered.astype(np.float32)
