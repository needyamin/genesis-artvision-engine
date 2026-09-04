"""High-level audio generation facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.audio.procedural_music import generate_procedural_audio, write_wav
from app.utils.logger import get_logger
from app.utils.paths import resolve_path, project_root

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
    ) -> Path | None:
        """
        Generate a WAV file. Returns path on success, None on failure.
        Optionally blends a random local asset from assets/music if present.
        """
        try:
            samples = generate_procedural_audio(
                duration,
                seed,
                sample_rate=self.sample_rate,
                style=style,
            )
            # Optional local asset overlay (not required)
            asset = self._pick_local_asset(seed)
            if asset is not None:
                try:
                    import wave

                    with wave.open(str(asset), "rb") as wf:
                        raw = wf.readframes(wf.getnframes())
                        import numpy as np

                        asset_audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                        # Mono mix
                        if wf.getnchannels() > 1:
                            asset_audio = asset_audio.reshape(-1, wf.getnchannels()).mean(axis=1)
                        target_n = len(samples)
                        if len(asset_audio) < target_n:
                            reps = int(np.ceil(target_n / max(1, len(asset_audio))))
                            asset_audio = np.tile(asset_audio, reps)[:target_n]
                        else:
                            asset_audio = asset_audio[:target_n]
                        samples = samples * 0.75 + asset_audio * 0.2
                        peak = float(np.max(np.abs(samples)) + 1e-9)
                        samples = samples / peak * 0.85
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Local asset mix skipped: %s", exc)

            write_wav(output_path, samples, self.sample_rate)
            logger.info("Wrote audio: %s", output_path)
            return output_path
        except Exception as exc:  # noqa: BLE001
            logger.exception("Audio generation failed: %s", exc)
            return None

    def _pick_local_asset(self, seed: int) -> Path | None:
        music_dir = project_root() / "assets" / "music"
        if not music_dir.exists():
            return None
        files = sorted(music_dir.glob("*.wav"))
        if not files:
            return None
        return files[seed % len(files)]
