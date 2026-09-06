"""High-level video factory orchestrating the full pipeline."""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from app.art.storybook_content import build_storybook_lesson
from app.audio.generator import AudioGenerator
from app.audio.kids_education import fit_lesson_to_narration
from app.core.project import cleanup_work_dir, make_work_dir, next_output_paths
from app.core.randomizer import KIDS_ENGINES, ProjectSpec, Randomizer, TOPIC_BRIEF_ENGINES
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
    youtube_url: str | None = None
    youtube_error: str | None = None
    caption_path: Path | None = None
    manifest_path: Path | None = None
    qc: dict[str, Any] = field(default_factory=dict)


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
        edit_preset: str | None = None,
        caption_mode: str | None = None,
        edit_intensity: float | None = None,
        control: RenderControl | None = None,
        on_progress: ProgressFn | None = None,
        output_dir: str | Path | None = None,
        user_prompt: str | None = None,
        prompt_mode: str | None = None,
        prompt_quality: str | None = None,
        youtube_upload: bool = False,
        youtube_privacy: str | None = None,
    ) -> GenerateResult:
        prompt = str(user_prompt or "").strip()
        if prompt:
            from app.ai.prompt_brief import classify_engine, detect_resolution, prompt_seed, suggested_duration

            engine, style = classify_engine(prompt, engine)
            if seed is None:
                seed = prompt_seed(prompt)
            if duration is None:
                duration = suggested_duration(prompt)
            if resolution is None:
                resolution = detect_resolution(prompt, prompt_quality or "1080")
            fps = 30 if fps is None else fps
            audio_enabled = True if audio_enabled is None else audio_enabled
            thumbnail = True if thumbnail is None else thumbnail
            random_resolution = False
            random_fps = False
            random_duration = False
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
            edit_preset=edit_preset,
            caption_mode=caption_mode,
            edit_intensity=edit_intensity,
        )
        if prompt:
            spec.params["user_prompt"] = prompt
            spec.params["prompt_mode"] = str(prompt_mode or "offline").strip().lower()
        result = self.render_spec(spec, control=control, on_progress=on_progress, output_dir=output_dir)
        if result.success and youtube_upload and result.output_path and result.spec:
            result = self._maybe_upload_youtube(
                result,
                privacy=youtube_privacy,
                on_progress=on_progress,
            )
        return result

    def _maybe_upload_youtube(
        self,
        result: GenerateResult,
        *,
        privacy: str | None,
        on_progress: ProgressFn | None,
    ) -> GenerateResult:
        from app.publish.youtube import YouTubePublishError, publish_to_youtube

        try:
            info = publish_to_youtube(
                video_path=Path(result.output_path),
                spec=result.spec,
                config=self.config,
                thumbnail_path=result.thumbnail_path,
                privacy=privacy,
                on_progress=on_progress,
            )
            result.youtube_url = info.get("url")
            if result.project_id and info.get("id"):
                self.db.update_youtube(result.project_id, info.get("id"), info.get("url"))
        except YouTubePublishError as exc:
            logger.warning("YouTube upload skipped: %s", exc)
            result.youtube_error = str(exc)
            if on_progress:
                on_progress(
                    {
                        "phase": "youtube",
                        "message": f"YouTube upload failed: {exc}",
                        "seed": result.seed,
                        "engine": result.engine,
                        "style": result.style,
                    }
                )
        except Exception as exc:  # noqa: BLE001
            from app.publish.youtube import friendly_google_error

            logger.exception("YouTube upload failed: %s", exc)
            result.youtube_error = friendly_google_error(exc)
        return result

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
            spec.params["audio_enabled"] = bool(spec.audio_enabled)
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

            if control and control.stopped:
                raise InterruptedError("Render cancelled by user")

            if spec.params.get("_replay_locked"):
                logger.info("Replaying locked project spec for seed=%s", spec.seed)
            elif spec.params.get("user_prompt"):
                from app.ai.prompt_brief import enrich_from_user_prompt

                spec = enrich_from_user_prompt(spec, self.config, on_progress=on_progress)
            else:
                from app.ai.advisor import maybe_enrich_spec

                spec = maybe_enrich_spec(spec, self.config, on_progress=on_progress)

            if control and control.stopped:
                raise InterruptedError("Render cancelled by user")

            # Engine owns the concept bag. Never mix story pages with topic briefs.
            if spec.engine in TOPIC_BRIEF_ENGINES:
                spec.params.pop("education_lesson", None)
                topic_data = spec.params.get("topic_data")
                if not isinstance(topic_data, dict):
                    topic_id = spec.params.get("topic_id")
                    if spec.engine == "how_it_works":
                        from app.art.how_it_works_content import build_how_it_works_topic

                        topic_data = build_how_it_works_topic(
                            spec.seed,
                            spec.duration,
                            topic_id=str(topic_id) if topic_id else None,
                            params=spec.params,
                        )
                    else:
                        from app.art.trend_content import build_trend_topic

                        topic_data = build_trend_topic(
                            spec.seed,
                            spec.duration,
                            topic_id=str(topic_id) if topic_id else None,
                            params=spec.params,
                        )
                    spec.params["topic_data"] = topic_data
                from app.art.editorial import build_editorial_plan

                plan = build_editorial_plan(
                    list(topic_data.get("segments") or []),
                    engine=spec.engine,
                    duration=spec.duration,
                    params=spec.params,
                )
                if spec.audio_enabled and isinstance(topic_data, dict):
                    if on_progress:
                        on_progress(
                            {
                                "phase": "voice",
                                "seed": spec.seed,
                                "engine": spec.engine,
                                "style": spec.style,
                                "message": "Timing pictures to the narration…",
                            }
                        )
                    from app.audio.documentary_soundtrack import fit_topic_to_narration

                    sample_rate = int(self.config.get("audio", {}).get("sample_rate", 44100))
                    topic_dur = fit_topic_to_narration(
                        topic_data,
                        seed=spec.seed,
                        sample_rate=sample_rate,
                        min_duration=spec.duration,
                        on_progress=on_progress,
                    )
                    spec.duration = max(spec.duration, topic_dur)
                    topic_data["duration"] = spec.duration
                    spec.params["topic_data"] = topic_data
                spec.params["_duration"] = spec.duration
            elif spec.engine in KIDS_ENGINES:
                spec.params.pop("topic_data", None)
                lesson = build_storybook_lesson(
                    spec.seed,
                    spec.duration,
                    params=spec.params,
                )
                if lesson:
                    from app.art.editorial import build_editorial_plan

                    plan = build_editorial_plan(
                        list(lesson.get("segments") or []),
                        engine=spec.engine,
                        duration=spec.duration,
                        params=spec.params,
                    )
                    spec.params["_duration"] = spec.duration
                    spec.params["education_lesson"] = lesson
                    spec.params["_kids_text"] = True
                    spec.params["easing"] = "smooth"
                    spec.params["camera_feel"] = "static"
                    spec.params["edit_feel"] = "kids_show"
                    spec.params["camera_push"] = 0.0
                    spec.params["grain"] = 0.0
                    profile = spec.params.get("audio_profile")
                    if not isinstance(profile, dict):
                        profile = {}
                    else:
                        profile = dict(profile)
                    try:
                        profile["voice_rate"] = min(max(float(profile.get("voice_rate") or 0.86), 0.78), 0.94)
                    except (TypeError, ValueError):
                        profile["voice_rate"] = 0.86
                    try:
                        profile["voice_pitch"] = min(max(float(profile.get("voice_pitch") or 1.10), 1.02), 1.16)
                    except (TypeError, ValueError):
                        profile["voice_pitch"] = 1.10
                    spec.params["audio_profile"] = profile
                    try:
                        spec.params["blur"] = min(float(spec.params.get("blur") or 0.0), 0.12)
                    except (TypeError, ValueError):
                        spec.params["blur"] = 0.08
                    try:
                        speed = float(spec.params.get("animation_speed") or 0.7)
                        spec.params["animation_speed"] = float(max(0.5, min(0.8, speed)))
                    except (TypeError, ValueError):
                        spec.params["animation_speed"] = 0.7
                    try:
                        spec.params["glow"] = min(float(spec.params.get("glow") or 0.12), 0.18)
                    except (TypeError, ValueError):
                        spec.params["glow"] = 0.12

                    # Hold each picture for the full spoken line so kids can follow.
                    should_fit = spec.audio_enabled
                    lesson_dur = float(lesson.get("duration") or spec.duration)
                    if should_fit:
                        if on_progress:
                            on_progress(
                                {
                                    "phase": "voice",
                                    "seed": spec.seed,
                                    "engine": spec.engine,
                                    "style": spec.style,
                                    "message": "Timing story pages to the narration…",
                                }
                            )
                        sample_rate = int(self.config.get("audio", {}).get("sample_rate", 44100))
                        lesson_dur = fit_lesson_to_narration(
                            lesson,
                            seed=spec.seed,
                            sample_rate=sample_rate,
                            audio_profile=profile,
                            min_duration=spec.duration,
                            on_progress=on_progress,
                        )
                    spec.duration = max(spec.duration, lesson_dur)
                    spec.params["_duration"] = spec.duration
                    lesson["duration"] = spec.duration
                    spec.params["education_lesson"] = lesson
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

            spec.duration = max(float(spec.duration), 1.0 / max(1, spec.fps))
            spec.duration = spec.total_frames / float(max(1, spec.fps))
            spec.params["_duration"] = spec.duration
            if isinstance(spec.params.get("education_lesson"), dict):
                spec.params["education_lesson"]["duration"] = spec.duration
            if isinstance(spec.params.get("topic_data"), dict):
                spec.params["topic_data"]["duration"] = spec.duration
            content = spec.params.get("education_lesson") or spec.params.get("topic_data")
            if isinstance(content, dict):
                from app.art.editorial import finalize_editorial_plan, validate_editorial_plan

                segments = list(content.get("segments") or [])
                existing_plan = spec.params.get("editorial_plan")
                if not isinstance(existing_plan, dict):
                    from app.art.editorial import build_editorial_plan

                    existing_plan = build_editorial_plan(
                        segments,
                        engine=spec.engine,
                        duration=spec.duration,
                        params=spec.params,
                    )
                spec.params["editorial_plan"] = finalize_editorial_plan(existing_plan, segments, spec.duration)
                plan_errors = validate_editorial_plan(spec.params["editorial_plan"])
                if plan_errors:
                    raise RuntimeError("Editorial plan is invalid: " + "; ".join(plan_errors))

            from app.ai.realize import realize_visual_assets

            spec = realize_visual_assets(spec, on_progress=on_progress)
            realized_content = spec.params.get("education_lesson") or spec.params.get("topic_data")
            if isinstance(realized_content, dict) and isinstance(spec.params.get("editorial_plan"), dict):
                from app.art.editorial import finalize_editorial_plan, validate_editorial_plan

                realized_segments = list(realized_content.get("segments") or [])
                spec.params["editorial_plan"] = finalize_editorial_plan(
                    spec.params["editorial_plan"],
                    realized_segments,
                    spec.duration,
                )
                realized_errors = validate_editorial_plan(spec.params["editorial_plan"])
                if realized_errors:
                    raise RuntimeError(
                        "Realized editorial plan is invalid: " + "; ".join(realized_errors)
                    )

            if control and control.stopped:
                raise InterruptedError("Render cancelled by user")

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
                    raise RuntimeError("Soundtrack generation failed; export stopped to avoid a silent video")

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

            render_metadata = self.renderer.render(
                spec,
                video_path,
                audio_file,
                control=control,
                on_progress=_frame_progress,
            )

            if on_progress:
                on_progress(
                    {
                        "phase": "qc",
                        "seed": spec.seed,
                        "engine": spec.engine,
                        "style": spec.style,
                        "message": "Checking audio, video, and captions…",
                    }
                )
            from app.video.captions import export_manifest, export_srt
            from app.video.qc import inspect_render

            plan_data = spec.params.get("editorial_plan")
            caption_mode = str(spec.params.get("caption_mode") or "sidecar").lower()
            caption_out = (
                export_srt(video_path, plan_data)
                if isinstance(plan_data, dict) and caption_mode in {"sidecar", "both"}
                else None
            )
            spec.params["caption_path"] = str(caption_out) if caption_out else None
            manifest_out = export_manifest(
                video_path,
                spec,
                caption_path=caption_out,
                qc={},
            )
            spec.params["manifest_path"] = str(manifest_out)
            qc_config = self.config.get("qc") or {}
            if bool(qc_config.get("enabled", True)):
                qc_report = inspect_render(
                    video_path,
                    expected_duration=spec.duration,
                    audio_path=audio_file,
                    config=qc_config,
                    expected_metadata={
                        **render_metadata,
                        "caption_path": str(caption_out) if caption_out else None,
                        "manifest_path": str(manifest_out),
                    },
                    caption_path=caption_out,
                    manifest_path=manifest_out,
                )
            else:
                qc_report = {
                    "passed": True,
                    "errors": [],
                    "warnings": ["QC disabled by configuration"],
                    "metrics": {"skipped": True},
                }
            if not qc_report.get("passed", False):
                raise RuntimeError("Render QC failed: " + "; ".join(qc_report.get("errors") or ["unknown error"]))
            spec.params["qc"] = qc_report
            export_manifest(
                video_path,
                spec,
                caption_path=caption_out,
                qc=qc_report,
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
                    status=(
                        f"ok: {len(qc_report.get('warnings') or [])} QC warning(s)"
                        if qc_report.get("warnings")
                        else "ok"
                    ),
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
                caption_path=caption_out,
                manifest_path=manifest_out,
                qc=qc_report,
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
