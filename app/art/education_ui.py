"""Shared UI helpers for the kids storybook engine."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from app.art.fonts import load_font, paint_text
from app.art.kids_layout import KidsLayout, kids_layout
from app.art.word_images import paste_segment_image

__all__ = [
    "draw_picture_card",
    "draw_title_banner",
    "kids_layout",
    "load_font",
    "paint_text",
    "paste_picture",
    "segment_at",
]


def segment_at(segments: list[dict], t: float) -> dict:
    for seg in segments:
        if float(seg["t0"]) <= t < float(seg["t1"]):
            return seg
    return segments[-1] if segments else {
        "headline": "Story time",
        "caption": "",
        "voice_line": "Let's read a story.",
        "word": "STORY",
        "t0": 0.0,
        "t1": 1.0,
        "index": 0,
    }


def _L(width: int, height: int, layout: KidsLayout | None) -> KidsLayout:
    return layout if layout is not None else kids_layout(width, height)


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
