"""Shared UI helpers for kids educational video engines."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.art.education_anim import draw_confetti, kids_pop
from app.art.fonts import load_font, paint_text, usable_caption
from app.art.kids_layout import KidsLayout, kids_layout
from app.art.word_images import paste_segment_image

__all__ = [
    "draw_closing_banner",
    "draw_engagement_overlay",
    "draw_kids_chrome",
    "draw_learning_strip",
    "draw_phonics_badge",
    "draw_picture_card",
    "draw_progress_dots",
    "draw_shape_properties_badge",
    "draw_stage_card",
    "draw_step_progress_bar",
    "draw_ten_frame",
    "draw_title_banner",
    "kids_layout",
    "load_font",
    "paint_text",
    "paste_picture",
    "pop_scale",
    "segment_at",
]


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
    return kids_pop(local_t)


def _L(width: int, height: int, layout: KidsLayout | None) -> KidsLayout:
    return layout if layout is not None else kids_layout(width, height)


def draw_stage_card(
    draw: ImageDraw.ImageDraw,
    layout: KidsLayout,
    *,
    fill: tuple[int, int, int] | None = (255, 255, 255),
    outline: tuple[int, int, int] = (50, 70, 100),
) -> None:
    b = layout.stage
    kwargs = {"outline": outline, "width": 4}
    if fill is not None:
        kwargs["fill"] = fill
    draw.rounded_rectangle(b.xy, radius=min(28, max(8, b.h // 8)), **kwargs)


def draw_picture_card(
    draw: ImageDraw.ImageDraw,
    layout: KidsLayout,
    *,
    fill: tuple[int, int, int] = (255, 255, 255),
    outline: tuple[int, int, int] = (50, 70, 100),
) -> None:
    b = layout.picture
    draw.rounded_rectangle(b.xy, radius=min(24, b.h // 10), fill=fill, outline=outline, width=4)


def paste_picture(
    img: Image.Image,
    seg: dict,
    layout: KidsLayout,
    *,
    bounce: int = 0,
) -> None:
    draw_picture_card(ImageDraw.Draw(img), layout)
    paste_segment_image(img, seg, layout.picture_xy, layout.picture_size, bounce=bounce)


def draw_title_banner(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    title: str,
    font: ImageFont.ImageFont,
    *,
    y_frac: float = 0.032,
    layout: KidsLayout | None = None,
    count_label: str = "",
) -> None:
    del y_frac
    L = _L(width, height, layout)
    b = L.title
    draw.rounded_rectangle(b.xy, radius=16, fill=(255, 255, 255), outline=(60, 80, 110), width=3)
    title_right = L.counter.x0 - 8 if count_label else b.x1
    title_cx = (b.x0 + title_right) // 2
    title_w = title_right - b.x0 - 16
    paint_text(draw, (title_cx, b.cy), title, font, (40, 60, 90), anchor="mm", max_width=title_w)
    if count_label:
        c = L.counter
        draw.rounded_rectangle(c.xy, radius=10, fill=(245, 248, 252), outline=(100, 120, 150), width=2)
        paint_text(draw, (c.cx, c.cy), count_label, font, (70, 85, 110), anchor="mm", max_width=c.w - 8)


def draw_closing_banner(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    message: str,
    font: ImageFont.ImageFont,
    *,
    layout: KidsLayout | None = None,
) -> None:
    L = _L(width, height, layout)
    b = L.caption
    draw.rounded_rectangle(b.xy, radius=16, fill=(255, 250, 230), outline=(80, 100, 60), width=3)
    paint_text(draw, (b.cx, b.cy), message, font, (50, 90, 50), anchor="mm", max_width=b.w - 32)


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
    layout: KidsLayout | None = None,
    caption_alpha: float = 1.0,
) -> None:
    del img, show_word_image, accent_color
    if caption_alpha < 0.12:
        return
    L = _L(width, height, layout)
    b = L.caption
    draw.rounded_rectangle(b.xy, radius=16, fill=(255, 255, 255), outline=(70, 90, 120), width=3)
    md = fonts.get("md") or fonts.get("sm")
    sm = fonts.get("sm") or md
    pad_x = max(18, int(b.w * 0.04))
    line = max(18, int(b.h * 0.22))
    x = b.x0 + pad_x
    y0 = b.y0 + max(12, int(b.h * 0.16))
    text_w = int(b.w * 0.90)
    headline = usable_caption(seg.get("overlay_text"), usable_caption(seg.get("line") or ""))
    if t > 0.0:
        local = (t - float(seg.get("t0", 0))) / max(1e-6, float(seg.get("t1", 1)) - float(seg.get("t0", 0)))
        if local > 0.85 and seg.get("celebrate"):
            headline = usable_caption(seg.get("celebrate"), headline)
    paint_text(draw, (x, y0), headline, md, (40, 55, 80), anchor="lm", max_width=text_w)
    phonics = usable_caption(seg.get("phonics", ""))
    if phonics and caption_alpha > 0.55:
        paint_text(draw, (x, y0 + line), phonics, sm, (60, 80, 110), anchor="lm", max_width=text_w)
    support = usable_caption(seg.get("caption") or seg.get("fact") or "")
    tip = usable_caption(seg.get("tip") or seg.get("challenge") or "")
    y2 = y0 + line * 2
    if support and caption_alpha > 0.7:
        paint_text(draw, (x, y2), support, sm, (80, 100, 70), anchor="lm", max_width=int(b.w * 0.55))
    if tip and caption_alpha > 0.7:
        paint_text(
            draw,
            (b.x1 - pad_x, y2),
            tip,
            sm,
            (120, 70, 40),
            anchor="rm",
            max_width=int(b.w * 0.32),
        )


def draw_progress_dots(
    draw: ImageDraw.ImageDraw,
    seg: dict,
    segments: list[dict],
    width: int,
    height: int,
    color: tuple[int, int, int],
    t: float = 0.0,
    *,
    layout: KidsLayout | None = None,
) -> None:
    dots = len(segments)
    if dots <= 1:
        return
    L = _L(width, height, layout)
    active = int(seg.get("index", 0))
    y = L.dots_y
    inner = L.caption.inset(max(20, int(L.caption.w * 0.08)))
    for i in range(dots):
        dx = int(inner.x0 + i * inner.w / max(1, dots - 1))
        is_active = i == active
        pulse = 1.0 + 0.12 * np.sin(t * np.pi * 1.6) if is_active else 1.0
        r = int((7 if is_active else 4) * pulse)
        fill = color if is_active else (180, 190, 200)
        draw.ellipse((dx - r, y - r, dx + r, y + r), fill=fill)


def draw_engagement_overlay(
    draw: ImageDraw.ImageDraw,
    seg: dict,
    width: int,
    height: int,
    font: ImageFont.ImageFont,
    t: float,
    confetti_seeds: np.ndarray | None = None,
    *,
    show_celebrate: bool = True,
    layout: KidsLayout | None = None,
) -> None:
    del confetti_seeds
    if not show_celebrate:
        return
    local = (t - float(seg.get("t0", 0))) / max(1e-6, float(seg.get("t1", 1)) - float(seg.get("t0", 0)))
    if local > 0.85 and seg.get("celebrate"):
        L = _L(width, height, layout)
        paint_text(
            draw,
            L.bubble_xy,
            str(seg["celebrate"]),
            font,
            (160, 90, 30),
            anchor="mm",
            max_width=int(L.caption.w * 0.8),
        )


def draw_kids_chrome(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    layout: KidsLayout,
    *,
    title: str,
    seg: dict,
    segments: list[dict],
    fonts: dict[str, ImageFont.ImageFont],
    t: float,
    closing: str = "",
    accent: tuple[int, int, int] = (80, 120, 180),
    confetti_seeds: np.ndarray | None = None,
    caption_alpha: float = 1.0,
    celebrate: bool = False,
) -> None:
    """Title, caption or closing, and progress dots — never stacked on the letter."""
    sm = fonts.get("sm") or fonts.get("md")
    count = f"{int(seg.get('index', 0)) + 1} / {max(1, len(segments))}"
    draw_title_banner(draw, layout.width, layout.height, title, sm, layout=layout, count_label=count)
    if t > 0.92:
        draw_closing_banner(draw, layout.width, layout.height, closing or "Great job!", sm, layout=layout)
        if confetti_seeds is not None:
            draw_confetti(draw, layout.width, layout.height, t, confetti_seeds, intensity=0.35)
        return
    draw_learning_strip(
        draw, img, seg, layout.width, layout.height, fonts, layout=layout, t=t,
        caption_alpha=caption_alpha,
    )
    draw_progress_dots(draw, seg, segments, layout.width, layout.height, accent, t=t, layout=layout)
    if celebrate and confetti_seeds is not None:
        draw_confetti(draw, layout.width, layout.height, t, confetti_seeds, intensity=0.22)


def draw_phonics_badge(
    draw: ImageDraw.ImageDraw,
    seg: dict,
    xy: tuple[int, int],
    w: int,
    h: int,
    fonts: dict[str, ImageFont.ImageFont],
    *,
    alpha: float = 1.0,
) -> None:
    """Master Teacher phonics badge: clear phoneme sound vs letter name."""
    if alpha < 0.15:
        return
    phoneme = str(seg.get("phoneme") or "")
    sound_spelling = str(seg.get("sound_spelling") or "")
    rhyme = str(seg.get("rhyme_family") or "")
    if not phoneme and not sound_spelling:
        return
    x0, y0 = xy
    x1, y1 = x0 + w, y0 + h
    draw.rounded_rectangle((x0, y0, x1, y1), radius=10, fill=(255, 255, 255), outline=(70, 110, 160), width=2)
    sm = fonts.get("sm") or fonts.get("md")
    label = f"Phonics: {phoneme} (says \"{sound_spelling}\")"
    paint_text(draw, (x0 + w // 2, y0 + (h // 3 if rhyme else h // 2)), label, sm, (30, 50, 90), anchor="mm", max_width=w - 10)
    if rhyme:
        paint_text(draw, (x0 + w // 2, y0 + (2 * h) // 3), f"Family: {rhyme}", sm, (80, 100, 70), anchor="mm", max_width=w - 10)


def draw_ten_frame(
    draw: ImageDraw.ImageDraw,
    count: int,
    xy: tuple[int, int],
    w: int,
    h: int,
    *,
    dot_color: tuple[int, int, int] = (230, 70, 70),
    alpha: float = 1.0,
) -> None:
    """Subitizing 2x5 Ten-Frame: standard kindergarten & 1st grade math foundation."""
    if alpha < 0.15 or count <= 0:
        return
    x0, y0 = xy
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=10, fill=(255, 255, 255), outline=(80, 100, 130), width=3)
    cell_w = w / 5.0
    cell_h = h / 2.0
    # Grid lines
    draw.line((x0, y0 + cell_h, x0 + w, y0 + cell_h), fill=(180, 195, 215), width=2)
    for c in range(1, 5):
        cx = x0 + c * cell_w
        draw.line((cx, y0, cx, y0 + h), fill=(180, 195, 215), width=2)
    # Draw filled dots
    r = max(4, int(min(cell_w, cell_h) * 0.36))
    for i in range(min(10, count)):
        row = i // 5
        col = i % 5
        dot_x = int(x0 + (col + 0.5) * cell_w)
        dot_y = int(y0 + (row + 0.5) * cell_h)
        draw.ellipse((dot_x - r, dot_y - r, dot_x + r, dot_y + r), fill=dot_color, outline=(40, 40, 40), width=2)


def draw_shape_properties_badge(
    draw: ImageDraw.ImageDraw,
    sides: int,
    vertices: int,
    xy: tuple[int, int],
    w: int,
    h: int,
    font: ImageFont.ImageFont,
    *,
    fact: str = "",
) -> None:
    """Geometry teacher badge: sides and vertices callout."""
    x0, y0 = xy
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=12, fill=(255, 255, 250), outline=(100, 130, 80), width=3)
    corner_txt = f"{sides} Sides  •  {vertices} Corners"
    paint_text(draw, (x0 + w // 2, y0 + (h // 3 if fact else h // 2)), corner_txt, font, (40, 80, 40), anchor="mm", max_width=w - 12)
    if fact:
        paint_text(draw, (x0 + w // 2, y0 + (2 * h) // 3), fact, font, (70, 90, 110), anchor="mm", max_width=w - 12)


def draw_step_progress_bar(
    draw: ImageDraw.ImageDraw,
    step_idx: int,
    total_steps: int,
    xy: tuple[int, int],
    w: int,
    h: int,
    font: ImageFont.ImageFont,
    *,
    step_label: str = "",
) -> None:
    """Drawing scaffolding progress: Step X of Y with label."""
    if total_steps <= 0:
        return
    x0, y0 = xy
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=8, fill=(240, 245, 250), outline=(120, 140, 170), width=2)
    frac = min(1.0, (step_idx + 1) / total_steps)
    fill_w = max(4, int(w * frac))
    draw.rounded_rectangle((x0, y0, x0 + fill_w, y0 + h), radius=8, fill=(100, 180, 120))
    txt = f"Step {step_idx + 1}/{total_steps}" + (f": {step_label}" if step_label else "")
    paint_text(draw, (x0 + w // 2, y0 + h // 2), txt, font, (30, 45, 60), anchor="mm", max_width=w - 8)
