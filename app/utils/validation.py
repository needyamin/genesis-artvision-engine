"""Configuration loading and validation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from app.utils.paths import project_root


DEFAULT_CONFIG: dict[str, Any] = {
    "resolution": "1920x1080",
    "fps": 30,
    "duration": {"min": 15, "max": 60, "default": 30, "options": [10, 15, 30, 60, 120]},
    "batch": {"default_count": 10},
    "audio": {"enabled": True, "sample_rate": 44100},
    "output": {
        "directory": "./output",
        "thumbnail": True,
        "bitrate": "8M",
        "bitrate_4k": "35M",
        "audio_bitrate": "192k",
    },
    "temp": {"directory": "./temp", "keep_on_failure": True},
    "performance": {"workers": "auto", "preview_scale": 0.25, "max_preview_fps": 15},
    "logging": {"level": "INFO", "directory": "./logs"},
    "database": {"path": "./data/history.db"},
    "styles": [
        "abstract",
        "cosmic",
        "minimal",
        "organic",
        "digital",
        "playful",
        "documentary",
    ],
    "engines": [
        "particles",
        "galaxy",
        "waves",
        "tunnel",
        "alphabet_cartoon",
        "hand_art",
        "kids_doodles",
        "infographic_explainer",
    ],
    "resolutions": [
        "1920x1080",
        "3840x2160",
        "1080x1920",
        "2160x3840",
        "1080x1080",
        "2160x2160",
    ],
    "fps_options": [24, 30, 60],
    "ai": {
        "enabled": False,
        "provider": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-4o-mini",
        "timeout_sec": 20,
        "cache_dir": "./data/ai_cache",
        "catalog_dir": "./data/ai_catalogs",
        "per_video": False,
    },
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into a copy of base."""
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def parse_resolution(value: str) -> tuple[int, int]:
    """Parse 'WIDTHxHEIGHT' into integers."""
    text = value.strip().lower().replace(" ", "").replace("×", "x")
    if "x" not in text:
        raise ValueError(f"Invalid resolution: {value}")
    w_str, h_str = text.split("x", 1)
    width, height = int(w_str), int(h_str)
    if width < 16 or height < 16 or width > 7680 or height > 7680:
        raise ValueError(f"Unsupported resolution: {value}")
    return width, height


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML config merged over defaults."""
    cfg_path = Path(path) if path else project_root() / "config.yaml"
    loaded: dict[str, Any] = {}
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh) or {}
    config = deep_merge(DEFAULT_CONFIG, loaded)
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    """Raise ValueError on invalid configuration values."""
    parse_resolution(str(config.get("resolution", "1920x1080")))
    fps = int(config.get("fps", 30))
    if fps < 1 or fps > 120:
        raise ValueError(f"Invalid fps: {fps}")
    duration = config.get("duration", {})
    if int(duration.get("min", 1)) > int(duration.get("max", 120)):
        raise ValueError("duration.min must be <= duration.max")
    for res in config.get("resolutions", []):
        parse_resolution(str(res))
