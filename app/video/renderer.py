"""Incremental video renderer piping frames to FFmpeg."""

from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from app.art.base import ArtEngine, get_engine
from app.core.randomizer import ProjectSpec
from app.utils.logger import get_logger
from app.video.effects import apply_effects
from app.video.ffmpeg import FFmpegError, build_raw_video_encode_cmd, find_ffmpeg

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
        preview_every: int = 5,
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
        # Auto bitrate: 4K needs much higher than Full HD
        pixels = spec.width * spec.height
        if pixels >= 3840 * 2160 * 0.9:
            bitrate = str(out_cfg.get("bitrate_4k", "35M"))
        elif pixels >= 1920 * 1080 * 0.9:
            bitrate = str(out_cfg.get("bitrate", "8M"))
        else:
            bitrate = str(out_cfg.get("bitrate", "8M"))
        audio_bitrate = str(out_cfg.get("audio_bitrate", "192k"))
        cmd = build_raw_video_encode_cmd(
            ffmpeg=ffmpeg,
            width=spec.width,
            height=spec.height,
            fps=spec.fps,
            output=output_path,
            audio_path=audio_path if (audio_path and audio_path.exists()) else None,
            video_bitrate=bitrate,
            audio_bitrate=audio_bitrate,
        )
        logger.info("Starting FFmpeg: %s", " ".join(cmd))

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
        try:
            for i in range(total):
                while control.pause.is_set() and not control.stop.is_set():
                    time.sleep(0.1)
                if control.stop.is_set():
                    logger.info("Render stopped by user at frame %s/%s", i, total)
                    break

                frame = engine.render_frame(i, total)
                frame = apply_effects(frame, spec.params)
                if frame.dtype != np.uint8 or frame.shape != (spec.height, spec.width, 3):
                    raise RuntimeError(
                        f"Engine {spec.engine} returned invalid frame shape {getattr(frame, 'shape', None)}"
                    )
                proc.stdin.write(frame.tobytes())

                if on_progress and (i % preview_every == 0 or i == total - 1):
                    preview = frame[::4, ::4].copy()
                    on_progress(i + 1, total, preview)

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
