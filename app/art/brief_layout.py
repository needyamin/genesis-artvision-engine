"""Responsive safe-zone layout and stateless segment compositing."""

from __future__ import annotations

from dataclasses import dataclass
import math

from PIL import Image, ImageDraw, ImageFont

from app.art import fonts as font_api


@dataclass(frozen=True)
class BriefBox:
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def w(self) -> int:
        return max(1, self.x1 - self.x0)

    @property
    def h(self) -> int:
        return max(1, self.y1 - self.y0)

    @property
    def cx(self) -> int:
        return (self.x0 + self.x1) // 2

    @property
    def cy(self) -> int:
        return (self.y0 + self.y1) // 2

    @property
    def xy(self) -> tuple[int, int, int, int]:
        return self.x0, self.y0, self.x1, self.y1

    def inset(self, amount: int) -> "BriefBox":
        p = max(0, min(int(amount), min(self.w, self.h) // 3))
        return BriefBox(self.x0 + p, self.y0 + p, self.x1 - p, self.y1 - p)


@dataclass(frozen=True)
class BriefLayout:
    width: int
    height: int
    orientation: str
    safe: BriefBox
    ticker: BriefBox
    header: BriefBox
    visual: BriefBox
    card: BriefBox
    footer: BriefBox
    gap: int
    pad: int
    title_font: int
    headline_font: int
    body_font: int
    small_font: int


BRIEF_LAYOUT_VARIANTS = {
    "how_it_works": ("split_right", "split_left", "stacked", "diagram_focus"),
    "trend_brief": ("broadcast", "card_emphasis", "full_bleed"),
}


def brief_layout_variants(engine: str) -> tuple[str, ...]:
    """Return the supported variants for a brief engine."""
    key = str(engine or "").strip().lower().replace("-", "_")
    return BRIEF_LAYOUT_VARIANTS.get(key, ())


def _split_horizontal(
    box: BriefBox,
    gap: int,
    first_fraction: float,
) -> tuple[BriefBox, BriefBox]:
    """Split ``box`` left-to-right with a real, bounded gutter."""
    gutter = min(max(0, int(gap)), max(0, box.w - 2))
    usable = max(2, box.w - gutter)
    first_w = max(1, min(usable - 1, int(usable * first_fraction)))
    cut = box.x0 + first_w
    return (
        BriefBox(box.x0, box.y0, cut, box.y1),
        BriefBox(cut + gutter, box.y0, box.x1, box.y1),
    )


def _split_vertical(
    box: BriefBox,
    gap: int,
    first_fraction: float,
) -> tuple[BriefBox, BriefBox]:
    """Split ``box`` top-to-bottom with a real, bounded gutter."""
    gutter = min(max(0, int(gap)), max(0, box.h - 2))
    usable = max(2, box.h - gutter)
    first_h = max(1, min(usable - 1, int(usable * first_fraction)))
    cut = box.y0 + first_h
    return (
        BriefBox(box.x0, box.y0, box.x1, cut),
        BriefBox(box.x0, cut + gutter, box.x1, box.y1),
    )


def brief_layout(
    width: int,
    height: int,
    *,
    ticker: bool = False,
    caption_band: bool = False,
    engine: str | None = None,
    variant: str | None = None,
) -> BriefLayout:
    """Build non-overlapping broadcast-safe regions for every aspect ratio.

    Omitting ``engine`` and ``variant`` preserves the original broadcast
    layout exactly. Unknown or cross-engine variants safely fall back to the
    corresponding engine default.
    """
    engine_key = str(engine or "").strip().lower().replace("-", "_")
    variant_key = str(variant or "").strip().lower().replace("-", "_")
    if not engine_key and variant_key:
        for candidate, names in BRIEF_LAYOUT_VARIANTS.items():
            if variant_key in names:
                engine_key = candidate
                break
    names = BRIEF_LAYOUT_VARIANTS.get(engine_key, ())
    if variant_key not in names:
        variant_key = names[0] if names else ""

    w, h = max(96, int(width)), max(96, int(height))
    short = min(w, h)
    margin = max(3, int(short * 0.055))
    gap = max(2, int(short * 0.022))
    pad = max(4, int(short * 0.030))
    safe = BriefBox(margin, margin, w - margin, h - margin)
    ticker_h = max(10, int(h * 0.055)) if ticker else 0
    ticker_box = BriefBox(0, 0, w, ticker_h)
    top = max(safe.y0, ticker_h + gap)
    header_h = max(14, min(int(h * 0.16), int(short * 0.22)))
    footer_h = max(5, int(short * 0.05), int(h * 0.18) if caption_band else 0)
    header = BriefBox(safe.x0, top, safe.x1, min(safe.y1, top + header_h))
    content_top = min(safe.y1 - 2, header.y1 + gap)
    content_bottom = max(content_top + 1, safe.y1 - footer_h - gap)
    content = BriefBox(safe.x0, content_top, safe.x1, content_bottom)
    ratio = w / max(1, h)
    if ratio >= 1.25:
        orientation = "landscape"
        split = content.x0 + int(content.w * 0.54)
        visual = BriefBox(content.x0, content.y0, split - gap // 2, content.y1)
        card = BriefBox(split + gap // 2, content.y0, content.x1, content.y1)
    elif ratio <= 0.86:
        orientation = "portrait"
        split = content.y0 + int(content.h * 0.46)
        visual = BriefBox(content.x0, content.y0, content.x1, split - gap // 2)
        card = BriefBox(content.x0, split + gap // 2, content.x1, content.y1)
    else:
        orientation = "square"
        split = content.y0 + int(content.h * 0.43)
        visual = BriefBox(content.x0, content.y0, content.x1, split - gap // 2)
        card = BriefBox(content.x0, split + gap // 2, content.x1, content.y1)

    # The defaults are deliberately left untouched above: explicit
    # ``split_right``/``broadcast`` and legacy calls are pixel-identical.
    if variant_key == "split_left":
        if orientation == "landscape":
            card, visual = _split_horizontal(content, gap, 0.46)
        else:
            card, visual = _split_vertical(content, gap, 0.46)
    elif variant_key == "stacked":
        visual, card = _split_vertical(content, gap, 0.54)
    elif variant_key == "diagram_focus":
        if orientation == "landscape":
            visual, card = _split_horizontal(content, gap, 0.70)
        else:
            visual, card = _split_vertical(content, gap, 0.64)
    elif variant_key == "card_emphasis":
        if orientation == "landscape":
            visual, card = _split_horizontal(content, gap, 0.36)
        else:
            visual, card = _split_vertical(content, gap, 0.34)
    elif variant_key == "full_bleed":
        if orientation == "landscape":
            visual, card = _split_horizontal(content, gap, 0.78)
        else:
            visual, card = _split_vertical(content, gap, 0.76)

    footer = BriefBox(safe.x0, content.y1 + gap, safe.x1, safe.y1)
    return BriefLayout(
        w,
        h,
        orientation,
        safe,
        ticker_box,
        header,
        visual,
        card,
        footer,
        gap,
        pad,
        max(18, int(short * 0.056)),
        max(16, int(short * 0.044)),
        max(13, int(short * 0.030)),
        max(11, int(short * 0.022)),
    )


def paint_text_block(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, ...],
    *,
    max_width: int,
    max_height: int,
    spacing: int = 4,
    anchor: str = "la",
) -> int:
    """Paint wrapped copy, preferring the shared fonts implementation when present."""
    shared = getattr(font_api, "paint_multiline_text", None)
    if callable(shared):
        try:
            result = shared(
                draw,
                xy,
                text,
                font,
                fill,
                max_width=max_width,
                max_height=max_height,
                line_spacing=spacing,
                anchor=anchor,
                fit_font_size=True,
                min_font_size=8,
                shadow_offset=(1, 2) if sum(fill[:3]) > 500 else None,
                shadow_fill=(0, 0, 0, 150),
            )
            bbox = result.get("bbox") if isinstance(result, dict) else None
            if isinstance(bbox, tuple) and len(bbox) == 4:
                return max(0, int(bbox[3] - bbox[1]))
            return 0
        except TypeError:
            pass
    lines = font_api.wrap_text_lines(draw, " ".join(str(text or "").split()), font, max_width)
    if not lines:
        return 0
    probe = draw.textbbox((0, 0), "Ag", font=font)
    line_h = max(1, probe[3] - probe[1] + spacing)
    count = max(1, max_height // line_h)
    lines = lines[:count]
    if count < len(font_api.wrap_text_lines(draw, text, font, max_width)):
        last = lines[-1].rstrip(" .,;:") + "…"
        lines[-1] = last
    x, y = xy
    for line in lines:
        font_api.paint_text(draw, (x, y), line, font, fill, anchor=anchor, max_width=max_width)
        y += line_h
    return len(lines) * line_h


def composite_segment_layers(
    outgoing: Image.Image | None,
    current: Image.Image,
    *,
    enter: float,
    leave: float,
    kind: str,
) -> Image.Image:
    """Statelessly composite complete outgoing/current layers across a cut."""
    if outgoing is None:
        return current
    p = max(0.0, min(1.0, float(enter)))
    outgoing_weight = max(0.0, min(1.0, float(leave)))
    if p >= 0.999:
        return current
    old = outgoing.convert("RGBA")
    new = current.convert("RGBA")
    w, h = current.size
    transition = str(kind or "dissolve").lower().replace("-", "_")
    if transition == "push":
        canvas = Image.new("RGBA", (w, h))
        direction = -1
        old_x = int(direction * p * w)
        new_x = int((1.0 - p) * w)
        canvas.alpha_composite(old, (old_x, 0))
        canvas.alpha_composite(new, (new_x, 0))
        return canvas.convert(current.mode)
    if transition in {"page_turn", "pageturn"}:
        canvas = old.copy()
        reveal_x = int((1.0 - p) * w)
        if reveal_x < w:
            canvas.alpha_composite(new.crop((reveal_x, 0, w, h)), (reveal_x, 0))
        fold_w = max(2, int(w * 0.035))
        fold = Image.new("RGBA", (fold_w, h), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fold, "RGBA")
        for x in range(fold_w):
            shade = int(110 * (1.0 - abs(x / max(1, fold_w - 1) - 0.5) * 2.0))
            fd.line((x, 0, x, h), fill=(65, 45, 30, shade))
        canvas.alpha_composite(fold, (max(0, reveal_x - fold_w // 2), 0))
        return canvas.convert(current.mode)
    mixed = Image.blend(old, new, p)
    if transition == "flash":
        flash = math.sin(math.pi * p)
        white = Image.new("RGBA", (w, h), (255, 250, 235, 255))
        mixed = Image.blend(mixed, white, min(0.70, flash * 0.70))
    elif outgoing_weight < 0.999:
        # The leave envelope independently softens the old layer.
        mixed = Image.blend(new, mixed, outgoing_weight)
    return mixed.convert(current.mode)
