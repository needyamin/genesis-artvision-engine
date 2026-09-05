"""Lightweight post-processing — grade, glow, and editorial finish."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.edit_brain import director_time, fade_alpha

_VIGNETTE_CACHE: dict[tuple[int, int, int], np.ndarray] = {}


def apply_contrast(frame: np.ndarray, amount: float) -> np.ndarray:
    """Adjust contrast around mid-gray. amount ~0.5-1.5."""
    f = frame.astype(np.float32)
    mid = 127.5
    f = (f - mid) * amount + mid
    return np.clip(f, 0, 255).astype(np.uint8)


def apply_glow(frame: np.ndarray, amount: float) -> np.ndarray:
    """Soft bloom based on bright areas."""
    if amount <= 0.05:
        return frame
    blur = cv2.GaussianBlur(frame, (0, 0), sigmaX=2 + amount * 6)
    return cv2.addWeighted(frame, 1.0, blur, amount * 0.45, 0)


def apply_bloom_highlights(frame: np.ndarray, amount: float, threshold: float = 185.0) -> np.ndarray:
    """Volumetric highlight bloom: extract specular brights, blur with dual radius, add back."""
    if amount <= 0.04:
        return frame
    f = frame.astype(np.float32)
    bright = np.maximum(0.0, f - threshold)
    if not np.any(bright > 0.0):
        return frame
    b1 = cv2.GaussianBlur(bright, (0, 0), sigmaX=4.0)
    b2 = cv2.GaussianBlur(bright, (0, 0), sigmaX=14.0)
    bloom = (b1 * 0.65 + b2 * 0.35) * (amount * 1.6)
    return np.clip(f + bloom, 0, 255).astype(np.uint8)


def apply_chromatic_aberration(frame: np.ndarray, shift: float) -> np.ndarray:
    """Lens fringe: red channel shifts slightly right, blue channel slightly left."""
    s = int(round(shift))
    if s <= 0:
        return frame
    h, w = frame.shape[:2]
    s = min(s, max(1, w // 40))
    out = frame.copy()
    out[:, s:, 0] = frame[:, :-s, 0]
    out[:, :-s, 2] = frame[:, s:, 2]
    return out


def apply_grade(frame: np.ndarray, grade: str) -> np.ndarray:
    """Offline color grade presets."""
    name = (grade or "").strip().lower()
    if name not in {"soft", "vivid", "pastel", "cinematic", "broadcast"}:
        return frame
    f = frame.astype(np.float32)
    if name == "soft":
        f = (f - 127.5) * 0.92 + 127.5 + 8.0
        f = _sat_float(f, 0.92)
    elif name == "vivid":
        f = (f - 127.5) * 1.12 + 127.5
        f = _sat_float(f, 1.18)
    elif name == "pastel":
        f = (f - 127.5) * 0.90 + 127.5 + 10.0
        f = _sat_float(f, 0.88)
        f = f * 0.98 + 8.0
    elif name == "broadcast":
        # Kids-TV: clean mids, slightly warm, readable blacks.
        f = (f - 127.5) * 1.08 + 127.5 + 4.0
        f = _sat_float(f, 1.10)
        f = f * np.array([1.03, 1.01, 0.98], dtype=np.float32)
    else:  # cinematic
        f = (f - 127.5) * 1.18 + 127.5 - 6.0
        f = _sat_float(f, 0.92)
        lift = np.array([6.0, 2.0, -8.0], dtype=np.float32)
        gain = np.array([1.05, 1.0, 0.94], dtype=np.float32)
        f = f * gain + lift
    return np.clip(f, 0, 255).astype(np.uint8)


def _sat_float(f: np.ndarray, amount: float) -> np.ndarray:
    gray = f.mean(axis=2, keepdims=True)
    return gray + (f - gray) * amount


def apply_effects(frame: np.ndarray, params: dict) -> np.ndarray:
    """Apply configured post effects including AI grade/glow/blur/contrast."""
    out = frame
    grade = str(params.get("grade") or "")
    if grade:
        out = apply_grade(out, grade)
    contrast = float(params.get("contrast", 1.0))
    if abs(contrast - 1.0) > 0.05:
        out = apply_contrast(out, contrast)
    glow = float(params.get("glow", 0.0))
    if params.get("_kids_text"):
        glow = min(glow, 0.22)
    if glow > 0.05:
        out = apply_glow(out, glow)
    blur = float(params.get("blur", 0.0))
    if params.get("_kids_text"):
        blur = min(blur, 0.12)
    if blur > 0.15:
        out = cv2.GaussianBlur(out, (0, 0), sigmaX=blur * 2)
    return out


def apply_push_in(
    frame: np.ndarray,
    zoom: float,
    cx: float = 0.5,
    cy: float = 0.5,
) -> np.ndarray:
    """Ken Burns / dolly-in by cropping toward a focus and scaling back."""
    if zoom <= 1.004:
        return frame
    h, w = frame.shape[:2]
    z = float(min(1.18, max(1.0, zoom)))
    nw = max(8, int(w / z))
    nh = max(8, int(h / z))
    x0 = int(np.clip(w * cx - nw / 2.0, 0, w - nw))
    y0 = int(np.clip(h * cy - nh / 2.0, 0, h - nh))
    crop = frame[y0 : y0 + nh, x0 : x0 + nw]
    return cv2.resize(crop, (w, h), interpolation=cv2.INTER_LINEAR)


def _vignette_mask(h: int, w: int, amount: float) -> np.ndarray:
    key = (h, w, int(round(amount * 100)))
    cached = _VIGNETTE_CACHE.get(key)
    if cached is not None:
        return cached
    ys = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, None]
    xs = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    # Slightly oval so landscape doesn't crush the sides.
    dist = np.sqrt((xs * 0.92) ** 2 + (ys * 1.05) ** 2)
    fall = 0.55 + (1.0 - amount) * 0.35
    mask = np.clip(1.0 - np.clip(dist - fall, 0.0, 2.0) * (0.55 * amount + 0.15), 1.0 - amount, 1.0)
    out = mask.astype(np.float32)[:, :, None]
    if len(_VIGNETTE_CACHE) > 24:
        _VIGNETTE_CACHE.clear()
    _VIGNETTE_CACHE[key] = out
    return out


def apply_vignette(frame: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0.03:
        return frame
    h, w = frame.shape[:2]
    mask = _vignette_mask(h, w, float(np.clip(amount, 0.0, 0.7)))
    f = frame.astype(np.float32) * mask
    return np.clip(f, 0, 255).astype(np.uint8)


def apply_grain(frame: np.ndarray, amount: float, seed: int, frame_number: int) -> np.ndarray:
    if amount <= 0.01:
        return frame
    h, w = frame.shape[:2]
    rng = np.random.default_rng(int(seed) * 10007 + int(frame_number))
    noise = rng.normal(0.0, 8.0 * amount, (h, w, 1)).astype(np.float32)
    return np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def apply_micro_contrast(frame: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0.02:
        return frame
    blur = cv2.GaussianBlur(frame, (0, 0), sigmaX=1.15)
    return cv2.addWeighted(frame, 1.0 + amount, blur, -amount, 0)


def apply_master_fade(
    frame: np.ndarray,
    alpha: float,
    *,
    kids: bool = False,
) -> np.ndarray:
    a = float(np.clip(alpha, 0.0, 1.0))
    if a >= 0.995:
        return frame
    color = np.array([248, 242, 228], dtype=np.float32) if kids else np.array([0.0, 0.0, 0.0], dtype=np.float32)
    f = frame.astype(np.float32)
    return np.clip(f * a + color * (1.0 - a), 0, 255).astype(np.uint8)


def apply_editorial_finish(
    frame: np.ndarray,
    params: dict,
    frame_number: int,
    total_frames: int,
    *,
    duration: float,
    fps: int,
    seed: int,
) -> np.ndarray:
    """What an editor does after the picture is locked: push, grade edges, fade."""
    del fps
    kids = bool(params.get("_kids_text"))
    t = frame_number / max(1, total_frames)
    feel = str(params.get("edit_feel") or ("kids_show" if kids else "cinematic"))
    out = frame

    push = float(params.get("camera_push") or 0.0)
    if kids:
        push = 0.0
    if push > 0.004:
        dt = director_time(t, feel)
        zoom = 1.0 + push * dt
        cx = float(params.get("focus_x", 0.5))
        cy = float(params.get("focus_y", 0.5))
        out = apply_push_in(out, zoom, cx, cy)

    bloom = float(params.get("bloom") or 0.0)
    if bloom > 0.04:
        out = apply_bloom_highlights(out, bloom)

    chroma = float(params.get("chroma") or 0.0)
    if kids:
        chroma = 0.0
    if chroma > 0.3:
        out = apply_chromatic_aberration(out, chroma)

    vignette = float(params.get("vignette") or (0.08 if kids else 0.32))
    if kids:
        vignette = min(vignette, 0.12)
    out = apply_vignette(out, vignette)

    sharpen = float(params.get("micro_contrast") or (0.06 if kids else 0.16))
    if kids:
        sharpen = 0.0
    out = apply_micro_contrast(out, sharpen)

    grain = float(params.get("grain") or (0.0 if kids else 0.045))
    if kids:
        grain = 0.0
    out = apply_grain(out, grain, seed, frame_number)

    fade_in = float(params.get("fade_in") or (0.35 if kids else 0.7))
    fade_out = float(params.get("fade_out") or (0.65 if kids else 1.1))
    alpha = fade_alpha(t, duration, fade_in, fade_out)
    out = apply_master_fade(out, alpha, kids=kids)
    return out
