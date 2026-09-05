"""Composite AI-suggested images and titles onto non-kids art frames."""

from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from app.art.fonts import load_font, paint_text
from app.art.word_images import paste_illustration


def _beat_at(beats: list[dict[str, Any]], t: float) -> dict[str, Any] | None:
    if not beats:
        return None
    for beat in beats:
        t0 = beat.get("t0")
        t1 = beat.get("t1")
        if t0 is not None and t1 is not None:
            if float(t0) <= t < float(t1) or (t >= 0.999 and float(t1) >= 0.999):
                return beat
    n = len(beats)
    idx = min(n - 1, max(0, int(t * n)))
    return beats[idx]


def apply_ai_overlays(frame: np.ndarray, spec: Any, frame_number: int, total_frames: int) -> np.ndarray:
    """Draw suggested title/caption and paste the offline illustration."""
    params = getattr(spec, "params", None) or {}
    beats = params.get("ai_visual_beats") or []
    title = str(params.get("ai_title") or "")
    if not beats and not title:
        return frame
    t = frame_number / max(1, total_frames)
    beat = _beat_at(list(beats), t) if beats else None
    h, w = frame.shape[:2]
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    font_md = load_font(max(18, int(min(w, h) * 0.038)))
    font_sm = load_font(max(14, int(min(w, h) * 0.028)))

    headline = ""
    caption = ""
    if beat:
        headline = str(beat.get("overlay_text") or beat.get("line") or beat.get("title") or "")
        caption = str(beat.get("caption") or beat.get("fact") or "")
        path = str(beat.get("image_path") or "")
        if path:
            paste_illustration(
                img,
                path,
                (int(w * 0.86), int(h * 0.78)),
                max(88, int(min(w, h) * 0.18)),
            )
            draw = ImageDraw.Draw(img)
    if not headline:
        headline = title

    if headline:
        pad_x = min(int(w * 0.42), max(160, 12 * min(len(headline), 24) + 36))
        y = int(h * 0.045)
        draw.rounded_rectangle(
            (w // 2 - pad_x, y - 6, w // 2 + pad_x, y + 34),
            radius=14,
            fill=(255, 255, 255),
            outline=(50, 70, 95),
            width=3,
        )
        paint_text(draw, (w // 2, y + 14), headline[:48], font_md, (30, 45, 70), anchor="mm", max_width=pad_x * 2 - 16)
    if caption:
        cy = int(h * 0.93)
        draw.rounded_rectangle(
            (int(w * 0.12), cy - 18, int(w * 0.72), cy + 18),
            radius=12,
            fill=(255, 255, 255),
            outline=(70, 90, 110),
            width=2,
        )
        paint_text(draw, (int(w * 0.14), cy), caption[:72], font_sm, (50, 70, 90), anchor="lm", max_width=int(w * 0.54))

    return np.array(img, dtype=np.uint8)
