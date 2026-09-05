"""Incremental video renderer piping frames to FFmpeg."""

from __future__ import annotations

import subprocess
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from app.art.base import ArtEngine, get_engine
from app.core.randomizer import ProjectSpec
from app.utils.logger import get_logger
from app.utils.performance import hardware_encode_enabled, resolve_workers
from app.video.effects import apply_editorial_finish, apply_effects
from app.video.ffmpeg import FFmpegError, build_raw_video_encode_cmd, detect_h264_encoder, find_ffmpeg

logger = get_logger("renderer")


@dataclass
class RenderControl:
    """Thread-safe pause / stop flags for a render job."""

    stop: threading.Event = field(default_factory=threading.Event)
    pause: threading.Event = field(default_factory=threading.Event)

    def request_stop(self) -> None:
        self.stop.set()
        self.pause.clear()

    def request_pause(self) -> None:
        self.pause.set()

    def request_resume(self) -> None:
        self.pause.clear()

    @property
    def stopped(self) -> bool:
        return self.stop.is_set()


ProgressCallback = Callable[[int, int, np.ndarray | None], None]


def _compose_frame(engine: ArtEngine, spec: ProjectSpec, index: int, total: int) -> np.ndarray:
    frame = engine.render_frame(index, total)
    frame = apply_effects(frame, spec.params)
    frame = apply_editorial_finish(
        frame,
        spec.params,
        index,
        total,
        duration=spec.duration,
        fps=spec.fps,
        seed=spec.seed,
    )
    if frame.dtype != np.uint8 or frame.shape != (spec.height, spec.width, 3):
        raise RuntimeError(
            f"Engine {spec.engine} returned invalid frame shape {getattr(frame, 'shape', None)}"
        )
    if not frame.flags["C_CONTIGUOUS"]:
        frame = np.ascontiguousarray(frame)
    return frame


class FrameRenderer:
    """Renders ProjectSpec frames and streams them into an MP4 via FFmpeg."""

    def __init__(self, config: dict) -> None:
        self.config = config

    def render(
        self,
        spec: ProjectSpec,
        output_path: Path,
        audio_path: Path | None = None,
        *,
        control: RenderControl | None = None,
        on_progress: ProgressCallback | None = None,
        preview_every: int | None = None,
    ) -> None:
        control = control or RenderControl()
        engine: ArtEngine = get_engine(spec.engine)
        engine.setup(
            spec.width,
            spec.height,
            spec.fps,
            spec.seed,
            spec.params,
            spec.palette(),
        )

        ffmpeg = find_ffmpeg()
        out_cfg = self.config.get("output", {})
        pixels = spec.width * spec.height
        if pixels >= 3840 * 2160 * 0.9:
            bitrate = str(out_cfg.get("bitrate_4k", "35M"))
        else:
            bitrate = str(out_cfg.get("bitrate", "8M"))
        audio_bitrate = str(out_cfg.get("audio_bitrate", "192k"))
        codec, codec_args, codec_label = detect_h264_encoder(
            ffmpeg,
            hardware=hardware_encode_enabled(self.config),
        )
        cmd = build_raw_video_encode_cmd(
            ffmpeg=ffmpeg,
            width=spec.width,
            height=spec.height,
            fps=spec.fps,
            output=output_path,
            audio_path=audio_path if (audio_path and audio_path.exists()) else None,
            video_bitrate=bitrate,
            audio_bitrate=audio_bitrate,
            video_codec=codec,
            codec_args=codec_args,
        )
        workers = 1
        if getattr(engine, "parallel_frames", True):
            workers = resolve_workers(self.config, width=spec.width, height=spec.height)
        logger.info(
            "Starting FFmpeg (%s) with %s frame worker(s): %s",
            codec_label,
            workers,
            " ".join(cmd),
        )

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        assert proc.stdin is not None
        stderr_chunks: list[bytes] = []

        def _drain_stderr() -> None:
            assert proc.stderr is not None
            while True:
                chunk = proc.stderr.read(4096)
                if not chunk:
                    break
                stderr_chunks.append(chunk)

        drain_thread = threading.Thread(target=_drain_stderr, daemon=True)
        drain_thread.start()

        total = spec.total_frames
        perf = self.config.get("performance") or {}
        max_preview = float(perf.get("max_preview_fps") or 4)
        if preview_every is None:
            preview_every = max(8, int(round(spec.fps / max(1.0, max_preview))))
        try:
            if workers <= 1:
                self._render_sequential(
                    engine,
                    spec,
                    proc,
                    control=control,
                    on_progress=on_progress,
                    preview_every=preview_every,
                )
            else:
                self._render_parallel(
                    spec,
                    proc,
                    workers=workers,
                    control=control,
                    on_progress=on_progress,
                    preview_every=preview_every,
                )

            proc.stdin.close()
            drain_thread.join(timeout=30)
            code = proc.wait(timeout=120)
            stderr = b"".join(stderr_chunks)
            if control.stop.is_set():
                if output_path.exists():
                    output_path.unlink(missing_ok=True)
                raise InterruptedError("Render cancelled by user")
            if code != 0:
                err = stderr.decode("utf-8", errors="replace")[-2000:]
                raise FFmpegError(f"FFmpeg encode failed ({code}): {err}")
            if on_progress:
                on_progress(total, total, None)
        except Exception:
            try:
                proc.stdin.close()
            except Exception:  # noqa: BLE001
                pass
            proc.kill()
            drain_thread.join(timeout=5)
            raise
        finally:
            engine.cleanup()

    def _write_frame(
        self,
        proc: subprocess.Popen,
        spec: ProjectSpec,
        frame: np.ndarray,
        index: int,
        total: int,
        *,
        on_progress: ProgressCallback | None,
        preview_every: int,
    ) -> None:
        assert proc.stdin is not None
        proc.stdin.write(frame.data)
        if on_progress and (index % preview_every == 0 or index == total - 1):
            step = max(4, spec.width // 480)
            preview = frame[::step, ::step].copy()
            on_progress(index + 1, total, preview)

    def _render_sequential(
        self,
        engine: ArtEngine,
        spec: ProjectSpec,
        proc: subprocess.Popen,
        *,
        control: RenderControl,
        on_progress: ProgressCallback | None,
        preview_every: int,
    ) -> None:
        total = spec.total_frames
        for i in range(total):
            while control.pause.is_set() and not control.stop.is_set():
                time.sleep(0.1)
            if control.stop.is_set():
                logger.info("Render stopped by user at frame %s/%s", i, total)
                break
            frame = _compose_frame(engine, spec, i, total)
            self._write_frame(
                proc,
                spec,
                frame,
                i,
                total,
                on_progress=on_progress,
                preview_every=preview_every,
            )

    def _render_parallel(
        self,
        spec: ProjectSpec,
        proc: subprocess.Popen,
        *,
        workers: int,
        control: RenderControl,
        on_progress: ProgressCallback | None,
        preview_every: int,
    ) -> None:
        total = spec.total_frames
        max_inflight = max(workers * 2, workers + 4)
        tls = threading.local()
        palette = spec.palette()

        def render_one(index: int) -> np.ndarray:
            try:
                cv2.setNumThreads(1)
            except Exception:
                pass
            eng: ArtEngine | None = getattr(tls, "engine", None)
            if eng is None:
                eng = get_engine(spec.engine)
                eng.setup(spec.width, spec.height, spec.fps, spec.seed, spec.params, palette)
                tls.engine = eng
            return _compose_frame(eng, spec, index, total)

        next_write = 0
        submitted = 0
        futures: dict[int, Future[np.ndarray]] = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            while next_write < total:
                while control.pause.is_set() and not control.stop.is_set():
                    time.sleep(0.05)
                if control.stop.is_set():
                    logger.info("Render stopped by user at frame %s/%s", next_write, total)
                    for fut in futures.values():
                        fut.cancel()
                    break
                while submitted < total and len(futures) < max_inflight:
                    futures[submitted] = pool.submit(render_one, submitted)
                    submitted += 1
                frame = futures.pop(next_write).result()
                self._write_frame(
                    proc,
                    spec,
                    frame,
                    next_write,
                    total,
                    on_progress=on_progress,
                    preview_every=preview_every,
                )
                next_write += 1
