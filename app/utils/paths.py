"""Path helpers for Genesis Artvision Engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def project_root() -> Path:
    """Return the repository / installation root directory."""
    return Path(__file__).resolve().parents[2]


def resolve_path(path: str | Path, base: Path | None = None) -> Path:
    """Resolve a possibly-relative path against the project root."""
    p = Path(path)
    if p.is_absolute():
        return p
    return (base or project_root()) / p


def ensure_directories(config: dict[str, Any] | None = None) -> dict[str, Path]:
    """Create standard application directories and return their paths."""
    root = project_root()
    cfg = config or {}
    paths = {
        "root": root,
        "output": resolve_path(cfg.get("output", {}).get("directory", "./output"), root),
        "temp": resolve_path(cfg.get("temp", {}).get("directory", "./temp"), root),
        "logs": resolve_path(cfg.get("logging", {}).get("directory", "./logs"), root),
        "assets": root / "assets",
        "data": root / "data",
        "music": root / "assets" / "music",
        "sounds": root / "assets" / "sounds",
        "fonts": root / "assets" / "fonts",
    }
    ai_cfg = cfg.get("ai") or {}
    paths["ai_cache"] = resolve_path(ai_cfg.get("cache_dir") or "./data/ai_cache", root)
    paths["ai_catalogs"] = resolve_path(ai_cfg.get("catalog_dir") or "./data/ai_catalogs", root)
    paths["youtube"] = root / "data" / "youtube"
    for key in ("output", "temp", "logs", "data", "music", "sounds", "fonts", "ai_cache", "ai_catalogs", "youtube"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def unique_output_name(prefix: str, extension: str, directory: Path) -> Path:
    """Create a unique filename that does not overwrite existing files."""
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = directory / f"{prefix}_{stamp}.{extension.lstrip('.')}"
    counter = 1
    while candidate.exists():
        candidate = directory / f"{prefix}_{stamp}_{counter:03d}.{extension.lstrip('.')}"
        counter += 1
    return candidate
