"""Offline procedural voice synthesis for kids educational narration."""

from __future__ import annotations

import re

import numpy as np

# Simplified phoneme inventory: (F1, F2, voiced, duration_ms_base)
_PHONEMES: dict[str, tuple[float, float, bool, float]] = {
    "AA": (800, 1200, True, 110),
    "AE": (700, 1800, True, 100),
    "AH": (600, 1400, True, 90),
    "AO": (650, 950, True, 110),
    "AW": (650, 1100, True, 130),
    "AY": (600, 1700, True, 120),
    "B": (200, 800, False, 70),
    "CH": (200, 1800, False, 80),
    "D": (250, 1700, False, 70),
    "DH": (200, 1600, False, 60),
    "EH": (550, 1900, True, 95),
    "ER": (500, 1500, True, 100),
    "EY": (450, 2200, True, 110),
    "F": (200, 1400, False, 75),
    "G": (250, 2000, False, 70),
    "HH": (400, 1500, False, 50),
    "IH": (350, 2300, True, 85),
    "IY": (300, 2500, True, 100),
    "JH": (250, 1800, False, 75),
    "K": (250, 2000, False, 70),
    "L": (350, 1200, True, 70),
    "M": (300, 1000, True, 85),
    "N": (350, 1500, True, 75),
    "NG": (350, 1400, True, 80),
    "OW": (500, 900, True, 120),
    "OY": (500, 1200, True, 130),
    "P": (200, 900, False, 65),
    "R": (400, 1300, True, 70),
    "S": (200, 5000, False, 90),
    "SH": (250, 2500, False, 95),
    "T": (250, 1800, False, 65),
    "TH": (200, 4500, False, 70),
    "UH": (450, 1100, True, 90),
    "UW": (350, 800, True, 110),
    "V": (200, 1200, False, 75),
    "W": (300, 900, True, 70),
    "Y": (300, 2200, True, 70),
    "Z": (250, 5000, False, 85),
    "ZH": (250, 2500, False, 85),
    "SIL": (0, 0, False, 60),
}

# Common kids words -> phoneme strings (ARPAbet-lite)
_WORD_PHONEMES: dict[str, str] = {
    "A": "EY",
    "B": "B IY",
    "C": "S IY",
    "D": "D IY",
    "E": "IY",
    "F": "EH F",
    "G": "JH IY",
    "H": "EY CH",
    "I": "AY",
    "J": "JH EY",
    "K": "K EY",
    "L": "EH L",
    "M": "EH M",
    "N": "EH N",
    "O": "OW",
    "P": "P IY",
    "Q": "K Y UW",
    "R": "AA R",
    "S": "EH S",
    "T": "T IY",
    "U": "Y UW",
    "V": "V IY",
    "W": "D AH B AH L Y UW",
    "X": "EH K S",
    "Y": "W AY",
    "Z": "Z IY",
    "APPLE": "AE P AH L",
    "BALL": "B AO L",
    "CAT": "K AE T",
    "DOG": "D AO G",
    "SUN": "S AH N",
    "STAR": "S T AA R",
    "CIRCLE": "S ER K AH L",
    "SQUARE": "S K W EH R",
    "TRIANGLE": "T R AY AE NG G AH L",
    "HEART": "HH AA R T",
    "RED": "R EH D",
    "BLUE": "B L UW",
    "GREEN": "G R IY N",
    "YELLOW": "Y EH L OW",
    "ORANGE": "AO R AH N JH",
    "PURPLE": "P ER P AH L",
    "PINK": "P IH NG K",
    "ONE": "W AH N",
    "TWO": "T UW",
    "THREE": "TH R IY",
    "FOUR": "F AO R",
    "FIVE": "F AY V",
    "DRAW": "D R AO",
    "LEARN": "L ER N",
    "FUN": "F AH N",
    "GREAT": "G R EY T",
    "HELLO": "HH AH L OW",
    "HOUSE": "HH AW S",
    "FLOWER": "F L AW ER",
    "CLOUD": "K L AW D",
    "FISH": "F IH SH",
    "BIRD": "B ER D",
    "TREE": "T R IY",
    "MOON": "M UW N",
    "RAINBOW": "R EY N B OW",
    "LET": "L EH T",
    "SAYS": "S EH Z",
    "THIS": "DH IH S",
    "IS": "IH Z",
    "FOR": "F AO R",
    "THE": "DH AH",
    "CAN": "K AE N",
    "YOU": "Y UW",
    "SEE": "S IY",
    "IT": "IH T",
    "COUNT": "K AW N T",
    "WITH": "W IH DH",
    "ME": "M IY",
    "COLOR": "K AH L ER",
    "SHAPE": "SH EY P",
    "SCRIBBLE": "S K R IH B AH L",
    "DOODLE": "D UW D AH L",
    "SKETCH": "S K EH CH",
    "STEP": "S T EH P",
}


def _grapheme_rules(word: str) -> str:
    """Fallback grapheme-to-phoneme for simple English words."""
    w = word.upper()
    if w in _WORD_PHONEMES:
        return _WORD_PHONEMES[w]

    out: list[str] = []
    i = 0
    while i < len(w):
        ch = w[i]
        nxt = w[i + 1] if i + 1 < len(w) else ""
        pair = ch + nxt

        if pair in {"TH", "SH", "CH"}:
            out.append(pair)
            i += 2
            continue
        if pair in {"EE", "EA"}:
            out.append("IY")
            i += 2
            continue
        if pair == "OO":
            out.append("UW")
            i += 2
            continue
        if pair == "OU":
            out.append("AW")
            i += 2
            continue
        if ch in "AEIOU":
            vowel = {"A": "AE", "E": "EH", "I": "IH", "O": "AO", "U": "AH"}.get(ch, "AH")
            out.append(vowel)
        elif ch == "Y" and i > 0:
            out.append("IY")
        elif ch == "R":
            out.append("R")
        elif ch == "L":
            out.append("L")
        elif ch == "W":
            out.append("W")
        elif ch in "BCDFGHJKPQSZ":
            out.append(ch if ch in _PHONEMES else "SIL")
        elif ch == "X":
            out.extend(["K", "S"])
        elif ch == "C" and nxt in "EIY":
            out.append("S")
        elif ch == "C":
            out.append("K")
        elif ch == "G":
            out.append("G")
        elif ch == "M":
            out.append("M")
        elif ch == "N":
            out.append("N")
        elif ch == "T":
            out.append("T")
        elif ch == "D":
            out.append("D")
        i += 1
    return " ".join(out) if out else "AH"


def text_to_phonemes(text: str) -> list[str]:
    """Convert kids-friendly text into a phoneme sequence."""
    text = re.sub(r"[^A-Za-z0-9\s'/]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ["SIL"]

    phonemes: list[str] = []
    for token in text.split():
        token = token.upper()
        if token in _WORD_PHONEMES:
            phonemes.extend(_WORD_PHONEMES[token].split())
        else:
            phonemes.extend(_grapheme_rules(token).split())
        phonemes.append("SIL")
    return phonemes


def _formant_tone(
    n: int,
    sr: int,
    f0: float,
    f1: float,
    f2: float,
    rng: np.random.Generator,
) -> np.ndarray:
    t = np.arange(n, dtype=np.float32) / sr
    # Gentle pitch vibrato for friendly kid-teacher tone
    vibrato = 1.0 + 0.012 * np.sin(2 * np.pi * 5.5 * t)
    phase = 2 * np.pi * f0 * vibrato * t
    glottal = np.sin(phase) + 0.35 * np.sin(2 * phase) + 0.15 * np.sin(3 * phase)
    form1 = 0.55 * np.sin(2 * np.pi * f1 * t)
    form2 = 0.35 * np.sin(2 * np.pi * f2 * t)
    return (glottal * 0.55 + form1 + form2).astype(np.float32)


def _noise_burst(n: int, sr: int, rng: np.random.Generator, bright: float = 1.0) -> np.ndarray:
    noise = (rng.random(n).astype(np.float32) * 2 - 1)
    t = np.arange(n, dtype=np.float32) / sr
    env = np.exp(-t * (18 + 8 * bright))
    return noise * env


def _synthesize_phoneme(
    ph: str,
    sr: int,
    f0: float,
    speed: float,
    rng: np.random.Generator,
) -> np.ndarray:
    spec = _PHONEMES.get(ph, _PHONEMES["AH"])
    f1, f2, voiced, dur_ms = spec
    n = max(1, int((dur_ms / speed) * sr / 1000))

    if ph == "SIL":
        return np.zeros(n, dtype=np.float32)

    env = np.ones(n, dtype=np.float32)
    attack = max(1, n // 12)
    release = max(1, n // 8)
    env[:attack] = np.linspace(0, 1, attack, dtype=np.float32)
    env[-release:] = np.linspace(1, 0, release, dtype=np.float32)

    if voiced:
        tone = _formant_tone(n, sr, f0, max(200, f1), max(400, f2), rng)
    else:
        bright = 1.0 if ph in {"S", "SH", "F", "TH", "Z", "ZH"} else 0.4
        tone = _noise_burst(n, sr, rng, bright=bright)
        if ph in {"B", "D", "G", "P", "T", "K"}:
            burst = max(1, n // 6)
            tone[:burst] *= 2.5

    return tone * env * 0.85


def synthesize_speech(
    text: str,
    *,
    sample_rate: int = 44100,
    pitch: float = 1.18,
    speed: float = 0.92,
    seed: int = 0,
) -> np.ndarray:
    """
    Synthesize kid-friendly narration from text entirely offline.

    Returns mono float32 audio in roughly [-1, 1].
    """
    rng = np.random.default_rng(seed)
    phonemes = text_to_phonemes(text)
    f0 = 195.0 * pitch
    chunks: list[np.ndarray] = []
    for ph in phonemes:
        chunks.append(_synthesize_phoneme(ph, sample_rate, f0, speed, rng))
    if not chunks:
        return np.zeros(1, dtype=np.float32)
    audio = np.concatenate(chunks).astype(np.float32)
    # Light warmth
    if len(audio) > 4:
        smoothed = np.copy(audio)
        smoothed[1:-1] = (audio[:-2] * 0.15 + audio[1:-1] * 0.7 + audio[2:] * 0.15)
        audio = smoothed
    peak = float(np.max(np.abs(audio)) + 1e-9)
    return (audio / peak * 0.82).astype(np.float32)


def mix_speech_at(
    bed: np.ndarray,
    speech: np.ndarray,
    start_sample: int,
    *,
    bed_gain: float = 0.35,
    speech_gain: float = 0.95,
    attack_samples: int | None = None,
    release_samples: int | None = None,
) -> None:
    """Mix speech into bed with a smooth, click-free ducking envelope."""
    if start_sample >= len(bed) or len(speech) == 0:
        return
    end = min(len(bed), start_sample + len(speech))
    n = end - start_sample
    if n <= 0:
        return
    seg = speech[:n]
    attack = min(n, max(1, int(attack_samples if attack_samples is not None else min(2205, n // 5))))
    release = min(n, max(1, int(release_samples if release_samples is not None else min(4410, n // 4))))
    duck = np.full(n, float(bed_gain), dtype=np.float32)
    duck[:attack] = np.linspace(1.0, bed_gain, attack, dtype=np.float32)
    duck[-release:] = np.maximum(
        duck[-release:],
        np.linspace(bed_gain, 1.0, release, dtype=np.float32),
    )
    bed[start_sample:end] = bed[start_sample:end] * duck + seg * speech_gain
