"""Build a 1280×720 YouTube thumbnail with a readable title card."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from app.art.fonts import load_font, paint_text

YOUTUBE_THUMB = (1280, 720)


def make_youtube_thumbnail(
    source: Path | None,
    dest: Path,
    *,
    title: str,
    badge: str = "",
) -> Path:
    """Write a 1280×720 JPEG (under 2 MB) suitable for thumbnails.set."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    w, h = YOUTUBE_THUMB
    canvas = Image.new("RGB", (w, h), (12, 22, 32))
    if source is not None and Path(source).is_file():
        try:
            src = Image.open(source).convert("RGB")
            src = _cover(src, w, h)
            canvas.paste(src, (0, 0))
        except OSError:
            pass
    canvas = canvas.filter(ImageFilter.GaussianBlur(radius=0.6))
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, int(h * 0.52), w, h), fill=(8, 16, 24, 200))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    if badge:
        font_sm = load_font(28)
        paint_text(draw, (48, 48), badge.upper()[:28], font_sm, (255, 214, 120), anchor="lt")
    font_lg = load_font(64)
    paint_text(
        draw,
        (w // 2, int(h * 0.72)),
        (title or "New video")[:48],
        font_lg,
        (255, 252, 245),
        anchor="mm",
        max_width=w - 96,
    )
    canvas.save(dest, format="JPEG", quality=88, optimize=True)
    if dest.stat().st_size > 1_800_000:
        canvas.save(dest, format="JPEG", quality=72, optimize=True)
    return dest


def _cover(img: Image.Image, width: int, height: int) -> Image.Image:
    src_w, src_h = img.size
    if src_w < 1 or src_h < 1:
        return Image.new("RGB", (width, height), (12, 22, 32))
    scale = max(width / src_w, height / src_h)
    new = img.resize((max(1, int(src_w * scale)), max(1, int(src_h * scale))), Image.Resampling.LANCZOS)
    left = max(0, (new.width - width) // 2)
    top = max(0, (new.height - height) // 2)
    return new.crop((left, top, left + width, top + height))
