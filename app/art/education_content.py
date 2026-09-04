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

KIDS_EDUCATION_ENGINES = frozenset({"alphabet_cartoon", "kids_doodles", "hand_art"})

DOODLE_THEMES = [
    "shape_fun",
    "color_rainbow",
    "count_along",
    "word_stickers",
    "creative_play",
]

HAND_ART_THEMES = [
    "draw_along",
    "sketch_practice",
    "doodle_story",
]

SHAPES = ["circle", "square", "triangle", "star", "heart", "blob"]

SHAPE_WORDS: dict[str, str] = {
    "circle": "BALL",
    "square": "BOX",
    "triangle": "TREE",
    "star": "STAR",
    "heart": "SUN",
    "blob": "CLOUD",
}

SHAPE_LINES: dict[str, list[str]] = {
    "circle": ["This is a circle!", "A circle is round!", "Can you trace a circle?"],
    "square": ["This is a square!", "Squares have four sides!", "Look at the corners!"],
    "triangle": ["This is a triangle!", "Triangles have three points!", "Point up to the sky!"],
    "star": ["This is a star!", "Stars can twinkle!", "Count the star points!"],
    "heart": ["This is a heart!", "Hearts mean love!", "Draw a heart for someone!"],
    "blob": ["This is a silly blob!", "Blobs are wiggly!", "Make a funny shape!"],
}

SHAPE_FACTS: dict[str, list[str]] = {
    "circle": ["Circles have no corners.", "Wheels are circles!", "Bubbles are circles too!"],
    "square": ["All sides are the same length.", "Windows can be square.", "Blocks are often square."],
    "triangle": ["A pizza slice is a triangle.", "Roofs can be triangles.", "Three sides make a triangle."],
    "star": ["Stars shine in the sky.", "You can wish on a star!", "Stars have pointy tips."],
    "heart": ["We draw hearts for friends.", "Hearts beat in your chest.", "Pink hearts are pretty!"],
    "blob": ["Blobs can be any shape!", "Clouds look like blobs.", "Squish and stretch blobs!"],
}

COLORS: list[tuple[str, str, tuple[int, int, int]]] = [
    ("red", "RED", (235, 70, 70)),
    ("blue", "BLUE", (70, 120, 235)),
    ("green", "GREEN", (70, 190, 90)),
    ("yellow", "YELLOW", (245, 220, 60)),
    ("orange", "ORANGE", (245, 150, 55)),
    ("purple", "PURPLE", (160, 90, 210)),
    ("pink", "PINK", (245, 130, 180)),
]

COLOR_LINES = [
    "This color is {name}!",
    "Can you find {name}?",
    "Say {name} with me!",
    "Look at the {name} shape!",
]

COLOR_FACTS: dict[str, list[str]] = {
    "red": ["Apples can be red.", "Stop signs are red.", "Red is a warm color."],
    "blue": ["The sky can be blue.", "Blue is a cool color.", "Water looks blue sometimes."],
    "green": ["Grass is green.", "Leaves are green.", "Green means go!"],
    "yellow": ["The sun looks yellow.", "Bananas can be yellow.", "Yellow is bright!"],
    "orange": ["Oranges are orange!", "Carrots can be orange.", "Orange is cheerful!"],
    "purple": ["Grapes can be purple.", "Purple mixes red and blue.", "Purple is royal!"],
    "pink": ["Some flowers are pink.", "Pink is soft and sweet.", "Flamingos can be pink!"],
}

DRAW_SUBJECTS = [
    ("house", "HOUSE", "Let's draw a house!", "A house keeps us warm."),
    ("flower", "FLOWER", "Let's draw a flower!", "Flowers need sunshine."),
    ("sun", "SUN", "Let's draw the sun!", "The sun gives us light."),
    ("star", "STAR", "Let's draw a star!", "Stars twinkle at night."),
    ("fish", "FISH", "Let's draw a fish!", "Fish swim in water."),
    ("cloud", "CLOUD", "Let's draw a cloud!", "Clouds float in the sky."),
    ("heart", "SUN", "Let's draw a heart!", "Hearts mean kindness."),
    ("stick", "BIRD", "Let's draw a person!", "People can wave hello."),
    ("spiral", "STAR", "Let's draw a spiral!", "Spirals go round and round."),
    ("tree", "TREE", "Let's draw a tree!", "Trees give us oxygen."),
]

DRAW_TIPS = [
    "Follow the lines slowly.",
    "Use your whole arm to draw.",
    "It's okay to wobble!",
    "Try it again — practice helps!",
    "Add your own details!",
]

DOODLE_TIPS = [
    "Trace the shape with your finger!",
    "Can you find this at home?",
    "Clap once for each shape!",
    "Say the word out loud!",
    "You're doing great!",
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
                "voice_line": f"{letter} is for {word}. {phonics}",
            }
        )

    spell_word = "".join(letters) if visual_mode == "spell" else ""

    return {
        "theme": theme,
        "title": title,
        "visual_mode": visual_mode,
        "engine": "alphabet_cartoon",
        "letters": letters,
        "spell_word": spell_word,
        "segments": segments,
        "duration": float(duration),
        "closing": str(rng.choice(["You did great!", "Learning is fun!", "See you next time!", "Keep practicing!"])),
    }


def _segment_edges(n: int) -> np.ndarray:
    return np.linspace(0.0, 1.0, max(2, n + 1))


def build_kids_doodle_lesson(
    seed: int,
    duration: float,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a shape/color/count lesson for the kids doodle board engine."""
    params = params or {}
    rng = np.random.default_rng(seed + 17)
    theme = str(params.get("lesson_theme", rng.choice(DOODLE_THEMES)))

    title_map = {
        "shape_fun": "Shape Time!",
        "color_rainbow": "Color Rainbow",
        "count_along": "Count With Me",
        "word_stickers": "Word Stickers",
        "creative_play": "Creative Play",
    }
    title = title_map.get(theme, "Doodle & Learn")

    segments: list[dict[str, Any]] = []
    if theme == "shape_fun":
        picks = list(rng.choice(SHAPES, size=int(rng.integers(5, 8)), replace=False))
        for i, shape in enumerate(picks):
            word = SHAPE_WORDS.get(shape, "STAR")
            line = str(rng.choice(SHAPE_LINES.get(shape, ["Let's learn shapes!"])))
            segments.append(
                {
                    "index": i,
                    "kind": "shape",
                    "shape": shape,
                    "word": word,
                    "motif": word,
                    "line": line,
                    "fact": str(rng.choice(SHAPE_FACTS.get(shape, ["Shapes are fun!"]))),
                    "tip": str(rng.choice(DOODLE_TIPS)),
                    "voice_line": f"{line} {rng.choice(SHAPE_FACTS.get(shape, ['']))}",
                }
            )
        visual_mode = "focus"
    elif theme == "color_rainbow":
        picks = list(rng.choice(len(COLORS), size=int(rng.integers(5, 7)), replace=False))
        for i, idx in enumerate(picks):
            key, name, rgb = COLORS[int(idx)]
            shape = str(rng.choice(SHAPES[:5]))
            word = SHAPE_WORDS.get(shape, "STAR")
            line = str(rng.choice(COLOR_LINES).format(name=name))
            segments.append(
                {
                    "index": i,
                    "kind": "color",
                    "shape": shape,
                    "color_key": key,
                    "color_name": name,
                    "color_rgb": list(rgb),
                    "word": word,
                    "motif": word,
                    "line": line,
                    "fact": str(rng.choice(COLOR_FACTS.get(key, ["Colors are beautiful!"]))),
                    "tip": "Point to the color!",
                    "voice_line": f"{line} {COLOR_FACTS.get(key, [''])[0]}",
                }
            )
        visual_mode = "color"
    elif theme == "count_along":
        count = int(rng.integers(3, 7))
        for i in range(count):
            n = i + 1
            shape = str(rng.choice(SHAPES[:5]))
            word = pick_word(rng, str(rng.choice(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))))
            line = f"Count {n}! Can you see {n} shapes?"
            segments.append(
                {
                    "index": i,
                    "kind": "count",
                    "shape": shape,
                    "count": n,
                    "word": word,
                    "motif": motif_key(word),
                    "line": line,
                    "fact": f"{n} is a number we can count.",
                    "tip": "Count with your fingers!",
                    "voice_line": f"Count {n} with me!",
                }
            )
        visual_mode = "count"
    elif theme == "word_stickers":
        letters = list(rng.choice(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), size=int(rng.integers(6, 9)), replace=False))
        for i, letter in enumerate(letters):
            word = pick_word(rng, letter)
            shape = str(rng.choice(SHAPES[:5]))
            line = f"{letter} — {word}!"
            segments.append(
                {
                    "index": i,
                    "kind": "word",
                    "letter": letter,
                    "shape": shape,
                    "word": word,
                    "motif": motif_key(word),
                    "line": line,
                    "phonics": PHONICS.get(letter, f"Learn {letter}!"),
                    "fact": pick_fact(rng, letter),
                    "tip": str(rng.choice(DOODLE_TIPS)),
                    "voice_line": f"{letter} is for {word}",
                }
            )
        visual_mode = "stickers"
    else:
        picks = list(rng.choice(SHAPES, size=int(rng.integers(6, 10)), replace=False))
        for i, shape in enumerate(picks):
            word = SHAPE_WORDS.get(shape, "STAR")
            segments.append(
                {
                    "index": i,
                    "kind": "play",
                    "shape": shape,
                    "word": word,
                    "motif": word,
                    "line": str(rng.choice(SHAPE_LINES.get(shape, ["Let's doodle!"]))),
                    "fact": str(rng.choice(SHAPE_FACTS.get(shape, ["Have fun drawing!"]))),
                    "tip": str(rng.choice(DOODLE_TIPS)),
                    "voice_line": f"Let's doodle a {shape}!",
                }
            )
        visual_mode = "playground"

    n = max(1, len(segments))
    edges = _segment_edges(n)
    for i, seg in enumerate(segments):
        seg["t0"] = float(edges[i])
        seg["t1"] = float(edges[i + 1])

    return {
        "theme": theme,
        "title": title,
        "visual_mode": visual_mode,
        "engine": "kids_doodles",
        "segments": segments,
        "duration": float(duration),
        "closing": str(rng.choice(["Great doodling!", "You are an artist!", "Keep creating!", "Amazing job!"])),
    }


def build_hand_art_lesson(
    seed: int,
    duration: float,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a step-by-step draw-along lesson for the hand art engine."""
    params = params or {}
    rng = np.random.default_rng(seed + 31)
    theme = str(params.get("lesson_theme", rng.choice(HAND_ART_THEMES)))

    title_map = {
        "draw_along": "Draw Along With Me",
        "sketch_practice": "Sketch Practice",
        "doodle_story": "Doodle Story Time",
    }
    title = title_map.get(theme, "Hand Art Class")

    pool = list(DRAW_SUBJECTS)
    rng.shuffle(pool)

    if theme == "draw_along":
        picks = pool[: int(rng.integers(4, 7))]
        visual_mode = "draw_along"
    elif theme == "sketch_practice":
        kind = pool[0][0]
        picks = [s for s in pool if s[0] == kind][:1]
        picks = picks * int(rng.integers(4, 6))
        visual_mode = "practice"
    else:
        picks = pool[: int(rng.integers(5, 8))]
        visual_mode = "story"

    segments: list[dict[str, Any]] = []
    for i, (kind, word, intro, fact) in enumerate(picks):
        step_lines = [
            f"Step one: start your {kind}.",
            f"Step two: add details to the {kind}.",
            f"Step three: finish your {kind}!",
        ]
        segments.append(
            {
                "index": i,
                "kind": "draw",
                "doodle_kind": kind,
                "word": word,
                "motif": word,
                "line": intro,
                "fact": fact,
                "tip": str(rng.choice(DRAW_TIPS)),
                "steps": step_lines,
                "voice_line": f"{intro} {fact}",
            }
        )

    n = max(1, len(segments))
    edges = _segment_edges(n)
    for i, seg in enumerate(segments):
        seg["t0"] = float(edges[i])
        seg["t1"] = float(edges[i + 1])

    story_intro = "Once upon a time, an artist began to draw..."
    story_outro = "And they drew a wonderful picture!"

    return {
        "theme": theme,
        "title": title,
        "visual_mode": visual_mode,
        "engine": "hand_art",
        "segments": segments,
        "duration": float(duration),
        "story_intro": story_intro if theme == "doodle_story" else "",
        "closing": str(rng.choice(["Beautiful drawing!", "You're an artist!", "Practice makes perfect!", "Great sketching!"])),
    }


def build_lesson_for_engine(
    engine: str,
    seed: int,
    duration: float,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Unified lesson builder for all kids educational engines."""
    if engine == "alphabet_cartoon":
        return build_education_lesson(seed, duration, params=params)
    if engine == "kids_doodles":
        return build_kids_doodle_lesson(seed, duration, params=params)
    if engine == "hand_art":
        return build_hand_art_lesson(seed, duration, params=params)
    return None
