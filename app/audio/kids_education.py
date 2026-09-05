"""Educational kids soundtrack synced to lesson segments with offline narration."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

import numpy as np

from app.audio.offline_tts import kids_narration_lines, speak_narration
from app.audio.procedural_music import _adsr, _midi_to_hz, _osc, _soft_reverb
from app.audio.procedural_voice import mix_speech_at

ProgressFn = Callable[[dict[str, Any]], None]

# Chime, then the teacher speaks. Short tail so the next letter follows promptly.
VOICE_LEAD_SEC = 0.40
VOICE_TAIL_SEC = 0.55
MIN_SEGMENT_SEC = 3.2
END_PAD_SEC = 1.4


def _letter_midi(letter: str) -> float:
    """Map A-Z / 0-9 to cheerful xylophone-ish pitches."""
    if letter.isdigit():
        return 60 + int(letter)  # C4..
    idx = ord(letter.upper()) - ord("A")
    # Major-ish steps across two octaves
    scale = [0, 2, 4, 5, 7, 9, 11]
    octave = 60 + (idx // 7) * 12
    return float(octave + scale[idx % 7])


def estimate_kids_speech_seconds(lines: list[str]) -> float:
    """Fallback length when TTS has not been generated yet."""
    cleaned = [" ".join(str(line).split()).strip() for line in lines if str(line).strip()]
    if not cleaned:
        return MIN_SEGMENT_SEC
    words = sum(max(1, len(line.split())) for line in cleaned)
    letters = sum(1 for line in cleaned for tok in line.split() if len(tok.strip(".,!?")) == 1)
    pauses = 0.35 * max(0, len(cleaned) - 1)
    return max(1.8, words / 1.85 + letters * 0.22 + pauses)


def fit_lesson_to_narration(
    lesson: dict[str, Any],
    *,
    seed: int,
    sample_rate: int = 44100,
    audio_profile: dict[str, Any] | None = None,
    min_duration: float = 0.0,
    measure_speech: bool = True,
    on_progress: ProgressFn | None = None,
) -> float:
    """
    Size each lesson beat so the full kids voice can play while that letter stays on screen.

    Returns the new duration in seconds. Updates segment t0/t1 fractions in place.
    """
    segments = list(lesson.get("segments") or [])
    if not segments:
        total = max(float(min_duration), float(lesson.get("duration") or 1.0), 1.0)
        lesson["duration"] = total
        return total

    profile = audio_profile if isinstance(audio_profile, dict) else {}
    voice_rate = float(max(0.70, min(0.94, profile.get("voice_rate", 0.86))))
    voice_pitch = float(max(1.02, min(1.16, profile.get("voice_pitch", 1.10))))
    engine = str(lesson.get("engine", "alphabet_cartoon"))
    pitch = voice_pitch if engine != "hand_art" else min(voice_pitch, 1.12)

    n_seg = len(segments)
    durations: list[float] = [0.0] * n_seg
    tts_workers = 1
    if measure_speech:
        tts_workers = max(1, min(8, n_seg, os.cpu_count() or 4))

    def _measure(i: int) -> tuple[int, float, float]:
        seg = segments[i]
        lines = kids_narration_lines(seg)
        speech_sec = estimate_kids_speech_seconds(lines)
        if measure_speech and lines:
            speech = speak_narration(
                lines,
                sample_rate=sample_rate,
                pitch=pitch,
                speed=voice_rate,
                seed=seed + int(seg.get("index", i)) * 131,
                kids=True,
            )
            if len(speech) > 8:
                speech_sec = max(speech_sec, len(speech) / float(sample_rate))
        lead = VOICE_LEAD_SEC if i else max(VOICE_LEAD_SEC, 0.7)
        return i, speech_sec, lead

    if tts_workers <= 1:
        measured = [_measure(i) for i in range(n_seg)]
    else:
        measured = []
        with ThreadPoolExecutor(max_workers=tts_workers) as pool:
            futs = {pool.submit(_measure, i): i for i in range(n_seg)}
            done = 0
            for fut in as_completed(futs):
                i, speech_sec, lead = fut.result()
                measured.append((i, speech_sec, lead))
                done += 1
                if on_progress:
                    seg = segments[i]
                    letter = str(seg.get("letter") or seg.get("word") or i + 1)
                    on_progress(
                        {
                            "phase": "voice",
                            "frame": done,
                            "total_frames": n_seg,
                            "message": f"Kids voice · {letter} ({done} of {n_seg})",
                        }
                    )
        measured.sort(key=lambda row: row[0])

    for i, speech_sec, lead in measured:
        if tts_workers <= 1 and on_progress:
            seg = segments[i]
            letter = str(seg.get("letter") or seg.get("word") or i + 1)
            on_progress(
                {
                    "phase": "voice",
                    "frame": i + 1,
                    "total_frames": n_seg,
                    "message": f"Kids voice · {letter} ({i + 1} of {n_seg})",
                }
            )
        hold = max(MIN_SEGMENT_SEC, lead + speech_sec + VOICE_TAIL_SEC)
        segments[i]["speech_lead"] = lead
        segments[i]["speech_seconds"] = float(speech_sec)
        durations[i] = hold

    total = float(sum(durations) + END_PAD_SEC)
    total = max(total, float(min_duration), 1.0)
    # If the user asked for a longer video, stretch beats evenly after speech is covered.
    extra = total - (sum(durations) + END_PAD_SEC)
    if extra > 0.05 and durations:
        bump = extra / len(durations)
        durations = [d + bump for d in durations]
        total = float(sum(durations) + END_PAD_SEC)

    t = 0.0
    for seg, hold in zip(segments, durations):
        seg["t0"] = t / total
        seg["t1"] = (t + hold) / total
        t += hold

    lesson["duration"] = total
    lesson["speech_synced"] = True
    return total


def generate_kids_education_audio(
    duration: float,
    seed: int,
    lesson: dict[str, Any],
    *,
    sample_rate: int = 44100,
    voice_enabled: bool = True,
    audio_profile: dict[str, Any] | None = None,
) -> np.ndarray:
    """
    Build a kids learning soundtrack aligned with lesson segments.

    - Soft happy pad bed
    - Letter/chime at each segment start
    - Short melody flourish for words
    - Offline kids voice: Windows TTS when available, procedural fallback
    """
    rng = np.random.default_rng(seed + 91)
    n = max(1, int(round(duration * sample_rate)))
    audio = np.zeros(n, dtype=np.float32)
    t = np.arange(n, dtype=np.float32) / sample_rate
    profile = audio_profile if isinstance(audio_profile, dict) else {}
    energy = float(max(0.0, min(1.0, profile.get("energy", 0.55))))
    pad_brightness = float(max(0.0, min(1.0, profile.get("pad_brightness", 0.45))))
    chime_density = float(max(0.0, min(1.0, profile.get("chime_density", 0.7))))
    voice_rate = float(max(0.70, min(0.94, profile.get("voice_rate", 0.86))))
    voice_pitch = float(max(1.02, min(1.16, profile.get("voice_pitch", 1.10))))

    # Cheerful pad bed (C major / profile scale)
    pad_notes = ((48, 0.07), (55, 0.05), (60, 0.04), (67, 0.03))
    if pad_brightness > 0.55:
        pad_notes = pad_notes + ((72, 0.025), (79, 0.02))
    pad_gain = 0.75 + 0.6 * energy
    for midi, amp in pad_notes:
        bright = 1.0 + 0.35 * pad_brightness
        wave = _osc(_midi_to_hz(midi + rng.uniform(-0.05, 0.05)), n, sample_rate, "sine", rng)
        lfo = 0.55 + 0.45 * np.sin(2 * np.pi * (0.05 + amp) * t)
        audio += wave * lfo * amp * pad_gain * bright

    engine = str(lesson.get("engine", "alphabet_cartoon"))
    segments = list(lesson.get("segments") or [])
    if not segments:
        segments = [{"t0": 0.0, "t1": 1.0, "letter": "A", "word": "APPLE", "voice_line": "A is for apple"}]

    tempo = float(profile.get("tempo_bpm") or rng.uniform(88, 112))
    tempo = max(40.0, min(180.0, tempo))
    beat = 60.0 / tempo
    chime_amp = 0.12 + 0.18 * chime_density * energy

    for seg in segments:
        t0 = float(seg.get("t0", 0.0)) * duration
        t1 = float(seg.get("t1", 1.0)) * duration
        letter = str(seg.get("letter", seg.get("color_name", "A"))[:1] or "A")
        word = str(seg.get("word", "FUN"))
        shape = str(seg.get("shape", ""))
        start = int(t0 * sample_rate)
        if start >= n:
            continue

        # Segment chime — letter, color name, or shape cue
        if engine == "kids_doodles" and seg.get("color_name"):
            root = _letter_midi(str(seg["color_name"])[0])
        elif engine == "hand_art":
            root = _letter_midi(word[0] if word else "A")
        else:
            root = _letter_midi(letter)

        chime_notes = ((root, 0.28, 0.22), (root + 7, 0.22, 0.16), (root + 12, 0.18, 0.12))
        if chime_density < 0.35:
            chime_notes = chime_notes[:1]
        elif chime_density > 0.8:
            chime_notes = chime_notes + ((root + 16, 0.14, 0.08),)

        for j, (midi, length, amp) in enumerate(chime_notes):
            nn = max(1, int(length * sample_rate))
            s0 = start + int(j * 0.12 * sample_rate)
            s1 = min(n, s0 + nn)
            if s0 >= n:
                break
            tone = _osc(_midi_to_hz(midi), s1 - s0, sample_rate, "triangle", rng)
            env = _adsr(s1 - s0, sample_rate, a=0.01, d=0.08, s=0.45, r=0.15)
            audio[s0:s1] += tone * env * amp * (0.55 + chime_amp)

        # Keep flourish off while the teacher is speaking so kids hear the word clearly.
        if not voice_enabled:
            flourish = word if word else shape.upper()
            flourish_n = max(2, int(round(6 * chime_density)))
            for k, ch in enumerate(flourish[:flourish_n]):
                midi = _letter_midi(ch if ch.isalpha() else letter)
                nn = max(1, int(0.14 * sample_rate))
                s0 = start + int((0.55 + k * 0.1) * sample_rate)
                s1 = min(n, s0 + nn)
                if s0 >= n:
                    break
                tone = _osc(_midi_to_hz(midi + 12), s1 - s0, sample_rate, "sine", rng)
                env = _adsr(s1 - s0, sample_rate, a=0.005, d=0.05, s=0.35, r=0.08)
                audio[s0:s1] += tone * env * (0.06 + 0.08 * energy)

        if voice_enabled:
            lines = kids_narration_lines(seg)
            if lines:
                pitch = voice_pitch if engine != "hand_art" else min(voice_pitch, 1.12)
                speech = speak_narration(
                    lines,
                    sample_rate=sample_rate,
                    pitch=pitch,
                    speed=voice_rate,
                    seed=seed + int(seg.get("index", 0)) * 131,
                    kids=True,
                )
                lead = float(seg.get("speech_lead", VOICE_LEAD_SEC))
                voice_start = start + int(lead * sample_rate)
                # Never cut the teacher mid-word. Clip only if the clip would leave the file.
                room = max(0, n - voice_start)
                if room <= 0:
                    continue
                if len(speech) > room:
                    speech = speech[:room]
                mix_speech_at(audio, speech, voice_start, bed_gain=0.18, speech_gain=1.0)

        # Soft learning ticks during the repeat/think tail, after speech when possible
        speech_end = t0 + float(seg.get("speech_lead", VOICE_LEAD_SEC)) + float(seg.get("speech_seconds") or 0.0)
        tick_t = max(t0 + 0.65, speech_end + 0.08)
        tick_step = beat / max(0.35, chime_density)
        while tick_t < t1 - 0.15:
            s0 = int(tick_t * sample_rate)
            nn = max(1, int(0.04 * sample_rate))
            s1 = min(n, s0 + nn)
            if s0 >= n:
                break
            click = rng.random(s1 - s0).astype(np.float32) * 2 - 1
            env = np.linspace(1.0, 0.0, s1 - s0, dtype=np.float32)
            audio[s0:s1] += click * env * (0.012 + 0.014 * chime_density)
            tick_t += tick_step

    # End celebration arpeggio in the reserved tail
    end_start = max(0.0, duration - END_PAD_SEC)
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
