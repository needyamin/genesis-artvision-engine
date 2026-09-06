"""Offline how-it-works catalog — everyday education, not space HUD science."""

from __future__ import annotations

from typing import Any

import numpy as np

PROCESSES: list[dict[str, Any]] = [
    {
        "id": "water_cycle",
        "title": "The Water Cycle",
        "subtitle": "How rain comes back",
        "domain": "earth",
        "domain_label": "EVERYDAY SCIENCE",
        "hook": "The same water has been traveling sky to sea for billions of years.",
        "schematic_type": "cycle",
        "diagram_labels": ["Sun", "Cloud", "Rain", "Sea"],
        "metrics": [
            {"label": "Ocean water", "val": "97%", "unit": "of Earth's water"},
            {"label": "Cloud height", "val": "2–12", "unit": "km typical"},
        ],
        "segments": [
            {"phase": "EVAPORATE", "headline": "Sun lifts the water", "body": "Heat turns ocean water into invisible vapor.", "data_point": "Liquid → vapor", "voice_line": "The sun warms lakes and oceans, and water rises as invisible vapor."},
            {"phase": "CONDENSE", "headline": "Clouds form", "body": "Cool air packs vapor into tiny droplets we see as clouds.", "data_point": "Vapor → droplets", "voice_line": "High up, cool air packs the vapor into tiny droplets. That is a cloud."},
            {"phase": "PRECIPITATE", "headline": "Rain falls", "body": "Droplets join until they are heavy enough to fall.", "data_point": "Rain, snow, hail", "voice_line": "Droplets join until they are heavy, then fall as rain or snow."},
            {"phase": "COLLECT", "headline": "Back to rivers", "body": "Water runs to rivers and seas, ready to rise again.", "data_point": "Rivers to ocean", "voice_line": "Rain runs into rivers and back to the ocean, and the cycle starts again."},
        ],
    },
    {
        "id": "heartbeat",
        "title": "How Your Heart Beats",
        "subtitle": "A pump you never stop",
        "domain": "body",
        "domain_label": "YOUR BODY",
        "hook": "Your heart is a muscle pump that works while you sleep.",
        "schematic_type": "heart",
        "metrics": [
            {"label": "Resting rate", "val": "60–100", "unit": "beats per minute"},
            {"label": "Daily beats", "val": "~100k", "unit": "beats a day"},
        ],
        "segments": [
            {"phase": "FILL", "headline": "Blood comes in", "body": "Chambers fill with blood returning from the body.", "data_point": "Atria fill", "voice_line": "Blood returns to the heart and fills the upper chambers."},
            {"phase": "SQUEEZE", "headline": "The squeeze", "body": "Muscle contracts and pushes blood out.", "data_point": "Ventricles pump", "voice_line": "The heart muscle squeezes and pushes blood out to the lungs and body."},
            {"phase": "OXYGEN", "headline": "Lungs add oxygen", "body": "Blood picks up oxygen, then returns for another push.", "data_point": "Red blood, oxygen", "voice_line": "In the lungs, blood picks up oxygen, then the heart sends it out again."},
            {"phase": "RHYTHM", "headline": "A steady rhythm", "body": "Electrical pulses keep the beat without you thinking.", "data_point": "Pacemaker cells", "voice_line": "Tiny electrical pulses keep a steady rhythm, even while you sleep."},
        ],
    },
    {
        "id": "electricity_home",
        "title": "Electricity in Your Home",
        "subtitle": "From power plant to lamp",
        "domain": "tech",
        "domain_label": "HOW THINGS WORK",
        "hook": "A lamp lights because electrons are pushed through a wire.",
        "schematic_type": "circuit",
        "metrics": [
            {"label": "Home voltage", "val": "120/230", "unit": "volts"},
            {"label": "Speed of field", "val": "~c", "unit": "near light speed"},
        ],
        "segments": [
            {"phase": "SOURCE", "headline": "Power is made", "body": "Generators spin magnets to push electrons.", "data_point": "Spinning magnets", "voice_line": "At a power plant, spinning magnets push electrons and make electric current."},
            {"phase": "GRID", "headline": "Wires carry it", "body": "High-voltage lines move energy across the land.", "data_point": "Transmission lines", "voice_line": "Wires carry that energy across cities to a transformer near your street."},
            {"phase": "HOME", "headline": "Into the wall", "body": "A transformer lowers voltage for safe outlets.", "data_point": "Safe outlet voltage", "voice_line": "A transformer lowers the voltage so wall outlets are safe for lamps and phones."},
            {"phase": "LIGHT", "headline": "A closed loop", "body": "The switch closes the loop. The bulb glows.", "data_point": "Circuit complete", "voice_line": "When you flip the switch, the circuit closes and the bulb glows."},
        ],
    },
    {
        "id": "rainbow",
        "title": "Why Rainbows Appear",
        "subtitle": "Sunlight split by rain",
        "domain": "earth",
        "domain_label": "EVERYDAY SCIENCE",
        "hook": "A rainbow is sunlight bent and split by raindrops.",
        "schematic_type": "rainbow",
        "metrics": [
            {"label": "Viewing angle", "val": "42°", "unit": "for red light"},
            {"label": "Colors", "val": "7", "unit": "ROYGBIV bands"},
        ],
        "segments": [
            {"phase": "SUN", "headline": "Sun behind you", "body": "You need sun at your back and rain ahead.", "data_point": "Sun + rain", "voice_line": "Stand with the sun behind you and rain in front. That is rainbow weather."},
            {"phase": "BEND", "headline": "Light bends", "body": "Each drop acts like a tiny prism.", "data_point": "Refraction", "voice_line": "Each raindrop bends sunlight like a tiny prism."},
            {"phase": "SPLIT", "headline": "Colors separate", "body": "Different wavelengths leave at different angles.", "data_point": "Dispersion", "voice_line": "Different colors leave the drop at slightly different angles, so we see bands."},
            {"phase": "ARC", "headline": "A circle in the sky", "body": "The ground hides the rest. We see an arc.", "data_point": "Full circle possible", "voice_line": "A rainbow is really a circle. The ground hides the bottom, so we see an arc."},
        ],
    },
    {
        "id": "plant_drink",
        "title": "How Plants Drink",
        "subtitle": "Roots to leaves",
        "domain": "life",
        "domain_label": "LIVING THINGS",
        "hook": "A tree can lift water many meters without a pump you can see.",
        "schematic_type": "plant",
        "metrics": [
            {"label": "Pull force", "val": "transpiration", "unit": "leaf evaporation"},
            {"label": "Tubes", "val": "xylem", "unit": "water highways"},
        ],
        "segments": [
            {"phase": "ROOTS", "headline": "Roots grab water", "body": "Fine root hairs soak water from soil.", "data_point": "Root hairs", "voice_line": "Tiny root hairs soak water and minerals from the soil."},
            {"phase": "XYLEM", "headline": "Tubes go up", "body": "Xylem tubes carry water toward the leaves.", "data_point": "One-way tubes", "voice_line": "Narrow tubes called xylem carry that water up the stem toward the leaves."},
            {"phase": "LEAVES", "headline": "Leaves breathe out", "body": "Water evaporates from leaf pores.", "data_point": "Stomata", "voice_line": "Leaves open tiny pores. Water evaporates, and that pull lifts more water up."},
            {"phase": "SUGAR", "headline": "Food comes down", "body": "Sugar made in leaves travels to roots.", "data_point": "Phloem", "voice_line": "Leaves make sugar with sunlight, then send food down to the rest of the plant."},
        ],
    },
    {
        "id": "day_night",
        "title": "Why Day Turns to Night",
        "subtitle": "Earth spins",
        "domain": "earth",
        "domain_label": "EVERYDAY SCIENCE",
        "hook": "Night is not the sun turning off. Earth is turning.",
        "schematic_type": "spin",
        "metrics": [
            {"label": "Spin period", "val": "24", "unit": "hours"},
            {"label": "Tilt", "val": "23.5°", "unit": "seasons"},
        ],
        "segments": [
            {"phase": "SPIN", "headline": "Earth rotates", "body": "One full spin is about twenty-four hours.", "data_point": "One rotation / day", "voice_line": "Earth spins once every twenty-four hours. That spin makes day and night."},
            {"phase": "SUNLIT", "headline": "The lit half", "body": "The side facing the sun is daytime.", "data_point": "Day face", "voice_line": "The half of Earth facing the sun is in daylight."},
            {"phase": "SHADOW", "headline": "The dark half", "body": "The far side sits in Earth's own shadow.", "data_point": "Night face", "voice_line": "The far side sits in shadow. That is night."},
            {"phase": "DAWN", "headline": "Dawn is a line", "body": "Sunrise is the shadow line sliding over you.", "data_point": "Terminator", "voice_line": "Sunrise is the shadow line sliding across your town as Earth turns."},
        ],
    },
    {
        "id": "sound_wave",
        "title": "How Sound Travels",
        "subtitle": "Air that shakes",
        "domain": "physics",
        "domain_label": "HOW THINGS WORK",
        "hook": "Sound is not a thing flying through air. It is air pushing air.",
        "schematic_type": "wave",
        "metrics": [
            {"label": "In air", "val": "~343", "unit": "m/s at 20°C"},
            {"label": "In space", "val": "0", "unit": "no air, no sound"},
        ],
        "segments": [
            {"phase": "SOURCE", "headline": "Something vibrates", "body": "A drum, a voice, a speaker cone moves.", "data_point": "Vibration", "voice_line": "Sound starts when something vibrates: a drum, a voice, a speaker."},
            {"phase": "PUSH", "headline": "Air is pushed", "body": "Molecules bump neighbors in a chain.", "data_point": "Compression", "voice_line": "That motion pushes air molecules, which bump the next ones in a chain."},
            {"phase": "EAR", "headline": "Your eardrum", "body": "The chain reaches your eardrum and it wiggles.", "data_point": "Eardrum wiggle", "voice_line": "When the chain reaches your eardrum, the drum wiggles, and you hear."},
            {"phase": "VACUUM", "headline": "No air, no sound", "body": "Space has almost no air to carry the push.", "data_point": "Vacuum silent", "voice_line": "In space there is almost no air, so the push has nothing to travel through."},
        ],
    },
    {
        "id": "fridge_cold",
        "title": "How a Fridge Stays Cold",
        "subtitle": "Heat is moved, not destroyed",
        "domain": "tech",
        "domain_label": "HOW THINGS WORK",
        "hook": "A fridge does not make cold. It moves heat outside the box.",
        "schematic_type": "cycle",
        "diagram_labels": ["Evap", "Pump", "Coils", "Loop"],
        "metrics": [
            {"label": "Inside", "val": "~4°C", "unit": "fridge shelf"},
            {"label": "Method", "val": "phase change", "unit": "liquid ↔ gas"},
        ],
        "segments": [
            {"phase": "EVAP", "headline": "Coolant boils inside", "body": "Liquid coolant takes heat as it turns to gas.", "data_point": "Absorbs heat", "voice_line": "Inside the fridge, liquid coolant boils and takes heat with it."},
            {"phase": "COMPRESS", "headline": "A pump squeezes", "body": "The compressor squeezes the warm gas.", "data_point": "Pressure up", "voice_line": "A pump squeezes that gas, making it hotter and ready to dump heat."},
            {"phase": "COILS", "headline": "Coils on the back", "body": "Hot coils dump heat into the kitchen air.", "data_point": "Heat leaves", "voice_line": "Coils on the back dump that heat into your kitchen. That is why the back feels warm."},
            {"phase": "REPEAT", "headline": "It loops", "body": "The coolant liquefies and cycles again.", "data_point": "Closed loop", "voice_line": "The coolant turns liquid again and the loop repeats, keeping food cold."},
        ],
    },
    {
        "id": "magnet_pull",
        "title": "Why Magnets Pull",
        "subtitle": "Invisible fields",
        "domain": "physics",
        "domain_label": "HOW THINGS WORK",
        "hook": "A magnet does not need to touch iron to move it.",
        "schematic_type": "field",
        "metrics": [
            {"label": "Poles", "val": "2", "unit": "north and south"},
            {"label": "Earth", "val": "magnetic", "unit": "compass north"},
        ],
        "segments": [
            {"phase": "POLES", "headline": "Two poles", "body": "Every magnet has a north and a south.", "data_point": "N and S", "voice_line": "Every magnet has two poles: north and south."},
            {"phase": "FIELD", "headline": "A hidden map", "body": "Field lines loop from one pole to the other.", "data_point": "Field lines", "voice_line": "Invisible field lines loop from one pole to the other through space."},
            {"phase": "IRON", "headline": "Iron lines up", "body": "Iron bits become tiny magnets and get pulled.", "data_point": "Domains align", "voice_line": "Iron bits inside a nail line up and become tiny magnets, so the nail jumps."},
            {"phase": "EARTH", "headline": "Earth is a magnet", "body": "A compass needle follows Earth's field.", "data_point": "Compass", "voice_line": "Earth itself is a giant magnet, which is why a compass needle points north."},
        ],
    },
    {
        "id": "bread_toast",
        "title": "How Bread Becomes Toast",
        "subtitle": "Maillard browning",
        "domain": "food",
        "domain_label": "KITCHEN SCIENCE",
        "hook": "Toast is not just dry bread. Heat builds new flavors.",
        "schematic_type": "heat",
        "metrics": [
            {"label": "Browning", "val": "~140°C+", "unit": "Maillard starts"},
            {"label": "Water", "val": "leaves", "unit": "steam from crumb"},
        ],
        "segments": [
            {"phase": "HEAT", "headline": "Coils glow", "body": "The toaster radiates infrared heat.", "data_point": "Infrared", "voice_line": "Toaster coils glow and send infrared heat into the slice."},
            {"phase": "DRY", "headline": "Water leaves", "body": "Steam escapes. The surface dries.", "data_point": "Steam out", "voice_line": "Water turns to steam and leaves, so the surface dries."},
            {"phase": "BROWN", "headline": "Sugars meet proteins", "body": "The Maillard reaction makes brown flavor.", "data_point": "New aromas", "voice_line": "Sugars and proteins react. That is the brown color and toasty smell."},
            {"phase": "POP", "headline": "Time to pop", "body": "A timer cuts power before it burns.", "data_point": "Timer", "voice_line": "A timer cuts the power so the bread pops up before it burns."},
        ],
    },
]


def _diagram_labels(base: dict[str, Any]) -> list[str]:
    labels = [str(x).strip() for x in (base.get("diagram_labels") or []) if str(x).strip()]
    if len(labels) >= 4:
        return labels[:4]
    from_phases = [str(s.get("phase") or f"Step {i + 1}").strip() for i, s in enumerate(base.get("segments") or [])]
    from_phases = [p for p in from_phases if p]
    return (from_phases or ["Sun", "Cloud", "Rain", "Sea"])[:4]


def _timed_segments(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    n = max(1, len(raw))
    step = 1.0 / n
    out: list[dict[str, Any]] = []
    for i, seg in enumerate(raw):
        t0 = i * step
        t1 = min(1.0, (i + 1) * step)
        out.append(
            {
                "index": i,
                "total_segments": n,
                "t0": float(t0),
                "t1": float(t1),
                "phase": str(seg.get("phase") or "STEP"),
                "headline": str(seg.get("headline") or seg.get("overlay_text") or f"Step {i + 1}"),
                "body": str(seg.get("body") or seg.get("caption") or ""),
                "data_point": str(seg.get("data_point") or seg.get("fact") or ""),
                "voice_line": str(seg.get("voice_line") or seg.get("headline") or ""),
            }
        )
    return out


def _topic_dict(base: dict[str, Any], seed: int, duration: float, segments: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": base.get("id", "process"),
        "domain": base.get("domain", "everyday"),
        "domain_label": base.get("domain_label", "HOW IT WORKS"),
        "title": base.get("title", "How It Works"),
        "subtitle": base.get("subtitle", ""),
        "hook": base.get("hook", ""),
        "schematic": base.get("schematic_type", "cycle"),
        "schematic_type": base.get("schematic_type", "cycle"),
        "diagram_labels": _diagram_labels(base),
        "metrics": list(base.get("metrics") or []),
        "duration": float(duration),
        "seed": int(seed),
        "segments": segments,
    }


def _infer_schematic(title: str, params: dict[str, Any]) -> str:
    blob = f"{title} {' '.join(str(v) for v in (params.get('ai_fun_facts') or [])[:2])}".lower()
    hints = (
        ("heart", "heart"),
        ("blood", "heart"),
        ("electric", "circuit"),
        ("circuit", "circuit"),
        ("lamp", "circuit"),
        ("rainbow", "rainbow"),
        ("plant", "plant"),
        ("root", "plant"),
        ("leaf", "plant"),
        ("day", "spin"),
        ("night", "spin"),
        ("earth", "spin"),
        ("sound", "wave"),
        ("wave", "wave"),
        ("magnet", "field"),
        ("toast", "heat"),
        ("heat", "heat"),
        ("oven", "heat"),
        ("water", "cycle"),
        ("rain", "cycle"),
        ("fridge", "cycle"),
    )
    for needle, kind in hints:
        if needle in blob:
            return kind
    return "cycle"


def _from_ai(params: dict[str, Any], seed: int, duration: float) -> dict[str, Any] | None:
    title = str(params.get("ai_title") or "").strip()
    facts = [str(f) for f in (params.get("ai_fun_facts") or []) if str(f).strip()]
    voices = [str(v) for v in (params.get("ai_voice_lines") or []) if str(v).strip()]
    beats = params.get("ai_segment_plan") or params.get("ai_visual_beats") or []
    if not title and not beats and not facts and not voices:
        return None
    raw: list[dict[str, Any]] = []
    if isinstance(beats, list) and beats:
        for i, beat in enumerate(beats[:8]):
            if not isinstance(beat, dict):
                continue
            raw.append(
                {
                    "phase": str(beat.get("phase") or f"STEP {i + 1}"),
                    "headline": str(beat.get("overlay_text") or beat.get("headline") or beat.get("title") or f"Step {i + 1}"),
                    "body": str(beat.get("caption") or beat.get("body") or beat.get("fact") or ""),
                    "data_point": str(beat.get("fact") or beat.get("data_point") or ""),
                    "voice_line": str(beat.get("voice_line") or (voices[i] if i < len(voices) else "")),
                }
            )
    elif facts or voices:
        lines = facts or voices
        for i, line in enumerate(lines[:6]):
            raw.append(
                {
                    "phase": f"STEP {i + 1}",
                    "headline": line[:48],
                    "body": line,
                    "data_point": "",
                    "voice_line": voices[i] if i < len(voices) else line,
                }
            )
    if not raw:
        raw = [{"phase": "OVERVIEW", "headline": title or "How it works", "body": "", "data_point": "", "voice_line": title}]
    metrics = params.get("ai_metrics") if isinstance(params.get("ai_metrics"), list) else []
    return _topic_dict(
        {
            "id": "ai_how_it_works",
            "title": title or "How It Works",
            "subtitle": "AI lesson",
            "domain": "everyday",
            "domain_label": "HOW IT WORKS",
            "hook": facts[0] if facts else title,
            "schematic_type": _infer_schematic(title or "", params),
            "diagram_labels": [str(b.get("phase") or f"Step {i + 1}") for i, b in enumerate(raw[:4])],
            "metrics": list(metrics),
        },
        seed,
        duration,
        _timed_segments(raw),
    )


def build_how_it_works_topic(
    seed: int,
    duration: float,
    *,
    topic_id: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    params = params or {}
    existing = params.get("topic_data")
    if isinstance(existing, dict) and existing.get("segments"):
        topic = dict(existing)
        topic["duration"] = float(duration)
        topic["seed"] = int(seed)
        if topic["segments"] and "t0" not in topic["segments"][0]:
            topic["segments"] = _timed_segments(topic["segments"])
        return topic
    ai_topic = _from_ai(params, seed, duration)
    if ai_topic:
        return ai_topic
    rng = np.random.default_rng(seed)
    if topic_id:
        match = next((p for p in PROCESSES if p["id"] == topic_id), None)
        chosen = match or PROCESSES[int(rng.integers(0, len(PROCESSES)))]
    else:
        chosen = PROCESSES[int(rng.integers(0, len(PROCESSES)))]
    return _topic_dict(chosen, seed, duration, _timed_segments(list(chosen["segments"])))
