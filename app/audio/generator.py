"""High-level audio generation facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.art.education_content import KIDS_EDUCATION_ENGINES, build_lesson_for_engine
from app.audio.kids_education import generate_kids_education_audio
from app.audio.procedural_music import generate_procedural_audio, write_wav
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

        For alphabet educational videos, builds a kids learning soundtrack
        synced to the lesson segments.
        """
        try:
            params = params or {}
            profile = params.get("audio_profile") if isinstance(params.get("audio_profile"), dict) else {}
            if engine == "infographic_explainer" or params.get("topic_data"):
                topic_data = params.get("topic_data")
                if not isinstance(topic_data, dict):
                    from app.art.knowledge_content import build_knowledge_topic
                    topic_data = build_knowledge_topic(seed, duration, params=params)
                from app.audio.documentary_soundtrack import generate_documentary_audio
                samples = generate_documentary_audio(
                    duration,
                    seed,
                    topic_data,
                    sample_rate=self.sample_rate,
                    audio_profile=profile,
                )
            elif engine in KIDS_EDUCATION_ENGINES or params.get("education_lesson"):
                lesson = params.get("education_lesson")
                if not isinstance(lesson, dict):
                    lesson = build_lesson_for_engine(engine or "", seed, duration, params=params)
                if not isinstance(lesson, dict):
                    from app.art.education_content import build_education_lesson
                    lesson = build_education_lesson(seed, duration, params=params)
                samples = generate_kids_education_audio(
                    duration,
                    seed,
                    lesson,
                    sample_rate=self.sample_rate,
                    audio_profile=profile,
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

            write_wav(output_path, samples, self.sample_rate)
            logger.info("Wrote audio: %s", output_path)
            return output_path
        except Exception as exc:  # noqa: BLE001
            logger.exception("Audio generation failed: %s", exc)
            return None

    def _mix_asset(self, samples, asset: Path):
        try:
            import wave

            import numpy as np

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
