"""Procedural music / ambient audio generation."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.utils.logger import get_logger

logger = get_logger("audio")

# Pleasant scales (semitone offsets)
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "pentatonic": [0, 2, 4, 7, 9],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
}


def _midi_to_hz(midi: float) -> float:
    return 440.0 * (2.0 ** ((midi - 69.0) / 12.0))


def _adsr(n: int, sr: int, a: float = 0.05, d: float = 0.1, s: float = 0.7, r: float = 0.2) -> np.ndarray:
    env = np.ones(n, dtype=np.float32) * s
    a_n = max(1, int(a * sr))
    d_n = max(1, int(d * sr))
    r_n = max(1, int(r * sr))
    env[:a_n] = np.linspace(0, 1, a_n, dtype=np.float32)
    start = a_n
    end = min(n, a_n + d_n)
    if end > start:
        env[start:end] = np.linspace(1, s, end - start, dtype=np.float32)
    if r_n < n:
        env[-r_n:] = np.linspace(env[-r_n] if r_n < n else s, 0, r_n, dtype=np.float32)
    return env


def _osc(freq: float, n: int, sr: int, kind: str, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(n, dtype=np.float32) / sr
    phase = 2 * np.pi * freq * t
    if kind == "sine":
        return np.sin(phase)
    if kind == "triangle":
        return 2 * np.abs(2 * (t * freq % 1) - 1) - 1
    if kind == "saw":
        return 2 * (t * freq % 1) - 1
    if kind == "square":
        return np.sign(np.sin(phase) + 1e-9)
    # soft noise burst
    return (rng.random(n).astype(np.float32) * 2 - 1) * 0.3


def _soft_reverb(x: np.ndarray, sr: int, amount: float) -> np.ndarray:
    if amount <= 0.05:
        return x
    delays = [int(0.03 * sr), int(0.07 * sr), int(0.13 * sr)]
    out = x.copy()
    for i, d in enumerate(delays):
        if d >= len(x):
            continue
        delayed = np.zeros_like(x)
        delayed[d:] = x[:-d] * (0.35 * amount / (i + 1))
        out += delayed
    return out


def generate_procedural_audio(
    duration: float,
    seed: int,
    *,
    sample_rate: int = 44100,
    style: str = "ambient",
) -> np.ndarray:
    """
    Generate a mono float32 waveform in [-1, 1] for the given duration.

    Styles lean ambient / synth pad / soft melody suitable for abstract video.
    """
    rng = np.random.default_rng(seed)
    n = max(1, int(duration * sample_rate))
    audio = np.zeros(n, dtype=np.float32)

    scale_name = str(rng.choice(list(SCALES.keys())))
    scale = SCALES[scale_name]
    root = int(rng.integers(48, 60))  # C2-C3 range-ish
    tempo = float(rng.uniform(60, 100))
    beat = 60.0 / tempo
    osc_kind = str(rng.choice(["sine", "triangle", "saw", "sine"]))
    mode = str(rng.choice(["drone", "pad", "melody", "rhythm"], p=[0.25, 0.35, 0.25, 0.15]))

    # Style bias
    if style in {"calm", "dreamlike", "organic"}:
        mode = str(rng.choice(["drone", "pad"]))
        osc_kind = "sine"
    elif style in {"neon", "futuristic", "digital"}:
        osc_kind = str(rng.choice(["saw", "square", "triangle"]))
        mode = str(rng.choice(["melody", "rhythm", "pad"]))
    elif style in {"chaotic", "psychedelic"}:
        mode = str(rng.choice(["melody", "rhythm"]))
        tempo = float(rng.uniform(90, 130))
        beat = 60.0 / tempo

    # Drone / pad bed
    for partial in range(3):
        deg = scale[int(rng.integers(0, len(scale)))]
        midi = root + deg + 12 * int(rng.integers(0, 2))
        freq = _midi_to_hz(midi + partial * 0.02)
        wave = _osc(freq, n, sample_rate, "sine" if mode == "drone" else osc_kind, rng)
        # slow amplitude LFO
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.03 + partial * 0.01) * np.arange(n) / sample_rate)
        audio += wave * lfo * (0.12 / (partial + 1))

    # Melodic / rhythmic notes
    if mode in {"melody", "rhythm", "pad"}:
        t = 0.0
        while t < duration - 0.2:
            note_len = beat * float(rng.choice([0.5, 1.0, 1.5, 2.0]))
            if mode == "rhythm":
                note_len = beat * float(rng.choice([0.25, 0.5, 1.0]))
            nn = max(1, int(note_len * sample_rate))
            start = int(t * sample_rate)
            end = min(n, start + nn)
            if start >= n:
                break
            deg = scale[int(rng.integers(0, len(scale)))]
            octave = int(rng.choice([0, 12, 24], p=[0.3, 0.5, 0.2]))
            freq = _midi_to_hz(root + deg + octave)
            seg = _osc(freq, end - start, sample_rate, osc_kind, rng)
            env = _adsr(end - start, sample_rate, a=0.02, d=0.08, s=0.55, r=min(0.3, note_len * 0.4))
            audio[start:end] += seg * env * float(rng.uniform(0.08, 0.18))
            # Rest occasionally
            t += note_len + float(rng.choice([0.0, 0.0, beat * 0.5]))

    # Soft high shimmer
    shimmer_freq = _midi_to_hz(root + 24 + scale[int(rng.integers(0, len(scale)))])
    shimmer = _osc(shimmer_freq, n, sample_rate, "sine", rng)
    shimmer_env = 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * np.arange(n) / sample_rate)
    audio += shimmer * shimmer_env * 0.04

    amount = float(rng.uniform(0.25, 0.7))
    audio = _soft_reverb(audio, sample_rate, amount)

    # Gentle fade in/out
    fade = min(n // 10, int(1.5 * sample_rate))
    if fade > 1:
        audio[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        audio[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)

    peak = float(np.max(np.abs(audio)) + 1e-9)
    audio = audio / peak * 0.85
    return audio.astype(np.float32)


def write_wav(path: Path, samples: np.ndarray, sample_rate: int = 44100) -> None:
    """Write mono float samples to a 16-bit PCM WAV file."""
    import wave
    import struct

    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
