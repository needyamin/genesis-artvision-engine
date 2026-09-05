"""CPU / GPU utilization helpers for faster local renders."""

from __future__ import annotations

import os
from typing import Any


def cpu_count() -> int:
    return max(1, int(os.cpu_count() or 4))


def resolve_workers(config: dict[str, Any] | None, *, width: int = 1920, height: int = 1080) -> int:
    """
    How many frames to paint at once.

    Leaves a couple of logical cores for FFmpeg + the GUI. Caps 4K lower so
    in-flight Full-frame buffers do not balloon RAM.
    """
    perf = (config or {}).get("performance") or {}
    spec = perf.get("workers", "auto")
    cpu = cpu_count()
    if spec in (None, "auto", "Auto"):
        workers = max(2, cpu - 2)
    else:
        try:
            workers = int(spec)
        except (TypeError, ValueError):
            workers = max(2, cpu - 2)
    workers = max(1, min(workers, 16))
    pixels = max(1, int(width) * int(height))
    if pixels >= 3840 * 2160 * 0.9:
        workers = min(workers, 8)
    elif pixels >= 1920 * 1080 * 0.9:
        workers = min(workers, 14)
    return workers


def hardware_encode_enabled(config: dict[str, Any] | None) -> bool:
    perf = (config or {}).get("performance") or {}
    return bool(perf.get("hardware_encode", True))
