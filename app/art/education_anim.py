"""Smooth animation, easing, and kid-engagement visual effects."""

from __future__ import annotations

import numpy as np
from PIL import ImageDraw, ImageFont


def ease_out_back(t: float, overshoot: float = 1.4) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    c1 = overshoot
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


def ease_in_out_cubic(t: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def ease_out_elastic(t: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 2.0 ** (-10.0 * t) * np.sin((t * 10.0 - 0.75) * (2.0 * np.pi) / 3.0) + 1.0


def smooth_pop(t: float, *, elastic: bool = True) -> float:
    """Kid-friendly pop-in scale 0→1 with bounce."""
    t = float(np.clip(t, 0.0, 1.0))
    if t <= 0:
        return 0.0
    return ease_out_elastic(t) if elastic else ease_out_back(t)


def segment_local(t: float, seg: dict) -> float:
    span = max(1e-6, float(seg["t1"]) - float(seg["t0"]))
    return float(np.clip((t - float(seg["t0"])) / span, 0.0, 1.0))


def weighted_segment_edges(n: int) -> np.ndarray:
    """Non-uniform timing: intro + body + celebration."""
    if n <= 0:
        return np.array([0.0, 1.0])
    if n == 1:
        return np.array([0.0, 1.0])
    weights = [1.35] + [1.0] * (n - 2) + [1.25]
    w = np.array(weights, dtype=np.float64)
    w /= w.sum()
    return np.concatenate([[0.0], np.cumsum(w)])


def draw_glow_ring(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int,
    color: tuple[int, int, int],
    t: float,
    *,
    layers: int = 4,
) -> None:
    pulse = 0.85 + 0.15 * np.sin(t * np.pi * 6)
    for i in range(layers, 0, -1):
        r = int(radius * pulse * (1.0 + i * 0.12))
        alpha = int(40 + 30 * (layers - i))
        fill = (*color, alpha)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)


def draw_prompt_bubble(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.ImageFont,
    t: float,
    *,
    fill: tuple[int, int, int] = (255, 252, 230),
    accent: tuple[int, int, int] = (255, 180, 60),
) -> None:
    bob = int(4 * np.sin(t * np.pi * 5))
    scale = smooth_pop(min(1.0, t * 3.0), elastic=False)
    if scale < 0.05:
        return
    pad_x, pad_y = 18, 10
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w = int((tw + pad_x * 2) * scale)
    h = int((th + pad_y * 2) * scale)
    draw.rounded_rectangle(
        (x - w // 2, y + bob - h // 2, x + w // 2, y + bob + h // 2),
        radius=14,
        fill=fill,
        outline=accent,
        width=3,
    )
    if scale > 0.5:
        draw.text((x, y + bob), text, font=font, fill=(60, 50, 40), anchor="mm")


def draw_confetti(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    t: float,
    seeds: np.ndarray,
    *,
    intensity: float = 1.0,
) -> None:
    if intensity <= 0.05:
        return
    colors = [
        (255, 90, 90), (255, 200, 60), (80, 200, 120),
        (80, 150, 255), (220, 100, 220), (255, 150, 80),
    ]
    n = min(len(seeds), 40)
    for i in range(n):
        phase = float(seeds[i])
        x = int((phase * 0.7 + t * 0.15 * (0.5 + phase)) % 1.0 * width)
        y = int(((t * 0.6 + phase * 0.3) % 1.0) * height * 0.55)
        size = int(3 + 4 * intensity * abs(np.sin(t * 8 + phase * 10)))
        col = colors[i % len(colors)]
        if i % 3 == 0:
            draw.rectangle((x, y, x + size, y + size // 2), fill=col)
        elif i % 3 == 1:
            draw.ellipse((x - size, y - size, x + size, y + size), fill=col)
        else:
            draw.polygon([(x, y - size), (x + size, y + size), (x - size, y + size)], fill=col)


def draw_segment_counter(
    draw: ImageDraw.ImageDraw,
    index: int,
    total: int,
    width: int,
    height: int,
    font: ImageFont.ImageFont,
) -> None:
    label = f"{index + 1} / {total}"
    draw.rounded_rectangle(
        (int(width * 0.04), int(height * 0.10), int(width * 0.16), int(height * 0.145)),
        radius=10,
        fill=(255, 255, 255),
        outline=(100, 120, 150),
        width=2,
    )
    draw.text((int(width * 0.10), int(height * 0.122)), label, font=font, fill=(70, 85, 110), anchor="mm")


def partial_polyline(pts: np.ndarray, progress: float) -> np.ndarray:
    """Return prefix of polyline up to progress (0–1) for smooth drawing."""
    if len(pts) < 2:
        return pts
    progress = float(np.clip(progress, 0.02, 1.0))
    seg_lens = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    total = float(seg_lens.sum()) + 1e-9
    target = total * progress
    out = [pts[0]]
    acc = 0.0
    for i, slen in enumerate(seg_lens):
        if acc + slen >= target:
            frac = (target - acc) / max(slen, 1e-9)
            pt = pts[i] + (pts[i + 1] - pts[i]) * frac
            out.append(pt)
            break
        out.append(pts[i + 1])
        acc += slen
    else:
        out.append(pts[-1])
    return np.asarray(out, dtype=np.float32)
