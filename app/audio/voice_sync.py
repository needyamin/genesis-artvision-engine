"""Hold each visual beat until its spoken line has finished."""

from __future__ import annotations

from typing import Any


def apply_speech_holds(
    segments: list[dict[str, Any]],
    holds: list[float],
    *,
    min_duration: float = 0.0,
    end_pad: float = 1.0,
    weights: list[float] | None = None,
) -> float:
    """Write t0/t1 from measured speech and editorial emphasis."""
    if not segments:
        return max(float(min_duration), 1.0)
    holds = [max(0.4, float(h)) for h in holds[: len(segments)]]
    while len(holds) < len(segments):
        holds.append(holds[-1] if holds else 4.0)
    emphasis = list(weights or [])
    for i, seg in enumerate(segments):
        try:
            weight = float(emphasis[i]) if i < len(emphasis) else float(seg.get("emphasis_weight", 1.0))
        except (TypeError, ValueError):
            weight = 1.0
        weight = max(0.5, min(2.0, weight))
        seg["emphasis_weight"] = weight
        # Emphasis adds reading/reaction room without ever compressing measured speech.
        holds[i] += max(0.0, weight - 1.0) * min(1.5, holds[i] * 0.18)
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
        seg["hold_seconds"] = float(hold)
        t += hold
    segments[-1]["t1"] = 1.0
    return total
