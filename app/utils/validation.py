"""Configuration loading and validation."""

from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path
from typing import Any

import yaml

from app.art.visual_variants import (
    BACKGROUND_VARIANTS,
    LAYOUT_VARIANTS,
    VISUAL_VARIANT_VERSION,
)
from app.utils.paths import project_root


DEFAULT_CONFIG: dict[str, Any] = {
    "resolution": "1920x1080",
    "fps": 30,
    "duration": {"min": 15, "max": 600, "default": 30, "options": [10, 15, 30, 60, 120, 180, 300, 600]},
    "batch": {"default_count": 10},
    "audio": {"enabled": True, "sample_rate": 44100, "target_lufs": -14.0, "ceiling_dbfs": -1.0},
    "editing": {
        "default_preset": "standard",
        "presets": {
            "draft": {"motion_scale": 0.65, "quality": "draft", "caption_mode": "sidecar"},
            "standard": {"motion_scale": 1.0, "quality": "standard", "caption_mode": "sidecar"},
            "master": {"motion_scale": 1.15, "quality": "master", "caption_mode": "both"},
        },
    },
    "qc": {
        "enabled": True,
        "max_av_drift_sec": 0.35,
        "min_lufs": -35.0,
        "clipping_peak_dbfs": -0.1,
        "max_silence_fraction": 0.8,
        "max_black_fraction": 0.25,
        "max_frozen_fraction": 0.75,
        "frame_samples": 12,
    },
    "output": {
        "directory": "./output",
        "thumbnail": True,
        "bitrate": "8M",
        "bitrate_4k": "35M",
        "audio_bitrate": "192k",
    },
    "temp": {"directory": "./temp", "keep_on_failure": True},
    "performance": {"workers": "auto", "hardware_encode": True, "preview_scale": 0.25, "max_preview_fps": 4},
    "logging": {"level": "INFO", "directory": "./logs"},
    "database": {"path": "./data/history.db"},
    "styles": [
        "storybook",
        "classroom",
        "pulse",
    ],
    "engines": [
        "kids_storybook",
        "how_it_works",
        "trend_brief",
    ],
    "visual_variation": {
        "enabled": True,
        "version": VISUAL_VARIANT_VERSION,
        "backgrounds": {
            engine: {name: 1.0 for name in names}
            for engine, names in BACKGROUND_VARIANTS.items()
        },
        "layouts": {
            engine: {name: 1.0 for name in names}
            for engine, names in LAYOUT_VARIANTS.items()
        },
    },
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
    "youtube": {
        "enabled": False,
        "privacy": "unlisted",
        "daily_limit": 6,
        "client_secret": "./data/youtube/client_secret.json",
        "token": "./data/youtube/token.json",
    },
    "trend_feed": {
        "enabled": True,
        "cache_dir": "./data/trend_cache",
        "cache_minutes": 45,
        "timeout_sec": 12,
        "rss_urls": [
            "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "https://trends.google.com/trending/rss?geo=US",
            "https://feeds.bbci.co.uk/news/rss.xml",
            "https://feeds.npr.org/1001/rss.xml",
        ],
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
    editing = config.get("editing") or {}
    presets = editing.get("presets") or {}
    default_preset = str(editing.get("default_preset") or "standard")
    if default_preset not in presets:
        raise ValueError(f"editing.default_preset is not defined: {default_preset}")
    for name, preset in presets.items():
        mode = str((preset or {}).get("caption_mode") or "sidecar")
        if mode not in {"off", "sidecar", "burn", "both"}:
            raise ValueError(f"editing.presets.{name}.caption_mode is invalid: {mode}")
    _validate_visual_variation(config.get("visual_variation", {}))
    _validate_trend_feed(config.get("trend_feed", {}))


def _validate_visual_variation(config: Any) -> None:
    if not isinstance(config, dict):
        raise ValueError("visual_variation must be a mapping")
    enabled = config.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("visual_variation.enabled must be true or false")
    version = config.get("version", VISUAL_VARIANT_VERSION)
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ValueError("visual_variation.version must be a positive integer")

    for section_name, registry in (
        ("backgrounds", BACKGROUND_VARIANTS),
        ("layouts", LAYOUT_VARIANTS),
    ):
        section = config.get(section_name) or {}
        if not isinstance(section, dict):
            raise ValueError(f"visual_variation.{section_name} must be a mapping")
        unknown_engines = set(section).difference(registry)
        if unknown_engines:
            names = ", ".join(sorted(map(str, unknown_engines)))
            raise ValueError(
                f"visual_variation.{section_name} has unknown engines: {names}"
            )
        for engine, weights in section.items():
            if not isinstance(weights, dict):
                raise ValueError(
                    f"visual_variation.{section_name}.{engine} must be a "
                    "name-to-weight mapping"
                )
            unknown_names = set(weights).difference(registry[engine])
            if unknown_names:
                names = ", ".join(sorted(map(str, unknown_names)))
                raise ValueError(
                    f"visual_variation.{section_name}.{engine} has unknown "
                    f"variants: {names}"
                )
            numeric_weights: list[float] = []
            for name, weight in weights.items():
                if isinstance(weight, bool) or not isinstance(weight, (int, float)):
                    raise ValueError(
                        f"visual_variation.{section_name}.{engine}.{name} "
                        "must be a numeric weight"
                    )
                value = float(weight)
                if not math.isfinite(value) or value < 0:
                    raise ValueError(
                        f"visual_variation.{section_name}.{engine}.{name} "
                        "must be a finite non-negative weight"
                    )
                numeric_weights.append(value)
            if not numeric_weights or not any(weight > 0 for weight in numeric_weights):
                raise ValueError(
                    f"visual_variation.{section_name}.{engine} must enable "
                    "at least one variant"
                )


def _validate_trend_feed(config: Any) -> None:
    if not isinstance(config, dict):
        raise ValueError("trend_feed must be a mapping")
    enabled = config.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("trend_feed.enabled must be true or false")
    minutes = config.get("cache_minutes", 45)
    if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or float(minutes) < 1:
        raise ValueError("trend_feed.cache_minutes must be a number of at least 1")
    timeout = config.get("timeout_sec", 12)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or float(timeout) <= 0:
        raise ValueError("trend_feed.timeout_sec must be a positive number")
    urls = config.get("rss_urls") or []
    if not isinstance(urls, list) or not urls:
        raise ValueError("trend_feed.rss_urls must be a non-empty list")
    for url in urls:
        if not str(url).strip():
            raise ValueError("trend_feed.rss_urls entries must be non-empty")
