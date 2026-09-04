"""Project helpers and temp cleanup."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from app.utils.paths import project_root, resolve_path, unique_output_name


def make_work_dir(temp_root: Path, project_id: str) -> Path:
    path = temp_root / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_work_dir(path: Path, *, force: bool = False) -> None:
    if path.exists() and (force or path.is_dir()):
        shutil.rmtree(path, ignore_errors=True)


def clean_all_temp(config: dict[str, Any]) -> int:
    """Delete everything under the temp directory. Returns removed entry count."""
    temp_dir = resolve_path(config.get("temp", {}).get("directory", "./temp"))
    if not temp_dir.exists():
        return 0
    count = 0
    for child in temp_dir.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)
        count += 1
    return count


def next_output_paths(output_dir: Path, project_id: str) -> tuple[Path, Path]:
    """Return unique (mp4, jpg) paths for a project."""
    video = unique_output_name(project_id, "mp4", output_dir)
    thumb = video.with_suffix(".jpg")
    return video, thumb
