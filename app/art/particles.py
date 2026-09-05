"""Particle universe art engine."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.base import ArtEngine, register_engine
from app.art.edit_brain import beat_pulse, director_time, style_motion


@register_engine
class ParticleUniverseEngine(ArtEngine):
    name = "particles"
    description = "Particle universe with gravity and turbulence"
    parallel_frames = False

    def _on_setup(self) -> None:
        assert self.rng is not None
        n = int(self.params.get("count", 800))
        self.pos = self.rng.random((n, 2), dtype=np.float32)
        self.pos[:, 0] *= self.width
        self.pos[:, 1] *= self.height
        speed = float(self.params.get("speed", 1.0))
        self.vel = (self.rng.random((n, 2), dtype=np.float32) - 0.5) * speed * 4
        # 3-depth plane hierarchy: 0.45 (far background), 0.8 (midground), 1.35 (hero foreground)
        self.depth = self.rng.choice([0.45, 0.80, 1.35], size=n, p=[0.45, 0.40, 0.15]).astype(np.float32)
        base_size = float(self.params.get("size", 2.5))
        self.sizes = (self.rng.uniform(0.6, base_size, size=n) * self.depth).astype(np.float32)
        self.hue = self.rng.random(n, dtype=np.float32)
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        bg = self.palette.as_uint8(0.0) if self.palette else (5, 5, 12)
        self.canvas[:] = bg
        self.cx = self.width * float(self.params.get("focus_x", 0.5))
        self.cy = self.height * float(self.params.get("focus_y", 0.5))

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.rng is not None and self.palette is not None
        trail = float(self.params.get("trail", 0.92))
        gravity = float(self.params.get("gravity", 0.01))
        style_key = str(self.params.get("style") or "abstract")
        sm = style_motion(style_key)
        turb = float(self.params.get("turbulence", 0.5)) * sm.turb
        attract = float(self.params.get("attraction", 0.3)) * sm.speed
        anim = float(self.params.get("animation_speed", 1.0)) * sm.speed

        # Fade trails toward background
        bg = np.array(self.palette.as_uint8(0.0), dtype=np.float32)
        faded = self.canvas.astype(np.float32) * trail + bg * (1.0 - trail)
        self.canvas = np.clip(faded, 0, 255).astype(np.uint8)

        t_lin = frame_number / max(1, total_frames)
        t = director_time(t_lin, str(self.params.get("edit_feel") or "cinematic"))
        pulse = 0.82 + sm.pulse * beat_pulse(
            t_lin,
            float(self.params.get("bpm") or 96.0),
            float(self.params.get("_duration") or 30.0),
        )
        tx = self.cx + np.sin(t * np.pi * 2 * anim * 0.45) * self.width * 0.12
        ty = self.cy + np.cos(t * np.pi * 2 * anim * 0.32) * self.height * 0.10

        dx = tx - self.pos[:, 0]
        dy = ty - self.pos[:, 1]
        dist = np.sqrt(dx * dx + dy * dy) + 1e-3

        # Hydrodynamic curl turbulence
        curl_freq = 0.005
        curl_ang = (
            np.sin(self.pos[:, 1] * curl_freq + t * 2.5) * np.pi
            + np.cos(self.pos[:, 0] * curl_freq - t * 1.8) * np.pi
        )
        curl_vx = np.cos(curl_ang) * turb * 1.6
        curl_vy = np.sin(curl_ang) * turb * 1.6

        self.vel[:, 0] += (dx / dist) * attract * anim * pulse + curl_vx
        self.vel[:, 1] += (dy / dist) * attract * anim * pulse + gravity + curl_vy
        self.vel += (self.rng.random(self.vel.shape, dtype=np.float32) - 0.5) * turb * 0.15
        self.vel *= 0.982

        # Step positions scaled by depth parallax
        step_v = self.vel * (anim * 0.85 * self.depth[:, None])
        old_x = self.pos[:, 0].copy()
        old_y = self.pos[:, 1].copy()
        self.pos += step_v
        self.pos[:, 0] %= self.width
        self.pos[:, 1] %= self.height

        # Plexus network lines for digital / abstract / documentary styles
        if sm.plexus > 0.08:
            n_plexus = min(90, len(self.pos))
            p_sub = self.pos[:n_plexus]
            dists = np.linalg.norm(p_sub[:, None, :] - p_sub[None, :, :], axis=-1)
            max_dist = min(self.width, self.height) * 0.075 * (0.8 + sm.plexus * 0.4)
            close_pairs = np.argwhere((dists > 0.0) & (dists < max_dist))
            for i, j in close_pairs[::2]:  # avoid duplicate reciprocal edges
                if i >= j:
                    continue
                d = dists[i, j]
                alpha = (1.0 - (d / max_dist)) * sm.plexus * 0.55
                if alpha > 0.05:
                    p1 = (int(p_sub[i, 0]), int(p_sub[i, 1]))
                    p2 = (int(p_sub[j, 0]), int(p_sub[j, 1]))
                    # Wrap check to prevent screen-spanning streaks
                    if abs(p1[0] - p2[0]) < self.width * 0.5 and abs(p1[1] - p2[1]) < self.height * 0.5:
                        edge_col = self.palette.as_uint8(float((self.hue[i] + 0.1) % 1.0))
                        line_col = tuple(int(c * alpha) for c in edge_col)
                        cv2.line(self.canvas, p1, p2, line_col, 1, lineType=cv2.LINE_AA)

        xs = np.clip(self.pos[:, 0].astype(np.int32), 0, self.width - 1)
        ys = np.clip(self.pos[:, 1].astype(np.int32), 0, self.height - 1)
        oxs = np.clip(old_x.astype(np.int32), 0, self.width - 1)
        oys = np.clip(old_y.astype(np.int32), 0, self.height - 1)

        for i in range(len(xs)):
            color = self.palette.as_uint8(float((self.hue[i] + t) % 1.0))
            r = max(1, int(round(float(self.sizes[i]))))
            pt = (int(xs[i]), int(ys[i]))
            # Draw motion streaks for fast foreground particles
            if self.depth[i] > 1.0 and abs(xs[i] - oxs[i]) < 40 and abs(ys[i] - oys[i]) < 40:
                cv2.line(self.canvas, (int(oxs[i]), int(oys[i])), pt, color, max(1, r - 1), lineType=cv2.LINE_AA)
            cv2.circle(self.canvas, pt, r, color, -1, lineType=cv2.LINE_AA)

        glow = float(self.params.get("glow", 0.4)) * sm.glow
        if glow > 0.2:
            blur = cv2.GaussianBlur(self.canvas, (0, 0), sigmaX=2 + glow * 3)
            return cv2.addWeighted(self.canvas, 0.75, blur, 0.45, 0)
        return self.canvas.copy()
