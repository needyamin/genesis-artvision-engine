"""High-level audio generation facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from app.art.storybook_content import build_storybook_lesson
from app.audio.kids_education import generate_kids_education_audio
from app.audio.mastering import master_audio
from app.audio.procedural_music import generate_procedural_audio, write_wav
from app.core.randomizer import KIDS_ENGINES, TOPIC_BRIEF_ENGINES
from app.utils.logger import get_logger
from app.utils.paths import project_root

logger = get_logger("audio.generator")


class AudioGenerator:
    """Creates background audio for a project, preferring procedural synthesis."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.sample_rate = int(config.get("audio", {}).get("sample_rate", 44100))

    def generate(
        self,
        output_path: Path,
        *,
        duration: float,
        seed: int,
        style: str = "abstract",
        engine: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> Path | None:
        """
        Generate a WAV file. Returns path on success, None on failure.

        For kids storybook videos, builds a soundtrack synced to story pages.
        """
        try:
            params = params or {}
            profile = (
                dict(params.get("audio_profile"))
                if isinstance(params.get("audio_profile"), dict)
                else {}
            )
            if "tempo_bpm" not in profile:
                root_tempo = params.get("tempo_bpm", params.get("bpm"))
                if root_tempo is not None:
                    profile["tempo_bpm"] = root_tempo
            if engine in KIDS_ENGINES:
                lesson = params.get("education_lesson")
                if not isinstance(lesson, dict):
                    lesson = build_storybook_lesson(seed, duration, params=params)
                samples = generate_kids_education_audio(
                    duration,
                    seed,
                    lesson,
                    sample_rate=self.sample_rate,
                    audio_profile=profile,
                )
            elif engine in TOPIC_BRIEF_ENGINES:
                topic_data = params.get("topic_data")
                if not isinstance(topic_data, dict):
                    if engine == "how_it_works":
                        from app.art.how_it_works_content import build_how_it_works_topic
                        topic_data = build_how_it_works_topic(seed, duration, params=params)
                    else:
                        from app.art.trend_content import build_trend_topic
                        topic_data = build_trend_topic(seed, duration, params=params)
                from app.audio.documentary_soundtrack import generate_documentary_audio
                samples = generate_documentary_audio(
                    duration,
                    seed,
                    topic_data,
                    sample_rate=self.sample_rate,
                    audio_profile=profile,
                    editorial_plan=(
                        params.get("editorial_plan")
                        if isinstance(params.get("editorial_plan"), dict)
                        else None
                    ),
                )
            else:
                samples = generate_procedural_audio(
                    duration,
                    seed,
                    sample_rate=self.sample_rate,
                    style=style,
                    audio_profile=profile,
                )
                asset = self._pick_local_asset(seed)
                if asset is not None:
                    samples = self._mix_asset(samples, asset)

            samples = self._fit_duration(samples, duration)
            audio_cfg = self.config.get("audio") or {}
            samples = master_audio(
                samples,
                target_lufs=float(audio_cfg.get("target_lufs", -14.0)),
                ceiling_dbfs=float(audio_cfg.get("ceiling_dbfs", -1.0)),
            )
            samples = self._fit_duration(samples, duration)
            write_wav(output_path, samples, self.sample_rate)
            logger.info("Wrote audio: %s", output_path)
            return output_path
        except Exception as exc:  # noqa: BLE001
            logger.exception("Audio generation failed: %s", exc)
            return None

    def _fit_duration(self, samples: Any, duration: float) -> np.ndarray:
        """Trim or zero-pad mono samples to the exact requested frame count."""
        target_n = max(1, int(round(float(duration) * self.sample_rate)))
        audio = np.asarray(samples, dtype=np.float32).reshape(-1)
        if len(audio) == target_n:
            return audio
        if len(audio) > target_n:
            return audio[:target_n].copy()
        return np.pad(audio, (0, target_n - len(audio))).astype(np.float32, copy=False)

    def _mix_asset(self, samples, asset: Path):
        try:
            import wave

            with wave.open(str(asset), "rb") as wf:
                raw = wf.readframes(wf.getnframes())
                asset_audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                if wf.getnchannels() > 1:
                    asset_audio = asset_audio.reshape(-1, wf.getnchannels()).mean(axis=1)
                target_n = len(samples)
                if len(asset_audio) < target_n:
                    reps = int(np.ceil(target_n / max(1, len(asset_audio))))
                    asset_audio = np.tile(asset_audio, reps)[:target_n]
                else:
                    asset_audio = asset_audio[:target_n]
                mixed = samples * 0.75 + asset_audio * 0.2
                peak = float(np.max(np.abs(mixed)) + 1e-9)
                return mixed / peak * 0.85
        except Exception as exc:  # noqa: BLE001
            logger.warning("Local asset mix skipped: %s", exc)
            return samples

    def _pick_local_asset(self, seed: int) -> Path | None:
        music_dir = project_root() / "assets" / "music"
        if not music_dir.exists():
            return None
        files = sorted(music_dir.glob("*.wav"))
        if not files:
            return None
        return files[seed % len(files)]
