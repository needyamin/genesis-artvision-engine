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
    """Split text into lines that fit, preserving explicit paragraph breaks."""
    text = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return []
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            pieces = _split_long_word(draw, word, font, max_width)
            for piece in pieces:
                candidate = f"{current} {piece}".strip()
                if current and _text_width(draw, candidate, font) > max_width:
                    lines.append(current)
                    current = piece
                else:
                    current = candidate
        if current:
            lines.append(current)
    return lines


def paint_multiline_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    fill: tuple[int, ...] | str,
    *,
    max_width: int,
    max_lines: int | None = None,
    max_height: int | None = None,
    anchor: str = "lt",
    line_spacing: int = 6,
    ellipsis: str = "…",
    stroke_width: int = 0,
    stroke_fill: tuple[int, ...] | str | None = None,
    shadow_offset: tuple[int, int] | None = None,
    shadow_fill: tuple[int, ...] | str = (0, 0, 0, 128),
    fit_font_size: bool = False,
    min_font_size: int = 12,
) -> dict[str, object]:
    """Wrap and paint a production-ready text block.

    The returned mapping includes the final ``lines``, ``font``, ``bbox`` and
    an ``overflow`` flag so callers can choose a shorter alternate caption.
    """
    max_width = max(1, int(max_width))
    max_lines = None if max_lines is None else max(1, int(max_lines))
    max_height = None if max_height is None else max(1, int(max_height))
    spacing = max(0, int(line_spacing))
    stroke = max(0, int(stroke_width))
    content_width = max(1, max_width - stroke * 2)
    chosen_font = font
    lines: list[str] = []
    overflow = False

    while True:
        all_lines = wrap_text_lines(draw, text, chosen_font, content_width)
        lines, truncated = _limit_lines(
            draw,
            all_lines,
            chosen_font,
            max_width=content_width,
            max_lines=max_lines,
            max_height=max_height,
            spacing=spacing,
            ellipsis=ellipsis,
            stroke_width=stroke,
        )
        fits_height = max_height is None or _lines_height(
            draw, lines, chosen_font, spacing, stroke
        ) <= max_height
        if (not truncated and fits_height) or not fit_font_size:
            overflow = truncated or not fits_height
            break
        smaller = _font_variant(chosen_font, max(min_font_size, _font_size(chosen_font) - 1))
        if smaller is chosen_font or _font_size(chosen_font) <= min_font_size:
            overflow = True
            break
        chosen_font = smaller

    rendered = "\n".join(lines)
    bbox = _multiline_bbox(
        draw, xy, rendered, chosen_font, anchor, spacing, stroke
    )
    if rendered:
        if shadow_offset is not None and (shadow_offset[0] or shadow_offset[1]):
            shadow_xy = (xy[0] + shadow_offset[0], xy[1] + shadow_offset[1])
            _draw_multiline(
                draw, shadow_xy, rendered, chosen_font, shadow_fill, anchor, spacing,
                stroke, stroke_fill,
            )
        _draw_multiline(
            draw, xy, rendered, chosen_font, fill, anchor, spacing,
            stroke, stroke_fill,
        )
    return {
        "text": rendered,
        "lines": lines,
        "line_count": len(lines),
        "font": chosen_font,
        "font_size": _font_size(chosen_font),
        "bbox": bbox,
        "overflow": overflow,
    }


def compose_multiline_text(*args: object, **kwargs: object) -> dict[str, object]:
    """Compatibility-friendly name for :func:`paint_multiline_text`."""
    return paint_multiline_text(*args, **kwargs)  # type: ignore[arg-type]


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return int(bbox[2] - bbox[0])


def _fit_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    suffix: str = "…",
) -> str:
    if _text_width(draw, text, font) <= max_width:
        return text
    for n in range(len(text), 0, -1):
        candidate = text[:n].rstrip() + suffix
        if _text_width(draw, candidate, font) <= max_width:
            return candidate
    return suffix if suffix and _text_width(draw, suffix, font) <= max_width else text[:1]


def _split_long_word(
    draw: ImageDraw.ImageDraw,
    word: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    if _text_width(draw, word, font) <= max_width:
        return [word]
    pieces: list[str] = []
    remaining = word
    while remaining:
        low, high = 1, len(remaining)
        while low < high:
            mid = (low + high + 1) // 2
            if _text_width(draw, remaining[:mid], font) <= max_width:
                low = mid
            else:
                high = mid - 1
        take = max(1, low)
        pieces.append(remaining[:take])
        remaining = remaining[take:]
    return pieces


def _limit_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.ImageFont,
    *,
    max_width: int,
    max_lines: int | None,
    max_height: int | None,
    spacing: int,
    ellipsis: str,
    stroke_width: int,
) -> tuple[list[str], bool]:
    limit = len(lines) if max_lines is None else min(len(lines), max_lines)
    if max_height is not None:
        while limit > 0 and _lines_height(draw, lines[:limit], font, spacing, stroke_width) > max_height:
            limit -= 1
    truncated = limit < len(lines)
    visible = list(lines[:limit])
    if truncated and visible:
        base = visible[-1].rstrip()
        visible[-1] = _ellipsize(draw, base, font, max_width, ellipsis)
    return visible, truncated


def _ellipsize(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    suffix: str,
) -> str:
    if _text_width(draw, text + suffix, font) <= max_width:
        return text + suffix
    for n in range(len(text), -1, -1):
        candidate = text[:n].rstrip() + suffix
        if candidate and _text_width(draw, candidate, font) <= max_width:
            return candidate
    return ""


def _lines_height(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.ImageFont,
    spacing: int,
    stroke_width: int,
) -> int:
    if not lines:
        return 0
    bbox = draw.multiline_textbbox(
        (0, 0), "\n".join(lines), font=font, spacing=spacing, stroke_width=stroke_width
    )
    return int(bbox[3] - bbox[1])


def _font_size(font: ImageFont.ImageFont) -> int:
    return max(1, int(getattr(font, "size", 12)))


def _font_variant(font: ImageFont.ImageFont, size: int) -> ImageFont.ImageFont:
    variant = getattr(font, "font_variant", None)
    if callable(variant):
        try:
            return variant(size=max(1, int(size)))
        except (OSError, TypeError, ValueError):
            pass
    return font


def _multiline_bbox(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    anchor: str,
    spacing: int,
    stroke_width: int,
) -> tuple[int, int, int, int]:
    if not text:
        x, y = int(round(xy[0])), int(round(xy[1]))
        return (x, y, x, y)
    try:
        return tuple(
            int(v) for v in draw.multiline_textbbox(
                xy, text, font=font, anchor=anchor, spacing=spacing, stroke_width=stroke_width
            )
        )
    except (TypeError, ValueError):
        origin = _anchor_origin(draw, xy, text, font, anchor, spacing, stroke_width)
        return tuple(
            int(v) for v in draw.multiline_textbbox(
                origin, text, font=font, spacing=spacing, stroke_width=stroke_width
            )
        )


def _draw_multiline(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, ...] | str,
    anchor: str,
    spacing: int,
    stroke_width: int,
    stroke_fill: tuple[int, ...] | str | None,
) -> None:
    kwargs = {
        "font": font,
        "fill": fill,
        "spacing": spacing,
        "stroke_width": stroke_width,
        "stroke_fill": stroke_fill,
    }
    try:
        draw.multiline_text(xy, text, anchor=anchor, **kwargs)
    except (TypeError, ValueError):
        origin = _anchor_origin(draw, xy, text, font, anchor, spacing, stroke_width)
        draw.multiline_text(origin, text, **kwargs)


def _anchor_origin(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    anchor: str,
    spacing: int,
    stroke_width: int,
) -> tuple[float, float]:
    bbox = draw.multiline_textbbox(
        (0, 0), text, font=font, spacing=spacing, stroke_width=stroke_width
    )
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = float(xy[0]) - bbox[0], float(xy[1]) - bbox[1]
    code = (anchor or "lt").lower()
    horizontal = code[0] if code else "l"
    vertical = code[1] if len(code) > 1 else "t"
    if horizontal == "m":
        x -= width / 2.0
    elif horizontal == "r":
        x -= width
    if vertical == "m":
        y -= height / 2.0
    elif vertical in {"b", "d"}:
        y -= height
    return x, y


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
