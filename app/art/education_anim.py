"""Smooth animation, easing, and kid-engagement visual effects."""

from __future__ import annotations

import numpy as np
from PIL import ImageDraw, ImageFont

from app.art.fonts import paint_text


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


def ease_by_name(t: float, name: str | None) -> float:
    """Map AI easing names onto motion curves."""
    key = str(name or "smooth").strip().lower()
    t = float(np.clip(t, 0.0, 1.0))
    if key == "snappy":
        return ease_out_back(t, overshoot=1.15)
    if key == "floaty":
        s = ease_in_out_cubic(t)
        return float(0.5 - 0.5 * np.cos(s * np.pi))
    return ease_in_out_cubic(t)


def camera_offset(
    t: float,
    feel: str | None,
    width: int,
    height: int,
    anim: float = 1.0,
) -> tuple[float, float]:
    """Subtle camera motion. Kids videos should stay nearly still."""
    key = str(feel or "static").strip().lower()
    if key == "drift":
        dx = np.sin(t * anim * np.pi * 0.35) * width * 0.006
        dy = np.cos(t * anim * np.pi * 0.28) * height * 0.005
        return float(dx), float(dy)
    if key == "pulse":
        dy = np.sin(t * anim * np.pi * 1.1) * height * 0.004
        return 0.0, float(dy)
    return 0.0, 0.0


def kids_pop(t: float) -> float:
    """Slow grow-in with a tiny overshoot — easy for ages 3–7 to follow."""
    t = float(np.clip(t, 0.0, 1.0))
    if t <= 0:
        return 0.0
    return ease_out_back(t, overshoot=0.45)


def kids_breathe(t: float, amp: float = 5.0) -> float:
    """Gentle idle bob after an object has appeared."""
    return float(amp * np.sin(t * np.pi * 1.1))


def motion_offset(
    t: float,
    anim: float,
    easing: str | None,
    camera_feel: str | None,
    amp: float,
    phase: float,
    width: int,
    height: int,
) -> tuple[float, float]:
    """Calm bounce plus optional camera. Default is a slow breathe, not a shake."""
    key = str(easing or "smooth").strip().lower()
    if key == "snappy":
        bounce = amp * 0.45 * np.sin((t * anim * 2.2 + phase) * np.pi * 2)
    elif key == "floaty":
        bounce = amp * 0.55 * np.sin((t * anim * 0.9 + phase) * np.pi * 2)
    else:
        bounce = kids_breathe(t * max(0.4, min(1.0, anim)), amp * 0.4)
    cam_x, cam_y = camera_offset(t, camera_feel, width, height, anim)
    return cam_x, float(bounce) + cam_y


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
    pulse = 0.96 + 0.04 * np.sin(t * np.pi * 1.3)
    layers = min(layers, 2)
    for i in range(layers, 0, -1):
        r = int(radius * pulse * (1.0 + i * 0.10))
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=max(2, 5 - i))


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
    bob = int(3 * np.sin(t * np.pi * 1.4))
    scale = kids_pop(min(1.0, t * 1.6))
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
        paint_text(draw, (x, y + bob), text, font, (60, 50, 40), anchor="mm")


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
    n = min(len(seeds), max(8, int(18 * intensity)))
    for i in range(n):
        phase = float(seeds[i])
        x = int((phase * 0.85 + t * 0.08 * (0.4 + phase)) % 1.0 * width)
        y = int(((t * 0.35 + phase * 0.4) % 1.0) * height * 0.5)
        size = int(4 + 3 * intensity)
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
    paint_text(draw, (int(width * 0.10), int(height * 0.122)), label, font, (70, 85, 110), anchor="mm")


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
