"""Advanced children's school alphabet — cinematic cartoon letter animations."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.art.base import ArtEngine, register_engine

LETTER_WORDS: dict[str, str] = {
    "A": "APPLE",
    "B": "BALL",
    "C": "CAT",
    "D": "DUCK",
    "E": "EGG",
    "F": "FISH",
    "G": "GRAPE",
    "H": "HOUSE",
    "I": "ICE",
    "J": "JAR",
    "K": "KITE",
    "L": "LEAF",
    "M": "MOON",
    "N": "NEST",
    "O": "ORANGE",
    "P": "PENCIL",
    "Q": "QUEEN",
    "R": "RAINBOW",
    "S": "SUN",
    "T": "TREE",
    "U": "UMBRELLA",
    "V": "VAN",
    "W": "WAVE",
    "X": "BOX",
    "Y": "YARN",
    "Z": "ZEBRA",
    "0": "ZERO",
    "1": "ONE",
    "2": "TWO",
    "3": "THREE",
    "4": "FOUR",
    "5": "FIVE",
    "6": "SIX",
    "7": "SEVEN",
    "8": "EIGHT",
    "9": "NINE",
}


def _load_font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
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


def _blend(
    c: tuple[int, int, int],
    factor: float,
    toward: tuple[int, int, int] = (255, 255, 255),
) -> tuple[int, int, int]:
    return tuple(int(np.clip(a * (1 - factor) + b * factor, 0, 255)) for a, b in zip(c, toward))


def _draw_bubble_letter(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    *,
    outline: tuple[int, int, int] = (35, 45, 70),
    outline_w: int = 6,
) -> None:
    """Cartoon bubble letter: shadow, thick outline, fill."""
    x, y = xy
    draw.text((x + outline_w, y + outline_w), text, font=font, fill=(40, 45, 60), anchor="mm")
    for dx, dy in (
        (-outline_w, 0),
        (outline_w, 0),
        (0, -outline_w),
        (0, outline_w),
        (-outline_w, -outline_w),
        (-outline_w, outline_w),
        (outline_w, -outline_w),
        (outline_w, outline_w),
    ):
        draw.text((x + dx, y + dy), text, font=font, fill=outline, anchor="mm")
    draw.text((x, y), text, font=font, fill=fill, anchor="mm")


def _draw_motif(
    draw: ImageDraw.ImageDraw,
    kind: str,
    cx: int,
    cy: int,
    s: int,
    color: tuple[int, int, int],
    t: float = 0.0,
) -> None:
    """Filled animated cartoon motif for letter association."""
    s = max(10, int(s * (1.0 + 0.08 * np.sin(t * np.pi * 4))))
    dark = _blend(color, 0.0, (20, 20, 30))
    light = _blend(color, 0.45)
    w = max(2, s // 10)

    if kind in {"APPLE", "ORANGE", "BALL", "EGG", "GRAPE", "ICE", "JAR", "YARN"}:
        draw.ellipse((cx - s, cy - s, cx + s, cy + s), fill=color, outline=dark, width=w)
        draw.ellipse((cx - s // 2, cy - s // 2, cx - s // 8, cy - s // 8), fill=light)
        if kind == "APPLE":
            draw.line((cx, cy - s, cx, cy - int(s * 1.35)), fill=(80, 50, 20), width=w)
            draw.ellipse((cx, cy - int(s * 1.4), cx + s // 2, cy - s), fill=(60, 160, 70), outline=dark)
        if kind == "BALL":
            draw.line((cx - s, cy, cx + s, cy), fill=dark, width=max(1, w - 1))
            draw.arc((cx - s, cy - s, cx + s, cy + s), 20, 160, fill=dark, width=w)
    elif kind in {"SUN", "MOON"}:
        draw.ellipse((cx - s, cy - s, cx + s, cy + s), fill=color, outline=dark, width=w)
        if kind == "SUN":
            for a in range(0, 360, 30):
                rad = np.radians(a + t * 40)
                draw.line(
                    (
                        cx + int(np.cos(rad) * s * 1.15),
                        cy + int(np.sin(rad) * s * 1.15),
                        cx + int(np.cos(rad) * s * 1.55),
                        cy + int(np.sin(rad) * s * 1.55),
                    ),
                    fill=color,
                    width=w,
                )
        else:
            draw.ellipse(
                (cx - s // 4, cy - s // 2, cx + s // 2, cy + s // 4),
                fill=_blend(color, 0.2, (30, 40, 70)),
            )
    elif kind in {"HOUSE", "VAN", "BOX"}:
        draw.rectangle((cx - s, cy - s // 3, cx + s, cy + s), fill=color, outline=dark, width=w)
        draw.polygon([(cx - s, cy - s // 3), (cx, cy - s), (cx + s, cy - s // 3)], fill=light, outline=dark)
        draw.rectangle((cx - s // 4, cy + s // 4, cx + s // 4, cy + s), fill=_blend(color, 0.3, (80, 50, 20)))
    elif kind in {"TREE", "LEAF", "NEST"}:
        draw.rectangle((cx - s // 8, cy, cx + s // 8, cy + s), fill=(120, 80, 40), outline=dark)
        draw.ellipse((cx - s, cy - s, cx + s, cy + s // 4), fill=color, outline=dark, width=w)
    elif kind == "FISH":
        draw.ellipse((cx - s, cy - s // 2, cx + s // 2, cy + s // 2), fill=color, outline=dark, width=w)
        draw.polygon([(cx + s // 2, cy), (cx + s, cy - s // 2), (cx + s, cy + s // 2)], fill=light, outline=dark)
        draw.ellipse((cx - s // 2, cy - s // 6, cx - s // 4, cy), fill=dark)
    elif kind in {"KITE", "STAR", "QUEEN"}:
        pts = []
        for i in range(10):
            ang = -np.pi / 2 + i * np.pi / 5 + t
            r = s if i % 2 == 0 else s * 0.45
            pts.append((cx + np.cos(ang) * r, cy + np.sin(ang) * r))
        draw.polygon(pts, fill=color, outline=dark)
        if kind == "KITE":
            draw.line((cx, cy + s // 2, cx, cy + int(s * 1.6)), fill=dark, width=w)
    elif kind == "RAINBOW":
        bands = [(255, 80, 80), (255, 160, 60), (255, 220, 80), (80, 200, 100), (80, 140, 255)]
        for i, band in enumerate(bands):
            r = s - i * max(2, s // 8)
            draw.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=band, width=max(2, s // 10))
    elif kind == "CAT":
        draw.ellipse((cx - s, cy - s // 2, cx + s, cy + s // 2), fill=color, outline=dark, width=w)
        draw.polygon([(cx - s // 2, cy - s // 2), (cx - s // 4, cy - s), (cx, cy - s // 3)], fill=color, outline=dark)
        draw.polygon([(cx + s // 2, cy - s // 2), (cx + s // 4, cy - s), (cx, cy - s // 3)], fill=color, outline=dark)
        draw.ellipse((cx - s // 3, cy - s // 8, cx - s // 8, cy + s // 8), fill=dark)
        draw.ellipse((cx + s // 8, cy - s // 8, cx + s // 3, cy + s // 8), fill=dark)
    elif kind == "DUCK":
        draw.ellipse((cx - s, cy - s // 3, cx + s // 2, cy + s // 2), fill=color, outline=dark, width=w)
        draw.ellipse((cx + s // 4, cy - s, cx + s, cy - s // 4), fill=color, outline=dark, width=w)
        draw.polygon(
            [(cx + s, cy - s // 2), (cx + int(s * 1.4), cy - s // 3), (cx + s, cy - s // 6)],
            fill=(255, 160, 60),
            outline=dark,
        )
    elif kind == "UMBRELLA":
        draw.pieslice((cx - s, cy - s, cx + s, cy + s // 3), 180, 360, fill=color, outline=dark)
        draw.line((cx, cy, cx, cy + s), fill=dark, width=w)
    elif kind == "PENCIL":
        draw.rectangle((cx - s // 4, cy - s, cx + s // 4, cy + s // 2), fill=color, outline=dark, width=w)
        draw.polygon(
            [(cx - s // 4, cy + s // 2), (cx, cy + s), (cx + s // 4, cy + s // 2)],
            fill=(240, 210, 160),
            outline=dark,
        )
    elif kind == "WAVE":
        pts = []
        for i in range(12):
            xx = cx - s + i * (2 * s / 11)
            yy = cy + np.sin(i * 0.8 + t * 6) * (s // 3)
            pts.append((xx, yy))
        draw.line(pts, fill=color, width=max(3, w + 1))
    elif kind == "ZEBRA":
        draw.ellipse((cx - s, cy - s // 2, cx + s, cy + s // 2), fill=(245, 245, 245), outline=dark, width=w)
        for i in range(-2, 3):
            draw.line((cx + i * s // 4, cy - s // 2, cx + i * s // 4, cy + s // 2), fill=dark, width=w)
    else:
        draw.ellipse((cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2), fill=color, outline=dark, width=w)


@register_engine
class AlphabetCartoonEngine(ArtEngine):
    """Advanced school alphabet engine with bubble letters, motifs, and scenes."""

    name = "alphabet_cartoon"
    description = "Advanced children's school alphabet — cartoon charts, lessons, and parades"

    def _on_setup(self) -> None:
        assert self.rng is not None
        modes = ["chart", "focus", "parade", "lesson", "spell"]
        mode = str(self.params.get("mode", "chart"))
        if mode not in modes:
            mode = str(self.rng.choice(modes))
        self.mode = mode

        include_numbers = bool(self.params.get("include_numbers", False))
        alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        if include_numbers:
            alphabet += list("0123456789")

        self.spell_word = ""
        if self.mode in {"focus", "lesson"}:
            order = list(alphabet)
            self.rng.shuffle(order)
            self.letters = order
        elif self.mode == "spell":
            word = str(self.rng.choice(list(LETTER_WORDS.values())))
            self.letters = list(word)
            self.spell_word = word
        else:
            if float(self.params.get("density", 0.7)) < 0.4:
                k = int(self.rng.integers(10, 18))
                self.letters = list(self.rng.choice(alphabet, size=min(k, len(alphabet)), replace=False))
            else:
                self.letters = alphabet

        self.cols = max(4, min(int(self.params.get("columns", 7)), 9))
        self.rows = max(1, int(np.ceil(len(self.letters) / self.cols)))
        n = len(self.letters)
        self.phases = self.rng.random(max(1, n)).astype(np.float32)
        self.hues = self.rng.random(max(1, n)).astype(np.float32)
        self.bounce = float(self.params.get("bounce", 0.75))
        self.wobble = float(self.params.get("wobble", 0.55))
        self.show_motifs = bool(self.params.get("show_motifs", True))
        self.show_lowercase = bool(self.params.get("show_lowercase", True))
        self.bg_style = str(
            self.params.get("background", self.rng.choice(["notebook", "sky", "classroom", "pastel"]))
        )
        self.sparkle = float(self.params.get("sparkle", 0.7))
        self.pop_in = bool(self.params.get("pop_in", True))

        base = min(self.width, self.height)
        self.font_size = max(36, int(base * float(self.params.get("letter_scale", 0.13))))
        self.font = _load_font(self.font_size)
        self.font_lg = _load_font(max(64, int(base * 0.28)))
        self.font_md = _load_font(max(28, int(base * 0.08)))
        self.font_sm = _load_font(max(18, int(base * 0.045)))
        self.outline_w = max(4, self.font_size // 10)

        sp = int(40 + 80 * self.sparkle)
        self.sparks_x = self.rng.random(sp).astype(np.float32)
        self.sparks_y = self.rng.random(sp).astype(np.float32)
        self.sparks_r = self.rng.uniform(1.5, 4.5, sp).astype(np.float32)
        self.sparks_ph = self.rng.random(sp).astype(np.float32)

    def _pop_scale(self, local_t: float) -> float:
        if not self.pop_in:
            return 1.0
        local_t = float(np.clip(local_t, 0.0, 1.0))
        if local_t <= 0:
            return 0.05
        if local_t < 0.7:
            return float(np.sin(local_t / 0.7 * np.pi * 0.5) * 1.12)
        return 1.0

    def _make_background(self, t: float) -> Image.Image:
        assert self.palette is not None
        if self.bg_style == "notebook":
            img = Image.new("RGB", (self.width, self.height), (250, 247, 235))
            draw = ImageDraw.Draw(img)
            step = max(28, self.height // 24)
            for y in range(int(self.height * 0.12), self.height, step):
                draw.line((40, y, self.width - 40, y), fill=(180, 210, 230), width=2)
            draw.line((int(self.width * 0.08), 0, int(self.width * 0.08), self.height), fill=(240, 140, 140), width=3)
        elif self.bg_style == "sky":
            top = np.array(self.palette.as_uint8(0.55), dtype=np.float32)
            bot = np.array((255, 230, 180), dtype=np.float32)
            arr = np.zeros((self.height, self.width, 3), dtype=np.float32)
            for y in range(self.height):
                f = y / max(1, self.height - 1)
                arr[y] = top * (1 - f) + bot * f
            img = Image.fromarray(arr.astype(np.uint8))
            draw = ImageDraw.Draw(img)
            for i in range(5):
                cx = int(((i * 0.22 + t * 0.05) % 1.2) * self.width)
                cy = int(self.height * (0.15 + 0.08 * (i % 3)))
                for ox, oy, r in ((-30, 0, 36), (0, -12, 42), (34, 0, 34)):
                    draw.ellipse((cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r), fill=(255, 255, 255))
        elif self.bg_style == "classroom":
            img = Image.new("RGB", (self.width, self.height), (62, 110, 78))
            draw = ImageDraw.Draw(img)
            m = int(min(self.width, self.height) * 0.04)
            draw.rectangle((m, m, self.width - m, self.height - m), outline=(230, 230, 210), width=4)
            draw.rectangle((0, int(self.height * 0.88), self.width, self.height), fill=(140, 90, 50))
        else:
            arr = np.full((self.height, self.width, 3), 240, dtype=np.float32)
            yy, xx = np.ogrid[: self.height, : self.width]
            for i in range(6):
                c = np.array(self.palette.as_uint8((i * 0.15 + t * 0.1) % 1.0), dtype=np.float32)
                cx = ((0.2 + 0.15 * i + 0.05 * np.sin(t * 3 + i)) % 1.0) * self.width
                cy = ((0.25 + 0.12 * i) % 1.0) * self.height
                dist = ((xx - cx) ** 2 + (yy - cy) ** 2) / (min(self.width, self.height) ** 2)
                mask = np.exp(-dist * 6)[..., None]
                arr = arr * (1 - 0.35 * mask) + c * (0.35 * mask)
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            draw = ImageDraw.Draw(img)

        if self.sparkle > 0.1:
            for i in range(len(self.sparks_x)):
                tw = 0.4 + 0.6 * abs(np.sin((t + self.sparks_ph[i]) * np.pi * 6))
                if tw < 0.35:
                    continue
                x = int((self.sparks_x[i] + 0.02 * np.sin(t * 2 + i)) % 1.0 * self.width)
                y = int((self.sparks_y[i] + t * 0.08 * (0.5 + self.sparks_ph[i])) % 1.0 * self.height)
                r = int(self.sparks_r[i] * tw)
                col = self.palette.as_uint8(float((self.sparks_ph[i] + t) % 1.0))
                draw.ellipse((x - r, y - r, x + r, y + r), fill=col)
        return img

    def _active_letter_index(self, t: float) -> int:
        if not self.letters:
            return 0
        idx = int(t * len(self.letters) * 0.999)
        return min(idx, len(self.letters) - 1)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))

        img = self._make_background(t)
        draw = ImageDraw.Draw(img)

        if self.mode == "parade":
            self._draw_parade(draw, t, anim)
        elif self.mode in {"focus", "lesson"}:
            self._draw_focus(draw, img, t, anim)
            draw = ImageDraw.Draw(img)
        elif self.mode == "spell":
            self._draw_spell(draw, t, anim)
        else:
            self._draw_chart(draw, t, anim)

        title = {
            "chart": "Alphabet Chart",
            "focus": "Letter Time!",
            "lesson": "Today's Letter",
            "parade": "ABC Parade",
            "spell": f"Spell: {self.spell_word or 'FUN'}",
        }.get(self.mode, "ABC Fun!")
        banner_y = int(self.height * 0.035)
        draw.rounded_rectangle(
            (self.width // 2 - 190, banner_y - 6, self.width // 2 + 190, banner_y + 34),
            radius=16,
            fill=(255, 255, 255),
            outline=(60, 80, 110),
            width=3,
        )
        draw.text((self.width // 2, banner_y + 14), title, font=self.font_sm, fill=(40, 60, 90), anchor="mm")

        arr = np.array(img, dtype=np.uint8, copy=True)
        blur = cv2.GaussianBlur(arr, (0, 0), sigmaX=2.2)
        return cv2.addWeighted(arr, 0.82, blur, 0.18, 0)

    def _cell_center(self, i: int) -> tuple[float, float]:
        row = i // self.cols
        col = i % self.cols
        cell_w = self.width / (self.cols + 0.6)
        cell_h = (self.height * 0.82) / (self.rows + 0.5)
        return 0.3 * cell_w + (col + 0.5) * cell_w, self.height * 0.14 + (row + 0.45) * cell_h

    def _draw_chart(self, draw: ImageDraw.ImageDraw, t: float, anim: float) -> None:
        assert self.palette is not None
        n = len(self.letters)
        for i, letter in enumerate(self.letters):
            reveal = (t * 1.2) - (i / max(1, n)) * 0.85
            scale = self._pop_scale(float(np.clip(reveal, 0, 1)))
            if scale < 0.08:
                continue
            cx, cy = self._cell_center(i)
            bounce = np.sin((t * anim * 4 + self.phases[i]) * np.pi * 2) * self.bounce * self.font_size * 0.12
            wob = np.sin((t * anim * 3 + self.phases[i] * 4) * np.pi) * self.wobble * 10
            x, y = int(cx + wob), int(cy + bounce)
            color = self.palette.as_uint8(float((self.hues[i] + t * 0.15) % 1.0))
            ow = max(3, int(self.outline_w * scale))
            _draw_bubble_letter(draw, letter, (x, y), self.font, color, outline_w=ow)
            if self.show_lowercase and letter.isalpha():
                draw.text(
                    (x + self.font_size // 2, y + self.font_size // 3),
                    letter.lower(),
                    font=self.font_sm,
                    fill=_blend(color, 0.2, (30, 40, 60)),
                    anchor="mm",
                )
            if self.show_motifs and letter in LETTER_WORDS:
                _draw_motif(
                    draw,
                    LETTER_WORDS[letter],
                    x,
                    y + int(self.font_size * 0.55),
                    max(10, int(self.font_size * 0.22 * scale)),
                    color,
                    t + float(self.phases[i]),
                )

    def _draw_focus(self, draw: ImageDraw.ImageDraw, img: Image.Image, t: float, anim: float) -> None:
        assert self.palette is not None
        idx = self._active_letter_index(t)
        letter = self.letters[idx]
        slot = 1.0 / max(1, len(self.letters))
        local = (t - idx * slot) / slot
        scale = self._pop_scale(float(np.clip(local * 3, 0, 1)))
        color = self.palette.as_uint8((float(self.hues[idx % len(self.hues)]) + t * 0.3) % 1.0)
        x, y = self.width // 2, int(self.height * 0.40)
        bounce = int(np.sin(t * anim * np.pi * 5) * 18 * scale)

        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        rw, rh = int(self.width * 0.42), int(self.height * 0.55)
        od.rounded_rectangle(
            (x - rw // 2, y - rh // 2, x + rw // 2, y + rh // 2 + 40),
            radius=28,
            fill=(255, 255, 255, 210),
            outline=(50, 70, 100, 255),
            width=4,
        )
        base = img.convert("RGBA")
        composed = Image.alpha_composite(base, overlay).convert("RGB")
        img.paste(composed)

        draw = ImageDraw.Draw(img)
        _draw_bubble_letter(draw, letter, (x, y + bounce), self.font_lg, color, outline_w=max(8, self.outline_w + 4))
        if self.show_lowercase and letter.isalpha():
            draw.text(
                (x + int(self.width * 0.12), y + bounce + 10),
                letter.lower(),
                font=self.font_md,
                fill=_blend(color, 0.15, (40, 50, 70)),
                anchor="mm",
            )

        word = LETTER_WORDS.get(letter, "FUN")
        draw.text((x, int(self.height * 0.62)), f"{letter} is for {word}", font=self.font_md, fill=(40, 55, 80), anchor="mm")
        _draw_motif(draw, word, x, int(self.height * 0.76), int(min(self.width, self.height) * 0.09 * scale), color, t)

        dots = min(len(self.letters), 26)
        for i in range(dots):
            dx = int(self.width * 0.15 + i * (self.width * 0.7) / max(1, dots - 1))
            r = 5 if i == idx else 3
            fill = color if i == idx else (180, 190, 200)
            draw.ellipse((dx - r, int(self.height * 0.93) - r, dx + r, int(self.height * 0.93) + r), fill=fill)

    def _draw_parade(self, draw: ImageDraw.ImageDraw, t: float, anim: float) -> None:
        assert self.palette is not None
        n = len(self.letters)
        gy = int(self.height * 0.72)
        draw.line((0, gy, self.width, gy), fill=(120, 160, 100), width=6)
        for i, letter in enumerate(self.letters):
            progress = (t * anim * 0.28 + i / max(1, n)) % 1.0
            x = int(progress * (self.width + 160) - 80)
            bounce = abs(np.sin(progress * np.pi * 8 + self.phases[i])) * 28 * self.bounce
            y = int(self.height * 0.48 - bounce)
            color = self.palette.as_uint8(float((self.hues[i] + t) % 1.0))
            _draw_bubble_letter(draw, letter, (x, y), self.font, color, outline_w=self.outline_w)
            if self.show_motifs and letter in LETTER_WORDS:
                _draw_motif(draw, LETTER_WORDS[letter], x, gy - 30, max(12, self.font_size // 4), color, t + i)

    def _draw_spell(self, draw: ImageDraw.ImageDraw, t: float, anim: float) -> None:
        assert self.palette is not None
        word = self.spell_word or "".join(self.letters)
        n = len(self.letters)
        reveal = int(min(n, np.floor(t * n * 1.15) + 1))
        total_w = n * self.font_size * 1.1
        start_x = self.width / 2 - total_w / 2
        for i, letter in enumerate(self.letters[:reveal]):
            local = float(np.clip((t * n * 1.15) - i, 0, 1))
            scale = self._pop_scale(local)
            x = int(start_x + (i + 0.5) * self.font_size * 1.1)
            y = int(self.height * 0.45 + np.sin((t * anim * 3 + i) * np.pi) * 12 * self.bounce)
            color = self.palette.as_uint8(float((self.hues[i % len(self.hues)] + t * 0.2) % 1.0))
            _draw_bubble_letter(draw, letter, (x, y), self.font, color, outline_w=max(3, int(self.outline_w * scale)))
        draw.text((self.width // 2, int(self.height * 0.7)), word, font=self.font_md, fill=(50, 70, 100), anchor="mm")
        if word and word[0] in LETTER_WORDS:
            _draw_motif(
                draw,
                LETTER_WORDS[word[0]],
                self.width // 2,
                int(self.height * 0.82),
                int(min(self.width, self.height) * 0.08),
                self.palette.as_uint8(t % 1.0),
                t,
            )
