"""Lightweight post-processing — grade, glow, and editorial finish."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.edit_brain import director_time, ease_in_out_cubic, ease_out_cubic, fade_alpha

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


def _active_shot(params: dict, second: float) -> tuple[dict | None, float]:
    plan = params.get("editorial_plan")
    if not isinstance(plan, dict):
        return None, 0.0
    shots = list(plan.get("shots") or [])
    for shot in shots:
        start = float(shot.get("start", 0.0))
        end = max(start + 1e-6, float(shot.get("end", start + 1.0)))
        if start <= second < end or shot is shots[-1]:
            return shot, float(np.clip((second - start) / (end - start), 0.0, 1.0))
    return None, 0.0


def composite_shot_layers(
    outgoing: np.ndarray,
    current: np.ndarray,
    *,
    enter: float,
    leave: float,
    kind: str,
) -> np.ndarray:
    """Composite two independently rendered shots without frame history."""
    if outgoing.shape != current.shape:
        raise ValueError("Transition layers must have matching shapes")
    p = float(np.clip(enter, 0.0, 1.0))
    old_weight = float(np.clip(leave, 0.0, 1.0))
    if p >= 0.999:
        return current
    transition = str(kind or "dissolve").lower().replace("-", "_")
    h, w = current.shape[:2]
    if transition == "push":
        out = np.zeros_like(current)
        shift = int(round(p * w))
        if shift < w:
            out[:, : w - shift] = outgoing[:, shift:]
        if shift > 0:
            out[:, w - shift :] = current[:, :shift]
        return out
    if transition in {"page_turn", "pageturn"}:
        out = outgoing.copy()
        edge = int(round((1.0 - p) * w))
        if edge < w:
            out[:, edge:] = current[:, edge:]
        fold = max(2, int(w * 0.035))
        x0, x1 = max(0, edge - fold), min(w, edge + fold)
        if x1 > x0:
            xx = np.linspace(-1.0, 1.0, x1 - x0, dtype=np.float32)
            shade = (1.0 - np.abs(xx))[:, None] * 0.42
            region = out[:, x0:x1].astype(np.float32)
            out[:, x0:x1] = np.clip(region * (1.0 - shade[None, :, :]), 0, 255).astype(np.uint8)
        return out
    old = outgoing.astype(np.float32)
    new = current.astype(np.float32)
    mixed = old * (1.0 - p) + new * p
    if transition == "flash":
        flash = min(0.72, float(np.sin(np.pi * p)) * 0.72)
        mixed = mixed * (1.0 - flash) + 245.0 * flash
    elif old_weight < 0.999:
        mixed = new * (1.0 - old_weight) + mixed * old_weight
    return np.clip(mixed, 0, 255).astype(np.uint8)


def apply_shot_transition(
    frame: np.ndarray,
    shot: dict | None,
    local: float,
    kids: bool,
    *,
    outgoing: np.ndarray | None = None,
    leave: float | None = None,
) -> np.ndarray:
    """Apply a cut only when both complete shot layers are available.

    The renderer supplies a single finished frame, so manufacturing a fade to a
    solid there would discard the outgoing shot. Engines can pass both layers,
    or composite them directly while they still own segment rendering.
    """
    del kids
    if not shot or int(shot.get("index", 0)) == 0 or outgoing is None:
        return frame
    window = 0.10
    if local >= window:
        return frame
    enter = ease_out_cubic(local / window)
    return composite_shot_layers(
        outgoing,
        frame,
        enter=enter,
        leave=(1.0 - enter if leave is None else leave),
        kind=str(shot.get("transition") or "dissolve"),
    )


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
    second = t * max(0.0, duration)
    shot, shot_t = _active_shot(params, second)
    feel = str(params.get("edit_feel") or ("kids_show" if kids else "cinematic"))
    out = frame

    push = float(params.get("camera_push") or 0.0)
    if kids:
        push = 0.0
    if push > 0.004:
        camera_feel = str(params.get("camera_feel") or feel).lower()
        easing = str(params.get("easing") or "smooth").lower()
        dt = shot_t if camera_feel == "static" else director_time(shot_t, feel)
        if easing == "smooth":
            dt = ease_in_out_cubic(dt)
        zoom = 1.0 + push * dt
        cx = float(params.get("focus_x", 0.5))
        cy = float(params.get("focus_y", 0.5))
        out = apply_push_in(out, zoom, cx, cy)

    out = apply_shot_transition(out, shot, shot_t, kids)

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
