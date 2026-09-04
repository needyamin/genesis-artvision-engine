"""Central randomization system with deterministic seeding."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.art.palette import Palette, generate_palette
from app.art.styles import list_styles, preferred_engines, sample_style_multiplier
from app.utils.validation import parse_resolution


@dataclass
class ProjectSpec:
    """Fully specified randomized project ready for rendering."""

    project_id: str
    seed: int
    engine: str
    style: str
    width: int
    height: int
    fps: int
    duration: float
    params: dict[str, Any] = field(default_factory=dict)
    palette_name: str = ""
    palette_colors: list[list[float]] = field(default_factory=list)
    audio_enabled: bool = True
    thumbnail: bool = True

    @property
    def total_frames(self) -> int:
        return max(1, int(round(self.duration * self.fps)))

    def palette(self) -> Palette:
        colors = tuple(tuple(c) for c in self.palette_colors)  # type: ignore[misc]
        return Palette(name=self.palette_name, colors=colors)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "seed": self.seed,
            "engine": self.engine,
            "style": self.style,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "duration": self.duration,
            "params": self.params,
            "palette_name": self.palette_name,
            "palette_colors": self.palette_colors,
            "audio_enabled": self.audio_enabled,
            "thumbnail": self.thumbnail,
        }


# Per-engine parameter ranges (min, max) or discrete choices
ENGINE_PARAM_SPECS: dict[str, dict[str, Any]] = {
    "particles": {
        "count": (200, 1200),
        "size": (1.0, 5.0),
        "speed": (0.3, 2.5),
        "gravity": (-0.02, 0.05),
        "turbulence": (0.0, 1.5),
        "trail": (0.85, 0.98),
        "attraction": (0.0, 0.8),
    },
    "galaxy": {
        "star_count": (400, 2200),
        "arm_count": (2, 6),
        "spin": (0.1, 1.2),
        "noise_strength": (0.1, 0.8),
        "core_glow": (0.3, 1.0),
        "drift": (0.05, 0.4),
    },
    "fractal": {
        "iterations": (3, 6),
        "zoom_speed": (0.2, 1.5),
        "rotation_speed": (0.1, 1.0),
        "bailout": (2.0, 8.0),
        "color_speed": (0.2, 1.5),
    },
    "mandelbrot": {
        "max_iter": (30, 80),
        "zoom_speed": (0.15, 0.8),
        "pan_x": (-0.8, 0.4),
        "pan_y": (-0.5, 0.5),
        "color_cycle": (0.3, 2.0),
    },
    "julia": {
        "max_iter": (30, 80),
        "cx_amp": (0.2, 0.8),
        "cy_amp": (0.2, 0.8),
        "zoom": (0.8, 1.6),
        "color_cycle": (0.3, 2.0),
    },
    "kaleidoscope": {
        "segments": (4, 16),
        "layers": (2, 6),
        "spin": (0.2, 1.5),
        "pulse": (0.2, 1.2),
        "complexity": (0.3, 1.0),
    },
    "geometric": {
        "shape_count": (5, 40),
        "rotation_speed": (0.1, 1.5),
        "size_variance": (0.2, 1.0),
        "line_width": (1.0, 4.0),
        "filled_ratio": (0.2, 0.8),
    },
    "flow_field": {
        "particle_count": (300, 1200),
        "noise_scale": (0.001, 0.01),
        "strength": (0.5, 3.0),
        "trail": (0.88, 0.98),
        "z_speed": (0.002, 0.02),
    },
    "waves": {
        "layers": (2, 7),
        "frequency": (0.5, 3.0),
        "amplitude": (0.05, 0.35),
        "speed": (0.3, 1.8),
        "distortion": (0.0, 0.8),
    },
    "tunnel": {
        "rings": (12, 48),
        "spokes": (8, 36),
        "speed": (0.5, 2.5),
        "twist": (0.0, 2.0),
        "pulse": (0.2, 1.2),
    },
    "voronoi": {
        "sites": (12, 50),
        "speed": (0.2, 1.2),
        "edge_width": (0.01, 0.08),
        "fill_mode": ["solid", "gradient", "distance"],
        "morph": (0.2, 1.0),
    },
    "reaction_diffusion": {
        "feed": (0.02, 0.08),
        "kill": (0.045, 0.07),
        "diffusion_a": (0.8, 1.2),
        "diffusion_b": (0.3, 0.6),
        "steps_per_frame": (2, 8),
        "scale": (0.5, 1.2),
    },
    "noise": {
        "octaves": (2, 5),
        "lacunarity": (1.8, 2.8),
        "gain": (0.4, 0.7),
        "speed": (0.2, 1.5),
        "warp": (0.0, 1.2),
        "contrast": (0.5, 1.5),
    },
    "l_system": {
        "iterations": (3, 5),
        "angle": (15.0, 45.0),
        "length_scale": (0.4, 0.75),
        "wind": (0.0, 1.0),
        "branch_count": (1, 3),
    },
    "neon_lines": {
        "line_count": (8, 40),
        "thickness": (1.5, 5.0),
        "speed": (0.4, 2.0),
        "glow": (0.5, 1.0),
        "chaos": (0.1, 1.0),
    },
    "particle_trails": {
        "count": (40, 120),
        "trail_length": (20, 60),
        "speed": (0.5, 2.5),
        "curl": (0.2, 2.0),
        "size": (1.0, 4.0),
    },
    "alphabet_cartoon": {
        "mode": ["chart", "focus", "parade", "lesson", "spell"],
        "columns": (5, 8),
        "bounce": (0.4, 1.0),
        "wobble": (0.2, 0.9),
        "letter_scale": (0.09, 0.15),
        "include_numbers": [False, False, True],
        "show_motifs": [True, True, False],
        "show_lowercase": [True, True, False],
        "background": ["notebook", "sky", "classroom", "pastel"],
        "sparkle": (0.3, 1.0),
        "pop_in": [True, True, False],
    },
    "hand_art": {
        "doodle_count": (8, 22),
        "stroke_width": (1, 4),
        "sketchiness": (0.3, 1.0),
        "paper_grain": (0.15, 0.55),
        "margin_scribbles": [True, True, False],
    },
    "kids_doodles": {
        "shape_count": (10, 28),
        "board_mode": ["colorful", "colorful", "chalkboard"],
    },
}


class Randomizer:
    """Creates reproducible ProjectSpec instances from seeds and config."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.engines = list(config.get("engines") or list(ENGINE_PARAM_SPECS.keys()))
        self.styles = list(config.get("styles") or list_styles())

    @staticmethod
    def new_seed() -> int:
        return secrets.randbelow(2**31 - 1) + 1

    def create_project(
        self,
        seed: int | None = None,
        *,
        engine: str | None = None,
        style: str | None = None,
        resolution: str | None = None,
        fps: int | None = None,
        duration: float | None = None,
        audio_enabled: bool | None = None,
        thumbnail: bool | None = None,
        random_resolution: bool = False,
        random_fps: bool = False,
        random_duration: bool = False,
    ) -> ProjectSpec:
        seed = int(seed) if seed is not None else self.new_seed()
        rng = np.random.default_rng(seed)

        style_name = style or str(rng.choice(self.styles))
        preferred = preferred_engines(style_name)
        engine_pool = [e for e in (preferred or self.engines) if e in self.engines] or self.engines
        engine_name = engine or str(rng.choice(engine_pool))

        if random_resolution or resolution in (None, "random", "Random"):
            res = str(rng.choice(self.config.get("resolutions", ["1920x1080"])))
        else:
            res = resolution or str(self.config.get("resolution", "1920x1080"))
        width, height = parse_resolution(res)

        if random_fps or fps is None:
            # When explicitly random or omitted with random mode, pick from options
            if random_fps:
                fps_val = int(rng.choice(self.config.get("fps_options", [24, 30, 60])))
            else:
                fps_val = int(self.config.get("fps", 30))
        else:
            fps_val = int(fps)

        dur_cfg = self.config.get("duration", {})
        if random_duration or duration is None:
            if random_duration:
                options = list(dur_cfg.get("options", [10, 15, 30, 60]))
                duration_val = float(rng.choice(options))
            else:
                duration_val = float(dur_cfg.get("default", 30))
        else:
            duration_val = float(duration)

        multipliers = sample_style_multiplier(rng, style_name)
        params = self._sample_engine_params(rng, engine_name, multipliers)
        params["style_multipliers"] = multipliers
        params["blur"] = float(rng.uniform(0.0, 0.6) * multipliers["glow"])
        params["glow"] = multipliers["glow"]
        params["animation_speed"] = multipliers["speed"]
        params["contrast"] = multipliers["contrast"]

        palette = generate_palette(rng, style_name)

        project_id = f"art_{seed:08d}"
        audio = (
            self.config.get("audio", {}).get("enabled", True)
            if audio_enabled is None
            else audio_enabled
        )
        thumbs = (
            self.config.get("output", {}).get("thumbnail", True)
            if thumbnail is None
            else thumbnail
        )

        return ProjectSpec(
            project_id=project_id,
            seed=seed,
            engine=engine_name,
            style=style_name,
            width=width,
            height=height,
            fps=fps_val,
            duration=duration_val,
            params=params,
            palette_name=palette.name,
            palette_colors=[list(c) for c in palette.colors],
            audio_enabled=bool(audio),
            thumbnail=bool(thumbs),
        )

    def _sample_engine_params(
        self,
        rng: np.random.Generator,
        engine: str,
        multipliers: dict[str, float],
    ) -> dict[str, Any]:
        specs = ENGINE_PARAM_SPECS.get(engine, {})
        params: dict[str, Any] = {}
        density = multipliers.get("density", 0.6)
        speed_m = multipliers.get("speed", 1.0)

        for key, spec in specs.items():
            if isinstance(spec, list):
                choice = rng.choice(np.asarray(spec, dtype=object))
                params[key] = choice.item() if hasattr(choice, "item") else choice
                if isinstance(spec[0], str):
                    params[key] = str(params[key])
                elif isinstance(spec[0], bool):
                    params[key] = bool(params[key])
                continue
            lo, hi = spec
            # Bias density-related counts upward/downward
            if key in {
                "count",
                "star_count",
                "particle_count",
                "shape_count",
                "sites",
                "line_count",
                "rings",
                "layers",
            }:
                mid = lo + (hi - lo) * density
                span = (hi - lo) * 0.25
                value = float(rng.uniform(max(lo, mid - span), min(hi, mid + span)))
            elif key in {"speed", "spin", "zoom_speed", "rotation_speed", "z_speed", "drift"}:
                mid = lo + (hi - lo) * min(1.0, speed_m / 1.5)
                span = (hi - lo) * 0.3
                value = float(rng.uniform(max(lo, mid - span), min(hi, mid + span)))
            else:
                value = float(rng.uniform(lo, hi))

            if isinstance(lo, int) and isinstance(hi, int):
                params[key] = int(round(value))
            else:
                params[key] = value
        return params
