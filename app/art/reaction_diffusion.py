"""Gray-Scott reaction-diffusion art engine."""

from __future__ import annotations

import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class ReactionDiffusionEngine(ArtEngine):
    name = "reaction_diffusion"
    description = "Gray-Scott reaction-diffusion patterns"

    def _on_setup(self) -> None:
        assert self.rng is not None
        scale = float(self.params.get("scale", 1.0))
        self.rw = max(64, min(self.width, int(240 * scale)))
        self.rh = max(64, int(self.rw * self.height / self.width))
        self.A = np.ones((self.rh, self.rw), dtype=np.float32)
        self.B = np.zeros((self.rh, self.rw), dtype=np.float32)
        # Seed blobs
        for _ in range(int(self.rng.integers(3, 10))):
            cx = int(self.rng.integers(10, self.rw - 10))
            cy = int(self.rng.integers(10, self.rh - 10))
            r = int(self.rng.integers(3, 12))
            self.B[cy - r : cy + r, cx - r : cx + r] = 1.0
        self.feed = float(self.params.get("feed", 0.04))
        self.kill = float(self.params.get("kill", 0.06))
        self.da = float(self.params.get("diffusion_a", 1.0))
        self.db = float(self.params.get("diffusion_b", 0.5))
        self.steps = int(self.params.get("steps_per_frame", 8))

    @staticmethod
    def _laplacian(z: np.ndarray) -> np.ndarray:
        return (
            np.roll(z, 1, 0)
            + np.roll(z, -1, 0)
            + np.roll(z, 1, 1)
            + np.roll(z, -1, 1)
            - 4 * z
        )

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        dt = 1.0
        for _ in range(self.steps):
            la = self._laplacian(self.A)
            lb = self._laplacian(self.B)
            abb = self.A * self.B * self.B
            self.A += (self.da * la - abb + self.feed * (1 - self.A)) * dt
            self.B += (self.db * lb + abb - (self.kill + self.feed) * self.B) * dt
            np.clip(self.A, 0, 1, out=self.A)
            np.clip(self.B, 0, 1, out=self.B)

        val = self.B
        lut = self.palette.array(256)
        idx = np.clip(((val + t * 0.1) % 1.0) * 255, 0, 255).astype(np.int32)
        small = lut[idx] * (0.3 + 0.7 * val)[..., None]
        y_idx = (np.linspace(0, self.rh - 1, self.height)).astype(np.int32)
        x_idx = (np.linspace(0, self.rw - 1, self.width)).astype(np.int32)
        frame = small[y_idx][:, x_idx]
        return self._to_uint8(frame * float(self.params.get("contrast", 0.9)))
