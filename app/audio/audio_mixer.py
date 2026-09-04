"""Audio mixer utilities."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.audio.procedural_music import write_wav


def mix_to_mono(tracks: list[np.ndarray], weights: list[float] | None = None) -> np.ndarray:
    if not tracks:
        return np.zeros(1, dtype=np.float32)
    length = max(len(t) for t in tracks)
    out = np.zeros(length, dtype=np.float32)
    weights = weights or [1.0] * len(tracks)
    for track, w in zip(tracks, weights):
        out[: len(track)] += track * float(w)
    peak = float(np.max(np.abs(out)) + 1e-9)
    return (out / peak * 0.9).astype(np.float32)


def save_mixed_wav(path: Path, tracks: list[np.ndarray], sample_rate: int = 44100) -> Path:
    write_wav(path, mix_to_mono(tracks), sample_rate)
    return path
