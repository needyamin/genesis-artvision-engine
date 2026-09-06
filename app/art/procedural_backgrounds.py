"""Seeded, reusable backgrounds for the three editorial art engines.

All public painters return a ``PIL.Image.Image`` in ``RGB`` mode.  Their
output is deterministic for identical arguments and they accept either an
``app.art.palette.Palette`` instance or a sequence of RGB colors (0..1 or
0..255).  Trend painters additionally accept normalized time ``t`` and a
normalized ``beat`` pulse.

Use :func:`paint_background` for dispatch, or call a named painter directly::

    image = paint_background("kids_storybook", 1280, 720, 42, palette,
                             variant="cozy_corner")
    image = grid_pulse(1280, 720, 42, palette, t=0.25, beat=0.8)

The default variants intentionally track the engines' original looks:
``desk_stack``, ``whiteboard``, and ``neon_ridge``.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RGB = tuple[int, int, int]
PaletteLike = Any

VARIANTS: dict[str, tuple[str, ...]] = {
    "kids_storybook": (
        "desk_stack",
        "cozy_corner",
        "window_day",
        "craft_mat",
        "night_lamp",
        "open_spread",
    ),
    "how_it_works": (
        "whiteboard",
        "chalkboard",
        "poster_wall",
        "worksheet",
        "lab_bench",
        "projection",
    ),
    "trend_brief": (
        "neon_ridge",
        "grid_pulse",
        "aurora_bands",
        "static_fizz",
        "mesh_glow",
        "radar_sweep",
    ),
}
DEFAULT_VARIANTS = {
    "kids_storybook": "desk_stack",
    "how_it_works": "whiteboard",
    "trend_brief": "neon_ridge",
}


@dataclass(frozen=True)
class ChromeTheme:
    """Suggested colors for text/card chrome over a background."""

    text: RGB
    muted_text: RGB
    card: tuple[int, int, int, int]
    accent: RGB
    border: tuple[int, int, int, int]
    dark: bool


_DEFAULT_PALETTES: dict[str, tuple[RGB, ...]] = {
    "kids_storybook": ((242, 228, 204), (180, 140, 100), (116, 82, 58), (246, 177, 91)),
    "how_it_works": ((236, 242, 248), (30, 110, 170), (40, 55, 70), (210, 220, 230)),
    "trend_brief": ((8, 10, 18), (0, 230, 180), (255, 80, 120), (70, 90, 255)),
}


def _size(width: int, height: int) -> tuple[int, int]:
    return max(1, int(width)), max(1, int(height))


def _rgb(value: Sequence[float | int]) -> RGB:
    vals = list(value)[:3]
    if len(vals) < 3:
        vals.extend([vals[-1] if vals else 0] * (3 - len(vals)))
    scale = 255.0 if max(abs(float(v)) for v in vals) <= 1.0 else 1.0
    return tuple(int(np.clip(round(float(v) * scale), 0, 255)) for v in vals)  # type: ignore[return-value]


def _colors(palette: PaletteLike, engine: str) -> tuple[RGB, ...]:
    raw = getattr(palette, "colors", palette)
    if raw is None:
        return _DEFAULT_PALETTES[engine]
    try:
        out = tuple(_rgb(c) for c in raw)
    except (TypeError, ValueError):
        return _DEFAULT_PALETTES[engine]
    return out or _DEFAULT_PALETTES[engine]


def _pick(colors: tuple[RGB, ...], index: int, fallback: RGB) -> RGB:
    return colors[index % len(colors)] if colors else fallback


def _mix(a: RGB, b: RGB, amount: float) -> RGB:
    q = float(np.clip(amount, 0.0, 1.0))
    return tuple(int(round(x * (1.0 - q) + y * q)) for x, y in zip(a, b))  # type: ignore[return-value]


def _gradient(width: int, height: int, top: RGB, bottom: RGB, horizontal: RGB | None = None) -> Image.Image:
    w, h = _size(width, height)
    yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    arr = np.asarray(top, dtype=np.float32) * (1.0 - yy) + np.asarray(bottom, dtype=np.float32) * yy
    arr = np.broadcast_to(arr, (h, w, 3)).copy()
    if horizontal is not None:
        xx = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :, None]
        arr = arr * (1.0 - 0.18 * xx) + np.asarray(horizontal, dtype=np.float32) * (0.18 * xx)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def _grain(image: Image.Image, seed: int, strength: float = 4.0) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=np.int16)
    rng = np.random.default_rng(int(seed))
    noise = rng.integers(-max(1, int(strength)), max(2, int(strength) + 1), (arr.shape[0], arr.shape[1], 1))
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8), "RGB")


def _line_width(width: int, height: int, fraction: float = 0.003) -> int:
    return max(1, int(round(min(width, height) * fraction)))


def _paper_sheet(image: Image.Image, box: tuple[int, int, int, int], fill: RGB, outline: RGB) -> None:
    x0, y0, x1, y1 = box
    if x1 < x0 or y1 < y0:
        return
    draw = ImageDraw.Draw(image, "RGBA")
    radius = max(1, min(18, (x1 - x0 + y1 - y0) // 24))
    draw.rounded_rectangle(box, radius=radius, fill=(*fill, 255), outline=(*outline, 210), width=1)


def variants_for(engine: str) -> tuple[str, ...]:
    """Return the ordered variant names supported by ``engine``."""

    try:
        return VARIANTS[str(engine)]
    except KeyError as exc:
        raise ValueError(f"Unknown background engine: {engine!r}") from exc


def get_chrome_theme(engine: str, variant: str | None = None, palette: PaletteLike = None) -> ChromeTheme:
    """Return readable text/card color suggestions for a variant."""

    engine = str(engine)
    variant = variant or DEFAULT_VARIANTS.get(engine)
    if variant not in VARIANTS.get(engine, ()):
        raise ValueError(f"Unknown {engine!r} background variant: {variant!r}")
    colors = _colors(palette, engine)
    accent = _pick(colors, 1, _DEFAULT_PALETTES[engine][1])
    dark = engine == "trend_brief" or variant in {"chalkboard", "projection", "night_lamp"}
    if dark:
        return ChromeTheme((248, 250, 255), (196, 207, 220), (9, 14, 26, 218), accent, (*accent, 155), True)
    ink = (48, 48, 45) if engine == "kids_storybook" else (40, 55, 70)
    return ChromeTheme(ink, _mix(ink, (255, 255, 255), 0.28), (255, 252, 245, 232), accent, (*accent, 125), False)


# Kids storybook -----------------------------------------------------------

def desk_stack(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Classic warm desk with a grainy stack of offset paper."""

    w, h = _size(width, height)
    colors = _colors(palette, "kids_storybook")
    cream = _mix((242, 228, 204), _pick(colors, 0, (242, 228, 204)), 0.28)
    desk = _gradient(w, h, _mix((116, 82, 58), _pick(colors, 2, (116, 82, 58)), 0.18), (83, 56, 41))
    desk = _grain(desk, seed + 1, 3)
    draw = ImageDraw.Draw(desk, "RGBA")
    margin = max(1, int(min(w, h) * 0.04))
    x1, y1 = max(margin, w - margin - 1), max(margin, h - margin - 1)
    for spread in range(4, 0, -1):
        off = spread * max(1, margin // 10)
        shadow = (margin + off, margin + off, min(w - 1, x1 + off), min(h - 1, y1 + off))
        if shadow[0] <= shadow[2] and shadow[1] <= shadow[3]:
            draw.rounded_rectangle(shadow, radius=max(1, margin // 3),
                                   fill=(35, 22, 15, 16 + spread * 9))
    _paper_sheet(desk, (margin, margin, x1, y1), cream, (180, 140, 100))
    paper = desk.crop((margin, margin, x1 + 1, y1 + 1))
    paper = _grain(paper, seed + 3, 4)
    desk.paste(paper, (margin, margin))
    draw = ImageDraw.Draw(desk, "RGBA")
    draw.rounded_rectangle((margin, margin, x1, y1), radius=max(1, margin // 3),
                           outline=(180, 140, 100, 230), width=_line_width(w, h))
    return desk.convert("RGB")


def cozy_corner(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Soft reading nook with rug, cushion, and a centered page."""

    w, h = _size(width, height)
    c = _colors(palette, "kids_storybook")
    img = _gradient(w, h, _mix((218, 185, 146), _pick(c, 0, (218, 185, 146)), 0.22), (118, 78, 58))
    draw = ImageDraw.Draw(img, "RGBA")
    floor_y = int(h * 0.63)
    draw.rectangle((0, floor_y, w, h), fill=(93, 61, 45, 115))
    draw.ellipse((-int(w * .18), int(h * .58), int(w * .72), int(h * 1.15)), fill=(*_pick(c, 3, (210, 115, 85)), 105))
    draw.rounded_rectangle((int(w * .04), int(h * .17), int(w * .28), int(h * .67)),
                           radius=max(1, int(min(w, h) * .04)), fill=(143, 75, 70, 150))
    m = max(1, int(min(w, h) * .075))
    _paper_sheet(img, (m, m, max(m, w - m - 1), max(m, h - m - 1)), (250, 239, 216), (178, 133, 91))
    return _grain(img, seed + 11, 2)


def window_day(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Daylit page beside a simple blue window."""

    w, h = _size(width, height)
    c = _colors(palette, "kids_storybook")
    img = _gradient(w, h, (224, 214, 190), (154, 113, 78), _pick(c, 0, (242, 228, 204)))
    draw = ImageDraw.Draw(img, "RGBA")
    wx0, wy0, wx1, wy1 = int(w * .64), int(h * .04), max(int(w * .64), int(w * .94)), max(int(h * .04), int(h * .42))
    draw.rectangle((wx0, wy0, wx1, wy1), fill=(145, 205, 235, 255), outline=(246, 246, 236, 255), width=_line_width(w, h, .009))
    draw.line((wx0, (wy0 + wy1) // 2, wx1, (wy0 + wy1) // 2), fill=(250, 250, 240, 220), width=_line_width(w, h, .006))
    draw.line(((wx0 + wx1) // 2, wy0, (wx0 + wx1) // 2, wy1), fill=(250, 250, 240, 220), width=_line_width(w, h, .006))
    draw.polygon([(wx0, wy1), (w, wy1), (w, h), (int(w * .28), h)], fill=(255, 241, 190, 48))
    m = max(1, int(min(w, h) * .055))
    _paper_sheet(img, (m, m, max(m, w - m - 1), max(m, h - m - 1)), (250, 241, 220), (185, 145, 103))
    return _grain(img, seed + 23, 2)


def craft_mat(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Colorful cutting mat with seeded paper scraps and supplies."""

    w, h = _size(width, height)
    c = _colors(palette, "kids_storybook")
    img = Image.new("RGB", (w, h), _mix((67, 151, 139), _pick(c, 1, (67, 151, 139)), .18))
    draw = ImageDraw.Draw(img, "RGBA")
    step = max(4, int(min(w, h) * .04))
    for x in range(0, w, step):
        draw.line((x, 0, x, h), fill=(255, 255, 245, 28))
    for y in range(0, h, step):
        draw.line((0, y, w, y), fill=(255, 255, 245, 28))
    rng = np.random.default_rng(seed + 31)
    for i in range(10):
        x, y = int(rng.random() * w), int(rng.random() * h)
        r = max(1, int(min(w, h) * rng.uniform(.012, .035)))
        col = _pick(c, i + 1, (240, 150, 80))
        draw.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=(*col, 145))
    m = max(1, int(min(w, h) * .07))
    _paper_sheet(img, (m, m, max(m, w - m - 1), max(m, h - m - 1)), (252, 245, 225), (160, 128, 92))
    return _grain(img, seed + 32, 2)


def night_lamp(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Deep-blue bedtime desk with a warm lamp pool."""

    w, h = _size(width, height)
    img = _gradient(w, h, (18, 24, 48), (46, 31, 35))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, "RGBA")
    cx, cy = int(w * .78), int(h * .15)
    for i in range(7, 0, -1):
        rx, ry = int(w * .08 * i), int(h * .09 * i)
        gd.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(255, 194, 91, max(3, 30 - i * 3)))
    img = Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(max(1, int(min(w, h) * .02)))))
    draw = ImageDraw.Draw(img, "RGBA")
    draw.polygon([(cx - int(w*.06), cy), (cx + int(w*.06), cy), (cx + int(w*.035), int(h*.29)), (cx - int(w*.035), int(h*.29))], fill=(245, 178, 76, 210))
    m = max(1, int(min(w, h) * .06))
    _paper_sheet(img, (m, m, max(m, w - m - 1), max(m, h - m - 1)), (244, 229, 198), (154, 111, 74))
    return _grain(img.convert("RGB"), seed + 41, 2)


def open_spread(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """An open two-page book on the classic warm desk."""

    w, h = _size(width, height)
    c = _colors(palette, "kids_storybook")
    img = _gradient(w, h, _mix((116, 82, 58), _pick(c, 2, (116, 82, 58)), .2), (76, 50, 37))
    draw = ImageDraw.Draw(img, "RGBA")
    m = max(1, int(min(w, h) * .055))
    mid = w // 2
    draw.rounded_rectangle((m, m, max(m, w-m-1), max(m, h-m-1)), radius=max(1, m//3), fill=(35, 22, 15, 70))
    _paper_sheet(img, (m, m, max(m, mid), max(m, h-m-1)), (247, 235, 211), (178, 136, 96))
    _paper_sheet(img, (mid, m, max(mid, w-m-1), max(m, h-m-1)), (250, 239, 217), (178, 136, 96))
    draw.line((mid, m, mid, max(m, h-m-1)), fill=(105, 75, 54, 105), width=max(1, m//5))
    return _grain(img, seed + 53, 3)


# How it works -------------------------------------------------------------

def _board_base(width: int, height: int, top: RGB, bottom: RGB, grid: tuple[int, int, int, int]) -> Image.Image:
    w, h = _size(width, height)
    img = _gradient(w, h, top, bottom)
    draw = ImageDraw.Draw(img, "RGBA")
    step = max(4, int(min(w, h) * .045))
    for x in range(0, w, step):
        draw.line((x, 0, x, h), fill=grid)
    for y in range(0, h, step):
        draw.line((0, y, w, y), fill=grid)
    rail = max(1, int(min(w, h) * .012))
    draw.rectangle((0, max(0, h - rail * 2), w, h), fill=(25, 35, 42, 65))
    draw.line((0, max(0, h - rail * 2), w, max(0, h - rail * 2)), fill=(255, 255, 255, 45), width=1)
    return img


def whiteboard(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Classic cool whiteboard and subtle accent grid."""

    c = _colors(palette, "how_it_works")
    accent = _pick(c, 1, (30, 110, 170))
    return _grain(_board_base(width, height, (236, 242, 248), (210, 220, 230), (*accent, 15)), seed + 61, 1)


def chalkboard(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Green chalkboard with seeded chalk dust."""

    img = _board_base(width, height, (46, 83, 57), (34, 65, 45), (255, 255, 255, 18))
    return _grain(img, seed + 67, 5)


def poster_wall(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Painted classroom wall with offset poster sheets."""

    w, h = _size(width, height)
    c = _colors(palette, "how_it_works")
    img = _grain(_gradient(w, h, (220, 211, 191), (190, 177, 155)), seed + 71, 3)
    if w < 8 or h < 8:
        return img
    draw = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed + 72)
    for i in range(5):
        pw, ph = max(2, int(w * rng.uniform(.12, .23))), max(2, int(h * rng.uniform(.22, .38)))
        x, y = int(rng.uniform(-.02, .88) * w), int(rng.uniform(.04, .56) * h)
        color = _mix((245, 242, 225), _pick(c, i + 1, (220, 230, 235)), .14)
        draw.rectangle((x + 2, y + 3, min(w-1, x+pw+2), min(h-1, y+ph+3)), fill=(40, 35, 30, 35))
        draw.rectangle((x, y, min(w-1, x+pw), min(h-1, y+ph)), fill=(*color, 215), outline=(90, 80, 65, 80))
        draw.ellipse((x + pw//2 - 2, y + 2, x + pw//2 + 2, y + 6), fill=(180, 55, 50, 180))
    return img


def worksheet(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Pale ruled worksheet suitable for diagram overlays."""

    w, h = _size(width, height)
    img = _grain(_gradient(w, h, (250, 249, 242), (231, 235, 232)), seed + 79, 2)
    draw = ImageDraw.Draw(img, "RGBA")
    gap = max(4, int(h * .055))
    margin = max(1, int(w * .075))
    for y in range(gap, h, gap):
        draw.line((0, y, w, y), fill=(70, 135, 190, 34))
    draw.line((margin, 0, margin, h), fill=(210, 70, 70, 65), width=max(1, _line_width(w, h)))
    return img


def lab_bench(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Clinical wall over a steel laboratory bench."""

    w, h = _size(width, height)
    c = _colors(palette, "how_it_works")
    img = _gradient(w, h, (224, 235, 238), (150, 169, 175))
    if w < 8 or h < 8:
        return _grain(img, seed + 84, 1)
    draw = ImageDraw.Draw(img, "RGBA")
    bench = int(h * .72)
    draw.rectangle((0, bench, w, h), fill=(72, 91, 98, 210))
    draw.line((0, bench, w, bench), fill=(245, 250, 250, 170), width=_line_width(w, h, .006))
    accent = _pick(c, 1, (30, 110, 170))
    rng = np.random.default_rng(seed + 83)
    for i in range(4):
        x = int((.08 + i * .24 + rng.uniform(-.025, .025)) * w)
        bw = max(2, int(w * .07))
        top = int(h * rng.uniform(.47, .59))
        draw.rectangle((x, top, x+bw, bench), fill=(225, 244, 247, 100), outline=(*accent, 120))
        liquid_top = min(bench - 1, int(top + (bench - top) * .65))
        if x + 1 <= x + bw - 1 and liquid_top <= bench - 1:
            draw.rectangle((x+1, liquid_top, x+bw-1, bench-1),
                           fill=(*_pick(c, i+1, accent), 75))
    return _grain(img, seed + 84, 1)


def projection(width: int, height: int, seed: int, palette: PaletteLike = None) -> Image.Image:
    """Dark lecture room with a softly glowing projection screen."""

    w, h = _size(width, height)
    c = _colors(palette, "how_it_works")
    img = _gradient(w, h, (18, 24, 34), (5, 8, 15))
    if w < 8 or h < 8:
        return _grain(img, seed + 89, 2)
    draw = ImageDraw.Draw(img, "RGBA")
    m = max(1, int(min(w, h) * .06))
    box = (m, m, max(m, w-m-1), max(m, h-m-1))
    draw.rectangle((box[0]+3, box[1]+5, min(w-1, box[2]+3), min(h-1, box[3]+5)), fill=(0, 0, 0, 90))
    accent = _pick(c, 1, (30, 110, 170))
    draw.rectangle(box, fill=(220, 231, 236, 225), outline=(*accent, 150), width=_line_width(w, h, .004))
    draw.polygon([(w//2, h), (int(w*.42), box[3]), (int(w*.58), box[3])], fill=(*accent, 28))
    return _grain(img, seed + 89, 2)


# Trend brief --------------------------------------------------------------

def _trend_fields(width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
    w, h = _size(width, height)
    return (
        np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :],
        np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None],
    )


def _trend_image(depth: np.ndarray, colors: tuple[RGB, ...], beat: float = 0.0) -> Image.Image:
    bg = np.asarray(_pick(colors, 0, (8, 10, 18)), dtype=np.float32)
    bg = np.minimum(bg, 40)
    accent = np.asarray(_pick(colors, 1, (0, 230, 180)), dtype=np.float32)
    hot = np.asarray(_pick(colors, 2, (255, 80, 120)), dtype=np.float32)
    d = np.clip(depth + np.clip(beat, 0, 1) * .12, 0, 1)[..., None]
    arr = bg + d * (accent * .16 + np.array([8, 13, 22], dtype=np.float32))
    arr += np.maximum(0, d - .72) * hot * .12
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def neon_ridge(width: int, height: int, seed: int, palette: PaletteLike = None,
               t: float = 0.0, beat: float = 0.0) -> Image.Image:
    """Classic animated layered neon ridges and seeded particles."""

    w, h = _size(width, height)
    c = _colors(palette, "trend_brief")
    xx, yy = _trend_fields(w, h)
    phase = float(t) * 1.25
    depth = np.zeros((h, w), dtype=np.float32)
    for layer in range(3):
        s = layer + 1.0
        depth += ((np.sin((xx*(2.5+s*2.2)+yy*(1.2+s)+phase*(1.4+s*.7))*np.pi) +
                   np.cos((yy*(3+s)-xx*(.8+s*.3)-phase*.7)*np.pi)) * .25 + .5) / s
    depth /= sum(1.0 / (i + 1) for i in range(3))
    img = _trend_image(depth, c, beat)
    draw = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed + 101)
    accent = _pick(c, 1, (0, 230, 180))
    for i in range(max(8, min(80, (w*h)//256))):
        px = (float(rng.random()) + math.sin(float(t)*4 + i*.17)*.035) % 1
        py = (float(rng.random()) + float(t)*(.04 + float(rng.random())*.12)) % 1
        r = max(1, 1 + i % max(1, min(3, min(w, h)//8)))
        x, y = int(px*w), int(py*h)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(*accent, 75+i%3*35))
    scan = min(h-1, max(0, int((float(t)*1.8 % 1.0)*h)))
    draw.line((0, scan, w, scan), fill=(255, 255, 255, 28), width=1)
    return img


def grid_pulse(width: int, height: int, seed: int, palette: PaletteLike = None,
               t: float = 0.0, beat: float = 0.0) -> Image.Image:
    """Perspective cyber-grid with a beat-reactive horizon."""

    w, h = _size(width, height)
    c = _colors(palette, "trend_brief")
    img = _gradient(w, h, _pick(c, 0, (8, 10, 18)), (3, 5, 12))
    draw = ImageDraw.Draw(img, "RGBA")
    accent, hot = _pick(c, 1, (0,230,180)), _pick(c, 2, (255,80,120))
    horizon = int(h * (.40 + .02 * math.sin(float(t)*math.tau)))
    alpha = int(75 + 90*np.clip(beat, 0, 1))
    for i in range(-8, 9):
        draw.line((w//2, horizon, w//2 + i*w//7, h), fill=(*accent, alpha), width=1)
    for i in range(12):
        q = i / 11
        y = horizon + int((q*q) * (h-horizon))
        draw.line((0, y, w, y), fill=(*accent, max(18, alpha-int(q*35))), width=1)
    draw.line((0, horizon, w, horizon), fill=(*hot, 150), width=max(1, _line_width(w,h,.004)))
    return img


def aurora_bands(width: int, height: int, seed: int, palette: PaletteLike = None,
                 t: float = 0.0, beat: float = 0.0) -> Image.Image:
    """Flowing luminous color bands on a dark field."""

    w, h = _size(width, height)
    c = _colors(palette, "trend_brief")
    xx, yy = _trend_fields(w, h)
    depth = np.zeros((h, w), np.float32)
    for i in range(4):
        center = .18 + i*.18 + .09*np.sin(xx*(4+i)*math.pi + float(t)*math.tau*(.3+i*.08) + seed*.001)
        depth += np.exp(-((yy-center)/(.055+i*.008))**2) * (.45-i*.055)
    return _trend_image(np.clip(depth, 0, 1), c, beat)


def static_fizz(width: int, height: int, seed: int, palette: PaletteLike = None,
                t: float = 0.0, beat: float = 0.0) -> Image.Image:
    """Seeded television-static texture with moving signal bars."""

    w, h = _size(width, height)
    c = _colors(palette, "trend_brief")
    frame_key = int(math.floor(float(t) * 240.0))
    rng = np.random.default_rng(seed + 1009 + frame_key)
    noise = rng.random((h, w), dtype=np.float32)
    bands = .16*np.sin(np.linspace(0, math.tau*14, h, dtype=np.float32)[:,None] + float(t)*math.tau*5)
    depth = np.clip(noise*.48 + bands + .18, 0, 1)
    img = _trend_image(depth, c, beat)
    draw = ImageDraw.Draw(img, "RGBA")
    hot = _pick(c, 2, (255,80,120))
    for k in range(3):
        y = int(((float(t)*(.7+k*.16) + rng.random()) % 1)*h)
        draw.rectangle((0, y, w, min(h-1, y+max(1,h//90))), fill=(*hot, 32+k*15))
    return img


def mesh_glow(width: int, height: int, seed: int, palette: PaletteLike = None,
              t: float = 0.0, beat: float = 0.0) -> Image.Image:
    """Seeded network mesh with drifting glow nodes."""

    w, h = _size(width, height)
    c = _colors(palette, "trend_brief")
    img = _gradient(w, h, _pick(c, 0, (8,10,18)), (3, 4, 11))
    draw = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed + 113)
    n = max(6, min(34, int(math.sqrt(w*h)/18)))
    base = rng.random((n, 2))
    points = [(
        int(((p[0] + .025*math.sin(float(t)*math.tau + i)) % 1)*w),
        int(((p[1] + .018*math.cos(float(t)*math.tau*.7 + i*.8)) % 1)*h),
    ) for i, p in enumerate(base)]
    accent, hot = _pick(c, 1, (0,230,180)), _pick(c, 2, (255,80,120))
    limit = max(w, h)*.25
    for i, a in enumerate(points):
        for b in points[i+1:]:
            d = math.hypot(a[0]-b[0], a[1]-b[1])
            if d < limit:
                draw.line((a, b), fill=(*accent, int(55*(1-d/limit))), width=1)
    pulse = 1 + int(np.clip(beat,0,1)*3)
    for i, (x,y) in enumerate(points):
        r = max(1, pulse + i%3)
        draw.ellipse((x-r,y-r,x+r,y+r), fill=(*(hot if i%5==0 else accent), 150))
    return img


def radar_sweep(width: int, height: int, seed: int, palette: PaletteLike = None,
                t: float = 0.0, beat: float = 0.0) -> Image.Image:
    """Circular radar scope with sweep beam and seeded contacts."""

    w, h = _size(width, height)
    c = _colors(palette, "trend_brief")
    img = _gradient(w, h, _pick(c, 0, (8,10,18)), (2, 8, 12))
    draw = ImageDraw.Draw(img, "RGBA")
    accent, hot = _pick(c, 1, (0,230,180)), _pick(c, 2, (255,80,120))
    cx, cy, radius = w//2, h//2, max(1, int(min(w,h)*.43))
    for i in range(1, 5):
        r = max(1, radius*i//4)
        draw.ellipse((cx-r,cy-r,cx+r,cy+r), outline=(*accent, 50), width=1)
    draw.line((cx-radius,cy,cx+radius,cy), fill=(*accent,35))
    draw.line((cx,cy-radius,cx,cy+radius), fill=(*accent,35))
    angle = float(t)*math.tau
    ex, ey = cx+int(math.cos(angle)*radius), cy+int(math.sin(angle)*radius)
    draw.polygon([(cx,cy), (cx+int(math.cos(angle-.16)*radius),cy+int(math.sin(angle-.16)*radius)), (ex,ey)], fill=(*accent,42))
    draw.line((cx,cy,ex,ey), fill=(*accent,175), width=max(1,_line_width(w,h,.004)))
    rng = np.random.default_rng(seed + 127)
    for i in range(12):
        a, r = rng.random()*math.tau, math.sqrt(rng.random())*radius
        x,y = cx+int(math.cos(a)*r), cy+int(math.sin(a)*r)
        rr = max(1, 1+i%2+int(np.clip(beat,0,1)*2))
        draw.ellipse((x-rr,y-rr,x+rr,y+rr), fill=(*(hot if i%4==0 else accent), 190))
    return img


Painter = Callable[..., Image.Image]
_PAINTERS: dict[str, dict[str, Painter]] = {
    "kids_storybook": {name: globals()[name] for name in VARIANTS["kids_storybook"]},
    "how_it_works": {name: globals()[name] for name in VARIANTS["how_it_works"]},
    "trend_brief": {name: globals()[name] for name in VARIANTS["trend_brief"]},
}


def paint_background(
    engine: str,
    width: int,
    height: int,
    seed: int,
    palette: PaletteLike = None,
    variant: str | None = None,
    *,
    t: float = 0.0,
    beat: float = 0.0,
) -> Image.Image:
    """Paint one background and return a deterministic ``PIL.Image`` RGB image.

    ``engine`` is one of the keys in :data:`VARIANTS`.  Omitting ``variant``
    preserves the corresponding engine's classic background.  ``t`` and
    ``beat`` are used only by ``trend_brief`` painters.
    """

    engine = str(engine)
    if engine not in _PAINTERS:
        raise ValueError(f"Unknown background engine: {engine!r}")
    variant = variant or DEFAULT_VARIANTS[engine]
    try:
        painter = _PAINTERS[engine][variant]
    except KeyError as exc:
        raise ValueError(
            f"Unknown {engine!r} background variant {variant!r}; "
            f"expected one of {VARIANTS[engine]!r}"
        ) from exc
    if engine == "trend_brief":
        image = painter(width, height, seed, palette, t=t, beat=beat)
    else:
        image = painter(width, height, seed, palette)
    return image.convert("RGB")


__all__ = [
    "ChromeTheme",
    "DEFAULT_VARIANTS",
    "VARIANTS",
    "variants_for",
    "get_chrome_theme",
    "paint_background",
    *VARIANTS["kids_storybook"],
    *VARIANTS["how_it_works"],
    *VARIANTS["trend_brief"],
]
