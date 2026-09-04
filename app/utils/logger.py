"""Logging setup for Genesis Artvision Engine."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def setup_logging(config: dict[str, Any] | None = None) -> logging.Logger:
    """Configure root application logger with console + file handlers."""
    log_cfg = (config or {}).get("logging", {})
    level_name = str(log_cfg.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    log_dir = Path(log_cfg.get("directory", "./logs"))
    if not log_dir.is_absolute():
        from app.utils.paths import project_root

        log_dir = project_root() / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("gae")
    logger.setLevel(level)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(fmt)
    logger.addHandler(console)

    stamp = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(log_dir / f"gae_{stamp}.log", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "gae") -> logging.Logger:
    """Return a child logger under the application namespace."""
    if name == "gae":
        return logging.getLogger("gae")
    return logging.getLogger(f"gae.{name}")
