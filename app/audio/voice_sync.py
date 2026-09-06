"""Hold each visual beat until its spoken line has finished."""

from __future__ import annotations

from typing import Any


def apply_speech_holds(
    segments: list[dict[str, Any]],
    holds: list[float],
    *,
    min_duration: float = 0.0,
    end_pad: float = 1.0,
) -> float:
    """Write t0/t1 from per-beat holds in seconds. Last beat runs to t=1."""
    if not segments:
        return max(float(min_duration), 1.0)
    holds = [max(0.4, float(h)) for h in holds[: len(segments)]]
    while len(holds) < len(segments):
        holds.append(holds[-1] if holds else 4.0)
    holds[-1] = holds[-1] + max(0.0, float(end_pad))
    raw = float(sum(holds))
    total = max(raw, float(min_duration), 1.0)
    extra = total - raw
    if extra > 0.0 and holds:
        if extra > 0.05:
            bump = extra / len(holds)
            holds = [h + bump for h in holds]
        else:
            holds[-1] += extra
        total = float(sum(holds))
    t = 0.0
    for seg, hold in zip(segments, holds):
        seg["t0"] = t / total
        seg["t1"] = min(1.0, (t + hold) / total)
        t += hold
    segments[-1]["t1"] = 1.0
    return total
