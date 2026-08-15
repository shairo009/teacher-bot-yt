"""AI Short Director: deterministic, reusable creative decisions for every video.
No extra API dependency. It works with the existing LLM call and local history.
"""
from __future__ import annotations
import json
from pathlib import Path

FORMATS = [
    ("challenge", "Can you predict what happens before the code runs?", "fast_reveal"),
    ("mystery", "Something looks wrong here. Find it before the reveal.", "delayed_reveal"),
    ("visual_lab", "Watch the algorithm change the system in real time.", "simulation_first"),
    ("myth_buster", "This common coding idea is not quite what you think.", "myth_then_proof"),
    ("speed_run", "We have one minute to understand this.", "rapid_steps"),
    ("reverse_engineer", "What is the code actually doing under the hood?", "deconstruct"),
    ("prediction", "Pause here and make your prediction.", "pause_then_answer"),
    ("debug", "This tiny mistake changes everything.", "bug_then_fix"),
    ("compare", "Two approaches. One is clearly better here.", "side_by_side"),
    ("physics", "The code is simple; the behavior is not.", "simulation_then_math"),
    ("mental_model", "Think of it like this and the whole idea clicks.", "analogy_then_code"),
    ("story", "One small input starts a surprising chain reaction.", "cause_to_effect"),
]

CTA = [
    "Follow for the next coding puzzle.",
    "Save this and test the idea yourself.",
    "Comment your answer before the reveal.",
    "Try changing one value and see what breaks.",
    "Follow for another visual coding experiment.",
]


def _load_history(path: Path) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def performance_hint(history_path: Path) -> str:
    """Return a small evidence-based hint from views/likes, never inventing metrics."""
    history = _load_history(history_path)
    scored = [h for h in history if h.get("uploaded") and h.get("views") is not None]
    if not scored:
        return "No performance history yet; prioritize clarity, novelty, and a strong first 2 seconds."
    top = sorted(scored, key=lambda h: (float(h.get("views", 0)), float(h.get("likes", 0))), reverse=True)[:5]
    labels = [str(x.get("topic") or x.get("title") or "video")[:70] for x in top]
    return "Top-performing prior topics (use as inspiration, not duplication): " + " | ".join(labels)


def director_brief(puzzle_num: int, history_path: Path) -> dict:
    idx = (max(1, int(puzzle_num)) - 1) % len(FORMATS)
    fmt, hook, pacing = FORMATS[idx]
    return {
        "format": fmt,
        "hook": hook,
        "pacing": pacing,
        "cta": CTA[(puzzle_num - 1) % len(CTA)],
        "performance_hint": performance_hint(history_path),
        "structure": [
            "0-2s: hook with immediate visual motion",
            "2-9s: establish the puzzle/question",
            "9-27s: demonstrate the concept visually",
            "27-45s: reveal the key code/mechanism",
            "45-58s: show result and explain why",
            "58-65s+: concise takeaway and CTA",
        ],
    }


def prompt_suffix(brief: dict) -> str:
    return (
        "\n\nAI DIRECTOR BRIEF (follow this creatively, while preserving factual correctness):\n"
        + json.dumps(brief, ensure_ascii=False, indent=2)
        + "\nRules: hook must be understandable without context; every visual action must explain the concept; "
          "avoid decorative motion that competes with code; use short spoken sentences; end with a concrete takeaway.\n"
    )
