"""Shared UI helpers for kids educational video engines."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.art.education_anim import draw_confetti, draw_prompt_bubble, draw_segment_counter, smooth_pop
from app.art.word_images import paste_word_image


def load_font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/comicbd.ttf",
        "C:/Windows/Fonts/comic.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Comic Sans MS.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def segment_at(segments: list[dict], t: float) -> dict:
    for seg in segments:
        if float(seg["t0"]) <= t < float(seg["t1"]):
            return seg
    return segments[-1] if segments else {
        "line": "Let's learn!",
        "fact": "Learning is fun!",
        "tip": "Say it out loud!",
        "voice_line": "Let's learn!",
        "t0": 0.0,
        "t1": 1.0,
        "index": 0,
    }


def pop_scale(local_t: float, enabled: bool = True) -> float:
    if not enabled:
        return 1.0
    return smooth_pop(local_t, elastic=True)


def draw_title_banner(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    title: str,
    font: ImageFont.ImageFont,
    *,
    y_frac: float = 0.032,
) -> None:
    banner_y = int(height * y_frac)
    pad_x = min(220, width // 3)
    draw.rounded_rectangle(
        (width // 2 - pad_x, banner_y - 4, width // 2 + pad_x, banner_y + 32),
        radius=14,
        fill=(255, 255, 255),
        outline=(60, 80, 110),
        width=3,
    )
    draw.text((width // 2, banner_y + 14), title, font=font, fill=(40, 60, 90), anchor="mm")


def draw_closing_banner(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    message: str,
    font: ImageFont.ImageFont,
) -> None:
    draw.rounded_rectangle(
        (width // 2 - 200, int(height * 0.88), width // 2 + 200, int(height * 0.96)),
        radius=12,
        fill=(255, 250, 230),
        outline=(80, 100, 60),
        width=3,
    )
    draw.text((width // 2, int(height * 0.92)), message, font=font, fill=(50, 90, 50), anchor="mm")


def draw_learning_strip(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    seg: dict,
    width: int,
    height: int,
    fonts: dict[str, ImageFont.ImageFont],
    *,
    show_word_image: bool = True,
    accent_color: tuple[int, int, int] = (80, 120, 180),
    t: float = 0.0,
) -> None:
    y0 = int(height * 0.78)
    draw.rounded_rectangle(
        (int(width * 0.06), y0, int(width * 0.94), int(height * 0.97)),
        radius=16,
        fill=(255, 255, 255),
        outline=(70, 90, 120),
        width=3,
    )
    md = fonts.get("md") or fonts.get("sm")
    sm = fonts.get("sm") or md
    draw.text((int(width * 0.12), y0 + 28), str(seg.get("line", "")), font=md, fill=(40, 55, 80), anchor="lm")
    if seg.get("phonics"):
        draw.text((int(width * 0.12), y0 + 70), str(seg.get("phonics", "")), font=sm, fill=(60, 80, 110), anchor="lm")
    draw.text((int(width * 0.12), y0 + 100), str(seg.get("fact", "")), font=sm, fill=(80, 100, 70), anchor="lm")
    tip = str(seg.get("tip", "") or seg.get("challenge", ""))
    if tip:
        draw.text((int(width * 0.62), y0 + 100), tip, font=sm, fill=(120, 70, 40), anchor="lm")
    word = str(seg.get("word") or seg.get("motif") or "")
    if show_word_image and word:
        paste_word_image(
            img,
            word,
            (int(width * 0.86), y0 + int((height * 0.97 - y0) / 2)),
            max(72, int(min(width, height) * 0.12)),
        )
    # Quiz / engage bubble
    quiz = str(seg.get("quiz") or seg.get("engage") or "")
    if quiz and t > 0.0:
        local = (t - float(seg.get("t0", 0))) / max(1e-6, float(seg.get("t1", 1)) - float(seg.get("t0", 0)))
        if local > 0.55:
            draw_prompt_bubble(
                draw, quiz,
                int(width * 0.5), y0 - 18,
                sm, max(0.0, (local - 0.55) * 2.5),
            )


def draw_progress_dots(
    draw: ImageDraw.ImageDraw,
    seg: dict,
    segments: list[dict],
    width: int,
    height: int,
    color: tuple[int, int, int],
    t: float = 0.0,
) -> None:
    dots = len(segments)
    if dots <= 1:
        return
    active = int(seg.get("index", 0))
    for i in range(dots):
        dx = int(width * 0.15 + i * (width * 0.7) / max(1, dots - 1))
        is_active = i == active
        pulse = 1.0 + 0.35 * np.sin(t * np.pi * 8) if is_active else 1.0
        r = int((7 if is_active else 3) * pulse)
        fill = color if is_active else (180, 190, 200)
        draw.ellipse((dx - r, int(height * 0.95) - r, dx + r, int(height * 0.95) + r), fill=fill)


def draw_engagement_overlay(
    draw: ImageDraw.ImageDraw,
    seg: dict,
    width: int,
    height: int,
    font: ImageFont.ImageFont,
    t: float,
    confetti_seeds: np.ndarray | None = None,
) -> None:
    """Draw segment counter, celebration, and confetti near segment end."""
    idx = int(seg.get("index", 0))
    total = int(seg.get("_total", idx + 1))
    draw_segment_counter(draw, idx, total, width, height, font)

    local = (t - float(seg.get("t0", 0))) / max(1e-6, float(seg.get("t1", 1)) - float(seg.get("t0", 0)))
    if local > 0.78 and seg.get("celebrate"):
        celeb_t = (local - 0.78) / 0.22
        draw_prompt_bubble(
            draw, str(seg["celebrate"]),
            int(width * 0.5), int(height * 0.66),
            font, celeb_t,
            fill=(255, 245, 200),
            accent=(255, 160, 50),
        )
        if confetti_seeds is not None:
            draw_confetti(draw, width, height, t, confetti_seeds, intensity=celeb_t)
