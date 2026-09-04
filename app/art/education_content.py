"""Random educational content for kids alphabet videos."""

from __future__ import annotations

from typing import Any

import numpy as np

# Multiple easy learning words per letter
LETTER_WORDS: dict[str, list[str]] = {
    "A": ["APPLE", "ANT", "AIRPLANE", "ALLIGATOR"],
    "B": ["BALL", "BIRD", "BUS", "BANANA"],
    "C": ["CAT", "CAKE", "CAR", "CLOUD"],
    "D": ["DOG", "DUCK", "DRUM", "DOOR"],
    "E": ["EGG", "ELEPHANT", "EAR", "EARTH"],
    "F": ["FISH", "FROG", "FLOWER", "FAN"],
    "G": ["GRAPE", "GOAT", "GIRL", "GIFT"],
    "H": ["HOUSE", "HAT", "HORSE", "HAND"],
    "I": ["ICE", "IGLOO", "INSECT", "ISLAND"],
    "J": ["JUICE", "JUMP", "JAM", "JACKET"],
    "K": ["KITE", "KING", "KEY", "KANGAROO"],
    "L": ["LION", "LEAF", "LAMP", "LEMON"],
    "M": ["MOON", "MOUSE", "MILK", "MONKEY"],
    "N": ["NEST", "NOSE", "NURSE", "NUT"],
    "O": ["ORANGE", "OWL", "OCTOPUS", "OCEAN"],
    "P": ["PENCIL", "PIG", "PIZZA", "PLANE"],
    "Q": ["QUEEN", "QUACK", "QUILT", "QUESTION"],
    "R": ["RAINBOW", "RABBIT", "ROSE", "ROBOT"],
    "S": ["SUN", "STAR", "SNAKE", "SHIP"],
    "T": ["TREE", "TRAIN", "TIGER", "TURTLE"],
    "U": ["UMBRELLA", "UNICORN", "UP", "UNDER"],
    "V": ["VAN", "VIOLIN", "VEST", "VOLCANO"],
    "W": ["WATER", "WAVE", "WOLF", "WATCH"],
    "X": ["XYLOPHONE", "BOX", "FOX", "SIX"],
    "Y": ["YELLOW", "YARN", "YOYO", "YAK"],
    "Z": ["ZEBRA", "ZOO", "ZIP", "ZERO"],
}

NUMBER_WORDS: dict[str, list[str]] = {
    "0": ["ZERO"],
    "1": ["ONE"],
    "2": ["TWO"],
    "3": ["THREE"],
    "4": ["FOUR"],
    "5": ["FIVE"],
    "6": ["SIX"],
    "7": ["SEVEN"],
    "8": ["EIGHT"],
    "9": ["NINE"],
}

PHONICS: dict[str, str] = {
    "A": "A says /a/ as in apple",
    "B": "B says /b/ as in ball",
    "C": "C says /k/ as in cat",
    "D": "D says /d/ as in dog",
    "E": "E says /e/ as in egg",
    "F": "F says /f/ as in fish",
    "G": "G says /g/ as in goat",
    "H": "H says /h/ as in hat",
    "I": "I says /i/ as in igloo",
    "J": "J says /j/ as in jam",
    "K": "K says /k/ as in kite",
    "L": "L says /l/ as in leaf",
    "M": "M says /m/ as in moon",
    "N": "N says /n/ as in nest",
    "O": "O says /o/ as in orange",
    "P": "P says /p/ as in pig",
    "Q": "Q says /kw/ as in queen",
    "R": "R says /r/ as in rose",
    "S": "S says /s/ as in sun",
    "T": "T says /t/ as in tree",
    "U": "U says /u/ as in up",
    "V": "V says /v/ as in van",
    "W": "W says /w/ as in water",
    "X": "X says /ks/ as in box",
    "Y": "Y says /y/ as in yellow",
    "Z": "Z says /z/ as in zebra",
}

FUN_FACTS: dict[str, list[str]] = {
    "A": ["Ants work as a team!", "Apples can be red or green."],
    "B": ["Birds build nests from twigs.", "Balls can bounce high!"],
    "C": ["Cats love to nap.", "Cars have four wheels."],
    "D": ["Dogs are loyal friends.", "Ducks say quack!"],
    "E": ["Elephants have long trunks.", "Eggs hatch into chicks."],
    "F": ["Fish breathe underwater.", "Flowers need sunshine."],
    "G": ["Goats love to climb.", "Green means go!"],
    "H": ["Horses can run fast.", "Hands help us write."],
    "I": ["Ice is frozen water.", "Insects have six legs."],
    "J": ["Juice comes from fruit.", "Jumping is great exercise!"],
    "K": ["Kites fly in the wind.", "Keys open doors."],
    "L": ["Lions are big cats.", "Leaves change color in fall."],
    "M": ["The moon lights the night.", "Milk helps bones grow."],
    "N": ["Birds live in nests.", "Your nose helps you smell."],
    "O": ["Owls hunt at night.", "The ocean is very deep."],
    "P": ["Pigs like mud baths.", "Pencils help us draw."],
    "Q": ["Queens wear crowns.", "Quilts keep us warm."],
    "R": ["Rabbits hop quickly.", "Rainbows need sun and rain."],
    "S": ["Stars shine at night.", "Snakes have no legs."],
    "T": ["Tigers have stripes.", "Trains ride on tracks."],
    "U": ["Umbrellas keep us dry.", "Unicorns are make-believe!"],
    "V": ["Violins make music.", "Vests keep us cozy."],
    "W": ["Water is important to drink.", "Wolves live in packs."],
    "X": ["A xylophone makes music.", "A fox is clever."],
    "Y": ["Yellow is a bright color!", "Yo-yos go up and down."],
    "Z": ["Zebras have stripes.", "Zoos care for animals."],
}

EASY_SPELL_WORDS = [
    "CAT", "DOG", "SUN", "HAT", "BUS", "RED", "BED", "PEN", "CUP", "MAP",
    "FISH", "BIRD", "TREE", "MOON", "STAR", "BALL", "BOOK", "FROG", "DUCK", "LION",
]

LEARN_TIPS = [
    "Say it out loud!",
    "Trace the letter with your finger.",
    "Can you find this letter at home?",
    "Clap the sounds!",
    "Great job learning!",
    "Try writing it next!",
    "What else starts with this letter?",
]

THEMES = [
    "letter_of_day",
    "abc_chart",
    "word_builder",
    "phonics",
    "animal_friends",
    "count_fun",
]


def pick_word(rng: np.random.Generator, letter: str) -> str:
    letter = letter.upper()
    if letter in LETTER_WORDS:
        return str(rng.choice(LETTER_WORDS[letter]))
    if letter in NUMBER_WORDS:
        return str(rng.choice(NUMBER_WORDS[letter]))
    return "FUN"


def pick_fact(rng: np.random.Generator, letter: str) -> str:
    letter = letter.upper()
    facts = FUN_FACTS.get(letter, ["Learning is fun!"])
    return str(rng.choice(facts))


def motif_key(word: str) -> str:
    """Map a learning word to a drawable motif name used by the engine."""
    known = {
        "APPLE", "BALL", "CAT", "DUCK", "EGG", "FISH", "GRAPE", "HOUSE", "ICE",
        "JAR", "KITE", "LEAF", "MOON", "NEST", "ORANGE", "PENCIL", "QUEEN",
        "RAINBOW", "SUN", "TREE", "UMBRELLA", "VAN", "WAVE", "BOX", "YARN", "ZEBRA",
        "STAR", "DOG", "BIRD", "FROG", "LION", "OWL", "PIG", "RABBIT", "SNAKE",
        "TIGER", "WATER", "FOX", "YELLOW",
    }
    w = word.upper()
    if w in known:
        return w
    # Fallbacks by first letter association
    return LETTER_WORDS.get(w[0], ["STAR"])[0] if w else "STAR"


def build_education_lesson(
    seed: int,
    duration: float,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a reproducible educational lesson plan for one video.

    Every call with the same seed (+ similar params) yields the same lesson.
    """
    params = params or {}
    rng = np.random.default_rng(seed)

    theme = str(params.get("lesson_theme", rng.choice(THEMES)))
    include_numbers = bool(params.get("include_numbers", rng.random() < 0.25))
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    digits = list("0123456789")

    title_map = {
        "letter_of_day": "Letter of the Day",
        "abc_chart": "ABC Learning Chart",
        "word_builder": "Build a Word",
        "phonics": "Phonics Fun",
        "animal_friends": "Animal Alphabet",
        "count_fun": "Numbers & Letters",
    }
    title = title_map.get(theme, "Let's Learn!")

    # Choose letters for this lesson
    if theme == "count_fun" or include_numbers and theme == "abc_chart":
        pool = alphabet + digits if include_numbers else alphabet
    else:
        pool = alphabet

    if theme in {"letter_of_day", "phonics", "animal_friends"}:
        # Focus on a random subset, one at a time
        count = int(rng.integers(5, 9))
        letters = list(rng.choice(pool, size=min(count, len(pool)), replace=False))
        visual_mode = "lesson"
    elif theme == "word_builder":
        word = str(rng.choice(EASY_SPELL_WORDS))
        letters = list(word)
        visual_mode = "spell"
    elif theme == "abc_chart":
        if rng.random() < 0.35:
            letters = list(rng.choice(pool, size=min(int(rng.integers(12, 20)), len(pool)), replace=False))
        else:
            letters = list(pool[:26] if not include_numbers else pool)
        visual_mode = "chart"
    else:
        letters = list(rng.choice(pool, size=min(8, len(pool)), replace=False))
        visual_mode = str(rng.choice(["lesson", "parade", "focus"]))

    n = max(1, len(letters))
    # Time segments covering the full duration
    edges = np.linspace(0.0, 1.0, n + 1)

    segments: list[dict[str, Any]] = []
    for i, letter in enumerate(letters):
        word = pick_word(rng, letter)
        if theme == "animal_friends":
            animal_prefs = {
                "A": "ALLIGATOR", "B": "BIRD", "C": "CAT", "D": "DOG", "E": "ELEPHANT",
                "F": "FISH", "G": "GOAT", "H": "HORSE", "I": "INSECT", "J": "JAM",
                "K": "KANGAROO", "L": "LION", "M": "MONKEY", "N": "NEST", "O": "OWL",
                "P": "PIG", "Q": "QUACK", "R": "RABBIT", "S": "SNAKE", "T": "TIGER",
                "U": "UNICORN", "V": "VAN", "W": "WOLF", "X": "FOX", "Y": "YAK", "Z": "ZEBRA",
            }
            word = animal_prefs.get(letter, word)
        fact = pick_fact(rng, letter if letter.isalpha() else "A")
        tip = str(rng.choice(LEARN_TIPS))
        phonics = PHONICS.get(letter, f"Learn {letter}!")
        if letter.isdigit():
            phonics = f"{letter} means {pick_word(rng, letter)}"
            tip = "Count with me!"
            fact = f"Number {letter} is {pick_word(rng, letter).lower()}."

        segments.append(
            {
                "index": i,
                "t0": float(edges[i]),
                "t1": float(edges[i + 1]),
                "letter": letter,
                "word": word,
                "motif": motif_key(word),
                "fact": fact,
                "phonics": phonics,
                "tip": tip,
                "line": f"{letter} is for {word}",
            }
        )

    spell_word = "".join(letters) if visual_mode == "spell" else ""

    return {
        "theme": theme,
        "title": title,
        "visual_mode": visual_mode,
        "letters": letters,
        "spell_word": spell_word,
        "segments": segments,
        "duration": float(duration),
        "closing": str(rng.choice(["You did great!", "Learning is fun!", "See you next time!", "Keep practicing!"])),
    }
