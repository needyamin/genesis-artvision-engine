"""Educational kids soundtrack synced to alphabet lesson segments."""

from __future__ import annotations

from typing import Any

import numpy as np

from app.audio.procedural_music import _adsr, _midi_to_hz, _osc, _soft_reverb


def _letter_midi(letter: str) -> float:
    """Map A-Z / 0-9 to cheerful xylophone-ish pitches."""
    if letter.isdigit():
        return 60 + int(letter)  # C4..
    idx = ord(letter.upper()) - ord("A")
    # Major-ish steps across two octaves
    scale = [0, 2, 4, 5, 7, 9, 11]
    octave = 60 + (idx // 7) * 12
    return float(octave + scale[idx % 7])


def generate_kids_education_audio(
    duration: float,
    seed: int,
    lesson: dict[str, Any],
    *,
    sample_rate: int = 44100,
) -> np.ndarray:
    """
    Build a kids learning soundtrack aligned with lesson segments.

    - Soft happy pad bed
    - Letter chime at each segment start
    - Short melody flourish for the word
    - Light rhythmic clap/tick for engagement
    """
    rng = np.random.default_rng(seed + 91)
    n = max(1, int(duration * sample_rate))
    audio = np.zeros(n, dtype=np.float32)
    t = np.arange(n, dtype=np.float32) / sample_rate

    # Cheerful pad bed (C major)
    for midi, amp in ((48, 0.07), (55, 0.05), (60, 0.04), (67, 0.03)):
        wave = _osc(_midi_to_hz(midi + rng.uniform(-0.05, 0.05)), n, sample_rate, "sine", rng)
        lfo = 0.55 + 0.45 * np.sin(2 * np.pi * (0.05 + amp) * t)
        audio += wave * lfo * amp

    segments = list(lesson.get("segments") or [])
    if not segments:
        segments = [{"t0": 0.0, "t1": 1.0, "letter": "A", "word": "APPLE"}]

    tempo = float(rng.uniform(88, 112))
    beat = 60.0 / tempo

    for seg in segments:
        t0 = float(seg.get("t0", 0.0)) * duration
        t1 = float(seg.get("t1", 1.0)) * duration
        letter = str(seg.get("letter", "A"))
        word = str(seg.get("word", "FUN"))
        start = int(t0 * sample_rate)
        if start >= n:
            continue

        # Letter chime (two-note "name" ping)
        root = _letter_midi(letter)
        for j, (midi, length, amp) in enumerate(
            ((root, 0.28, 0.22), (root + 7, 0.22, 0.16), (root + 12, 0.18, 0.12))
        ):
            nn = max(1, int(length * sample_rate))
            s0 = start + int(j * 0.12 * sample_rate)
            s1 = min(n, s0 + nn)
            if s0 >= n:
                break
            tone = _osc(_midi_to_hz(midi), s1 - s0, sample_rate, "triangle", rng)
            env = _adsr(s1 - s0, sample_rate, a=0.01, d=0.08, s=0.45, r=0.15)
            audio[s0:s1] += tone * env * amp

        # Word flourish — short ascending notes for each letter of word (max 6)
        for k, ch in enumerate(word[:6]):
            midi = _letter_midi(ch if ch.isalpha() else letter)
            nn = max(1, int(0.14 * sample_rate))
            s0 = start + int((0.45 + k * 0.12) * sample_rate)
            s1 = min(n, s0 + nn)
            if s0 >= n:
                break
            tone = _osc(_midi_to_hz(midi + 12), s1 - s0, sample_rate, "sine", rng)
            env = _adsr(s1 - s0, sample_rate, a=0.005, d=0.05, s=0.35, r=0.08)
            audio[s0:s1] += tone * env * 0.11

        # Soft learning ticks during segment
        seg_len = max(0.2, t1 - t0)
        tick_t = t0 + 0.5
        while tick_t < t1 - 0.15:
            s0 = int(tick_t * sample_rate)
            nn = max(1, int(0.04 * sample_rate))
            s1 = min(n, s0 + nn)
            click = rng.random(s1 - s0).astype(np.float32) * 2 - 1
            env = np.linspace(1.0, 0.0, s1 - s0, dtype=np.float32)
            audio[s0:s1] += click * env * 0.03
            tick_t += beat

    # End celebration arpeggio
    end_start = max(0.0, duration - 1.4)
    for j, midi in enumerate((60, 64, 67, 72, 79)):
        s0 = int((end_start + j * 0.18) * sample_rate)
        nn = max(1, int(0.3 * sample_rate))
        s1 = min(n, s0 + nn)
        if s0 >= n:
            break
        tone = _osc(_midi_to_hz(midi), s1 - s0, sample_rate, "triangle", rng)
        env = _adsr(s1 - s0, sample_rate, a=0.01, d=0.08, s=0.4, r=0.2)
        audio[s0:s1] += tone * env * 0.14

    audio = _soft_reverb(audio, sample_rate, 0.35)
    fade = min(n // 12, int(0.8 * sample_rate))
    if fade > 1:
        audio[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        audio[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    peak = float(np.max(np.abs(audio)) + 1e-9)
    return (audio / peak * 0.85).astype(np.float32)
