"""
Animal Anatomy Researcher
=========================
Upload se PEHLE internet par animal ki real anatomy search karta hai.
Wikipedia summary + DuckDuckGo se:
  - Real body colors / fur patterns
  - Correct class_type (quadruped / arachnid / serpent / reptile / crustacean / aquatic / insect / cephalopod)
  - Body proportions (leg length, body width ratio, head size)
  - Accent color (dominant visible color)
  - Unique_id check — already-used animals ko skip karta hai

Usage:
    from src.animal_researcher import research_animal, is_already_used, mark_used
"""
from __future__ import annotations

import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
USED_FILE = DATA_DIR / "used_animals.json"   # <-- permanent "no-repeat" registry

# ─────────────────────────────────────────────────────────────────────────────
# Duplicate-guard helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_used() -> set[str]:
    """Return set of animal IDs that have already been uploaded."""
    try:
        data = json.loads(USED_FILE.read_text(encoding="utf-8"))
        return set(data.get("used", []))
    except (OSError, json.JSONDecodeError):
        return set()


def _save_used(used: set[str]) -> None:
    USED_FILE.parent.mkdir(parents=True, exist_ok=True)
    USED_FILE.write_text(
        json.dumps({"used": sorted(used)}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def is_already_used(animal_name: str) -> bool:
    """True if this animal has already been uploaded to YouTube."""
    uid = _normalise_id(animal_name)
    return uid in _load_used()


def mark_used(animal_name: str) -> None:
    """Permanently mark this animal as used so it is never repeated."""
    used = _load_used()
    used.add(_normalise_id(animal_name))
    _save_used(used)
    print(f"  ✅ Marked as used (no-repeat): {animal_name}")


def _normalise_id(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower().strip()).strip("_")


# ─────────────────────────────────────────────────────────────────────────────
# Wikipedia search
# ─────────────────────────────────────────────────────────────────────────────

def _wikipedia_summary(animal_name: str, sentences: int = 6) -> str:
    """Fetch the first N sentences of a Wikipedia article for the animal.
    Tries multiple title variations for best match."""

    def _fetch(title: str) -> str:
        query = urllib.parse.quote(title.strip().title())
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "TeacherBotAnatomyResearcher/1.0 (educational)"},
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read())
            extract = data.get("extract", "")
            if len(extract) < 50:
                return ""
            parts = re.split(r"(?<=[.!?])\s+", extract)
            return " ".join(parts[:sentences])
        except Exception:
            return ""

    # Try progressively simpler titles
    clean = animal_name.strip().title()
    words = clean.split()

    candidates = [
        clean,                          # "Golden Shepherd Dog"
        " ".join(words[-2:]),           # "Shepherd Dog"
        words[-1],                      # "Dog"
        " ".join(words[:2]),            # "Golden Shepherd"
        words[0],                       # "Golden"
    ]
    # Remove duplicates while preserving order
    seen = set()
    unique = [c for c in candidates if c not in seen and not seen.add(c)]

    for title in unique:
        result = _fetch(title)
        if result:
            print(f"  📖 Wikipedia hit: '{title}'")
            return result
        time.sleep(0.15)

    print(f"  ⚠ Wikipedia: no good match found for '{animal_name}'")
    return ""


def _ddg_snippet(animal_name: str) -> str:
    """DuckDuckGo Instant Answer API for quick anatomy facts."""
    query = urllib.parse.quote(f"{animal_name} animal anatomy body color")
    url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&no_html=1"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TeacherBotAnatomyResearcher/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        abstract = data.get("Abstract", "") or data.get("Answer", "")
        return abstract[:600]
    except Exception as exc:
        print(f"  ⚠ DuckDuckGo fetch failed: {exc}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Color extraction from text
# ─────────────────────────────────────────────────────────────────────────────

# Map common color words → approximate RGB
_COLOR_MAP: dict[str, tuple[int, int, int]] = {
    "golden":    (218, 165, 32),
    "yellow":    (230, 200, 30),
    "orange":    (220, 110, 20),
    "amber":     (210, 150, 20),
    "tawny":     (200, 130, 35),
    "brown":     (130, 75, 30),
    "tan":       (185, 150, 80),
    "beige":     (200, 180, 130),
    "white":     (240, 235, 225),
    "cream":     (240, 220, 180),
    "silver":    (180, 180, 190),
    "grey":      (140, 140, 145),
    "gray":      (140, 140, 145),
    "charcoal":  (70, 70, 75),
    "black":     (25, 20, 18),
    "red":       (200, 60, 40),
    "crimson":   (185, 30, 40),
    "pink":      (230, 140, 155),
    "violet":    (120, 60, 160),
    "purple":    (100, 50, 140),
    "blue":      (50, 130, 200),
    "cyan":      (30, 180, 200),
    "teal":      (20, 155, 150),
    "green":     (50, 140, 60),
    "olive":     (100, 120, 50),
    "lime":      (130, 200, 40),
    "scarlet":   (190, 40, 30),
    "rust":      (160, 70, 20),
    "copper":    (180, 100, 45),
    "ivory":     (235, 225, 195),
    "slate":     (100, 115, 130),
    "indigo":    (60, 50, 150),
}

_CLASS_KEYWORDS: dict[str, list[str]] = {
    "quadruped":   ["mammal", "dog", "wolf", "cat", "lion", "tiger", "leopard",
                    "cheetah", "fox", "deer", "horse", "bear", "hyena", "mongoose",
                    "panda", "jaguar", "cougar", "lynx", "puma", "chimpanzee",
                    "gorilla", "baboon", "meerkat", "otter", "weasel", "badger",
                    "elk", "bison", "buffalo", "rhinoceros", "hippopotamus",
                    "giraffe", "zebra", "camel", "llama", "alpaca", "koala",
                    "kangaroo", "wallaby", "wombat", "platypus", "echidna",
                    "mole", "hedgehog", "rabbit", "hare"],
    "arachnid":    ["spider", "scorpion", "tarantula", "black widow", "brown recluse",
                    "jumping spider", "wolf spider", "orb weaver", "arachnid",
                    "mite", "tick"],
    "serpent":     ["snake", "boa", "python", "cobra", "mamba", "viper", "anaconda",
                    "rattlesnake", "kingsnake", "coral snake", "serpent"],
    "reptile":     ["lizard", "gecko", "iguana", "chameleon", "monitor", "komodo",
                    "tortoise", "turtle", "crocodile", "alligator", "caiman",
                    "skink", "tuatara", "dragon"],
    "crustacean":  ["crab", "lobster", "shrimp", "prawn", "crayfish", "mantis shrimp",
                    "barnacle", "krill", "crustacean"],
    "insect":      ["mantis", "praying mantis", "beetle", "butterfly", "moth",
                    "grasshopper", "locust", "cricket", "dragonfly", "damselfly",
                    "wasp", "bee", "ant", "termite", "cockroach", "katydid",
                    "stick insect", "walking stick", "firefly"],
    "cephalopod":  ["octopus", "squid", "cuttlefish", "nautilus", "cephalopod",
                    "blue-ringed"],
    "aquatic":     ["fish", "shark", "ray", "manta", "eel", "catfish", "tuna",
                    "salmon", "trout", "bass", "cod", "pike", "barracuda",
                    "swordfish", "marlin", "clownfish", "seahorse", "jellyfish",
                    "stingray", "whale", "dolphin", "porpoise", "seal", "walrus",
                    "manatee", "dugong", "narwhal"],
}


def _detect_class(text: str) -> str:
    """Guess the animation class from anatomy text."""
    lower = text.lower()
    scores: dict[str, int] = {k: 0 for k in _CLASS_KEYWORDS}
    for cls, keywords in _CLASS_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[cls] += 1
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "quadruped"


def _extract_colors(text: str) -> list[tuple[int, int, int]]:
    """Find up to 3 color mentions in the text and return as RGB tuples.
    Prioritizes colors mentioned near anatomy-related words."""
    lower = text.lower()
    found: list[tuple[int, int, int]] = []

    # Boost words near anatomy-related context
    anatomy_context_words = ["fur", "coat", "skin", "feathers", "scales", "body", "colou", "color",
                              "stripe", "spot", "patch", "markings", "pelage", "plumage"]

    # Find sentences/phrases that mention anatomy context
    context_text = lower
    for ctx_word in anatomy_context_words:
        idx = lower.find(ctx_word)
        if idx >= 0:
            # Extract surrounding window
            start = max(0, idx - 80)
            end = min(len(lower), idx + 120)
            snippet = lower[start:end]
            # Search colors in this snippet first (higher priority)
            for word, rgb in _COLOR_MAP.items():
                if word in snippet and rgb not in found:
                    found.append(rgb)
                    if len(found) >= 3:
                        break

    # Then search the full text for any remaining colors
    for word, rgb in _COLOR_MAP.items():
        if word in lower and rgb not in found:
            found.append(rgb)
        if len(found) >= 3:
            break

    # Always return at least one fallback color (dynamically derived from text hash so animals differ)
    if not found:
        # Generate deterministic but unique fallback color based on text
        h = sum(ord(c) for c in text[:100])
        r = (h % 155) + 50
        g = ((h // 155) % 155) + 50
        b = ((h // (155*155)) % 155) + 50
        found.append((r, g, b))
    return found[:3]


def _pick_accent(colors: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    """Choose the most 'vivid' color from the list (max saturation)."""
    def saturation(rgb):
        r, g, b = [x / 255.0 for x in rgb]
        cmax = max(r, g, b); cmin = min(r, g, b)
        return cmax - cmin

    return max(colors, key=saturation)


# ─────────────────────────────────────────────────────────────────────────────
# Main research function
# ─────────────────────────────────────────────────────────────────────────────

def research_animal(animal_name: str, scientific: str = "") -> dict:
    """
    Internet par animal search karke uski real anatomy decide karo.

    Returns a dict with keys:
        name, scientific, class_type, accent (RGB tuple),
        body_colors (list of RGB), anatomy_notes (str),
        fur_primary, fur_secondary, fur_highlight, fur_belly,
        proportions (dict: body_length, body_width, head_size, leg_length_ratio)
    """
    print(f"\n🔍 Researching anatomy for: {animal_name} ...")

    # 1. Fetch from Wikipedia
    wiki_text = _wikipedia_summary(animal_name)
    time.sleep(0.3)

    # 2. Fetch from DuckDuckGo (complementary data)
    ddg_text = _ddg_snippet(animal_name)
    time.sleep(0.2)

    combined = f"{wiki_text} {ddg_text}".strip()

    if not combined:
        print(f"  ⚠ No web data found. Using defaults for {animal_name}.")
        combined = f"{animal_name} is an animal."

    print(f"  📖 Source text ({len(combined)} chars): {combined[:120]}...")

    # 3. Detect locomotion class
    class_type = _detect_class(combined)
    print(f"  🦎 Detected class: {class_type}")

    # 4. Extract real colors from text
    body_colors = _extract_colors(combined)
    accent = _pick_accent(body_colors)
    print(f"  🎨 Body colors extracted: {body_colors}")
    print(f"  ⭐ Accent color chosen: {accent}")

    # 5. Derive fur layer colors from primary color
    primary = body_colors[0]
    secondary = body_colors[1] if len(body_colors) > 1 else _darken(primary, 0.75)
    highlight = body_colors[2] if len(body_colors) > 2 else _lighten(primary, 1.35)

    fur_dark      = _darken(primary, 0.55)
    fur_mid       = primary
    fur_gold      = _lighten(primary, 1.15)
    fur_light     = _lighten(primary, 1.40)
    fur_cream     = _lighten(secondary, 1.55)
    fur_highlight = highlight

    # 6. Proportions based on class
    proportions = _class_proportions(class_type)

    result = {
        "name":            animal_name.upper(),
        "scientific":      scientific or animal_name,
        "class_type":      class_type,
        "accent":          list(accent),
        "body_colors":     [list(c) for c in body_colors],
        "anatomy_notes":   combined[:400],
        # Per-layer fur colors for the renderer
        "fur_dark":        list(fur_dark),
        "fur_mid":         list(fur_mid),
        "fur_gold":        list(fur_gold),
        "fur_light":       list(fur_light),
        "fur_cream":       list(fur_cream),
        "fur_highlight":   list(fur_highlight),
        # Body shape multipliers
        "proportions":     proportions,
    }

    print(f"  ✅ Research complete for {animal_name}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Color math helpers
# ─────────────────────────────────────────────────────────────────────────────

def _darken(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, int(c * factor)) for c in rgb)  # type: ignore[return-value]


def _lighten(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(min(255, int(c * factor)) for c in rgb)  # type: ignore[return-value]


# ─────────────────────────────────────────────────────────────────────────────
# Class-specific default proportions
# ─────────────────────────────────────────────────────────────────────────────

def _class_proportions(class_type: str) -> dict:
    """Return body-shape multipliers per locomotion class."""
    defaults = {
        "quadruped":  {"body_width_scale": 1.0,  "leg_length_scale": 1.0,  "head_size_scale": 1.0,  "tail_wag": 0.65},
        "arachnid":   {"body_width_scale": 0.85, "leg_length_scale": 1.20, "head_size_scale": 0.70, "tail_wag": 0.0},
        "serpent":    {"body_width_scale": 0.35, "leg_length_scale": 0.0,  "head_size_scale": 0.90, "tail_wag": 0.0},
        "reptile":    {"body_width_scale": 0.90, "leg_length_scale": 0.80, "head_size_scale": 1.00, "tail_wag": 0.45},
        "crustacean": {"body_width_scale": 1.10, "leg_length_scale": 0.75, "head_size_scale": 0.80, "tail_wag": 0.0},
        "insect":     {"body_width_scale": 0.60, "leg_length_scale": 1.10, "head_size_scale": 0.75, "tail_wag": 0.0},
        "cephalopod": {"body_width_scale": 0.95, "leg_length_scale": 1.05, "head_size_scale": 1.10, "tail_wag": 0.0},
        "aquatic":    {"body_width_scale": 0.80, "leg_length_scale": 0.60, "head_size_scale": 0.85, "tail_wag": 0.0},
    }
    return defaults.get(class_type, defaults["quadruped"])
