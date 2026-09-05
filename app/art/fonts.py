"""Shared TrueType loading and text painting for on-screen captions."""

from __future__ import annotations

from pathlib import Path

from PIL import ImageDraw, ImageFont

_MODERN_FONT_CANDIDATES = (
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/tahomabd.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
)

_COMIC_FONT_CANDIDATES = (
    "C:/Windows/Fonts/comicbd.ttf",
    "C:/Windows/Fonts/comic.ttf",
    "/System/Library/Fonts/Supplemental/Comic Sans MS.ttf",
)

_FONT_CANDIDATES = _MODERN_FONT_CANDIDATES + _COMIC_FONT_CANDIDATES


def usable_caption(value: object, fallback: str = "") -> str:
    """Drop empty or punctuation-only AI captions such as a lone '.'."""
    text = " ".join(str(value or "").split())
    if not text or not any(ch.isalnum() for ch in text):
        return fallback
    return text


def load_font(size: int, family: str = "modern") -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    """Load a real TTF so captions are readable. Modern clean sans-serif by default."""
    size = max(12, int(size))
    candidates = _COMIC_FONT_CANDIDATES + _MODERN_FONT_CANDIDATES if family == "comic" else _MODERN_FONT_CANDIDATES + _COMIC_FONT_CANDIDATES
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def wrap_text_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """Split text into lines that fit within max_width pixels."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    curr = words[0]
    for w in words[1:]:
        test = curr + " " + w
        if _text_width(draw, test, font) <= max_width:
            curr = test
        else:
            lines.append(curr)
            curr = w
    if curr:
        lines.append(curr)
    return lines


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return int(bbox[2] - bbox[0])


def _fit_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    if _text_width(draw, text, font) <= max_width:
        return text
    for n in range(len(text), 0, -1):
        candidate = text[:n].rstrip() + "…"
        if _text_width(draw, candidate, font) <= max_width:
            return candidate
    return text[:1]


def paint_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    fill: tuple[int, ...],
    *,
    anchor: str = "lt",
    max_width: int | None = None,
) -> None:
    """Draw text even when the font is a bitmap (anchors only work on TrueType)."""
    text = " ".join(str(text or "").split())
    if not text:
        return
    if max_width is not None and max_width > 24:
        text = _fit_width(draw, text, font, int(max_width))
    try:
        draw.text(xy, text, font=font, fill=fill, anchor=anchor)
        return
    except (TypeError, ValueError):
        pass
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x, y = float(xy[0]), float(xy[1])
    code = (anchor or "lt")[:2]
    ax = code[0]
    ay = code[1] if len(code) > 1 else "t"
    if ax == "m":
        x -= tw / 2.0 + bbox[0]
    elif ax == "r":
        x -= tw + bbox[0]
    else:
        x -= bbox[0]
    if ay == "m":
        y -= th / 2.0 + bbox[1]
    elif ay == "b":
        y -= th + bbox[1]
    else:
        y -= bbox[1]
    draw.text((int(round(x)), int(round(y))), text, font=font, fill=fill)
