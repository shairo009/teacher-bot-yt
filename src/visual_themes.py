"""
Visual Themes — 20+ unique world aesthetics for Tech Bot videos.
Each video picks ONE theme randomly (seeded by topic_idx so same topic = same theme always).
"""

# ─────────────────────────────────────────────────────────────────────────────
# Each theme defines:
#   bg          : background fill color (RGB)
#   grid        : grid line color (RGB)
#   primary     : main accent / node color (RGB)
#   secondary   : secondary accent (RGB)
#   tertiary    : third accent (RGB)
#   text_bright : bright text (RGB)
#   text_dim    : dim text / labels (RGB)
#   node_fill   : node interior color (RGB)
#   node_border : node border color (RGB)
#   glow        : glow halo color (RGB)
#   grid_style  : "lines" | "dots" | "hex" | "circuit" | "diagonal" | "none"
#   particle    : "sparks" | "rain" | "stars" | "bubbles" | "pixels" | "dust"
#   name        : display name
# ─────────────────────────────────────────────────────────────────────────────

THEMES = {

    # ── 1. CYBERPUNK CITY ────────────────────────────────────────────────────
    "CYBERPUNK": {
        "name":        "CYBERPUNK CITY",
        "bg":          (4, 4, 14),
        "grid":        (30, 10, 50),
        "primary":     (255, 200, 0),
        "secondary":   (220, 50, 200),
        "tertiary":    (0, 220, 255),
        "text_bright": (255, 245, 200),
        "text_dim":    (130, 80, 180),
        "node_fill":   (20, 8, 35),
        "node_border": (255, 200, 0),
        "glow":        (255, 180, 0),
        "grid_style":  "diagonal",
        "particle":    "rain",
    },

    # ── 2. MATRIX ────────────────────────────────────────────────────────────
    "MATRIX": {
        "name":        "THE MATRIX",
        "bg":          (0, 5, 0),
        "grid":        (0, 25, 0),
        "primary":     (0, 255, 65),
        "secondary":   (0, 180, 40),
        "tertiary":    (150, 255, 150),
        "text_bright": (200, 255, 200),
        "text_dim":    (0, 100, 20),
        "node_fill":   (0, 12, 0),
        "node_border": (0, 220, 50),
        "glow":        (0, 200, 50),
        "grid_style":  "none",
        "particle":    "rain",
    },

    # ── 3. DEEP SPACE ────────────────────────────────────────────────────────
    "SPACE": {
        "name":        "DEEP SPACE",
        "bg":          (3, 3, 18),
        "grid":        (10, 10, 40),
        "primary":     (120, 80, 255),
        "secondary":   (255, 120, 50),
        "tertiary":    (80, 200, 255),
        "text_bright": (230, 225, 255),
        "text_dim":    (70, 60, 130),
        "node_fill":   (10, 8, 35),
        "node_border": (120, 80, 255),
        "glow":        (100, 60, 220),
        "grid_style":  "dots",
        "particle":    "stars",
    },

    # ── 4. RETRO ARCADE ──────────────────────────────────────────────────────
    "ARCADE": {
        "name":        "RETRO ARCADE",
        "bg":          (8, 0, 20),
        "grid":        (40, 0, 80),
        "primary":     (255, 60, 120),
        "secondary":   (255, 230, 0),
        "tertiary":    (0, 255, 200),
        "text_bright": (255, 255, 255),
        "text_dim":    (150, 0, 100),
        "node_fill":   (20, 0, 40),
        "node_border": (255, 60, 120),
        "glow":        (200, 0, 100),
        "grid_style":  "lines",
        "particle":    "pixels",
    },

    # ── 5. LAVA FORGE ────────────────────────────────────────────────────────
    "LAVA": {
        "name":        "LAVA FORGE",
        "bg":          (10, 2, 0),
        "grid":        (40, 10, 0),
        "primary":     (255, 100, 0),
        "secondary":   (255, 220, 50),
        "tertiary":    (200, 30, 0),
        "text_bright": (255, 240, 220),
        "text_dim":    (130, 50, 0),
        "node_fill":   (25, 5, 0),
        "node_border": (255, 100, 0),
        "glow":        (200, 60, 0),
        "grid_style":  "hex",
        "particle":    "sparks",
    },

    # ── 6. ICE CRYSTAL ───────────────────────────────────────────────────────
    "ICE": {
        "name":        "ICE CRYSTAL",
        "bg":          (2, 8, 20),
        "grid":        (10, 25, 55),
        "primary":     (160, 230, 255),
        "secondary":   (80, 160, 255),
        "tertiary":    (200, 245, 255),
        "text_bright": (220, 245, 255),
        "text_dim":    (60, 100, 160),
        "node_fill":   (5, 15, 38),
        "node_border": (160, 230, 255),
        "glow":        (100, 200, 255),
        "grid_style":  "diagonal",
        "particle":    "dust",
    },

    # ── 7. PLASMA STORM ──────────────────────────────────────────────────────
    "PLASMA": {
        "name":        "PLASMA STORM",
        "bg":          (6, 0, 18),
        "grid":        (25, 0, 60),
        "primary":     (200, 0, 255),
        "secondary":   (255, 255, 100),
        "tertiary":    (0, 255, 255),
        "text_bright": (255, 240, 255),
        "text_dim":    (100, 0, 150),
        "node_fill":   (15, 0, 35),
        "node_border": (200, 0, 255),
        "glow":        (180, 0, 220),
        "grid_style":  "lines",
        "particle":    "sparks",
    },

    # ── 8. AURORA BOREALIS ───────────────────────────────────────────────────
    "AURORA": {
        "name":        "AURORA BOREALIS",
        "bg":          (0, 5, 15),
        "grid":        (0, 20, 35),
        "primary":     (0, 230, 150),
        "secondary":   (120, 80, 255),
        "tertiary":    (0, 180, 255),
        "text_bright": (200, 255, 240),
        "text_dim":    (0, 80, 80),
        "node_fill":   (0, 10, 28),
        "node_border": (0, 200, 130),
        "glow":        (0, 200, 120),
        "grid_style":  "dots",
        "particle":    "dust",
    },

    # ── 9. BLOOD MOON ────────────────────────────────────────────────────────
    "BLOOD_MOON": {
        "name":        "BLOOD MOON",
        "bg":          (12, 0, 0),
        "grid":        (40, 0, 0),
        "primary":     (220, 20, 20),
        "secondary":   (255, 150, 0),
        "tertiary":    (180, 0, 80),
        "text_bright": (255, 220, 220),
        "text_dim":    (100, 10, 10),
        "node_fill":   (25, 0, 0),
        "node_border": (220, 20, 20),
        "glow":        (180, 0, 0),
        "grid_style":  "hex",
        "particle":    "sparks",
    },

    # ── 10. QUANTUM FIELD ────────────────────────────────────────────────────
    "QUANTUM": {
        "name":        "QUANTUM FIELD",
        "bg":          (2, 5, 12),
        "grid":        (8, 20, 45),
        "primary":     (50, 200, 255),
        "secondary":   (180, 50, 255),
        "tertiary":    (255, 200, 0),
        "text_bright": (200, 240, 255),
        "text_dim":    (30, 80, 140),
        "node_fill":   (5, 12, 30),
        "node_border": (50, 200, 255),
        "glow":        (30, 160, 220),
        "grid_style":  "circuit",
        "particle":    "bubbles",
    },

    # ── 11. NEON SAMURAI ─────────────────────────────────────────────────────
    "SAMURAI": {
        "name":        "NEON SAMURAI",
        "bg":          (5, 0, 0),
        "grid":        (30, 5, 5),
        "primary":     (255, 30, 50),
        "secondary":   (255, 255, 255),
        "tertiary":    (200, 0, 30),
        "text_bright": (255, 255, 255),
        "text_dim":    (120, 30, 30),
        "node_fill":   (15, 0, 0),
        "node_border": (255, 30, 50),
        "glow":        (200, 0, 30),
        "grid_style":  "diagonal",
        "particle":    "dust",
    },

    # ── 12. VAPORWAVE ────────────────────────────────────────────────────────
    "VAPORWAVE": {
        "name":        "VAPORWAVE",
        "bg":          (15, 5, 30),
        "grid":        (50, 10, 80),
        "primary":     (255, 100, 200),
        "secondary":   (100, 200, 255),
        "tertiary":    (255, 220, 80),
        "text_bright": (255, 230, 255),
        "text_dim":    (120, 50, 150),
        "node_fill":   (30, 10, 50),
        "node_border": (255, 100, 200),
        "glow":        (200, 50, 180),
        "grid_style":  "lines",
        "particle":    "stars",
    },

    # ── 13. BIOLUMINESCENT DEEP ──────────────────────────────────────────────
    "DEEP_SEA": {
        "name":        "DEEP SEA",
        "bg":          (0, 5, 15),
        "grid":        (0, 15, 35),
        "primary":     (0, 255, 200),
        "secondary":   (50, 150, 255),
        "tertiary":    (180, 255, 220),
        "text_bright": (180, 255, 240),
        "text_dim":    (0, 70, 80),
        "node_fill":   (0, 10, 25),
        "node_border": (0, 200, 160),
        "glow":        (0, 180, 140),
        "grid_style":  "none",
        "particle":    "bubbles",
    },

    # ── 14. SOLAR FLARE ──────────────────────────────────────────────────────
    "SOLAR": {
        "name":        "SOLAR FLARE",
        "bg":          (8, 3, 0),
        "grid":        (35, 15, 0),
        "primary":     (255, 230, 0),
        "secondary":   (255, 130, 0),
        "tertiary":    (255, 255, 200),
        "text_bright": (255, 250, 230),
        "text_dim":    (120, 70, 0),
        "node_fill":   (20, 8, 0),
        "node_border": (255, 200, 0),
        "glow":        (220, 160, 0),
        "grid_style":  "none",
        "particle":    "sparks",
    },

    # ── 15. CIRCUIT BOARD ────────────────────────────────────────────────────
    "CIRCUIT": {
        "name":        "CIRCUIT BOARD",
        "bg":          (0, 12, 4),
        "grid":        (0, 35, 12),
        "primary":     (0, 220, 80),
        "secondary":   (150, 255, 100),
        "tertiary":    (255, 200, 0),
        "text_bright": (200, 255, 210),
        "text_dim":    (0, 80, 30),
        "node_fill":   (0, 20, 8),
        "node_border": (0, 180, 60),
        "glow":        (0, 160, 50),
        "grid_style":  "circuit",
        "particle":    "pixels",
    },

    # ── 16. VOID MINIMAL ─────────────────────────────────────────────────────
    "VOID": {
        "name":        "THE VOID",
        "bg":          (0, 0, 0),
        "grid":        (12, 12, 12),
        "primary":     (255, 255, 255),
        "secondary":   (180, 180, 180),
        "tertiary":    (100, 100, 100),
        "text_bright": (255, 255, 255),
        "text_dim":    (80, 80, 80),
        "node_fill":   (5, 5, 5),
        "node_border": (200, 200, 200),
        "glow":        (150, 150, 150),
        "grid_style":  "dots",
        "particle":    "dust",
    },

    # ── 17. HOLOGRAM ─────────────────────────────────────────────────────────
    "HOLOGRAM": {
        "name":        "HOLOGRAM",
        "bg":          (0, 8, 20),
        "grid":        (0, 25, 55),
        "primary":     (100, 220, 255),
        "secondary":   (180, 240, 255),
        "tertiary":    (60, 180, 240),
        "text_bright": (200, 245, 255),
        "text_dim":    (40, 100, 160),
        "node_fill":   (0, 15, 35),
        "node_border": (100, 200, 255),
        "glow":        (60, 170, 230),
        "grid_style":  "diagonal",
        "particle":    "bubbles",
    },

    # ── 18. ANCIENT RUINS ────────────────────────────────────────────────────
    "ANCIENT": {
        "name":        "ANCIENT RUINS",
        "bg":          (10, 8, 2),
        "grid":        (35, 28, 8),
        "primary":     (220, 180, 50),
        "secondary":   (180, 120, 30),
        "tertiary":    (255, 220, 100),
        "text_bright": (255, 240, 200),
        "text_dim":    (100, 80, 20),
        "node_fill":   (22, 16, 4),
        "node_border": (200, 160, 40),
        "glow":        (180, 130, 20),
        "grid_style":  "hex",
        "particle":    "dust",
    },

    # ── 19. TOXIC WASTE ──────────────────────────────────────────────────────
    "TOXIC": {
        "name":        "TOXIC WASTELAND",
        "bg":          (4, 10, 0),
        "grid":        (15, 35, 0),
        "primary":     (150, 255, 0),
        "secondary":   (200, 255, 50),
        "tertiary":    (80, 200, 0),
        "text_bright": (220, 255, 180),
        "text_dim":    (60, 100, 0),
        "node_fill":   (8, 18, 0),
        "node_border": (130, 220, 0),
        "glow":        (100, 200, 0),
        "grid_style":  "lines",
        "particle":    "bubbles",
    },

    # ── 20. GHOST SIGNAL ─────────────────────────────────────────────────────
    "GHOST": {
        "name":        "GHOST SIGNAL",
        "bg":          (5, 5, 10),
        "grid":        (18, 18, 35),
        "primary":     (200, 200, 255),
        "secondary":   (150, 150, 240),
        "tertiary":    (255, 255, 255),
        "text_bright": (230, 230, 255),
        "text_dim":    (70, 70, 120),
        "node_fill":   (10, 10, 20),
        "node_border": (180, 180, 255),
        "glow":        (140, 140, 220),
        "grid_style":  "dots",
        "particle":    "stars",
    },
}

THEME_KEYS = list(THEMES.keys())


def pick_theme(topic_idx: int) -> dict:
    """Pick a deterministic theme for a given topic index."""
    import random
    rng = random.Random(topic_idx * 31337 + 7)
    key = rng.choice(THEME_KEYS)
    return THEMES[key], key
