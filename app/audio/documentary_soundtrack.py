"""Documentary soundtrack generator with cinematic pads, telemetry SFX, and articulate narration."""

from __future__ import annotations

from typing import Any
import numpy as np

from app.audio.offline_tts import documentary_narration_lines, speak_documentary
from app.audio.procedural_music import _adsr, _midi_to_hz, _osc, _soft_reverb
from app.audio.procedural_voice import mix_speech_at


def _add_whoosh_transition(audio: np.ndarray, start_idx: int, sr: int, rng: np.random.Generator) -> None:
    """Subtle cinematic whoosh / sweep for segment transitions."""
    dur = 0.75
    n_w = int(dur * sr)
    if start_idx + n_w > len(audio):
        n_w = len(audio) - start_idx
    if n_w <= 0:
        return

    t = np.linspace(0.0, 1.0, n_w, dtype=np.float32)
    # Band-passed noise sweep
    noise = rng.uniform(-1.0, 1.0, n_w).astype(np.float32)
    env = np.sin(t * np.pi) ** 2
    # Pitch sweep oscillator
    freq = 120.0 + 380.0 * (t ** 1.5)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    sweep = np.sin(phase) * 0.08
    whoosh = (noise * 0.12 + sweep) * env * 0.35
    audio[start_idx : start_idx + n_w] += whoosh


def _add_telemetry_beep(audio: np.ndarray, start_idx: int, sr: int, pitch: float = 880.0) -> None:
    """Soft high-tech data beep for metric callouts."""
    dur = 0.08
    n_b = int(dur * sr)
    if start_idx + n_b > len(audio):
        n_b = len(audio) - start_idx
    if n_b <= 0:
        return

    t = np.arange(n_b, dtype=np.float32) / sr
    env = np.linspace(1.0, 0.0, n_b, dtype=np.float32) ** 2
    beep = (np.sin(2 * np.pi * pitch * t) + 0.3 * np.sin(2 * np.pi * (pitch * 2) * t)) * env * 0.06
    audio[start_idx : start_idx + n_b] += beep


def generate_documentary_audio(
    duration: float,
    seed: int,
    topic_data: dict[str, Any],
    *,
    sample_rate: int = 44100,
    voice_enabled: bool = True,
    audio_profile: dict[str, Any] | None = None,
) -> np.ndarray:
    """
    Synthesize a cinematic documentary soundtrack synchronized to topic segments:
    - Deep ambient modal pad with slow evolving harmonics
    - Subtle rhythm sequencer pulses
    - Whoosh and telemetry transition SFX
    - Synchronized offline voice narration with intelligent audio ducking
    """
    rng = np.random.default_rng(seed + 107)
    n = max(1, int(duration * sample_rate))
    audio = np.zeros(n, dtype=np.float32)
    t = np.arange(n, dtype=np.float32) / sample_rate

    profile = audio_profile if isinstance(audio_profile, dict) else {}
    energy = float(max(0.2, min(1.0, profile.get("energy", 0.6))))

    # 1. Cinematic Ambient Pad (D minor / Dorian: D2, A2, D3, F3, A3, C4)
    chord_sets = [
        # Segment 1: D minor mysterious open fifth
        ((38, 0.12), (45, 0.09), (50, 0.07), (57, 0.05)),
        # Segment 2: F major lift
        ((41, 0.12), (48, 0.09), (53, 0.07), (60, 0.05)),
        # Segment 3: G Dorian / C major expansive
        ((43, 0.12), (50, 0.09), (55, 0.07), (62, 0.05)),
        # Segment 4: Resolving D minor / octave finish
        ((38, 0.13), (45, 0.10), (53, 0.08), (62, 0.06)),
    ]

    segments = list(topic_data.get("segments", []))
    if not segments:
        segments = [{"t0": 0.0, "t1": 1.0, "headline": topic_data.get("title", "Explainer")}]

    for i, seg in enumerate(segments):
        t0 = float(seg.get("t0", 0.0)) * duration
        t1 = float(seg.get("t1", 1.0)) * duration
        s0 = int(t0 * sample_rate)
        s1 = min(n, int(t1 * sample_rate))
        if s0 >= n or s1 <= s0:
            continue

        chord = chord_sets[i % len(chord_sets)]
        seg_n = s1 - s0
        seg_t = np.arange(seg_n, dtype=np.float32) / sample_rate

        seg_dur = max(0.05, (s1 - s0) / sample_rate)
        att = min(0.3, seg_dur * 0.2)
        dec = min(0.2, seg_dur * 0.15)
        rel = min(0.3, seg_dur * 0.2)
        env = _adsr(seg_n, sample_rate, a=att, d=dec, s=0.75, r=rel)
        for midi, amp in chord:
            freq = _midi_to_hz(midi + rng.uniform(-0.03, 0.03))
            # Lush dual oscillator detune
            osc1 = np.sin(2 * np.pi * freq * seg_t)
            osc2 = np.sin(2 * np.pi * (freq * 1.003) * seg_t)
            wave = (osc1 + osc2) * 0.5
            lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.15 * seg_t)
            audio[s0:s1] += wave * lfo * env * (amp * energy * 1.2)

        # Subtle rhythmic clock pulses
        beat_interval = 0.5  # 120 bpm half-second clicks
        clock_t = t0 + 0.2
        while clock_t < t1 - 0.2:
            cs = int(clock_t * sample_rate)
            _add_telemetry_beep(audio, cs, sample_rate, pitch=1200.0)
            clock_t += beat_interval

        # Whoosh at segment start
        if i > 0:
            _add_whoosh_transition(audio, s0 - int(0.2 * sample_rate), sample_rate, rng)

        # 2. Synchronized Offline Narration with Music Ducking
        if voice_enabled:
            lines = documentary_narration_lines(seg)
            if lines:
                speech = speak_documentary(
                    lines,
                    sample_rate=sample_rate,
                    pitch=1.0,
                    speed=0.98,
                    seed=seed + i * 47,
                )
                max_speech_len = int(max(0.5, (t1 - t0) - 0.4) * sample_rate)
                if len(speech) > max_speech_len:
                    speech = speech[:max_speech_len]

                speech_start = s0 + int(0.3 * sample_rate)
                # Intelligently duck the background bed music during speech
                mix_speech_at(
                    audio,
                    speech,
                    speech_start,
                    bed_gain=0.20,     # Music drops to 20% (-14dB) while speaking
                    speech_gain=1.05,   # Clear articulate voice level
                )

    # Reverb and smooth master fade
    audio = _soft_reverb(audio, sample_rate, 0.38)
    fade_len = min(n // 8, int(1.2 * sample_rate))
    if fade_len > 1:
        audio[:fade_len] *= np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        audio[-fade_len:] *= np.linspace(1.0, 0.0, fade_len, dtype=np.float32)

    peak = float(np.max(np.abs(audio)) + 1e-9)
    return (audio / peak * 0.88).astype(np.float32)
