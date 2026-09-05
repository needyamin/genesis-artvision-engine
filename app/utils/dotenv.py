"""Load key=value pairs from a root .env file into os.environ (stdlib only)."""

from __future__ import annotations

import os
from pathlib import Path

from app.utils.paths import project_root


def load_dotenv(path: Path | None = None, *, override: bool = False) -> Path | None:
    """
    Load OPENROUTER_API_KEY (and other vars) from project-root `.env`.

    Does not override existing environment variables unless override=True.
    Returns the path loaded, or None if missing.
    """
    env_path = path or (project_root() / ".env")
    if not env_path.is_file():
        return None
    try:
        text = env_path.read_text(encoding="utf-8")
    except OSError:
        return None

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if not override and key in os.environ and os.environ.get(key, "").strip():
            continue
        os.environ[key] = value
    return env_path
