"""Offline word illustration pack for kids alphabet videos.

Images are drawn locally with Pillow and cached under assets/education/words/.
No internet download is required at any time.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.art.education_content import LETTER_WORDS, NUMBER_WORDS
from app.art.fonts import load_font
from app.utils.paths import project_root


def word_image_dir() -> Path:
    path = project_root() / "assets" / "education" / "words"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    return load_font(size)


def _all_words() -> list[str]:
    words: set[str] = set()
    for lst in LETTER_WORDS.values():
        words.update(lst)
    for lst in NUMBER_WORDS.values():
        words.update(lst)
    # Motif aliases used by lessons
    words.update(
        {
            "STAR", "SUN", "MOON", "TREE", "HOUSE", "FISH", "CAT", "DOG", "BALL",
            "APPLE", "RAINBOW", "UMBRELLA", "PENCIL", "ZEBRA", "BOX", "WAVE",
            "HEART", "FRIEND", "SPIRAL", "X-RAY", "X-RAY FISH", "JAGUAR", "NEWT",
            "QUAIL", "VULTURE", "IGUANA", "CLOUD",
        }
    )
    return sorted(words)


def _palette_for(word: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    """Background, main, accent colors from word hash (stable offline)."""
    h = sum(ord(c) * (i + 3) for i, c in enumerate(word.upper()))
    hues = [
        ((h * 37) % 360),
        ((h * 59 + 80) % 360),
        ((h * 17 + 160) % 360),
    ]

    def hsl(hdeg: int, s: float, l: float) -> tuple[int, int, int]:
        import colorsys

        r, g, b = colorsys.hls_to_rgb(hdeg / 360.0, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))

    return hsl(hues[0], 0.55, 0.88), hsl(hues[1], 0.75, 0.48), hsl(hues[2], 0.7, 0.35)


def _draw_scene(draw: ImageDraw.ImageDraw, word: str, w: int, h: int, main: tuple[int, int, int], accent: tuple[int, int, int]) -> None:
    """Draw a simple but recognizable offline illustration for the word."""
    cx, cy = w // 2, int(h * 0.46)
    s = int(min(w, h) * 0.28)
    dark = tuple(max(0, c - 60) for c in main)
    light = tuple(min(255, c + 70) for c in main)
    word = word.upper()

    def circle(x: int, y: int, r: int, fill=main, outline=dark) -> None:
        draw.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=max(2, r // 12))

    def rect(x0, y0, x1, y1, fill=main, outline=dark) -> None:
        draw.rectangle((x0, y0, x1, y1), fill=fill, outline=outline, width=3)

    # Category-style drawings
    if word in {"APPLE", "ORANGE", "LEMON", "BANANA", "GRAPE", "CHERRY"}:
        fill = (220, 50, 50) if word == "APPLE" else (255, 140, 40) if word != "GRAPE" else (120, 60, 160)
        if word == "LEMON":
            fill = (250, 220, 60)
        if word == "BANANA":
            draw.pieslice((cx - s, cy - s // 2, cx + s, cy + s), 200, 340, fill=(250, 220, 70), outline=dark)
        elif word == "GRAPE":
            for ox, oy in ((-20, 0), (20, 0), (0, -22), (-10, 20), (12, 18), (0, 8)):
                circle(cx + ox, cy + oy, s // 3, fill=fill)
        else:
            circle(cx, cy, s, fill=fill)
            draw.line((cx, cy - s, cx, cy - int(s * 1.35)), fill=(90, 55, 25), width=5)
            draw.ellipse((cx, cy - int(s * 1.4), cx + s // 2, cy - s), fill=(50, 160, 70))
    elif word in {"BALL", "EARTH", "MOON", "SUN", "STAR", "YELLOW"}:
        fill = (255, 200, 40) if word in {"SUN", "STAR", "YELLOW"} else main
        circle(cx, cy, s, fill=fill)
        if word in {"SUN", "STAR", "YELLOW"}:
            for a in range(0, 360, 30):
                import math

                rad = math.radians(a)
                draw.line(
                    (
                        cx + int(math.cos(rad) * s * 1.1),
                        cy + int(math.sin(rad) * s * 1.1),
                        cx + int(math.cos(rad) * s * 1.5),
                        cy + int(math.sin(rad) * s * 1.5),
                    ),
                    fill=fill,
                    width=5,
                )
        if word == "BALL":
            draw.arc((cx - s, cy - s, cx + s, cy + s), 20, 160, fill=dark, width=4)
            draw.line((cx - s, cy, cx + s, cy), fill=dark, width=3)
    elif word in {"CAT", "DOG", "LION", "TIGER", "WOLF", "FOX", "PIG", "MOUSE", "MONKEY", "RABBIT", "GOAT", "HORSE", "YAK", "ZEBRA", "COW", "JAGUAR", "IGUANA", "NEWT"}:
        fill = (240, 180, 80) if word != "ZEBRA" else (245, 245, 245)
        if word == "JAGUAR":
            fill = (235, 170, 60)
        circle(cx, cy + s // 8, int(s * 0.85), fill=fill)
        circle(cx, cy - s // 2, int(s * 0.55), fill=fill)
        # ears
        draw.polygon([(cx - s // 2, cy - s // 2), (cx - s // 4, cy - s), (cx - s // 8, cy - s // 3)], fill=fill, outline=dark)
        draw.polygon([(cx + s // 2, cy - s // 2), (cx + s // 4, cy - s), (cx + s // 8, cy - s // 3)], fill=fill, outline=dark)
        circle(cx - s // 5, cy - s // 2, s // 10, fill=dark)
        circle(cx + s // 5, cy - s // 2, s // 10, fill=dark)
        if word == "ZEBRA":
            for i in range(-2, 3):
                draw.line((cx + i * s // 5, cy - s // 5, cx + i * s // 5, cy + s // 2), fill=(30, 30, 30), width=4)
        if word == "JAGUAR":
            for ox, oy in ((-s // 3, 0), (s // 4, s // 5), (0, -s // 6), (s // 3, -s // 8)):
                circle(cx + ox, cy + oy + s // 8, s // 14, fill=(90, 55, 20))
        if word in {"IGUANA", "NEWT"}:
            for i in range(4):
                circle(cx - s // 2 + i * s // 4, cy - s, s // 14, fill=(70, 150, 90))
    elif word in {"BIRD", "DUCK", "OWL", "CHICKEN", "QUAIL", "VULTURE"}:
        circle(cx, cy, int(s * 0.7), fill=(255, 210, 80))
        circle(cx + s // 2, cy - s // 3, int(s * 0.35), fill=(255, 210, 80))
        draw.polygon([(cx + int(s * 0.75), cy - s // 3), (cx + int(s * 1.2), cy - s // 5), (cx + int(s * 0.75), cy - s // 8)], fill=(255, 140, 40))
        circle(cx + s // 2, cy - s // 3, s // 12, fill=dark)
    elif word in {"FISH", "SNAKE", "OCTOPUS"}:
        draw.ellipse((cx - s, cy - s // 2, cx + s // 2, cy + s // 2), fill=(80, 160, 255), outline=dark, width=3)
        draw.polygon([(cx + s // 2, cy), (cx + s, cy - s // 2), (cx + s, cy + s // 2)], fill=(60, 120, 220), outline=dark)
        circle(cx - s // 3, cy - s // 8, s // 10, fill=dark)
    elif word in {"HOUSE", "SCHOOL", "DOOR", "IGLOO"}:
        rect(cx - s, cy - s // 4, cx + s, cy + s, fill=(240, 210, 160))
        draw.polygon([(cx - s, cy - s // 4), (cx, cy - s), (cx + s, cy - s // 4)], fill=(200, 70, 70), outline=dark)
        rect(cx - s // 5, cy + s // 4, cx + s // 5, cy + s, fill=(120, 70, 30))
    elif word in {"TREE", "LEAF", "FLOWER", "ROSE", "NEST"}:
        rect(cx - s // 8, cy, cx + s // 8, cy + s, fill=(120, 75, 35))
        circle(cx, cy - s // 4, int(s * 0.75), fill=(50, 170, 70))
        if word in {"FLOWER", "ROSE"}:
            for ox, oy in ((-s // 2, 0), (s // 2, 0), (0, -s // 2), (0, s // 2)):
                circle(cx + ox, cy - s // 4 + oy, s // 3, fill=(240, 80, 120))
            circle(cx, cy - s // 4, s // 4, fill=(255, 220, 60))
    elif word in {"CAR", "BUS", "VAN", "TRAIN", "PLANE", "AIRPLANE", "SHIP"}:
        rect(cx - s, cy - s // 4, cx + s, cy + s // 3, fill=(70, 140, 230))
        rect(cx - s // 2, cy - s // 2, cx + s // 3, cy - s // 4, fill=(180, 220, 255))
        circle(cx - s // 2, cy + s // 3, s // 4, fill=(40, 40, 40))
        circle(cx + s // 2, cy + s // 3, s // 4, fill=(40, 40, 40))
    elif word in {"KITE", "RAINBOW"}:
        if word == "RAINBOW":
            bands = [(255, 80, 80), (255, 160, 60), (255, 220, 80), (80, 200, 100), (80, 140, 255)]
            for i, band in enumerate(bands):
                r = s - i * max(3, s // 8)
                draw.arc((cx - r, cy - r // 2, cx + r, cy + r), 200, 340, fill=band, width=max(4, s // 10))
        else:
            draw.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s // 2), (cx - s, cy)], fill=(255, 90, 90), outline=dark)
            draw.line((cx, cy + s // 2, cx, cy + int(s * 1.4)), fill=dark, width=3)
    elif word in {"UMBRELLA", "HAT", "CROWN", "QUEEN"}:
        draw.pieslice((cx - s, cy - s // 2, cx + s, cy + s // 2), 180, 360, fill=(220, 60, 90), outline=dark)
        draw.line((cx, cy, cx, cy + s), fill=dark, width=5)
    elif word in {"PENCIL", "BOOK", "LAMP", "KEY", "WATCH", "DRUM", "VIOLIN"}:
        rect(cx - s // 3, cy - s, cx + s // 3, cy + s // 2, fill=(255, 210, 70))
        draw.polygon([(cx - s // 3, cy + s // 2), (cx, cy + s), (cx + s // 3, cy + s // 2)], fill=(240, 200, 150), outline=dark)
    elif word == "XYLOPHONE":
        bar_colors = [(230, 70, 70), (240, 140, 60), (240, 210, 70), (110, 190, 100), (70, 150, 220), (140, 100, 210)]
        bar_w = int(s * 1.7 / len(bar_colors))
        start_x = cx - int(s * 0.85)
        for i, bc in enumerate(bar_colors):
            bar_len = int(s * 1.1 - i * (s * 0.09))
            x0 = start_x + i * bar_w
            rect(x0, cy - bar_len // 2, x0 + bar_w - 4, cy + bar_len // 2, fill=bc, outline=dark)
    elif word == "X-RAY" or word == "X-RAY FISH":
        # Simple bone icon representing an X-ray image
        circle(cx - s // 2, cy, s // 4, fill=(235, 235, 235), outline=dark)
        circle(cx + s // 2, cy, s // 4, fill=(235, 235, 235), outline=dark)
        rect(cx - s // 2, cy - s // 10, cx + s // 2, cy + s // 10, fill=(235, 235, 235), outline=dark)
    elif word == "SPIRAL":
        import math

        pts = []
        turns = 3.2
        max_r = s
        for i in range(80):
            frac = i / 79
            ang = frac * turns * 2 * math.pi
            r = frac * max_r
            pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        draw.line(pts, fill=main, width=max(4, s // 12), joint="curve")
    elif word == "FRIEND":
        circle(cx, cy - s // 2, s // 3, fill=(250, 210, 170), outline=dark)
        rect(cx - s // 3, cy - s // 8, cx + s // 3, cy + s, fill=main, outline=dark)
        draw.line((cx - s // 3, cy, cx - int(s * 0.8), cy - s // 4), fill=main, width=max(4, s // 10))
        draw.line((cx + s // 3, cy, cx + int(s * 0.8), cy - s // 4), fill=main, width=max(4, s // 10))
    elif word == "HEART":
        import math

        pts = []
        for i in range(50):
            v = i / 49 * 2 * math.pi
            x = 16 * (math.sin(v) ** 3)
            y = -(13 * math.cos(v) - 5 * math.cos(2 * v) - 2 * math.cos(3 * v) - math.cos(4 * v))
            pts.append((cx + x * s / 16, cy + y * s / 16))
        draw.polygon(pts, fill=(230, 60, 90), outline=(150, 30, 50))
    elif word in {"CLOUD", "WATER", "WAVE", "OCEAN", "ICE", "SNOW"}:
        for ox, oy, r in ((-s // 2, 0, s // 2), (0, -s // 4, int(s * 0.6)), (s // 2, 0, s // 2)):
            circle(cx + ox, cy + oy, r, fill=(230, 240, 255), outline=(140, 170, 210))
    elif word in {"EGG", "CAKE", "PIZZA", "MILK", "JUICE", "JAM"}:
        circle(cx, cy, int(s * 0.7), fill=(255, 245, 210))
        if word == "CAKE":
            rect(cx - s, cy, cx + s, cy + s // 2, fill=(255, 160, 180))
            circle(cx, cy, s // 4, fill=(255, 80, 100))
    elif word.isdigit() or word in {"ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"}:
        # Number badge
        circle(cx, cy, s, fill=(90, 150, 255))
        label = word if word.isdigit() else {"ZERO": "0", "ONE": "1", "TWO": "2", "THREE": "3", "FOUR": "4", "FIVE": "5", "SIX": "6", "SEVEN": "7", "EIGHT": "8", "NINE": "9"}.get(word, "?")
        draw.text((cx, cy), label, font=_font(max(40, s)), fill=(255, 255, 255), anchor="mm")
    else:
        # Generic friendly blob + icon mark
        circle(cx, cy, s, fill=main)
        circle(cx - s // 3, cy - s // 4, s // 8, fill=light)
        draw.arc((cx - s // 2, cy - s // 6, cx + s // 2, cy + s // 2), 20, 160, fill=dark, width=4)

    # Soft ground shadow
    draw.ellipse((cx - s, int(h * 0.78), cx + s, int(h * 0.86)), fill=(210, 200, 180))


def render_word_image(word: str, size: int = 512) -> Image.Image:
    """Create an offline illustrated card for a learning word."""
    word = word.upper().strip() or "FUN"
    bg, main, accent = _palette_for(word)
    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)
    # Decorative border
    m = max(8, size // 28)
    draw.rounded_rectangle((m, m, size - m, size - m), radius=size // 12, outline=accent, width=max(4, size // 64))
    _draw_scene(draw, word, size, size, main, accent)
    # Word label
    font = _font(max(22, size // 11))
    draw.rounded_rectangle(
        (size // 8, int(size * 0.82), size - size // 8, int(size * 0.94)),
        radius=14,
        fill=(255, 255, 255),
        outline=accent,
        width=3,
    )
    draw.text((size // 2, int(size * 0.88)), word, font=font, fill=(40, 55, 80), anchor="mm")
    return img


def ensure_word_image(word: str, size: int = 512) -> Path:
    """Generate and cache a PNG for the word if missing. Fully offline."""
    word = word.upper().strip()
    path = word_image_dir() / f"{word}.png"
    if path.exists() and path.stat().st_size > 100:
        return path
    img = render_word_image(word, size=size)
    img.save(path, format="PNG", optimize=True)
    return path


def ensure_word_pack(size: int = 512) -> int:
    """Generate the full offline word pack. Returns number of images ensured."""
    count = 0
    for word in _all_words():
        ensure_word_image(word, size=size)
        count += 1
    return count


@lru_cache(maxsize=128)
def load_word_image(word: str, target_size: int = 256) -> Image.Image:
    """Load a cached/generated word illustration, resized."""
    path = ensure_word_image(word)
    img = Image.open(path).convert("RGBA")
    if img.size[0] != target_size:
        img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
    return img


def paste_illustration(
    base: Image.Image,
    source: str | Path,
    center: tuple[int, int],
    size: int,
    *,
    bounce: int = 0,
) -> Image.Image:
    """Paste a generated scene PNG (or fall back to a word card)."""
    path = Path(str(source)) if source else None
    if path is not None and path.is_file():
        card = Image.open(path).convert("RGBA")
        target = max(32, int(size))
        if card.size[0] != target:
            card = card.resize((target, target), Image.Resampling.LANCZOS)
        frame = Image.new("RGBA", (target + 16, target + 16), (0, 0, 0, 0))
        fd = ImageDraw.Draw(frame)
        fd.rounded_rectangle(
            (0, 0, target + 15, target + 15),
            radius=18,
            fill=(255, 255, 255, 240),
            outline=(60, 80, 110, 255),
            width=3,
        )
        frame.paste(card, (8, 8), card)
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        x = int(center[0] - frame.size[0] / 2)
        y = int(center[1] - frame.size[1] / 2 + bounce)
        overlay.paste(frame, (x, y), frame)
        composed = Image.alpha_composite(base.convert("RGBA"), overlay)
        rgb = composed.convert("RGB")
        base.paste(rgb)
        return base
    return paste_word_image(base, str(source), center, size, bounce=bounce)


def paste_segment_image(
    base: Image.Image,
    seg: dict,
    center: tuple[int, int],
    size: int,
    *,
    bounce: int = 0,
) -> Image.Image:
    """Prefer an AI-realized image_path, otherwise the lesson word card."""
    path = str(seg.get("image_path") or "")
    if path:
        return paste_illustration(base, path, center, size, bounce=bounce)
    word = str(seg.get("word") or seg.get("motif") or "")
    if word:
        return paste_word_image(base, word, center, size, bounce=bounce)
    return base


def paste_word_image(
    base: Image.Image,
    word: str,
    center: tuple[int, int],
    size: int,
    *,
    bounce: int = 0,
) -> Image.Image:
    """Paste a rounded word illustration onto a PIL image. Returns RGB image."""
    card = load_word_image(word, target_size=max(32, size))
    frame = Image.new("RGBA", (size + 16, size + 16), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)
    fd.rounded_rectangle(
        (0, 0, size + 15, size + 15),
        radius=18,
        fill=(255, 255, 255, 240),
        outline=(60, 80, 110, 255),
        width=3,
    )
    frame.paste(card, (8, 8), card)

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    x = int(center[0] - frame.size[0] / 2)
    y = int(center[1] - frame.size[1] / 2 + bounce)
    overlay.paste(frame, (x, y), frame)
    composed = Image.alpha_composite(base.convert("RGBA"), overlay)
    rgb = composed.convert("RGB")
    base.paste(rgb)
    return base
