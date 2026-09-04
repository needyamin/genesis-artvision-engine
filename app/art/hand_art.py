"""Hand-drawn / doodle art engine — sketchy random drawings."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.base import ArtEngine, register_engine


def _wobble_polyline(
    pts: np.ndarray,
    rng: np.random.Generator,
    amount: float = 2.0,
) -> np.ndarray:
    """Add hand-drawn jitter to a polyline."""
    noise = (rng.random(pts.shape) - 0.5) * amount
    return pts + noise


def _hand_circle(cx: float, cy: float, r: float, n: int = 36) -> np.ndarray:
    a = np.linspace(0, 2 * np.pi, n, endpoint=True)
    return np.column_stack([cx + np.cos(a) * r, cy + np.sin(a) * r])


def _hand_star(cx: float, cy: float, r: float) -> np.ndarray:
    pts = []
    for i in range(10):
        ang = -np.pi / 2 + i * np.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append([cx + np.cos(ang) * rad, cy + np.sin(ang) * rad])
    pts.append(pts[0])
    return np.asarray(pts, dtype=np.float32)


@register_engine
class HandArtEngine(ArtEngine):
    """Random hand-art doodles: sketches, stick figures, scribbles."""

    name = "hand_art"
    description = "Hand-drawn random doodles and sketchy illustrations"

    def _on_setup(self) -> None:
        assert self.rng is not None
        n = int(self.params.get("doodle_count", 14))
        self.kinds = [
            "scribble",
            "star",
            "sun",
            "flower",
            "house",
            "stick",
            "spiral",
            "heart",
            "cloud",
            "zigzag",
        ]
        self.doodles = []
        for _ in range(n):
            kind = str(self.rng.choice(self.kinds))
            self.doodles.append(
                {
                    "kind": kind,
                    "x": float(self.rng.uniform(0.08, 0.92)),
                    "y": float(self.rng.uniform(0.12, 0.88)),
                    "scale": float(self.rng.uniform(0.04, 0.14)),
                    "hue": float(self.rng.random()),
                    "phase": float(self.rng.random() * np.pi * 2),
                    "spin": float(self.rng.uniform(-1.0, 1.0)),
                    "seed": int(self.rng.integers(1, 1_000_000)),
                }
            )
        self.stroke = max(1, int(self.params.get("stroke_width", 2)))
        self.sketchiness = float(self.params.get("sketchiness", 0.7))
        self.paper_grain = float(self.params.get("paper_grain", 0.35))
        # Trail canvas for growing doodles
        self.canvas = None

    def _paper(self) -> np.ndarray:
        assert self.palette is not None and self.rng is not None
        base = np.array(self.palette.as_uint8(0.05), dtype=np.float32)
        # Cream paper lean
        paper = np.full((self.height, self.width, 3), [236, 228, 210], dtype=np.float32)
        paper = paper * 0.75 + base * 0.25
        if self.paper_grain > 0.05:
            grain = self.rng.normal(0, 6 * self.paper_grain, (self.height, self.width, 1)).astype(np.float32)
            paper = paper + grain
        return np.clip(paper, 0, 255).astype(np.uint8)

    def _stroke(self, img: np.ndarray, pts: np.ndarray, color: tuple[int, int, int], rng: np.random.Generator) -> None:
        if len(pts) < 2:
            return
        wob = _wobble_polyline(pts.astype(np.float32), rng, amount=1.2 + self.sketchiness * 2.5)
        # Double-pass for hand-ink feel
        arr = wob.astype(np.int32)
        cv2.polylines(img, [arr], False, color, self.stroke + 1, lineType=cv2.LINE_AA)
        faint = tuple(min(255, c + 40) for c in color)
        cv2.polylines(img, [arr], False, faint, max(1, self.stroke), lineType=cv2.LINE_AA)

    def _draw_doodle(
        self,
        img: np.ndarray,
        d: dict,
        t: float,
        anim: float,
    ) -> None:
        assert self.palette is not None
        rng = np.random.default_rng(d["seed"] + int(t * 40))
        cx = d["x"] * self.width + np.sin(t * anim * 2 + d["phase"]) * 8
        cy = d["y"] * self.height + np.cos(t * anim * 1.5 + d["phase"]) * 6
        s = d["scale"] * min(self.width, self.height) * (0.9 + 0.1 * np.sin(t * 4 + d["phase"]))
        color = self.palette.as_uint8((d["hue"] + t * 0.15) % 1.0)
        # Darker ink-like
        color = tuple(max(0, int(c * 0.75)) for c in color)
        kind = d["kind"]

        if kind == "scribble":
            n = 20
            ang = np.linspace(0, 4 * np.pi, n) + d["phase"] + t * anim * d["spin"]
            rad = np.linspace(s * 0.2, s, n)
            pts = np.column_stack([cx + np.cos(ang) * rad, cy + np.sin(ang) * rad])
            self._stroke(img, pts, color, rng)
        elif kind == "spiral":
            n = 60
            ang = np.linspace(0, 5 * np.pi, n) + t * anim * 2
            rad = np.linspace(2, s, n)
            pts = np.column_stack([cx + np.cos(ang) * rad, cy + np.sin(ang) * rad])
            self._stroke(img, pts, color, rng)
        elif kind == "star":
            pts = _hand_star(cx, cy, s)
            self._stroke(img, pts, color, rng)
        elif kind == "sun":
            pts = _hand_circle(cx, cy, s * 0.45)
            self._stroke(img, pts, color, rng)
            for a in range(0, 360, 30):
                rad = np.radians(a + t * 40 * d["spin"])
                p0 = np.array([[cx + np.cos(rad) * s * 0.55, cy + np.sin(rad) * s * 0.55]])
                p1 = np.array([[cx + np.cos(rad) * s, cy + np.sin(rad) * s]])
                self._stroke(img, np.vstack([p0, p1]), color, rng)
        elif kind == "flower":
            for k in range(6):
                ang = k * np.pi / 3 + t * anim
                px = cx + np.cos(ang) * s * 0.55
                py = cy + np.sin(ang) * s * 0.55
                self._stroke(img, _hand_circle(px, py, s * 0.28), color, rng)
            self._stroke(img, _hand_circle(cx, cy, s * 0.2), color, rng)
        elif kind == "house":
            base = np.array(
                [
                    [cx - s, cy + s * 0.6],
                    [cx + s, cy + s * 0.6],
                    [cx + s, cy - s * 0.1],
                    [cx - s, cy - s * 0.1],
                    [cx - s, cy + s * 0.6],
                ],
                dtype=np.float32,
            )
            roof = np.array(
                [[cx - s, cy - s * 0.1], [cx, cy - s], [cx + s, cy - s * 0.1]],
                dtype=np.float32,
            )
            self._stroke(img, base, color, rng)
            self._stroke(img, roof, color, rng)
        elif kind == "stick":
            # Stick figure
            head = _hand_circle(cx, cy - s * 0.55, s * 0.22)
            body = np.array([[cx, cy - s * 0.3], [cx, cy + s * 0.35]], dtype=np.float32)
            arms = np.array([[cx - s * 0.45, cy], [cx + s * 0.45, cy]], dtype=np.float32)
            leg1 = np.array([[cx, cy + s * 0.35], [cx - s * 0.35, cy + s * 0.85]], dtype=np.float32)
            leg2 = np.array([[cx, cy + s * 0.35], [cx + s * 0.35, cy + s * 0.85]], dtype=np.float32)
            for poly in (head, body, arms, leg1, leg2):
                self._stroke(img, poly, color, rng)
        elif kind == "heart":
            a = np.linspace(0, 2 * np.pi, 50)
            x = cx + s * 0.08 * (16 * np.sin(a) ** 3)
            y = cy - s * 0.08 * (13 * np.cos(a) - 5 * np.cos(2 * a) - 2 * np.cos(3 * a) - np.cos(4 * a))
            self._stroke(img, np.column_stack([x, y]), color, rng)
        elif kind == "cloud":
            for ox, oy, rr in ((-0.4, 0.0, 0.35), (0.0, -0.15, 0.42), (0.4, 0.0, 0.35), (0.0, 0.15, 0.3)):
                self._stroke(img, _hand_circle(cx + ox * s, cy + oy * s, rr * s), color, rng)
        else:  # zigzag
            xs = np.linspace(cx - s, cx + s, 9)
            ys = cy + np.resize([ -s * 0.35, s * 0.35], 9)
            self._stroke(img, np.column_stack([xs, ys]), color, rng)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        img = self._paper()

        # Progressive reveal for "drawing over time" feel
        reveal = 0.25 + 0.75 * min(1.0, t * 1.25)
        count = max(1, int(len(self.doodles) * reveal))

        # Occasional freehand scribble across page
        if self.params.get("margin_scribbles", True):
            rng = np.random.default_rng(self.seed + 7)
            for k in range(3):
                y = self.height * (0.15 + 0.3 * k) + np.sin(t * 3 + k) * 10
                xs = np.linspace(20, self.width - 20, 40)
                ys = y + np.sin(xs * 0.02 + t * 4 + k) * (8 + 6 * k)
                color = (90, 90, 110)
                self._stroke(img, np.column_stack([xs, ys]), color, rng)

        for d in self.doodles[:count]:
            self._draw_doodle(img, d, t, anim)

        # Growing signature-like swirl in corner
        rng = np.random.default_rng(self.seed)
        sig_t = np.linspace(0, t * 4 * np.pi, max(4, int(30 * t) + 2))
        sx = self.width * 0.78 + np.cos(sig_t) * 40
        sy = self.height * 0.88 + np.sin(sig_t * 1.3) * 18
        self._stroke(img, np.column_stack([sx, sy]), (70, 70, 90), rng)
        return img
