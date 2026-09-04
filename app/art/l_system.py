"""L-System / procedural plant art engine."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.base import ArtEngine, register_engine


def _expand_lsystem(axiom: str, rules: dict[str, str], iterations: int) -> str:
    s = axiom
    for _ in range(iterations):
        s = "".join(rules.get(ch, ch) for ch in s)
        if len(s) > 5000:
            break
    return s


@register_engine
class LSystemEngine(ArtEngine):
    name = "l_system"
    description = "Animated L-system plant / fractal trees"

    def _on_setup(self) -> None:
        assert self.rng is not None
        variants = [
            ("F", {"F": "F[+F]F[-F]F"}, 25.0),
            ("F", {"F": "FF+[+F-F-F]-[-F+F+F]"}, 22.5),
            ("X", {"X": "F[+X][-X]FX", "F": "FF"}, 30.0),
            ("F", {"F": "F[+F][-F]"}, 35.0),
        ]
        axiom, rules, default_angle = variants[int(self.rng.integers(0, len(variants)))]
        iters = int(self.params.get("iterations", 4))
        self.sequence = _expand_lsystem(axiom, rules, iters)
        self.base_angle = float(self.params.get("angle", default_angle))
        self.length_scale = float(self.params.get("length_scale", 0.55))
        self.branch_count = int(self.params.get("branch_count", 2))

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        wind = float(self.params.get("wind", 0.4)) * np.sin(t * np.pi * 2 * anim)
        angle = self.base_angle + wind * 8

        img = self._to_uint8(self._blank())
        progress = 0.3 + 0.7 * min(1.0, t * 1.4)  # grow over time
        max_cmds = max(1, int(len(self.sequence) * progress))

        for b in range(max(1, self.branch_count)):
            x = self.width * (0.3 + 0.4 * (b + 0.5) / max(1, self.branch_count))
            y = self.height * 0.95
            heading = -90.0 + wind * 5 + (b - self.branch_count / 2) * 8
            stack: list[tuple[float, float, float, float]] = []
            length = min(self.width, self.height) * 0.12
            depth = 0
            for ch in self.sequence[:max_cmds]:
                if ch == "F":
                    rad = np.radians(heading)
                    nx = x + np.cos(rad) * length
                    ny = y + np.sin(rad) * length
                    color = self.palette.as_uint8((0.2 + depth * 0.07 + t) % 1.0)
                    thickness = max(1, 4 - depth // 2)
                    cv2.line(
                        img,
                        (int(x), int(y)),
                        (int(nx), int(ny)),
                        color,
                        thickness,
                        lineType=cv2.LINE_AA,
                    )
                    x, y = nx, ny
                elif ch == "+":
                    heading += angle
                elif ch == "-":
                    heading -= angle
                elif ch == "[":
                    stack.append((x, y, heading, length))
                    length *= self.length_scale
                    depth += 1
                elif ch == "]":
                    if stack:
                        x, y, heading, length = stack.pop()
                        depth = max(0, depth - 1)
        return img
