"""Deterministic visual-idea bank for the coding-game Shorts pipeline.

24 motion/animation systems × 24 technical motifs = 576 distinct visual directions.
The renderer keeps the core reference style (big animated concept + code panel) while
using the direction to change motion, particles, geometry, and composition details.
"""

EFFECTS = [
    "orbit", "pulse", "scan", "flow", "radar", "wave", "constellation", "matrix",
    "glitch", "circuit", "rings", "particles", "trail", "signal", "gridwarp", "heatmap",
    "spiral", "nodes", "beams", "spectrum", "dots", "arcs", "shards", "comet",
]

MOTIFS = [
    "cache", "memory", "packet", "branch", "token", "queue", "stack", "tree",
    "graph", "kernel", "tensor", "query", "stream", "lock", "route", "cluster",
    "clock", "hash", "vector", "heap", "pipeline", "neuron", "shader", "fractal",
]

VISUAL_VARIANTS = [f"{effect} {motif}" for effect in EFFECTS for motif in MOTIFS]

assert len(VISUAL_VARIANTS) == 576


def variant_for(puzzle_num: int) -> str:
    """Return a stable variant so the same puzzle number is reproducible."""
    return VISUAL_VARIANTS[(max(1, int(puzzle_num)) - 1) % len(VISUAL_VARIANTS)]
