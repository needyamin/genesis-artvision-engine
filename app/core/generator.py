"""High-level video factory orchestrating the full pipeline."""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from app.art.education_content import KIDS_EDUCATION_ENGINES, build_lesson_for_engine
from app.audio.generator import AudioGenerator
from app.core.project import cleanup_work_dir, make_work_dir, next_output_paths
from app.core.randomizer import ProjectSpec, Randomizer
from app.core.scheduler import BatchScheduler
from app.database.database import Database, HistoryRow
from app.utils.logger import get_logger
from app.utils.paths import resolve_path
from app.video.ffmpeg import extract_thumbnail
from app.video.renderer import FrameRenderer, RenderControl

logger = get_logger("generator")

ProgressFn = Callable[[dict[str, Any]], None]


@dataclass
class GenerateResult:
    success: bool
    seed: int
    engine: str
    style: str
    output_path: Path | None
    thumbnail_path: Path | None = None
    project_id: str = ""
    error: str | None = None
    render_time: float = 0.0
    spec: ProjectSpec | None = None


@dataclass
class VideoFactory:
    """Creates randomized procedural art videos end-to-end."""

    config: dict[str, Any]
    randomizer: Randomizer = field(init=False)
    renderer: FrameRenderer = field(init=False)
    audio: AudioGenerator = field(init=False)
    db: Database = field(init=False)
    scheduler: BatchScheduler = field(init=False)

    def __post_init__(self) -> None:
        self.randomizer = Randomizer(self.config)
        self.renderer = FrameRenderer(self.config)
        self.audio = AudioGenerator(self.config)
        db_path = self.config.get("database", {}).get("path", "./data/history.db")
        self.db = Database(db_path)
        self.scheduler = BatchScheduler()

    def generate_one(
        self,
        *,
        seed: int | None = None,
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
        control: RenderControl | None = None,
        on_progress: ProgressFn | None = None,
        output_dir: str | Path | None = None,
    ) -> GenerateResult:
        spec = self.randomizer.create_project(
            seed=seed,
            engine=engine,
            style=style,
            resolution=resolution,
            fps=fps,
            duration=duration,
            audio_enabled=audio_enabled,
            thumbnail=thumbnail,
            random_resolution=random_resolution,
            random_fps=random_fps,
            random_duration=random_duration,
        )
        return self.render_spec(spec, control=control, on_progress=on_progress, output_dir=output_dir)

    def render_spec(
        self,
        spec: ProjectSpec,
        *,
        control: RenderControl | None = None,
        on_progress: ProgressFn | None = None,
        output_dir: str | Path | None = None,
    ) -> GenerateResult:
        out_root = resolve_path(
            output_dir or self.config.get("output", {}).get("directory", "./output")
        )
        out_root.mkdir(parents=True, exist_ok=True)
        temp_root = resolve_path(self.config.get("temp", {}).get("directory", "./temp"))
        work = make_work_dir(temp_root, spec.project_id)
        video_path, thumb_path = next_output_paths(out_root, spec.project_id)
        audio_path = work / "audio.wav"
        started = time.perf_counter()
        audio_file: Path | None = None

        try:
            if on_progress:
                on_progress(
                    {
                        "phase": "start",
                        "seed": spec.seed,
                        "engine": spec.engine,
                        "style": spec.style,
                        "frame": 0,
                        "total_frames": spec.total_frames,
                        "preview": None,
                    }
                )

            # Kids educational engines: shared lesson for video + audio
            if spec.engine in KIDS_EDUCATION_ENGINES:
                lesson = build_lesson_for_engine(
                    spec.engine,
                    spec.seed,
                    spec.duration,
                    params=spec.params,
                )
                if lesson:
                    spec.params["_duration"] = spec.duration
                    spec.params["education_lesson"] = lesson
                    if spec.engine == "alphabet_cartoon":
                        if spec.params.get("mode") not in {
                            "chart", "focus", "parade", "lesson", "spell",
                        }:
                            spec.params["mode"] = lesson.get("visual_mode", "lesson")

            if spec.audio_enabled:
                if on_progress:
                    on_progress({"phase": "audio", "seed": spec.seed, "engine": spec.engine, "style": spec.style})
                audio_file = self.audio.generate(
                    audio_path,
                    duration=spec.duration,
                    seed=spec.seed,
                    style=spec.style,
                    engine=spec.engine,
                    params=spec.params,
                )
                if audio_file is None:
                    logger.warning("Continuing without audio for seed=%s", spec.seed)

            def _frame_progress(frame: int, total: int, preview: Any) -> None:
                if on_progress:
                    on_progress(
                        {
                            "phase": "render",
                            "seed": spec.seed,
                            "engine": spec.engine,
                            "style": spec.style,
                            "frame": frame,
                            "total_frames": total,
                            "preview": preview,
                        }
                    )

            self.renderer.render(
                spec,
                video_path,
                audio_file,
                control=control,
                on_progress=_frame_progress,
            )

            thumb_out: Path | None = None
            if spec.thumbnail and video_path.exists():
                try:
                    extract_thumbnail(video_path, thumb_path, time_seconds=spec.duration * 0.45)
                    thumb_out = thumb_path
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Thumbnail failed: %s", exc)

            elapsed = time.perf_counter() - started
            self.db.insert_video(
                HistoryRow(
                    project_id=spec.project_id,
                    seed=spec.seed,
                    created_at=Database.now_iso(),
                    duration=spec.duration,
                    width=spec.width,
                    height=spec.height,
                    fps=spec.fps,
                    engine=spec.engine,
                    style=spec.style,
                    params_json=json.dumps(spec.to_dict(), default=str),
                    output_path=str(video_path),
                    thumbnail_path=str(thumb_out) if thumb_out else None,
                    render_time=elapsed,
                    status="ok",
                )
            )
            cleanup_work_dir(work, force=True)
            logger.info(
                "Generated %s (%s / %s) in %.1fs -> %s",
                spec.project_id,
                spec.engine,
                spec.style,
                elapsed,
                video_path,
            )
            return GenerateResult(
                success=True,
                seed=spec.seed,
                engine=spec.engine,
                style=spec.style,
                output_path=video_path,
                thumbnail_path=thumb_out,
                project_id=spec.project_id,
                render_time=elapsed,
                spec=spec,
            )
        except InterruptedError as exc:
            keep = bool(self.config.get("temp", {}).get("keep_on_failure", True))
            if not keep:
                cleanup_work_dir(work, force=True)
            return GenerateResult(
                success=False,
                seed=spec.seed,
                engine=spec.engine,
                style=spec.style,
                output_path=None,
                project_id=spec.project_id,
                error=str(exc),
                spec=spec,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Render failed for seed=%s: %s\n%s", spec.seed, exc, traceback.format_exc())
            keep = bool(self.config.get("temp", {}).get("keep_on_failure", True))
            if not keep:
                cleanup_work_dir(work, force=True)
            try:
                self.db.insert_video(
                    HistoryRow(
                        project_id=spec.project_id,
                        seed=spec.seed,
                        created_at=Database.now_iso(),
                        duration=spec.duration,
                        width=spec.width,
                        height=spec.height,
                        fps=spec.fps,
                        engine=spec.engine,
                        style=spec.style,
                        params_json=json.dumps(spec.to_dict(), default=str),
                        output_path=str(video_path),
                        thumbnail_path=None,
                        render_time=time.perf_counter() - started,
                        status=f"error: {exc}",
                    )
                )
            except Exception:  # noqa: BLE001
                pass
            return GenerateResult(
                success=False,
                seed=spec.seed,
                engine=spec.engine,
                style=spec.style,
                output_path=None,
                project_id=spec.project_id,
                error=str(exc),
                spec=spec,
            )

    def generate_batch(
        self,
        *,
        count: int = 1,
        unlimited: bool = False,
        on_progress: ProgressFn | None = None,
        **kwargs: Any,
    ) -> list[GenerateResult]:
        results: list[GenerateResult] = []
        total = 10**9 if unlimited else max(1, int(count))
        self.scheduler.start(total if not unlimited else 0, unlimited=unlimited)
        i = 0
        while i < total:
            if self.scheduler.should_stop:
                break
            self.scheduler.mark_video_started(i + 1)
            if on_progress:
                on_progress(
                    {
                        "phase": "batch",
                        "video_index": i + 1,
                        "video_total": None if unlimited else total,
                    }
                )
            result = self.generate_one(control=self.scheduler.control, on_progress=on_progress, **kwargs)
            results.append(result)
            self.scheduler.mark_video_done()
            i += 1
            if self.scheduler.should_stop:
                break
            # For seeded single regenerate, don't keep same seed
            if "seed" in kwargs:
                kwargs = {**kwargs, "seed": None}
        self.scheduler.finish()
        return results
