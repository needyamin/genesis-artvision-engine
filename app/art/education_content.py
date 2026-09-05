"""Random educational content for kids alphabet videos."""

from __future__ import annotations

from typing import Any

import numpy as np

from app.utils.logger import get_logger
from app.utils.paths import resolve_path

logger = get_logger("education_content")

_AI_CATALOGS_LOADED = False

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
    "U": ["UMBRELLA", "UNICORN", "UKULELE"],
    "V": ["VAN", "VIOLIN", "VEST", "VOLCANO"],
    "W": ["WATER", "WAVE", "WOLF", "WATCH"],
    "X": ["XYLOPHONE", "X-RAY"],
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
    "U": "U says /u/ as in umbrella",
    "V": "V says /v/ as in van",
    "W": "W says /w/ as in water",
    "X": "X sounds like /z/ as in xylophone",
    "Y": "Y says /y/ as in yellow",
    "Z": "Z says /z/ as in zebra",
}

# Master Teacher Pedagogy: exact IPA phonemes, sound spelling, and rhyme families
PHONEME_DATA: dict[str, dict[str, Any]] = {
    "A": {"phoneme": "/æ/", "sound_name": "short a", "sound_spelling": "ah", "rhyme_family": "-at (cat, hat, bat)", "stroke_count": 3},
    "B": {"phoneme": "/b/", "sound_name": "voiced stop", "sound_spelling": "buh", "rhyme_family": "-all (ball, fall, tall)", "stroke_count": 2},
    "C": {"phoneme": "/k/", "sound_name": "hard c", "sound_spelling": "kuh", "rhyme_family": "-at (cat, bat, mat)", "stroke_count": 1},
    "D": {"phoneme": "/d/", "sound_name": "voiced stop", "sound_spelling": "duh", "rhyme_family": "-og (dog, frog, log)", "stroke_count": 2},
    "E": {"phoneme": "/ɛ/", "sound_name": "short e", "sound_spelling": "eh", "rhyme_family": "-ed (bed, red, fed)", "stroke_count": 4},
    "F": {"phoneme": "/f/", "sound_name": "fricative", "sound_spelling": "fff", "rhyme_family": "-ish (fish, wish, dish)", "stroke_count": 3},
    "G": {"phoneme": "/ɡ/", "sound_name": "hard g", "sound_spelling": "guh", "rhyme_family": "-oat (goat, boat, coat)", "stroke_count": 2},
    "H": {"phoneme": "/h/", "sound_name": "aspirate", "sound_spelling": "huh", "rhyme_family": "-at (hat, cat, rat)", "stroke_count": 3},
    "I": {"phoneme": "/ɪ/", "sound_name": "short i", "sound_spelling": "ih", "rhyme_family": "-in (pin, win, fin)", "stroke_count": 3},
    "J": {"phoneme": "/dʒ/", "sound_name": "affricate", "sound_spelling": "juh", "rhyme_family": "-am (jam, ham, ram)", "stroke_count": 2},
    "K": {"phoneme": "/k/", "sound_name": "velar stop", "sound_spelling": "kuh", "rhyme_family": "-ite (kite, bite, white)", "stroke_count": 3},
    "L": {"phoneme": "/l/", "sound_name": "liquid", "sound_spelling": "lll", "rhyme_family": "-ion (lion)", "stroke_count": 2},
    "M": {"phoneme": "/m/", "sound_name": "nasal", "sound_spelling": "mmm", "rhyme_family": "-oon (moon, spoon, soon)", "stroke_count": 4},
    "N": {"phoneme": "/n/", "sound_name": "nasal", "sound_spelling": "nnn", "rhyme_family": "-est (nest, best, rest)", "stroke_count": 3},
    "O": {"phoneme": "/ɒ/", "sound_name": "short o", "sound_spelling": "aw", "rhyme_family": "-ot (hot, pot, dot)", "stroke_count": 1},
    "P": {"phoneme": "/p/", "sound_name": "unvoiced stop", "sound_spelling": "puh", "rhyme_family": "-ig (pig, dig, big)", "stroke_count": 2},
    "Q": {"phoneme": "/kw/", "sound_name": "cluster", "sound_spelling": "kwuh", "rhyme_family": "-een (queen, green, seen)", "stroke_count": 2},
    "R": {"phoneme": "/r/", "sound_name": "liquid", "sound_spelling": "rrr", "rhyme_family": "-ed (red, bed) / -ose (rose)", "stroke_count": 3},
    "S": {"phoneme": "/s/", "sound_name": "sibilant", "sound_spelling": "sss", "rhyme_family": "-un (sun, run, fun)", "stroke_count": 1},
    "T": {"phoneme": "/t/", "sound_name": "unvoiced stop", "sound_spelling": "tuh", "rhyme_family": "-ee (tree, bee, see)", "stroke_count": 2},
    "U": {"phoneme": "/ʌ/", "sound_name": "short u", "sound_spelling": "uh", "rhyme_family": "-up (cup, pup)", "stroke_count": 1},
    "V": {"phoneme": "/v/", "sound_name": "voiced fricative", "sound_spelling": "vvv", "rhyme_family": "-an (van, pan, can)", "stroke_count": 2},
    "W": {"phoneme": "/w/", "sound_name": "glide", "sound_spelling": "wuh", "rhyme_family": "-et (wet, pet, net)", "stroke_count": 4},
    "X": {"phoneme": "/ks/", "sound_name": "cluster", "sound_spelling": "ks", "rhyme_family": "-ox (box, fox)", "stroke_count": 2},
    "Y": {"phoneme": "/j/", "sound_name": "glide", "sound_spelling": "yuh", "rhyme_family": "-ellow (yellow)", "stroke_count": 3},
    "Z": {"phoneme": "/z/", "sound_name": "voiced sibilant", "sound_spelling": "zzz", "rhyme_family": "-oo (zoo, too)", "stroke_count": 3},
}

SHAPE_PEDAGOGY: dict[str, dict[str, Any]] = {
    "CIRCLE": {"sides": 0, "vertices": 0, "fact": "1 continuous curved line, 0 corners"},
    "TRIANGLE": {"sides": 3, "vertices": 3, "fact": "3 straight sides and 3 sharp corners"},
    "SQUARE": {"sides": 4, "vertices": 4, "fact": "4 equal sides and 4 square corners"},
    "RECTANGLE": {"sides": 4, "vertices": 4, "fact": "4 sides: 2 long and 2 short"},
    "STAR": {"sides": 10, "vertices": 5, "fact": "5 shining points reaching out"},
    "HEART": {"sides": 0, "vertices": 1, "fact": "2 round curves meeting at 1 bottom point"},
}

TEN_FRAME_DATA: dict[int, dict[str, Any]] = {
    i: {
        "count": i,
        "filled": [(idx // 5, idx % 5) for idx in range(i)],
        "equation": f"{i}" if i <= 5 else f"5 + {i - 5} = {i}",
    }
    for i in range(1, 11)
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
    "X": ["A xylophone makes music when you tap its bars.", "Doctors use X-rays to see bones inside our bodies."],
    "Y": ["Yellow is a bright color!", "Yo-yos go up and down."],
    "Z": ["Zebras have stripes.", "Zoos care for animals."],
}

EASY_SPELL_WORDS = [
    "CAT", "DOG", "SUN", "HAT", "BUS", "RED", "BED", "PEN", "CUP", "MAP",
    "FISH", "BIRD", "TREE", "MOON", "STAR", "BALL", "BOOK", "FROG", "DUCK", "LION",
    "APPLE", "CAKE", "LEAF", "NEST", "KITE", "LAMP", "MILK", "OWL", "PIG", "ROSE",
    "SHIP", "VAN", "WAVE", "YARN", "ZIP", "HAND",
]


def _alpha_word(raw: object) -> str:
    return "".join(ch for ch in str(raw or "").upper() if ch.isalpha())


def _known_kid_words() -> set[str]:
    words = {_alpha_word(w) for w in EASY_SPELL_WORDS}
    for lst in LETTER_WORDS.values():
        words.update(_alpha_word(w) for w in lst if " " not in str(w) and "-" not in str(w))
    words.update(_alpha_word(w) for lst in NUMBER_WORDS.values() for w in lst)
    words.discard("")
    return words


_KNOWN_KID_WORDS = _known_kid_words()


def _is_letter_salad(candidate: str, sources: list[str]) -> bool:
    """True when CANDIDATE is just the first letters of other words (e.g. SABP)."""
    word = _alpha_word(candidate)
    parts = [_alpha_word(s) for s in sources if _alpha_word(s)]
    if len(word) < 2 or len(parts) < 2:
        return False
    initials = "".join(p[0] for p in parts)
    return word == initials and word not in _KNOWN_KID_WORDS


def choose_spell_word(
    rng: np.random.Generator,
    *,
    focus_words: list[str] | None = None,
    segment_plan: list[dict[str, Any]] | None = None,
    focus_letters: list[str] | None = None,
) -> str:
    """Pick one real kid word to spell — never join unrelated first letters."""
    words = [str(w) for w in (focus_words or []) if str(w).strip()]
    plan = [dict(s) for s in (segment_plan or []) if isinstance(s, dict)]
    plan_words = [str(s.get("word") or "") for s in plan]
    sources = words + plan_words

    candidates: list[str] = []
    for raw in words + plan_words:
        cleaned = _alpha_word(raw)
        if cleaned and cleaned not in candidates:
            candidates.append(cleaned)
    joined_letters = _alpha_word("".join(str(c) for c in (focus_letters or [])))
    if joined_letters:
        candidates.append(joined_letters)
    plan_letters = _alpha_word("".join(str(s.get("letter") or "")[:1] for s in plan))
    if plan_letters:
        candidates.append(plan_letters)

    for cand in candidates:
        if len(cand) < 3 or len(cand) > 10:
            continue
        if _is_letter_salad(cand, sources):
            continue
        if cand in _KNOWN_KID_WORDS:
            return cand
        if len(words) == 1 and cand.isalpha() and 3 <= len(cand) <= 8:
            return cand
    return str(rng.choice(EASY_SPELL_WORDS))

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
    "real_world_math",
    "dictionary",
]

# Prefer focused one-letter-at-a-time lessons over crowded charts
THEME_WEIGHTS = [
    "letter_of_day", "letter_of_day",
    "phonics", "phonics",
    "dictionary", "dictionary",
    "real_world_math", "real_world_math", "real_world_math",
    "word_builder", "word_builder",
    "animal_friends",
    "count_fun",
    "abc_chart",
]

KIDS_EDUCATION_ENGINES = frozenset({"alphabet_cartoon", "kids_doodles", "hand_art"})

ALPHABET_AZ = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
# Floor so each A–Z letter can be spoken slowly even before TTS timing is measured.
MIN_SECONDS_PER_AZ_LETTER = 5.5
AZ_END_PAD_SEC = 1.4

DOODLE_THEMES = [
    "shape_fun",
    "color_rainbow",
    "count_along",
    "real_world_math",
    "word_stickers",
    "dictionary",
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
    "heart": "HEART",
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
    ("heart", "HEART", "Let's draw a heart!", "Hearts mean kindness."),
    ("stick", "FRIEND", "Let's draw a person!", "People can wave hello."),
    ("spiral", "SPIRAL", "Let's draw a spiral!", "Spirals go round and round."),
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
    "Point and say the name!",
    "Can you draw it too?",
]

ENGAGE_HOOKS = [
    "Are you ready?",
    "Let's go!",
    "Here we go!",
    "Watch this!",
    "Your turn next!",
    "Can you do it?",
    "Let's try together!",
]

CELEBRATION_LINES = [
    "Amazing!",
    "You got it!",
    "Super star!",
    "High five!",
    "Wow, great job!",
    "Fantastic learning!",
    "You're so smart!",
]

QUIZ_PROMPTS = [
    "What do you see?",
    "Can you name it?",
    "Do you remember?",
    "What letter is this?",
    "Say it with me!",
    "Point to it!",
]

INTERACTIVE_CHALLENGES = [
    "Clap your hands!",
    "Jump once!",
    "Touch your nose!",
    "Spin around!",
    "Make a happy face!",
    "Wave hello!",
]

NUMBER_FACTS = {
    1: "One sun in the sky!",
    2: "Two eyes to see!",
    3: "Three wheels on a tricycle!",
    4: "Four legs on a dog!",
    5: "Five fingers on one hand!",
    6: "Six sides on a honeycomb!",
    7: "Seven colors in a rainbow!",
    8: "Eight legs on a spider!",
    9: "A baseball team has nine players!",
    10: "Ten toes on your feet!",
}

# Kid-dictionary: one clear meaning per learning word.
WORD_MEANINGS: dict[str, str] = {
    "APPLE": "An apple is a fruit you can eat.",
    "ANT": "An ant is a tiny bug that works in a team.",
    "AIRPLANE": "An airplane is a machine that flies in the sky.",
    "ALLIGATOR": "An alligator is a long animal with a strong jaw.",
    "BALL": "A ball is a round toy you can throw and catch.",
    "BIRD": "A bird is an animal with wings. Birds can fly.",
    "BUS": "A bus is a big car that carries many people.",
    "BANANA": "A banana is a yellow fruit you can peel.",
    "CAT": "A cat is a pet. Cats say meow.",
    "CAKE": "A cake is a sweet treat we eat on birthdays.",
    "CAR": "A car is a machine we ride to go places.",
    "CLOUD": "A cloud is water in the sky. It looks fluffy.",
    "DOG": "A dog is a pet and a friend. Dogs say woof.",
    "DUCK": "A duck is a bird that swims. Ducks say quack.",
    "DRUM": "A drum is an instrument you tap to make music.",
    "EGG": "An egg can hatch into a chick.",
    "ELEPHANT": "An elephant is a big animal with a long trunk.",
    "FISH": "A fish lives in water and swims with fins.",
    "FROG": "A frog is a small animal that hops and says ribbit.",
    "FLOWER": "A flower is a plant with pretty petals.",
    "GRAPE": "A grape is a small fruit that grows in a bunch.",
    "GOAT": "A goat is a farm animal that likes to climb.",
    "HOUSE": "A house is a building where people live.",
    "HAT": "A hat is something you wear on your head.",
    "HORSE": "A horse is a big animal you can ride.",
    "HAND": "A hand has five fingers. You use hands to hold things.",
    "ICE": "Ice is frozen water. It feels cold.",
    "KITE": "A kite is a toy that flies on the wind.",
    "LION": "A lion is a big cat. Lions have a fluffy mane.",
    "LEAF": "A leaf grows on a tree. Leaves can be green.",
    "MOON": "The moon is the bright light we see at night.",
    "MOUSE": "A mouse is a tiny animal with a long tail.",
    "NEST": "A nest is a home that birds build.",
    "ORANGE": "An orange is a round fruit. It tastes juicy.",
    "OWL": "An owl is a bird that stays awake at night.",
    "PENCIL": "A pencil is a tool we use to write and draw.",
    "PIG": "A pig is a farm animal. Pigs like mud.",
    "QUEEN": "A queen is a leader. Some stories have queens.",
    "RAINBOW": "A rainbow is colors in the sky after rain.",
    "RABBIT": "A rabbit is a soft animal that hops.",
    "SUN": "The sun is the bright star that gives us light.",
    "STAR": "A star is a tiny light in the night sky.",
    "SNAKE": "A snake is a long animal with no legs.",
    "TREE": "A tree is a tall plant with a trunk and leaves.",
    "TRAIN": "A train is a long vehicle that rides on tracks.",
    "TIGER": "A tiger is a big cat with stripes.",
    "UMBRELLA": "An umbrella keeps you dry in the rain.",
    "VAN": "A van is a car with extra room inside.",
    "WATER": "Water is what we drink. Rain is water too.",
    "WAVE": "A wave is water moving in the ocean.",
    "YELLOW": "Yellow is a bright color, like the sun.",
    "YARN": "Yarn is a string we use to make warm things.",
    "ZEBRA": "A zebra is a horse-like animal with black and white stripes.",
    "ZERO": "Zero means none. Zero apples means no apples.",
    "ONE": "One means a single thing. One sun in the sky.",
    "TWO": "Two means a pair. You have two eyes.",
    "THREE": "Three means one more than two.",
    "HEART": "A heart is a shape that means love and kindness.",
    "BOOK": "A book has pages with stories and words.",
    "ROBOT": "A robot is a machine that can move and help.",
    "RED": "Red is a bright color, like an apple or a stop sign.",
    "BED": "A bed is where we sleep at night.",
    "PEN": "A pen is a tool we use to write.",
    "CUP": "A cup holds a drink, like water or milk.",
    "MAP": "A map shows us where places are.",
    "LAMP": "A lamp gives light when it is dark.",
    "MILK": "Milk is a drink that helps bones grow.",
    "ROSE": "A rose is a flower with soft petals.",
    "SHIP": "A ship is a big boat that travels on water.",
    "ZIP": "Zip means to close something, like a zipper on a coat.",
}

# Everyday counting stories kids can see around them.
MATH_STORIES: list[dict[str, Any]] = [
    {"left": 1, "right": 1, "op": "+", "item": "suns", "word": "SUN", "place": "in the sky"},
    {"left": 2, "right": 1, "op": "+", "item": "apples", "word": "APPLE", "place": "in the basket"},
    {"left": 2, "right": 2, "op": "+", "item": "balls", "word": "BALL", "place": "on the floor"},
    {"left": 3, "right": 1, "op": "+", "item": "birds", "word": "BIRD", "place": "in the tree"},
    {"left": 3, "right": 2, "op": "+", "item": "stars", "word": "STAR", "place": "at night"},
    {"left": 1, "right": 2, "op": "+", "item": "cats", "word": "CAT", "place": "in the house"},
    {"left": 2, "right": 3, "op": "+", "item": "dogs", "word": "DOG", "place": "in the park"},
    {"left": 4, "right": 1, "op": "+", "item": "cars", "word": "CAR", "place": "on the road"},
    {"left": 1, "right": 3, "op": "+", "item": "ducks", "word": "DUCK", "place": "on the pond"},
    {"left": 4, "right": 2, "op": "+", "item": "flowers", "word": "FLOWER", "place": "in the garden"},
    {"left": 5, "right": 1, "op": "-", "item": "cakes", "word": "CAKE", "place": "on the plate"},
    {"left": 4, "right": 1, "op": "-", "item": "ducks", "word": "DUCK", "place": "on the pond"},
    {"left": 3, "right": 1, "op": "-", "item": "fish", "word": "FISH", "place": "in the water"},
    {"left": 5, "right": 2, "op": "-", "item": "birds", "word": "BIRD", "place": "in the tree"},
    {"left": 4, "right": 2, "op": "-", "item": "apples", "word": "APPLE", "place": "in the basket"},
    {"left": 3, "right": 2, "op": "-", "item": "balls", "word": "BALL", "place": "on the floor"},
]

# Extra narration lines from AI catalogs (letter -> lines)
AI_VOICE_LINES: dict[str, list[str]] = {}


def ensure_ai_catalogs_loaded(config: dict[str, Any] | None = None) -> None:
    """Merge optional offline AI catalogs into LETTER_WORDS / FUN_FACTS / AI_VOICE_LINES."""
    global _AI_CATALOGS_LOADED
    if _AI_CATALOGS_LOADED:
        return
    _AI_CATALOGS_LOADED = True
    try:
        from app.ai.curate import load_catalog_file
    except ImportError:
        return

    ai = (config or {}).get("ai") or {}
    catalog_path = resolve_path(ai.get("catalog_dir") or "./data/ai_catalogs") / "education.json"
    if not catalog_path.is_file():
        return
    catalog = load_catalog_file(catalog_path)
    _merge_into(LETTER_WORDS, catalog.get("words", {}), upper_items=True)
    _merge_into(FUN_FACTS, catalog.get("fun_facts", {}), upper_items=False)
    _merge_into(AI_VOICE_LINES, catalog.get("voice_lines", {}), upper_items=False)
    logger.info("Loaded AI education catalog from %s", catalog_path)


def _merge_into(
    target: dict[str, list[str]],
    extra: dict[str, list[str]],
    *,
    upper_items: bool,
) -> None:
    for letter, values in (extra or {}).items():
        key = str(letter).upper()
        bucket = target.setdefault(key, [])
        seen = {x.upper() for x in bucket}
        for item in values:
            text = str(item).strip()
            if not text:
                continue
            if upper_items:
                text = text.upper()
            if text.upper() not in seen:
                bucket.append(text)
                seen.add(text.upper())


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


def word_meaning(word: str) -> str:
    """One-sentence kid dictionary definition."""
    w = _alpha_word(word)
    if w in WORD_MEANINGS:
        return WORD_MEANINGS[w]
    if w:
        return f"{w.title()} is a word we can read and say."
    return "Words help us name the world."


def spell_spoken(word: str) -> str:
    """Slow letter-by-letter spelling for TTS."""
    letters = [ch for ch in _alpha_word(word)]
    if not letters:
        return ""
    return ". ".join(letters) + "."


def count_spoken(n: int) -> str:
    n = max(1, min(10, int(n)))
    return ". ".join(str(i) for i in range(1, n + 1)) + "."


def math_answer(story: dict[str, Any]) -> int:
    left = int(story["left"])
    right = int(story["right"])
    if str(story.get("op")) == "-":
        return max(0, left - right)
    return left + right


def _math_voice(story: dict[str, Any], *, intro: str = "") -> str:
    left = int(story["left"])
    right = int(story["right"])
    item = str(story["item"])
    if left == 1 and item.endswith("s") and not item.endswith("ss"):
        item_left = item[:-1]
    else:
        item_left = item
    place = str(story.get("place") or "")
    ans = math_answer(story)
    start = f"{intro} " if intro else ""
    if str(story.get("op")) == "-":
        return (
            f"{start}Look. {left} {item_left} {place}. "
            f"Take away {right}. "
            f"{left} take away {right} is {ans}. "
            f"{count_spoken(ans)}"
        )
    return (
        f"{start}Look. {left} {item_left} {place}. "
        f"Plus {right} more. "
        f"{left} plus {right} is {ans}. "
        f"{count_spoken(ans)}"
    )


def _dictionary_voice(word: str, *, intro: str = "") -> str:
    start = f"{intro} " if intro else ""
    spelled = spell_spoken(word)
    meaning = word_meaning(word)
    return f"{start}{word.title()}. {spelled} {meaning} Say {word.lower()}."


def _math_shape(item: str) -> str:
    key = str(item or "").lower()
    if "star" in key:
        return "star"
    if "heart" in key:
        return "heart"
    if any(w in key for w in ("bird", "tree", "flower")):
        return "triangle"
    if any(w in key for w in ("car", "bus", "box", "cookie", "cake")):
        return "square"
    return "circle"


def _math_lesson_segments(
    rng: np.random.Generator,
    count: int,
    intro_hook: str,
) -> list[dict[str, Any]]:
    stories = list(MATH_STORIES)
    rng.shuffle(stories)
    segments: list[dict[str, Any]] = []
    for i, story in enumerate(stories[: max(1, count)]):
        ans = math_answer(story)
        word = str(story["word"])
        op = str(story["op"])
        left = int(story["left"])
        right = int(story["right"])
        equation = f"{left} {op} {right} = {ans}"
        item = str(story["item"])
        if op == "-":
            line = f"{left} take away {right} is {ans}"
            fact = f"If you start with {left} {item} and take {right} away, {ans} are left."
        else:
            line = f"{left} plus {right} is {ans}"
            fact = f"{left} {item} and {right} more make {ans}."
        segments.append(
            {
                "index": i,
                "kind": "math",
                "letter": str(ans),
                "word": word,
                "motif": motif_key(word),
                "count": ans,
                "math_left": left,
                "math_right": right,
                "math_op": op,
                "shape": _math_shape(item),
                "line": equation,
                "overlay_text": equation,
                "caption": line,
                "fact": fact,
                "phonics": "Count slowly with your fingers.",
                "tip": "Use your fingers!",
                "voice_line": _math_voice(story, intro=intro_hook if i == 0 else ""),
            }
        )
    return segments


def _dictionary_lesson_segments(
    rng: np.random.Generator,
    count: int,
    intro_hook: str,
    *,
    focus_words: list[str] | None = None,
) -> list[dict[str, Any]]:
    words: list[str] = []
    for w in focus_words or []:
        clean = _alpha_word(w)
        if clean and clean not in words:
            words.append(clean)
    pool = [w for w in EASY_SPELL_WORDS if w in WORD_MEANINGS]
    rng.shuffle(pool)
    for w in pool:
        if len(words) >= count:
            break
        if w not in words:
            words.append(w)
    segments: list[dict[str, Any]] = []
    for i, word in enumerate(words[: max(1, count)]):
        letter = word[0]
        meaning = word_meaning(word)
        spelled = spell_spoken(word)
        segments.append(
            {
                "index": i,
                "kind": "dictionary",
                "letter": letter,
                "word": word,
                "spell_word": word,
                "motif": motif_key(word),
                "line": f"{word} — {meaning}",
                "overlay_text": word,
                "caption": f"{letter} is for {word}",
                "fact": meaning,
                "phonics": f"{word} is spelled {spelled.replace('. ', '-')}",
                "tip": "Say the word slowly!",
                "voice_line": _dictionary_voice(word, intro=intro_hook if i == 0 else ""),
            }
        )
    return segments


def motif_key(word: str) -> str:
    """Map a learning word to a drawable motif name used by the engine."""
    known = {
        "APPLE", "BALL", "CAT", "DUCK", "EGG", "FISH", "GRAPE", "HOUSE", "ICE",
        "JAR", "KITE", "LEAF", "MOON", "NEST", "ORANGE", "PENCIL", "QUEEN",
        "RAINBOW", "SUN", "TREE", "UMBRELLA", "VAN", "WAVE", "BOX", "YARN", "ZEBRA",
        "STAR", "DOG", "BIRD", "FROG", "LION", "OWL", "PIG", "RABBIT", "SNAKE",
        "TIGER", "WATER", "FOX", "YELLOW", "HEART", "FRIEND", "SPIRAL", "CLOUD",
        "CAKE", "CAR", "FLOWER", "BOOK", "ROBOT",
        "IGUANA", "ALLIGATOR", "ELEPHANT", "GOAT", "HORSE", "INSECT", "KANGAROO",
        "MONKEY", "UNICORN", "WOLF", "YAK",
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

    theme = str(params.get("lesson_theme", str(rng.choice(THEME_WEIGHTS))))
    include_numbers = bool(params.get("include_numbers", rng.random() < 0.25))
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    digits = list("0123456789")
    intro_hook = str(rng.choice(ENGAGE_HOOKS))
    seg_count = _segment_count_for_duration(duration, lo=2, hi=4)

    title_map = {
        "letter_of_day": "Letter of the Day",
        "abc_chart": "ABC Learning Chart",
        "abc_complete": "A to Z Alphabet",
        "word_builder": "Spell the Word",
        "phonics": "Letter Sounds",
        "animal_friends": "Animal Alphabet",
        "count_fun": "Real World Math",
        "real_world_math": "Math Around Us",
        "dictionary": "Word Dictionary",
    }
    title = title_map.get(theme, "Let's Learn!")
    complete_az = bool(params.get("complete_alphabet"))
    if complete_az:
        theme = "abc_complete"
        include_numbers = False
        title = "A to Z Alphabet"
        intro_hook = "Let's learn A to Z together!"

    # Choose letters for this lesson
    focus_letters = [
        str(c).upper()
        for c in (params.get("focus_letters") or [])
        if isinstance(c, str) and len(c) == 1 and c.isalnum()
    ]
    focus_words = [
        str(w).upper() for w in (params.get("focus_words") or []) if str(w).strip()
    ]
    ai_voice_pool = [str(v) for v in (params.get("ai_voice_lines") or []) if str(v).strip()]
    ai_fact_pool = [str(f) for f in (params.get("ai_fun_facts") or []) if str(f).strip()]
    segment_plan = [
        dict(s)
        for s in (params.get("ai_segment_plan") or params.get("ai_visual_beats") or [])
        if isinstance(s, dict)
    ]

    if theme in {"real_world_math", "count_fun"} and not complete_az:
        segments = _math_lesson_segments(rng, seg_count, intro_hook)
        n = max(1, len(segments))
        edges = _segment_edges(n, duration, weights=params.get("segment_weights"))
        _overlay_ai_copy(segments, params, lock_teaching=True)
        letters = [str(s.get("letter", "1")) for s in segments]
        for i, seg in enumerate(segments):
            seg["t0"] = float(edges[i])
            seg["t1"] = float(edges[i + 1])
            seg["_total"] = n
            _enrich_segment(seg, rng, is_first=(i == 0))
        lock_kids_segments(segments)
        return {
            "theme": theme,
            "title": title_map.get(theme, "Math Around Us"),
            "visual_mode": "lesson",
            "engine": "alphabet_cartoon",
            "letters": letters,
            "spell_word": "",
            "segments": segments,
            "duration": float(duration),
            "closing": str(rng.choice(["You counted it!", "Great math!", "Numbers are everywhere!", "Keep counting!"])),
            "engage_intro": intro_hook,
        }

    if theme == "dictionary" and not complete_az:
        segments = _dictionary_lesson_segments(rng, seg_count, intro_hook, focus_words=focus_words)
        n = max(1, len(segments))
        edges = _segment_edges(n, duration, weights=params.get("segment_weights"))
        _overlay_ai_copy(segments, params, lock_teaching=True)
        letters = [str(s.get("letter", "A")) for s in segments]
        for i, seg in enumerate(segments):
            seg["t0"] = float(edges[i])
            seg["t1"] = float(edges[i + 1])
            seg["_total"] = n
            _enrich_segment(seg, rng, is_first=(i == 0))
        lock_kids_segments(segments)
        return {
            "theme": theme,
            "title": "Word Dictionary",
            "visual_mode": "lesson",
            "engine": "alphabet_cartoon",
            "letters": letters,
            "spell_word": "",
            "segments": segments,
            "duration": float(duration),
            "closing": str(rng.choice(["You learned new words!", "Great reading!", "Say them again tomorrow!", "Words are fun!"])),
            "engage_intro": intro_hook,
        }

    if theme == "count_fun" or include_numbers and theme == "abc_chart":
        pool = alphabet + digits if include_numbers else alphabet
    else:
        pool = alphabet

    want_spell = (not complete_az) and (
        theme == "word_builder"
        or (
            str(params.get("mode") or "").lower() == "spell"
            and theme not in {
                "letter_of_day", "phonics", "animal_friends", "abc_chart",
                "abc_complete", "real_world_math", "count_fun", "dictionary",
            }
        )
    )
    spell_word = ""
    if complete_az:
        letters = list(ALPHABET_AZ)
        visual_mode = "lesson"
        title = "A to Z Alphabet"
        duration = max(float(duration), len(letters) * MIN_SECONDS_PER_AZ_LETTER + AZ_END_PAD_SEC)
    elif want_spell:
        spell_word = choose_spell_word(
            rng,
            focus_words=focus_words,
            segment_plan=segment_plan,
            focus_letters=focus_letters,
        )
        letters = list(spell_word)
        visual_mode = "spell"
        title = f"Spell {spell_word}!"
    elif focus_letters:
        letters = [c for c in focus_letters if c in pool or c in digits][:seg_count]
        if not letters:
            letters = list(rng.choice(pool, size=min(seg_count, len(pool)), replace=False))
        visual_mode = "lesson"
    elif segment_plan:
        letters = [
            str(s.get("letter", "A")).upper()[:1] or "A" for s in segment_plan[:seg_count]
        ]
        visual_mode = "lesson"
    elif theme in {"letter_of_day", "phonics", "animal_friends"}:
        count = seg_count
        letters = list(rng.choice(pool, size=min(count, len(pool)), replace=False))
        letters.sort(key=lambda c: pool.index(c) if c in pool else 0)
        visual_mode = "lesson"
    elif theme == "abc_chart":
        count = min(seg_count, 8)
        start = int(rng.integers(0, max(1, len(pool) - count + 1)))
        letters = list(pool[start : start + count])
        visual_mode = "chart"
    elif theme == "count_fun":
        count = min(seg_count, 6)
        letters = list(digits[:count])
        visual_mode = "lesson"
    else:
        count = seg_count
        letters = list(rng.choice(pool, size=min(count, len(pool)), replace=False))
        letters.sort(key=lambda c: pool.index(c) if c in pool else 0)
        visual_mode = "lesson"

    n = max(1, len(letters))
    az_weights = [1.0] * n if complete_az else params.get("segment_weights")
    edges = _segment_edges(n, duration, weights=az_weights)

    # Map focus words by first letter for quick lookup
    focus_by_letter: dict[str, list[str]] = {}
    for w in focus_words:
        key = _alpha_word(w)[:1]
        if key:
            focus_by_letter.setdefault(key, []).append(w)

    hyphen = "-".join(letters)
    segments: list[dict[str, Any]] = []
    for i, letter in enumerate(letters):
        plan = {} if complete_az else (segment_plan[i] if i < len(segment_plan) else {})
        if visual_mode == "spell" and spell_word:
            word = spell_word
            revealed = "".join(letters[: i + 1])
            overlay = f"{letter} in {spell_word}"
            line = f"{'-'.join(letters[: i + 1])}  →  {spell_word}"
            phonics = f"{letter} is letter {i + 1} of {spell_word}"
            fact = f"{spell_word} is spelled {hyphen}."
            tip = "Say each letter!"
            caption = f"Letter {i + 1} of {len(letters)}"
            voice = _spell_voice_line(i, letter, spell_word, letters, intro=intro_hook if i == 0 else "")
            motif = motif_key(spell_word)
        else:
            word = str(plan.get("word") or "").upper()
            word = _alpha_word(word)
            if word and letter.isalpha() and not word.startswith(letter):
                word = ""
            if not word:
                if letter in focus_by_letter and focus_by_letter[letter]:
                    word = focus_by_letter[letter][i % len(focus_by_letter[letter])]
                else:
                    word = pick_word(rng, letter)
            if theme == "animal_friends" and not plan.get("word"):
                animal_prefs = {
                    "A": "ALLIGATOR", "B": "BIRD", "C": "CAT", "D": "DOG", "E": "ELEPHANT",
                    "F": "FISH", "G": "GOAT", "H": "HORSE", "I": "IGUANA", "J": "JAGUAR",
                    "K": "KANGAROO", "L": "LION", "M": "MONKEY", "N": "NEWT", "O": "OWL",
                    "P": "PIG", "Q": "QUAIL", "R": "RABBIT", "S": "SNAKE", "T": "TIGER",
                    "U": "UNICORN", "V": "VULTURE", "W": "WOLF", "X": "X-RAY FISH", "Y": "YAK", "Z": "ZEBRA",
                }
                word = animal_prefs.get(letter, word)
            fact = str(plan.get("fact") or "")
            if fact and not _text_fits_teaching(fact, letter=letter, word=word):
                fact = ""
            if not fact:
                if ai_fact_pool:
                    cand = ai_fact_pool[i % len(ai_fact_pool)]
                    if _text_fits_teaching(cand, letter=letter, word=word):
                        fact = cand
                if not fact:
                    fact = word_meaning(word)
            tip = str(rng.choice(LEARN_TIPS))
            phonics = PHONICS.get(letter, f"Learn {letter}!")
            if letter.isdigit():
                phonics = f"{letter} means {pick_word(rng, letter)}"
                tip = "Count with me!"
                fact = f"Number {letter} is {pick_word(rng, letter).lower()}."
            voice = str(plan.get("voice_line") or "")
            if complete_az:
                voice = _az_voice_line(letter, word, intro=intro_hook if i == 0 else "")
            if voice and not _text_fits_teaching(voice, letter=letter, word=word):
                voice = ""
            if not voice and not complete_az and ai_voice_pool:
                cand = ai_voice_pool[i % len(ai_voice_pool)]
                if _text_fits_teaching(cand, letter=letter, word=word):
                    voice = cand
            if not voice:
                catalog_lines = AI_VOICE_LINES.get(letter, [])
                if catalog_lines:
                    cand = str(rng.choice(catalog_lines))
                    if _text_fits_teaching(cand, letter=letter, word=word):
                        voice = cand
            if not voice:
                if complete_az:
                    voice = _az_voice_line(letter, word, intro=intro_hook if i == 0 else "")
                else:
                    voice = _voice_line(letter, word, phonics=phonics)
            overlay = str(plan.get("overlay_text") or "")
            if overlay and not _text_fits_teaching(overlay, letter=letter, word=word):
                overlay = ""
            line = overlay or str(plan.get("line") or f"{letter} is for {word}")
            if not _text_fits_teaching(line, letter=letter, word=word):
                line = f"{letter} is for {word}"
            caption = str(plan.get("caption") or "")
            if caption and not _text_fits_teaching(caption, letter=letter, word=word):
                caption = ""
            if complete_az:
                caption = f"Letter {i + 1} of {len(letters)}"
            overlay = overlay or line
            motif = motif_key(word)
            revealed = ""

        segments.append(
            {
                "index": i,
                "t0": float(edges[i]),
                "t1": float(edges[i + 1]),
                "letter": letter,
                "word": word,
                "spell_word": spell_word,
                "revealed": revealed,
                "motif": motif,
                "fact": fact,
                "phonics": phonics,
                "tip": tip,
                "line": line,
                "overlay_text": overlay,
                "caption": caption,
                "image_brief": str(plan.get("image_brief") or ""),
                "image_path": str(plan.get("image_path") or ""),
                "voice_line": voice,
                "complete_alphabet": bool(complete_az),
                "_total": n,
            }
        )

    if not complete_az:
        _overlay_ai_copy(segments, params, lock_spelling=(visual_mode == "spell"))
    for i, seg in enumerate(segments):
        _enrich_segment(seg, rng, is_first=(i == 0))
        if complete_az:
            seg["complete_alphabet"] = True
            seg.pop("quiz", None)
            seg.pop("challenge", None)
    lock_kids_segments(segments, intro=intro_hook)

    return {
        "theme": theme,
        "title": title,
        "visual_mode": visual_mode,
        "engine": "alphabet_cartoon",
        "letters": letters,
        "spell_word": spell_word,
        "segments": segments,
        "duration": float(duration),
        "complete_alphabet": bool(complete_az),
        "closing": str(rng.choice(["You did great!", "Learning is fun!", "See you next time!", "Keep practicing!"])),
        "engage_intro": intro_hook,
    }


def _text_fits_teaching(text: str, *, letter: str = "", word: str = "") -> bool:
    """True when on-screen/voice copy is about this letter and word."""
    blob = " ".join(str(text or "").lower().split())
    if not blob:
        return False
    token = _alpha_word(word).lower()
    compact = blob.replace("-", "").replace(" ", "")
    if token and len(token) >= 2:
        if token not in blob and token.replace("-", "") not in compact:
            return False
    letter = str(letter or "").upper()
    if letter.isalpha() and token and token[:1] != letter.lower():
        return False
    return True


def _brief_fits_word(brief: str, word: str) -> bool:
    token = _alpha_word(word).lower()
    if not token:
        return True
    blob = str(brief or "").lower()
    return token in blob.replace("-", " ") or token in blob.replace("-", "")


def lock_kids_segments(segments: list[dict[str, Any]], *, intro: str = "") -> None:
    """Force letter, word, caption, voice, and picture to teach the same thing."""
    for i, seg in enumerate(segments):
        lock_kids_segment(seg, intro=intro if i == 0 else "")


def lock_kids_segment(seg: dict[str, Any], *, intro: str = "") -> dict[str, Any]:
    kind = str(seg.get("kind") or "").lower()
    word = _alpha_word(seg.get("word") or "")
    letter = str(seg.get("letter") or "")[:1].upper()

    if kind == "math" or seg.get("math_op"):
        left = int(seg.get("math_left") or 1)
        right = int(seg.get("math_right") or 1)
        op = str(seg.get("math_op") or "+")
        ans = int(seg.get("count") or (left - right if op == "-" else left + right))
        ans = max(0, ans)
        word = word or "APPLE"
        eq = f"{left} {op} {right} = {ans}"
        seg["kind"] = "math"
        seg["word"] = word
        seg["motif"] = motif_key(word)
        seg["letter"] = str(ans)
        seg["count"] = ans
        seg["spell_word"] = ""
        seg["overlay_text"] = eq
        seg["line"] = eq
        if op == "-":
            seg["caption"] = f"{left} take away {right} is {ans}"
        else:
            seg["caption"] = f"{left} plus {right} is {ans}"
        voice = str(seg.get("voice_line") or "")
        if "plus" not in voice.lower() and "take away" not in voice.lower():
            story = {"left": left, "right": right, "op": op, "item": word.lower() + "s", "place": "", "word": word}
            seg["voice_line"] = _math_voice(story, intro=intro)
        if not _text_fits_teaching(str(seg.get("fact") or ""), word=word):
            seg["fact"] = str(seg.get("caption") or "")
        brief = str(seg.get("image_brief") or "")
        if brief and not _brief_fits_word(brief, word):
            seg["image_brief"] = f"a friendly {word.lower()} kids can count"
        return seg

    if kind == "dictionary" or (str(seg.get("spell_word") or "").strip() and kind not in {"draw", "shape", "color", "play"}):
        if kind != "dictionary" and str(seg.get("spell_word") or "").strip():
            # Spell-the-word beats: keep letter-in-word copy, but the picture is the full word.
            spell = _alpha_word(seg.get("spell_word") or word)
            if spell:
                word = spell
                seg["word"] = word
                seg["motif"] = motif_key(word)
                if letter.isalpha() and letter not in spell:
                    letter = spell[min(int(seg.get("index") or 0), len(spell) - 1)]
                    seg["letter"] = letter
                if not _text_fits_teaching(str(seg.get("voice_line") or ""), letter=letter, word=word):
                    letters = list(spell)
                    idx = int(seg.get("index") or 0)
                    seg["voice_line"] = _spell_voice_line(idx, letter, word, letters, intro=intro)
                if not _text_fits_teaching(str(seg.get("overlay_text") or ""), word=word):
                    seg["overlay_text"] = f"{letter} in {word}"
                    seg["line"] = seg["overlay_text"]
            return seg
        word = word or "CAT"
        letter = word[0]
        seg["kind"] = "dictionary"
        seg["word"] = word
        seg["letter"] = letter
        seg["spell_word"] = word
        seg["motif"] = motif_key(word)
        seg["overlay_text"] = word
        seg["line"] = f"{word} — {word_meaning(word)}"
        seg["caption"] = f"{letter} is for {word}"
        if not _text_fits_teaching(str(seg.get("fact") or ""), word=word):
            seg["fact"] = word_meaning(word)
        if not _text_fits_teaching(str(seg.get("voice_line") or ""), word=word):
            seg["voice_line"] = _dictionary_voice(word, intro=intro)
        brief = str(seg.get("image_brief") or "")
        if brief and not _brief_fits_word(brief, word):
            seg["image_brief"] = f"a clear picture of a {word.lower()}"
        return seg

    if kind in {"shape", "color", "play"}:
        shape = str(seg.get("shape") or "")
        spdata = SHAPE_PEDAGOGY.get(shape.upper(), {})
        if spdata:
            seg["shape_sides"] = spdata.get("sides", 0)
            seg["shape_vertices"] = spdata.get("vertices", 0)
            seg["shape_fact"] = spdata.get("fact", "")
        voice = str(seg.get("voice_line") or "")
        if shape and shape.lower() not in voice.lower() and kind != "color":
            seg["voice_line"] = f"This is a {shape}. Can you draw a {shape}?"
            if intro and intro.lower() not in seg["voice_line"].lower():
                seg["voice_line"] = f"{intro} {seg['voice_line']}"
        color_name = str(seg.get("color_name") or "")
        if kind == "color" and color_name and color_name.lower() not in voice.lower():
            seg["voice_line"] = f"This color is {color_name}! Can you find {color_name}?"
        if word:
            seg["motif"] = motif_key(word)
        return seg

    if kind == "draw":
        doodle = str(seg.get("doodle_kind") or "")
        voice = str(seg.get("voice_line") or "")
        if word and not _text_fits_teaching(voice, word=word) and doodle.lower() not in voice.lower():
            seg["voice_line"] = (
                f"{intro} Draw a {doodle} with me. {word_meaning(word)}".strip()
                if doodle
                else f"{intro} {word_meaning(word)}".strip()
            )
        if word:
            seg["motif"] = motif_key(word)
        return seg

    # Math or number counting beats: attach ten-frame subitizing data
    if kind in {"math", "count"} or str(seg.get("count", "")).isdigit():
        cnt = int(seg.get("count", 0))
        if 1 <= cnt <= 10:
            seg["ten_frame"] = TEN_FRAME_DATA.get(cnt)

    if letter.isalpha():
        if not word or not word.startswith(letter):
            word = LETTER_WORDS.get(letter, ["FUN"])[0]
        seg["word"] = word
        seg["letter"] = letter
        seg["motif"] = motif_key(word)
        pdata = PHONEME_DATA.get(letter.upper(), {})
        if pdata:
            seg["phoneme"] = pdata.get("phoneme", "")
            seg["sound_name"] = pdata.get("sound_name", "")
            seg["sound_spelling"] = pdata.get("sound_spelling", "")
            seg["rhyme_family"] = pdata.get("rhyme_family", "")
            seg["stroke_count"] = pdata.get("stroke_count", 1)
        overlay = str(seg.get("overlay_text") or "")
        if not _text_fits_teaching(overlay, letter=letter, word=word):
            overlay = f"{letter} is for {word}"
        seg["overlay_text"] = overlay
        seg["line"] = overlay
        phonics = str(seg.get("phonics") or PHONICS.get(letter, f"Learn {letter}!"))
        voice = str(seg.get("voice_line") or "")
        if not _text_fits_teaching(voice, letter=letter, word=word):
            seg["voice_line"] = _voice_line(letter, word, phonics=phonics, intro=intro)
        if not _text_fits_teaching(str(seg.get("fact") or ""), word=word):
            seg["fact"] = word_meaning(word)
        brief = str(seg.get("image_brief") or "")
        if brief and not _brief_fits_word(brief, word):
            seg["image_brief"] = f"a friendly {word.lower()} kids can recognize"
        elif not brief:
            seg["image_brief"] = f"a friendly {word.lower()} kids can recognize"
    return seg


def _overlay_ai_copy(
    segments: list[dict[str, Any]],
    params: dict[str, Any],
    *,
    lock_spelling: bool = False,
    lock_teaching: bool = False,
) -> None:
    """Copy AI image briefs that match this beat. Never swap in a different word or voice."""
    lock_teaching = lock_teaching or lock_spelling
    voices = [str(v) for v in (params.get("ai_voice_lines") or []) if str(v).strip()]
    facts = [str(f) for f in (params.get("ai_fun_facts") or []) if str(f).strip()]
    words = [_alpha_word(w) for w in (params.get("focus_words") or []) if str(w).strip()]
    words = [w for w in words if w]
    plan = [
        dict(s)
        for s in (params.get("ai_segment_plan") or params.get("ai_visual_beats") or [])
        if isinstance(s, dict)
    ]
    for i, seg in enumerate(segments):
        kind = str(seg.get("kind") or "")
        letter = str(seg.get("letter") or "")[:1]
        word = str(seg.get("word") or "")
        teaching = lock_teaching or kind in {"math", "dictionary"}
        if i < len(plan):
            p = plan[i]
            brief = str(p.get("image_brief") or p.get("image") or "")
            if brief:
                if _brief_fits_word(brief, word) or not word:
                    seg["image_brief"] = brief
                else:
                    seg["image_brief"] = f"a friendly {word.lower()} kids can recognize"
            if teaching:
                continue
            if p.get("word"):
                cand = _alpha_word(p["word"])
                if cand and (not letter.isalpha() or cand.startswith(letter)):
                    seg["word"] = cand
                    word = cand
            if p.get("voice_line") and _text_fits_teaching(str(p["voice_line"]), letter=letter, word=word):
                seg["voice_line"] = str(p["voice_line"])
            if p.get("fact") and _text_fits_teaching(str(p["fact"]), letter=letter, word=word):
                seg["fact"] = str(p["fact"])
            if p.get("overlay_text") and _text_fits_teaching(str(p["overlay_text"]), letter=letter, word=word):
                seg["overlay_text"] = str(p["overlay_text"])
                if not p.get("line"):
                    seg["line"] = str(p["overlay_text"])
            if p.get("caption") and _text_fits_teaching(str(p["caption"]), letter=letter, word=word):
                seg["caption"] = str(p["caption"])
            if p.get("shape"):
                seg["shape"] = str(p["shape"])
            if p.get("motif") and _alpha_word(p["motif"]) in {word, _alpha_word(seg.get("motif"))}:
                seg["motif"] = str(p["motif"])
        if teaching:
            continue
        letter = str(seg.get("letter") or "")[:1]
        word = str(seg.get("word") or "")
        if voices:
            cand = voices[i % len(voices)]
            if _text_fits_teaching(cand, letter=letter, word=word):
                seg["voice_line"] = cand
        if facts:
            cand = facts[i % len(facts)]
            if _text_fits_teaching(cand, letter=letter, word=word):
                seg["fact"] = cand
        if words and "word" in seg:
            cand = words[i % len(words)]
            if cand and (not letter.isalpha() or cand.startswith(letter)):
                seg["word"] = cand


def _has_ai_voice(params: dict[str, Any]) -> bool:
    """True when AI already supplied narration that must not be overwritten."""
    if any(str(v).strip() for v in (params.get("ai_voice_lines") or [])):
        return True
    for item in list(params.get("ai_segment_plan") or []) + list(params.get("ai_visual_beats") or []):
        if isinstance(item, dict) and str(item.get("voice_line") or "").strip():
            return True
    return False


def _segment_edges(n: int, duration: float = 30.0, weights: Any = None) -> np.ndarray:
    """Lesson timing — intro a bit longer, last beat a rest, never a metronome click."""
    n = max(1, n)
    if isinstance(weights, (list, tuple)) and len(weights) > 0:
        w = []
        for item in list(weights)[:n]:
            try:
                w.append(float(item))
            except (TypeError, ValueError):
                w.append(1.0)
        while len(w) < n:
            w.append(1.0)
        arr = np.clip(np.array(w, dtype=np.float64), 0.05, 20.0)
        arr /= float(arr.sum())
        return np.concatenate([[0.0], np.cumsum(arr)])
    from app.art.education_anim import weighted_segment_edges

    return weighted_segment_edges(n)


def _segment_count_for_duration(duration: float, *, lo: int = 2, hi: int = 4) -> int:
    """Fewer beats so slow kids TTS can finish and a child can think."""
    return int(np.clip(int(duration / 8.0), lo, hi))


def _enrich_segment(seg: dict, rng: np.random.Generator, *, is_first: bool = False) -> dict:
    """Add on-screen engagement — keep voice lines short and clear."""
    seg["celebrate"] = str(rng.choice(CELEBRATION_LINES))
    if is_first:
        seg["engage"] = str(rng.choice(ENGAGE_HOOKS))
    if rng.random() < 0.3:
        seg["quiz"] = str(rng.choice(QUIZ_PROMPTS))
    if rng.random() < 0.25:
        seg["challenge"] = str(rng.choice(INTERACTIVE_CHALLENGES))
    return seg


def _voice_line(letter: str, word: str, phonics: str = "", *, intro: str = "") -> str:
    """Slow, repeatable narration: letter, sound, word, meaning."""
    start = f"{intro} " if intro else ""
    sound = phonics or PHONICS.get(letter.upper(), f"Learn {letter}!")
    meaning = word_meaning(word)
    return (
        f"{start}Letter {letter}. {sound}. "
        f"{letter} is for {word.lower()}. {meaning} "
        f"Say {word.lower()}."
    )


def _az_voice_line(letter: str, word: str, *, intro: str = "") -> str:
    """Short A–Z line: letter, then word, so kids can follow one idea at a time."""
    start = f"{intro} " if intro else ""
    return f"{start}This is the letter {letter}. {letter} is for {word.lower()}."


def _spell_voice_line(index: int, letter: str, word: str, letters: list[str], *, intro: str = "") -> str:
    hyphen = ". ".join(letters) + "."
    meaning = word_meaning(word)
    start = f"{intro} " if intro else ""
    if index == 0:
        return f"{start}Let's spell {word.lower()}. The first letter is {letter}. {letter}."
    if index >= len(letters) - 1:
        return f"{letter}. {hyphen} That spells {word.lower()}. {meaning} Say {word.lower()}!"
    return f"Next letter. {letter}."


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
        "real_world_math": "Math Around Us",
        "word_stickers": "Word Dictionary",
        "dictionary": "Word Dictionary",
        "creative_play": "Creative Play",
    }
    title = title_map.get(theme, "Doodle & Learn")
    intro_hook = str(rng.choice(ENGAGE_HOOKS))
    seg_count = _segment_count_for_duration(duration)

    segments: list[dict[str, Any]] = []
    if theme == "shape_fun":
        picks = list(rng.choice(SHAPES, size=min(seg_count, 6), replace=False))
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
                    "voice_line": f"{line.split('!')[0]}! Can you draw a {shape}?" if "!" in line else f"{line} Can you draw a {shape}?",
                }
            )
        visual_mode = "focus"
    elif theme == "color_rainbow":
        picks = list(rng.choice(len(COLORS), size=min(seg_count, 6), replace=False))
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
                    "voice_line": f"This color is {name}! Can you find {name}?",
                }
            )
        visual_mode = "color"
    elif theme in {"count_along", "real_world_math"}:
        segments = _math_lesson_segments(rng, min(seg_count, 4), intro_hook)
        visual_mode = "count"
    elif theme in {"word_stickers", "dictionary"}:
        segments = _dictionary_lesson_segments(rng, min(seg_count, 4), intro_hook)
        visual_mode = "stickers"
    else:
        picks = list(rng.choice(SHAPES, size=min(seg_count, 6), replace=False))
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
                    "voice_line": f"Let's doodle a {shape}! Draw it with me!",
                }
            )
        visual_mode = "playground"

    n = max(1, len(segments))
    edges = _segment_edges(n, duration, weights=params.get("segment_weights"))
    _overlay_ai_copy(segments, params)
    for i, seg in enumerate(segments):
        seg["t0"] = float(edges[i])
        seg["t1"] = float(edges[i + 1])
        _enrich_segment(seg, rng, is_first=(i == 0))
    lock_kids_segments(segments, intro=intro_hook)

    return {
        "theme": theme,
        "title": title,
        "visual_mode": visual_mode,
        "engine": "kids_doodles",
        "segments": segments,
        "duration": float(duration),
        "closing": str(rng.choice(["Great doodling!", "You are an artist!", "Keep creating!", "Amazing job!"])),
        "engage_intro": intro_hook,
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
    intro_hook = str(rng.choice(ENGAGE_HOOKS))
    seg_count = _segment_count_for_duration(duration, lo=3, hi=6)

    pool = list(DRAW_SUBJECTS)
    rng.shuffle(pool)

    if theme == "draw_along":
        picks = pool[:seg_count]
        visual_mode = "draw_along"
    elif theme == "sketch_practice":
        kind = pool[0][0]
        base = [s for s in pool if s[0] == kind][:1]
        picks = (base * seg_count)[:seg_count]
        visual_mode = "practice"
    else:
        picks = pool[:seg_count]
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
                "voice_line": (
                    f"{intro.rstrip('!')}! {word_meaning(word)} Draw a {kind} with me!"
                    if intro
                    else f"Draw a {kind} with me. {word_meaning(word)}"
                ),
            }
        )

    n = max(1, len(segments))
    edges = _segment_edges(n, duration, weights=params.get("segment_weights"))
    _overlay_ai_copy(segments, params)
    for i, seg in enumerate(segments):
        seg["t0"] = float(edges[i])
        seg["t1"] = float(edges[i + 1])
        _enrich_segment(seg, rng, is_first=(i == 0))
    lock_kids_segments(segments, intro=intro_hook)

    story_intro = "Once upon a time, an artist began to draw..."

    return {
        "theme": theme,
        "title": title,
        "visual_mode": visual_mode,
        "engine": "hand_art",
        "segments": segments,
        "duration": float(duration),
        "story_intro": story_intro if theme == "doodle_story" else "",
        "closing": str(rng.choice(["Beautiful drawing!", "You're an artist!", "Practice makes perfect!", "Great sketching!"])),
        "engage_intro": intro_hook,
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
