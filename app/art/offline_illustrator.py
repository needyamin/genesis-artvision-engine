"""Offline illustrator: turn AI image briefs into unique Pillow scenes.

No cloud image APIs. Briefs are parsed into subject, color, and setting,
then drawn locally and cached under data/ai_scenes/.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from app.art.word_images import _draw_scene, _font, _palette_for
from app.utils.paths import project_root

_COLOR_WORDS: dict[str, tuple[int, int, int]] = {
    "red": (230, 70, 70),
    "blue": (70, 120, 235),
    "green": (70, 190, 90),
    "yellow": (245, 220, 60),
    "orange": (245, 150, 55),
    "purple": (160, 90, 210),
    "pink": (245, 130, 180),
    "gold": (240, 190, 70),
    "golden": (240, 190, 70),
    "white": (245, 245, 250),
    "black": (40, 40, 48),
    "teal": (40, 170, 170),
    "brown": (150, 95, 55),
}

_SETTINGS: dict[str, tuple[int, int, int]] = {
    "night": (22, 28, 52),
    "sky": (150, 205, 245),
    "sunset": (255, 150, 90),
    "sunrise": (255, 190, 130),
    "ocean": (40, 95, 165),
    "sea": (40, 95, 165),
    "garden": (170, 215, 140),
    "forest": (90, 140, 80),
    "classroom": (245, 236, 214),
    "space": (16, 18, 42),
    "snow": (230, 240, 250),
    "beach": (250, 220, 150),
    "sunshine": (255, 230, 150),
    "sunny": (255, 230, 150),
}

_SUBJECTS = (
    "RAINBOW", "AIRPLANE", "UMBRELLA", "XYLOPHONE", "ELEPHANT", "BUTTERFLY",
    "APPLE", "ORANGE", "LEMON", "BANANA", "GRAPE", "HOUSE", "FLOWER", "ROSE",
    "TREE", "LEAF", "STAR", "MOON", "SUN", "CLOUD", "FISH", "BIRD", "CAT",
    "DOG", "LION", "TIGER", "BALL", "CAR", "BUS", "TRAIN", "SHIP", "KITE",
    "HEART", "FRIEND", "ROBOT", "ROCKET", "CASTLE", "MOUNTAIN", "CIRCLE",
    "SQUARE", "TRIANGLE", "PENCIL", "BOOK", "HAT", "QUEEN", "KING",
)


def scene_dir() -> Path:
    path = project_root() / "data" / "ai_scenes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def parse_image_brief(brief: str, fallback_word: str = "STAR") -> dict[str, str]:
    """Extract subject/color/setting keywords from a short AI image brief."""
    text = re.sub(r"[^A-Za-z0-9\s-]", " ", brief or "")
    tokens = [t.lower() for t in text.split() if t]
    joined = " ".join(tokens)
    color = next((c for c in _COLOR_WORDS if c in tokens), "")
    setting = next((s for s in _SETTINGS if s in tokens or s in joined), "")
    subject = ""
    upper_join = joined.upper()
    for word in _SUBJECTS:
        if word in upper_join.split() or word.lower() in tokens:
            subject = word
            break
        if word.lower().replace("-", " ") in joined:
            subject = word
            break
    if not subject:
        subject = (fallback_word or "STAR").upper().split()[0]
    fb = (fallback_word or "").upper().split()[0]
    if fb and fb not in {"FUN", "STAR", ""}:
        # Teaching word wins so the picture matches the letter/voice.
        if fb in _SUBJECTS or fb in upper_join.split() or len(fb) >= 3:
            subject = fb
    extras: list[str] = []
    for extra in ("sparkle", "sparkles", "stars", "glow", "rainbow", "clouds", "hearts"):
        if extra in tokens or extra in joined:
            extras.append(extra)
    return {
        "subject": subject,
        "color": color,
        "setting": setting,
        "extras": ",".join(extras),
        "label": (fallback_word or subject).upper()[:18],
    }


def _tint(color: tuple[int, int, int], toward: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(int(max(0, min(255, a * (1 - amount) + b * amount))) for a, b in zip(color, toward))


def render_brief_image(
    brief: str,
    *,
    word: str = "",
    seed: int = 0,
    size: int = 512,
    label: str | None = None,
) -> Image.Image:
    """Paint an offline illustration matching the AI brief."""
    parsed = parse_image_brief(brief, fallback_word=word or "STAR")
    subject = parsed["subject"]
    bg, main, accent = _palette_for(subject + str(seed))
    if parsed["setting"] and parsed["setting"] in _SETTINGS:
        bg = _SETTINGS[parsed["setting"]]
        if parsed["setting"] in {"night", "space"}:
            main = _tint(main, (255, 255, 255), 0.25)
    if parsed["color"] and parsed["color"] in _COLOR_WORDS:
        main = _COLOR_WORDS[parsed["color"]]
        accent = _tint(main, (20, 20, 30), 0.35)

    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)
    # Soft sky gradient
    top = _tint(bg, (255, 255, 255), 0.18)
    for y in range(size):
        t = y / max(1, size - 1)
        row = tuple(int(top[i] * (1 - t) + bg[i] * t) for i in range(3))
        draw.line((0, y, size, y), fill=row)

    extras = set((parsed["extras"] or "").split(",")) - {""}
    if parsed["setting"] in {"night", "space"} or "stars" in extras or "sparkle" in extras or "sparkles" in extras:
        rng_step = max(1, 17 + (seed % 13))
        for i in range(18):
            x = (i * 73 + seed * 11) % (size - 20) + 10
            y = (i * 47 + seed * 5) % int(size * 0.55) + 8
            r = 1 + (i + seed) % 3
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 250, 210))
    if parsed["setting"] in {"sky", "garden", "sunshine", "sunny"} or "clouds" in extras:
        for i, ox in enumerate((-size // 4, size // 5)):
            cx, cy, r = size // 2 + ox, int(size * 0.18 + i * 8), size // 10
            draw.ellipse((cx - r, cy - r // 2, cx + r, cy + r // 2), fill=(255, 255, 255))

    m = max(8, size // 28)
    draw.rounded_rectangle((m, m, size - m, size - m), radius=size // 12, outline=accent, width=max(4, size // 64))
    _draw_scene(draw, subject, size, size, main, accent)

    if "rainbow" in extras and subject != "RAINBOW":
        bands = [(255, 80, 80), (255, 160, 60), (255, 220, 80), (80, 200, 100), (80, 140, 255)]
        for i, band in enumerate(bands):
            r = int(size * 0.22) - i * 6
            draw.arc((size // 2 - r, int(size * 0.08), size // 2 + r, int(size * 0.42)), 200, 340, fill=band, width=5)
    if "hearts" in extras or "glow" in extras:
        draw.ellipse((size // 2 - 8, int(size * 0.12), size // 2 + 8, int(size * 0.12) + 16), fill=(255, 120, 150))

    caption = (label or parsed["label"] or subject).upper()[:18]
    font = _font(max(22, size // 11))
    draw.rounded_rectangle(
        (size // 8, int(size * 0.82), size - size // 8, int(size * 0.94)),
        radius=14,
        fill=(255, 255, 255),
        outline=accent,
        width=3,
    )
    draw.text((size // 2, int(size * 0.88)), caption, font=font, fill=(40, 55, 80), anchor="mm")
    return img.filter(ImageFilter.SMOOTH)


def ensure_brief_image(
    brief: str,
    *,
    word: str = "",
    seed: int = 0,
    size: int = 512,
    label: str | None = None,
) -> Path:
    """Generate and cache a PNG for this brief. Fully offline."""
    key_src = f"{brief.strip().lower()}|{word.upper()}|{seed}|{size}|{label or ''}"
    digest = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:16]
    path = scene_dir() / f"{digest}.png"
    if path.exists() and path.stat().st_size > 100:
        return path
    img = render_brief_image(brief, word=word, seed=seed, size=size, label=label)
    img.save(path, format="PNG", optimize=True)
    return path
