"""Flagship documentary & scientific infographic art engine.

Generates high-tech procedural explainer videos featuring:
- Topic-adaptive background atmospheres (space, abyss, cyber, biology)
- Mathematical scientific schematics (orbital systems, depth layers, neural lattices, wave fields, blueprints)
- Glassmorphic HUD data cards with modern typography and corner brackets
- Dynamic metric callout badges with real-time numeric counters
- Multi-segment narrative progression synced with documentary audio
"""

from __future__ import annotations

import math
from typing import Any
import cv2
import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.edit_brain import documentary_shot, director_time, style_motion
from app.art.fonts import load_font, paint_text, wrap_text_lines
from app.art.knowledge_content import build_knowledge_topic


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / max(1e-6, edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


@register_engine
class InfographicExplainerEngine(ArtEngine):
    name = "infographic_explainer"
    description = "Procedural scientific infographic & documentary video generator"

    def _on_setup(self) -> None:
        assert self.rng is not None

        # Load or generate structured knowledge topic
        duration = float(self.params.get("_duration", 30.0))
        topic_data = self.params.get("topic_data")
        if not isinstance(topic_data, dict):
            domain = str(self.params.get("domain") or "all")
            topic_id = self.params.get("topic_id")
            topic_data = build_knowledge_topic(
                self.seed,
                duration,
                domain=domain,
                topic_id=str(topic_id) if topic_id else None,
                params=self.params,
            )
        self.topic: dict[str, Any] = topic_data
        self.params["topic_data"] = topic_data

        # Determine domain-themed visual palette
        domain = self.topic.get("domain", "astronomy")
        if domain == "astronomy":
            self.c_bg_top = (8, 10, 24)
            self.c_bg_bot = (3, 4, 10)
            self.c_accent = (0, 220, 255)       # Cyan
            self.c_secondary = (255, 190, 40)   # Gold/Amber
            self.c_grid = (20, 35, 65)
        elif domain == "earth_science":
            self.c_bg_top = (6, 24, 28)
            self.c_bg_bot = (2, 8, 12)
            self.c_accent = (0, 240, 180)       # Emerald Aqua
            self.c_secondary = (255, 210, 60)   # Sunlight Gold
            self.c_grid = (15, 45, 55)
        elif domain == "technology":
            self.c_bg_top = (12, 14, 28)
            self.c_bg_bot = (4, 5, 12)
            self.c_accent = (0, 210, 255)       # Electric Blue
            self.c_secondary = (180, 100, 255)  # Violet
            self.c_grid = (25, 30, 70)
        else:  # biology
            self.c_bg_top = (10, 22, 18)
            self.c_bg_bot = (3, 8, 6)
            self.c_accent = (80, 240, 130)      # Bio Neon Green
            self.c_secondary = (0, 210, 240)    # Bio Aqua
            self.c_grid = (18, 50, 40)

        # Allow palette override if custom palette supplied
        if self.palette is not None and len(self.palette.colors) >= 3:
            p0 = tuple(int(c * 255) for c in self.palette.colors[0])
            p1 = tuple(int(c * 255) for c in self.palette.colors[1])
            p2 = tuple(int(c * 255) for c in self.palette.colors[2])
            self.c_accent = p1
            self.c_secondary = p2

        # Initialize background particles
        n_particles = 140
        self.p_x = self.rng.random(n_particles).astype(np.float32)
        self.p_y = self.rng.random(n_particles).astype(np.float32)
        self.p_speed = self.rng.uniform(0.015, 0.05, n_particles).astype(np.float32)
        self.p_size = self.rng.uniform(1.0, 2.5, n_particles).astype(np.float32)
        self.p_alpha = self.rng.uniform(0.2, 0.7, n_particles).astype(np.float32)

        # Neural lattice / network nodes if applicable
        n_nodes = 16
        self.node_x = self.rng.uniform(0.12, 0.44, n_nodes).astype(np.float32)
        self.node_y = self.rng.uniform(0.24, 0.82, n_nodes).astype(np.float32)
        self.edges = []
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                dist = np.hypot(self.node_x[i] - self.node_x[j], self.node_y[i] - self.node_y[j])
                if dist < 0.18:
                    self.edges.append((i, j))

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        t_lin = frame_number / max(1, total_frames)
        t = director_time(t_lin, str(self.params.get("edit_feel") or "documentary"))
        sm = style_motion(str(self.params.get("style") or "documentary"))
        t_motion = t * sm.speed

        # 1. Render base gradient background
        frame = self._render_background(t_motion)

        # 2. Convert to PIL for crisp anti-aliased HUD and schematics
        img = Image.fromarray(frame)
        draw = ImageDraw.Draw(img, "RGBA")

        # 3. Render Active Segment Info — linear t so narration stays locked
        segments = list(self.topic.get("segments", []))
        seg_idx = 0
        seg_local = 0.0
        active_seg = segments[0] if segments else {}

        for i, s in enumerate(segments):
            if s["t0"] <= t_lin <= s["t1"] or (i == len(segments) - 1 and t_lin >= s["t0"]):
                seg_idx = i
                active_seg = s
                seg_dur = max(1e-4, s["t1"] - s["t0"])
                seg_local = max(0.0, min(1.0, (t_lin - s["t0"]) / seg_dur))
                break

        # 4. Draw Schematic Visualizer (Left / Center Region)
        schematic_type = self.topic.get("schematic_type", "orbital_system")
        if self.width >= self.height:
            # Landscape layout: Visualizer on left, HUD cards on right
            schematic_box = (
                int(self.width * 0.04),
                int(self.height * 0.16),
                int(self.width * 0.48),
                int(self.height * 0.88),
            )
            card_box = (
                int(self.width * 0.52),
                int(self.height * 0.16),
                int(self.width * 0.96),
                int(self.height * 0.88),
            )
        else:
            # Portrait / Square layout: Visualizer top, Cards bottom
            schematic_box = (
                int(self.width * 0.06),
                int(self.height * 0.14),
                int(self.width * 0.94),
                int(self.height * 0.52),
            )
            card_box = (
                int(self.width * 0.06),
                int(self.height * 0.54),
                int(self.width * 0.94),
                int(self.height * 0.92),
            )

        self._draw_schematic(draw, schematic_type, schematic_box, t_motion, seg_local)

        # 5. Draw Header HUD (Domain tag, Title, Timeline Progress)
        self._draw_header_hud(draw, t_lin, seg_idx, len(segments))

        # 6. Draw Information Cards (Segment Data, Mechanism, Metric Badges)
        self._draw_info_cards(draw, active_seg, card_box, seg_local)

        # 7. Post-process: Convert back and apply subtle vignette
        out = np.array(img.convert("RGB"), dtype=np.uint8)
        return self._apply_vignette(out)

    def _render_background(self, t: float) -> np.ndarray:
        """Create a smooth vertical gradient with drifting particles and tech grid."""
        frame = np.empty((self.height, self.width, 3), dtype=np.uint8)

        # Vertical background gradient
        r = np.linspace(self.c_bg_top[0], self.c_bg_bot[0], self.height, dtype=np.float32)
        g = np.linspace(self.c_bg_top[1], self.c_bg_bot[1], self.height, dtype=np.float32)
        b = np.linspace(self.c_bg_top[2], self.c_bg_bot[2], self.height, dtype=np.float32)
        gradient = np.stack([r, g, b], axis=-1)[:, np.newaxis, :].astype(np.uint8)
        frame[:, :] = gradient

        # Drifting particles
        py = ((self.p_y + t * self.p_speed) % 1.0 * self.height).astype(np.int32)
        px = ((self.p_x + np.sin(t * 2.0 + self.p_speed * 10) * 0.02) % 1.0 * self.width).astype(np.int32)
        for i in range(len(self.p_x)):
            x, y = int(px[i]), int(py[i])
            if 0 <= x < self.width and 0 <= y < self.height:
                alpha = self.p_alpha[i] * (0.6 + 0.4 * np.sin(t * 8.0 + i))
                color = tuple(int(c * alpha) for c in self.c_accent)
                cv2.circle(frame, (x, y), max(1, int(self.p_size[i])), color, -1, lineType=cv2.LINE_AA)

        # Subtle cybernetic scanning laser beam
        scan_y = int(((t * 1.5) % 1.0) * self.height)
        if 0 <= scan_y < self.height:
            cv2.line(
                frame,
                (0, scan_y),
                (self.width, scan_y),
                tuple(min(255, int(c * 0.22)) for c in self.c_accent),
                1,
                lineType=cv2.LINE_AA,
            )

        return frame

    def _draw_header_hud(
        self,
        draw: ImageDraw.ImageDraw,
        t: float,
        seg_idx: int,
        total_segs: int,
    ) -> None:
        """Top HUD bar: domain badge, main topic title, and segment timeline."""
        hud_h = int(self.height * 0.12)
        pad_x = int(self.width * 0.04)

        # Header background strip
        draw.rectangle((0, 0, self.width, hud_h), fill=(5, 8, 16, 200))
        draw.line((0, hud_h, self.width, hud_h), fill=(*self.c_accent, 80), width=1)

        # Domain Badge Pill
        domain_label = str(self.topic.get("domain_label", "SCIENCE")).upper()
        f_badge = load_font(max(11, int(self.height * 0.02)), family="modern")
        draw.rounded_rectangle(
            (pad_x, int(hud_h * 0.18), pad_x + int(self.width * 0.26), int(hud_h * 0.44)),
            radius=4,
            fill=(*self.c_accent, 40),
            outline=(*self.c_accent, 180),
            width=1,
        )
        paint_text(
            draw,
            (pad_x + 8, int(hud_h * 0.31)),
            f"[ {domain_label} ]",
            f_badge,
            (*self.c_accent, 240),
            anchor="lm",
            max_width=int(self.width * 0.25),
        )

        # Main Topic Title
        title = self.topic.get("title", "Informative Explainer")
        f_title = load_font(max(15, int(self.height * 0.038)), family="modern")
        paint_text(
            draw,
            (pad_x, int(hud_h * 0.72)),
            title,
            f_title,
            (245, 248, 255, 255),
            anchor="lm",
            max_width=int(self.width * 0.58),
        )

        # Segment Timeline Steps on the Right
        bar_w = int(self.width * 0.28)
        bar_x = self.width - pad_x - bar_w
        bar_y = int(hud_h * 0.65)
        bar_h = 6

        # Step indicator text: e.g. "PHASE 02 / 04"
        f_step = load_font(max(10, int(self.height * 0.018)), family="modern")
        paint_text(
            draw,
            (bar_x, bar_y - 12),
            f"SECTION {seg_idx + 1:02d} / {total_segs:02d}",
            f_step,
            (*self.c_secondary, 220),
            anchor="ls",
        )

        # Timeline progress track
        draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=3, fill=(30, 40, 60, 180))
        # Active filled portion
        filled_w = int(bar_w * t)
        if filled_w > 2:
            draw.rounded_rectangle(
                (bar_x, bar_y, bar_x + filled_w, bar_y + bar_h),
                radius=3,
                fill=(*self.c_accent, 255),
            )

    def _draw_schematic(
        self,
        draw: ImageDraw.ImageDraw,
        kind: str,
        box: tuple[int, int, int, int],
        t: float,
        seg_local: float,
    ) -> None:
        """Draw interactive mathematical schematics."""
        x0, y0, x1, y1 = box
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2
        w = x1 - x0
        h = y1 - y0
        r_max = int(min(w, h) * 0.42)

        # Schematic frame box & corner brackets
        draw.rectangle((x0, y0, x1, y1), fill=(10, 14, 26, 140), outline=(*self.c_accent, 60), width=1)
        bracket_len = 16
        for bx, by, dx, dy in (
            (x0, y0, 1, 1),
            (x1, y0, -1, 1),
            (x0, y1, 1, -1),
            (x1, y1, -1, -1),
        ):
            draw.line((bx, by, bx + dx * bracket_len, by), fill=(*self.c_accent, 220), width=2)
            draw.line((bx, by, bx, by + dy * bracket_len), fill=(*self.c_accent, 220), width=2)

        # Telemetry Reticle Rings & Crosshair
        draw.ellipse(
            (cx - r_max, cy - r_max, cx + r_max, cy + r_max),
            outline=(*self.c_grid, 120),
            width=1,
        )
        r_mid = int(r_max * 0.65)
        draw.ellipse(
            (cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid),
            outline=(*self.c_grid, 90),
            width=1,
        )
        # Radar sweep ray
        sweep_ang = t * math.pi * 2.0
        draw.line(
            (cx, cy, cx + int(math.cos(sweep_ang) * r_max), cy + int(math.sin(sweep_ang) * r_max)),
            fill=(*self.c_accent, 140),
            width=1,
        )

        if kind == "orbital_system":
            self._draw_orbital_schematic(draw, cx, cy, r_max, t)
        elif kind == "layer_stack":
            self._draw_layer_schematic(draw, x0, y0, x1, y1, t, seg_local)
        elif kind == "network_lattice":
            self._draw_network_schematic(draw, cx, cy, r_max, t)
        elif kind == "quantum_field":
            self._draw_quantum_schematic(draw, cx, cy, r_max, t)
        else:  # spec_blueprint
            self._draw_blueprint_schematic(draw, cx, cy, r_max, t)

    def _draw_orbital_schematic(
        self,
        draw: ImageDraw.ImageDraw,
        cx: int,
        cy: int,
        r_max: int,
        t: float,
    ) -> None:
        """Glowing central body and multiple orbital trajectories."""
        # Core glowing body (Sun / Black Hole / Atom nucleus)
        core_r = max(10, int(r_max * 0.22))
        pulse = 1.0 + 0.08 * math.sin(t * 8.0)
        core_r = int(core_r * pulse)
        # Outer glow
        draw.ellipse(
            (cx - int(core_r * 1.6), cy - int(core_r * 1.6), cx + int(core_r * 1.6), cy + int(core_r * 1.6)),
            fill=(*self.c_secondary, 45),
        )
        # Core body
        draw.ellipse(
            (cx - core_r, cy - core_r, cx + core_r, cy + core_r),
            fill=(*self.c_secondary, 230),
            outline=(255, 255, 255, 240),
            width=2,
        )

        # 3 Orbit rings with elliptical tilt
        radii = (int(r_max * 0.45), int(r_max * 0.72), int(r_max * 0.95))
        speeds = (1.4, -0.9, 0.6)

        for i, (r_orb, spd) in enumerate(zip(radii, speeds)):
            # Orbit ellipse
            draw.ellipse(
                (cx - r_orb, cy - int(r_orb * 0.65), cx + r_orb, cy + int(r_orb * 0.65)),
                outline=(*self.c_accent, 90 + i * 20),
                width=1,
            )
            # Orbiting satellite / particle
            angle = t * math.pi * 2.0 * spd + (i * math.pi / 2.5)
            ox = cx + int(math.cos(angle) * r_orb)
            oy = cy + int(math.sin(angle) * r_orb * 0.65)
            sat_r = max(4, int(r_max * 0.045))
            draw.ellipse(
                (ox - sat_r, oy - sat_r, ox + sat_r, oy + sat_r),
                fill=(*self.c_accent, 240),
                outline=(255, 255, 255, 220),
                width=1,
            )
            # Satellite coordinate cross
            draw.line((ox - 8, oy, ox + 8, oy), fill=(*self.c_accent, 160), width=1)
            draw.line((ox, oy - 8, ox, oy + 8), fill=(*self.c_accent, 160), width=1)

    def _draw_layer_schematic(
        self,
        draw: ImageDraw.ImageDraw,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        t: float,
        seg_local: float,
    ) -> None:
        """Stratified depth/altitude scale with vertical milestones and probe."""
        n_layers = 5
        lh = (y1 - y0) / n_layers
        layer_names = ["Troposphere / Sunlight", "Stratosphere / Twilight", "Mesosphere / Midnight", "Abyss / Hadal", "Trench Floor"]
        f_layer = load_font(max(10, int(self.height * 0.017)), family="modern")

        for i in range(n_layers):
            ly0 = int(y0 + i * lh)
            ly1 = int(y0 + (i + 1) * lh)
            alpha = int(40 + i * 30)
            draw.rectangle((x0 + 8, ly0 + 4, x1 - 8, ly1 - 4), fill=(*self.c_accent, alpha))
            draw.line((x0 + 8, ly0, x1 - 8, ly0), fill=(*self.c_accent, 80), width=1)
            paint_text(
                draw,
                (x0 + 16, ly0 + int(lh * 0.5)),
                f"LEVEL {i+1}: {layer_names[i]}",
                f_layer,
                (220, 240, 255, 210),
                anchor="lm",
            )

        # Depth probe indicator gliding down
        probe_y = int(y0 + (0.15 + 0.7 * ((t * 0.8) % 1.0)) * (y1 - y0))
        draw.line((x0 + 8, probe_y, x1 - 8, probe_y), fill=(*self.c_secondary, 230), width=2)
        draw.polygon(
            [(x1 - 20, probe_y - 6), (x1 - 8, probe_y), (x1 - 20, probe_y + 6)],
            fill=(*self.c_secondary, 255),
        )

    def _draw_network_schematic(
        self,
        draw: ImageDraw.ImageDraw,
        cx: int,
        cy: int,
        r_max: int,
        t: float,
    ) -> None:
        """Neural network nodes and propagating synaptic pulse packets."""
        xs = cx + ((self.node_x - 0.28) * r_max * 2.8).astype(np.int32)
        ys = cy + ((self.node_y - 0.53) * r_max * 2.4).astype(np.int32)

        # Draw connecting synaptic edges
        for i, j in self.edges:
            p1 = (xs[i], ys[i])
            p2 = (xs[j], ys[j])
            draw.line((p1[0], p1[1], p2[0], p2[1]), fill=(*self.c_grid, 120), width=1)
            # Propagating data packet
            pkt_u = (t * 2.0 + (i + j) * 0.15) % 1.0
            px = int(p1[0] + (p2[0] - p1[0]) * pkt_u)
            py = int(p1[1] + (p2[1] - p1[1]) * pkt_u)
            draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(*self.c_accent, 220))

        # Draw neural nodes
        for i in range(len(xs)):
            act = 0.5 + 0.5 * math.sin(t * 10.0 + i * 1.3)
            nr = max(4, int(r_max * 0.04 * (0.8 + 0.4 * act)))
            color = self.c_accent if act > 0.6 else self.c_secondary
            draw.ellipse((xs[i] - nr, ys[i] - nr, xs[i] + nr, ys[i] + nr), fill=(*color, 240), outline=(255, 255, 255, 200), width=1)

    def _draw_quantum_schematic(
        self,
        draw: ImageDraw.ImageDraw,
        cx: int,
        cy: int,
        r_max: int,
        t: float,
    ) -> None:
        """Quantum wave-particle superposition harmonic interference curves."""
        n_pts = 60
        for wave_i in range(3):
            pts = []
            freq = 2.0 + wave_i * 1.5
            phase = t * math.pi * 3.0 + wave_i * 1.2
            amp = r_max * (0.2 + wave_i * 0.1)
            for k in range(n_pts):
                u = k / (n_pts - 1)
                x = cx - r_max + int(u * r_max * 2.0)
                y = cy + int(math.sin(u * math.pi * freq + phase) * amp * math.cos(u * math.pi - math.pi / 2))
                pts.append((x, y))
            for k in range(len(pts) - 1):
                draw.line((pts[k][0], pts[k][1], pts[k+1][0], pts[k+1][1]), fill=(*self.c_accent, 140 + wave_i * 40), width=2)

        # Central quantum probability orb
        orb_r = max(8, int(r_max * 0.18))
        draw.ellipse((cx - orb_r, cy - orb_r, cx + orb_r, cy + orb_r), fill=(*self.c_secondary, 180), outline=(255, 255, 255, 240), width=2)

    def _draw_blueprint_schematic(
        self,
        draw: ImageDraw.ImageDraw,
        cx: int,
        cy: int,
        r_max: int,
        t: float,
    ) -> None:
        """High-tech engineering blueprint with telemetry dials and wireframes."""
        # Hexagonal wireframe mesh
        for r_scale in (0.35, 0.65, 0.95):
            r_curr = int(r_max * r_scale)
            hex_pts = []
            for ang_deg in range(0, 360, 60):
                rad = math.radians(ang_deg + t * 20.0 * (1.0 if r_scale < 0.5 else -1.0))
                hex_pts.append((cx + int(math.cos(rad) * r_curr), cy + int(math.sin(rad) * r_curr)))
            draw.polygon(hex_pts, outline=(*self.c_accent, 130), width=1)

        # Angle degree markings
        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            x_in = cx + int(math.cos(rad) * (r_max - 8))
            y_in = cy + int(math.sin(rad) * (r_max - 8))
            x_out = cx + int(math.cos(rad) * r_max)
            y_out = cy + int(math.sin(rad) * r_max)
            draw.line((x_in, y_in, x_out, y_out), fill=(*self.c_secondary, 180), width=1)

    def _draw_info_cards(
        self,
        draw: ImageDraw.ImageDraw,
        seg: dict[str, Any],
        box: tuple[int, int, int, int],
        seg_local: float,
    ) -> None:
        """Right panel: Glassmorphic cards with headline, body, data callout, and metrics."""
        x0, y0, x1, y1 = box
        w = x1 - x0
        h = y1 - y0

        # Card entry / hold / exit — documentary editor pacing
        shot = documentary_shot(seg_local)
        entry_alpha = shot.entry
        slide_offset = int((1.0 - shot.entry) * 16)

        # --- Main Information Glass Card ---
        main_h = int(h * 0.62)
        card_y0 = y0 + slide_offset
        card_y1 = card_y0 + main_h

        # Glass background fill + glowing border
        draw.rounded_rectangle(
            (x0, card_y0, x1, card_y1),
            radius=8,
            fill=(12, 16, 28, int(210 * entry_alpha)),
            outline=(*self.c_accent, int(180 * entry_alpha)),
            width=1,
        )
        # Tech corner accents on card
        for ax, ay, dx, dy in (
            (x0, card_y0, 1, 1),
            (x1, card_y0, -1, 1),
            (x0, card_y1, 1, -1),
            (x1, card_y1, -1, -1),
        ):
            draw.line((ax, ay, ax + dx * 10, ay), fill=(*self.c_accent, 255), width=2)
            draw.line((ax, ay, ax, ay + dy * 10), fill=(*self.c_accent, 255), width=2)

        pad_in = int(w * 0.05)
        text_w = w - pad_in * 2

        # Phase tag badge: e.g. "PHASE: MECHANISM"
        phase = str(seg.get("phase", "FACT")).upper()
        f_tag = load_font(max(10, int(self.height * 0.018)), family="modern")
        draw.rounded_rectangle(
            (x0 + pad_in, card_y0 + int(main_h * 0.08), x0 + pad_in + int(w * 0.4), card_y0 + int(main_h * 0.18)),
            radius=3,
            fill=(*self.c_secondary, 45),
            outline=(*self.c_secondary, 200),
            width=1,
        )
        paint_text(
            draw,
            (x0 + pad_in + 8, card_y0 + int(main_h * 0.13)),
            f"// {phase}",
            f_tag,
            (*self.c_secondary, 240),
            anchor="lm",
        )

        # Headline
        headline = seg.get("headline", "")
        f_head = load_font(max(14, int(self.height * 0.03)), family="modern")
        paint_text(
            draw,
            (x0 + pad_in, card_y0 + int(main_h * 0.28)),
            headline,
            f_head,
            (255, 255, 255, int(255 * shot.body)),
            anchor="lm",
            max_width=text_w,
        )

        # Multi-line Body Explanation
        body = seg.get("body", "")
        f_body = load_font(max(11, int(self.height * 0.021)), family="modern")
        body_lines = wrap_text_lines(draw, body, f_body, text_w)
        line_y = card_y0 + int(main_h * 0.40)
        line_step = max(16, int(self.height * 0.03))

        for line in body_lines[:4]:
            paint_text(
                draw,
                (x0 + pad_in, line_y),
                line,
                f_body,
                (200, 215, 235, int(240 * shot.body)),
                anchor="lm",
            )
            line_y += line_step

        # Data Point Callout Pill at bottom of card
        data_point = seg.get("data_point", "")
        if data_point:
            callout_y = card_y0 + int(main_h * 0.82)
            draw.rounded_rectangle(
                (x0 + pad_in, callout_y - 12, x1 - pad_in, callout_y + 14),
                radius=4,
                fill=(*self.c_accent, 35),
                outline=(*self.c_accent, 140),
                width=1,
            )
            f_data = load_font(max(10, int(self.height * 0.019)), family="modern")
            paint_text(
                draw,
                (x0 + pad_in + 10, callout_y),
                f"KEY FACT: {data_point}",
                f_data,
                (*self.c_accent, 245),
                anchor="lm",
                max_width=text_w - 20,
            )

        # --- Metric Callout Badges (Lower Row) ---
        metrics = list(self.topic.get("metrics", []))[:2]
        if metrics:
            metric_y0 = card_y1 + int(h * 0.04)
            metric_h = y1 - metric_y0
            card_gap = 10
            single_w = (w - (len(metrics) - 1) * card_gap) // len(metrics)

            f_val = load_font(max(15, int(self.height * 0.034)), family="modern")
            f_lbl = load_font(max(10, int(self.height * 0.017)), family="modern")

            for m_i, m in enumerate(metrics):
                mx0 = x0 + m_i * (single_w + card_gap)
                mx1 = mx0 + single_w

                draw.rounded_rectangle(
                    (mx0, metric_y0, mx1, y1),
                    radius=6,
                    fill=(8, 12, 22, 190),
                    outline=(*self.c_secondary, 130),
                    width=1,
                )
                val_text = str(m.get("val", ""))
                unit_text = str(m.get("unit", ""))
                label_text = str(m.get("label", ""))

                paint_text(
                    draw,
                    (mx0 + int(single_w * 0.08), metric_y0 + int(metric_h * 0.38)),
                    val_text,
                    f_val,
                    (*self.c_secondary, 255),
                    anchor="lm",
                )
                paint_text(
                    draw,
                    (mx0 + int(single_w * 0.08), metric_y0 + int(metric_h * 0.68)),
                    unit_text,
                    f_lbl,
                    (*self.c_accent, 210),
                    anchor="lm",
                    max_width=single_w - 12,
                )
                paint_text(
                    draw,
                    (mx0 + int(single_w * 0.08), metric_y0 + int(metric_h * 0.88)),
                    label_text.upper(),
                    f_lbl,
                    (160, 180, 200, 180),
                    anchor="lm",
                    max_width=single_w - 12,
                )

    def _apply_vignette(self, frame: np.ndarray) -> np.ndarray:
        """Apply smooth edge vignette for cinematic depth."""
        # Fast vignette via corner darkening
        h, w = frame.shape[:2]
        xv = np.linspace(-1.0, 1.0, w, dtype=np.float32)
        yv = np.linspace(-1.0, 1.0, h, dtype=np.float32)
        xx, yy = np.meshgrid(xv, yv)
        dist = np.sqrt(xx * xx + yy * yy)
        vignette = np.clip(1.0 - (dist - 0.75) * 0.45, 0.45, 1.0)[:, :, np.newaxis]
        return (frame * vignette).astype(np.uint8)
