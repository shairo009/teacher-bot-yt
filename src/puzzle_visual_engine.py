"""
Puzzle Visual Engine — Coding Game Style Renderer v4
Looks like a real coding puzzle game (Human Resource Machine / Zachtronics / CodeCombat).
Layout:
  [0   – 250]  Game header: puzzle# + stars + topic title + difficulty badge
  [250 – 950]  Python code editor panel (syntax highlighted, line cursor, 0 text overlap)
  [950 – 1530] Execution visualization (animated cyber grid, particles, neon glow, bars/graph/grid/stack)
  [1530– 1750] Test cases panel (animated pass badges)
  [1750– 1920] Step dots + complexity stats + speedrun timer footer
"""

import math, random, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH  = 1080
HEIGHT = 1920
FPS    = 30

# ── Zone constants (Strict Non-Overlapping Boundaries) ──────────────────────
HEADER_TOP   = 0
HEADER_BOT   = 250
CODE_TOP     = 250
CODE_BOT     = 950
VIZ_TOP      = 950
VIZ_BOT      = 1530
TESTS_TOP    = 1530
TESTS_BOT    = 1750
FOOTER_TOP   = 1750
FOOTER_BOT   = 1920

CODE_PAD_L   = 28
CODE_PAD_R   = 28
LINE_H       = 42          # pixels per code line
MAX_VISIBLE  = 15          # max code lines visible at once

# ── Color palette (VS Code Dark+ inspired) ───────────────────────────────────
EDITOR_BG     = (18,  20,  28)
EDITOR_BORDER = (50,  55,  75)
GUTTER_BG     = (22,  24,  32)
GUTTER_FG     = (70,  80, 110)
LINE_HL       = (40,  48,  72)   # active line highlight
CURSOR_COL    = (220, 220, 80)   # cursor color

# Dynamic vibrant neon color palettes (Rotates per puzzle so EVERY video looks unique & fresh!)
DYNAMIC_PALETTES = [
    ( 80, 220, 160),   # Electric Emerald
    (160, 110, 255),   # Cyber Violet
    (255, 130,  50),   # Solar Orange
    ( 80, 200, 255),   # Ice Cyan
    (255,  80, 140),   # Neon Pink
    (255, 200,  60),   # Cyber Gold
    ( 80, 240, 220),   # Matrix Mint
    (220,  80, 220),   # Synth Wave Purple
]

# Syntax colors (Ultra-high contrast for crystal clear reading on phones)
SYN = {
    "keyword":   (215, 130, 255),  # vibrant purple – def, for, if, return, class
    "builtin":   ( 90, 215, 235),  # vibrant cyan   – range, len, print, enumerate
    "string":    (160, 230, 120),  # vibrant lime   – "text", 'text'
    "number":    (255, 175,  90),  # solar amber    – 42, 3.14
    "comment":   (110, 120, 150),  # crisp gray     – # comment
    "decorator": (255, 110,  90),  # coral red      – @property
    "operator":  ( 90, 215, 235),  # cyan           – == != <= >=
    "class_name":(255, 215, 100),  # bright gold    – ClassName
    "func_name": (110, 200, 255),  # electric blue  – function name after def
    "default":   (220, 230, 245),  # crisp white    – everything else
    "self_kw":   (255, 110,  90),  # coral red      – self
    "bracket":   (255, 215, 100),  # bright gold    – ( ) [ ] { }
}


PY_KEYWORDS = {
    "def","class","return","if","elif","else","for","while","in","not","and",
    "or","is","None","True","False","import","from","as","with","pass","break",
    "continue","raise","try","except","finally","yield","lambda","del","global",
    "nonlocal","assert","async","await",
}
PY_BUILTINS = {
    "range","len","print","enumerate","zip","map","filter","sorted","reversed",
    "list","dict","set","tuple","int","str","float","bool","type","isinstance",
    "hasattr","getattr","setattr","max","min","sum","abs","round","input","open",
    "super","property","staticmethod","classmethod","any","all","next","iter",
}

# Theme colors per series (for header accent)
SERIES_COLORS = {
    "Systems":     (255, 130,  50),
    "Compilers":   (160, 110, 255),
    "Distributed": ( 80, 200, 255),
    "Databases":   (255, 200,  60),
    "Algorithms":  ( 80, 220, 160),
    "Concurrency": (255,  80, 120),
    "Networking":  ( 60, 180, 255),
    "AI/ML":       (220,  80, 220),
    "Security":    (220,  60,  60),
    "Cloud":       (100, 200, 255),
    "Python":      (255, 220,  60),
}


# ─────────────────────────────────────────────────────────────────────────────
# FONT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_FC = {}
def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold, mono)
    if key in _FC:
        return _FC[key]
    mono_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
    ]
    ui_candidates = [
        "assets/fonts/Montserrat-Bold.ttf" if bold else "assets/fonts/Montserrat-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in (mono_candidates if mono else ui_candidates):
        try:
            f = ImageFont.truetype(p, size)
            _FC[key] = f
            return f
        except:
            pass
    f = ImageFont.load_default()
    _FC[key] = f
    return f


def text_w(text: str, font) -> int:
    try:
        return int(font.getlength(text))
    except:
        return len(text) * 10


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return int(a + (b - a) * t)


def lerp_c(c1, c2, t):
    return tuple(lerp(a, b, t) for a, b in zip(c1, c2))


# ─────────────────────────────────────────────────────────────────────────────
# SYNTAX HIGHLIGHTER
# ─────────────────────────────────────────────────────────────────────────────

def tokenize_python_line(line: str) -> list[tuple[str, tuple[int,int,int]]]:
    if not line.strip():
        return [(" ", SYN["default"])]
    tokens = []
    stripped = line.lstrip()
    if stripped.startswith("#"):
        return [(line, SYN["comment"])]

    comment = ""
    code_part = line
    in_str, str_char = False, ""
    for i, ch in enumerate(line):
        if not in_str and ch in ('"', "'"):
            in_str = True
            str_char = ch
        elif in_str and ch == str_char:
            in_str = False
        elif not in_str and ch == "#":
            code_part = line[:i]
            comment   = line[i:]
            break

    pattern = re.compile(
        r'(""".*?"""|\'\'\'.*?\'\'\'|"[^"\n]*"|\'[^\'\n]*\')'   # strings
        r'|(\b\d+\.?\d*\b)'                                       # numbers
        r'|(@\w+)'                                                 # decorators
        r'|([(){}\[\]])'                                           # brackets
        r'|(\b\w+\b)'                                             # words
        r'|([-+*/=<>!&|^~%.,:;]+)'                               # operators
        r'|(\s+)'                                                  # whitespace
    )

    after_def = False
    for m in pattern.finditer(code_part):
        s, num, dec, brk, word, op, ws = m.groups()
        if ws:
            tokens.append((ws, SYN["default"]))
        elif s:
            tokens.append((s, SYN["string"]))
        elif num:
            tokens.append((num, SYN["number"]))
        elif dec:
            tokens.append((dec, SYN["decorator"]))
        elif brk:
            tokens.append((brk, SYN["bracket"]))
        elif word:
            if word in PY_KEYWORDS:
                tokens.append((word, SYN["keyword"]))
                after_def = word == "def"
            elif after_def:
                tokens.append((word, SYN["func_name"]))
                after_def = False
            elif word in PY_BUILTINS:
                tokens.append((word, SYN["builtin"]))
            elif word == "self":
                tokens.append((word, SYN["self_kw"]))
            elif word[0].isupper():
                tokens.append((word, SYN["class_name"]))
            else:
                tokens.append((word, SYN["default"]))
                after_def = False
        elif op:
            tokens.append((op, SYN["operator"]))

    if comment:
        tokens.append((comment, SYN["comment"]))

    return tokens or [(line, SYN["default"])]


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: CODE EDITOR
# ─────────────────────────────────────────────────────────────────────────────

def draw_code_editor(draw: ImageDraw.Draw, code_lines: list[str],
                     active_line: int, accent: tuple, step_progress: float):
    GUTTER_W    = 52
    CODE_LEFT   = CODE_PAD_L + GUTTER_W
    font        = get_font(25, mono=True)
    font_lnum   = get_font(19, mono=True)

    draw.rectangle([0, CODE_TOP, WIDTH, CODE_BOT], fill=EDITOR_BG)
    draw.line([0, CODE_TOP, WIDTH, CODE_TOP], fill=accent, width=3)
    draw.line([0, CODE_BOT, WIDTH, CODE_BOT], fill=EDITOR_BORDER, width=2)
    draw.rectangle([0, CODE_TOP, CODE_PAD_L + GUTTER_W, CODE_BOT], fill=GUTTER_BG)
    draw.line([CODE_PAD_L + GUTTER_W, CODE_TOP, CODE_PAD_L + GUTTER_W, CODE_BOT],
              fill=EDITOR_BORDER, width=1)

    tab_text = "  puzzle.py  "
    tab_font = get_font(20, bold=True)
    tab_w    = text_w(tab_text, tab_font) + 4
    draw.rectangle([0, CODE_TOP, tab_w, CODE_TOP + 32], fill=accent)
    draw.text((tab_w // 2, CODE_TOP + 16), tab_text, font=tab_font, fill=(0, 0, 0), anchor="mm")

    scroll_start = max(0, active_line - MAX_VISIBLE // 2)
    visible_lines = code_lines[scroll_start: scroll_start + MAX_VISIBLE]

    for i, line in enumerate(visible_lines):
        abs_line = scroll_start + i
        y_top    = CODE_TOP + 38 + i * LINE_H

        is_active = (abs_line == active_line)
        if is_active:
            draw.rectangle([0, y_top, WIDTH, y_top + LINE_H], fill=LINE_HL)
            draw.rectangle([0, y_top, 4, y_top + LINE_H], fill=accent)

        lnum_str = str(abs_line + 1)
        lnum_x   = CODE_PAD_L + GUTTER_W - 8
        lnum_col = accent if is_active else GUTTER_FG
        draw.text((lnum_x, y_top + LINE_H // 2), lnum_str,
                  font=font_lnum, fill=lnum_col, anchor="rm")

        tokens = tokenize_python_line(line)
        x = CODE_LEFT + 8
        max_x = WIDTH - CODE_PAD_R - 10
        for token_text, color in tokens:
            if x >= max_x:
                break
            tw_val = text_w(token_text, font)
            if x + tw_val > max_x:
                avail_chars = max(1, int(len(token_text) * (max_x - x) / max(1, tw_val)))
                token_text = token_text[:avail_chars]
                draw.text((x, y_top + LINE_H // 2 - 1), token_text,
                          font=font, fill=color, anchor="lm")
                break
            draw.text((x, y_top + LINE_H // 2 - 1), token_text,
                      font=font, fill=color, anchor="lm")
            x += tw_val

        if is_active:
            cursor_blink = step_progress % 0.5 < 0.25 or step_progress > 0.8
            if cursor_blink:
                cursor_x = x + 2
                cursor_x = max(CODE_LEFT + 10, min(cursor_x, max_x))
                draw.rectangle([cursor_x, y_top + 6, cursor_x + 3, y_top + LINE_H - 6],
                               fill=CURSOR_COL)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: GAME HEADER (0 Text Overlaps)
# ─────────────────────────────────────────────────────────────────────────────

def draw_game_header(draw: ImageDraw.Draw, scene: dict, accent: tuple,
                     step_idx: int, total_steps: int):
    puzzle_num = scene.get("puzzle_num", 1)
    title      = scene.get("title", "Algorithm Deep Dive")
    subtitle   = scene.get("subtitle", "")
    series     = scene.get("series", "Systems")
    chapter    = scene.get("chapter", "")
    stars      = scene.get("puzzle_stars", 3)
    diff       = scene.get("difficulty", "HARD")
    game_tag   = scene.get("game_tag", "⚔ BOSS FIGHT")

    draw.rectangle([0, HEADER_TOP, WIDTH, HEADER_BOT], fill=(12, 14, 22))
    draw.line([0, HEADER_BOT, WIDTH, HEADER_BOT], fill=EDITOR_BORDER, width=2)

    fn_badge = get_font(22, bold=True)
    fn_star  = get_font(28, bold=True)

    # Row 1 (Y = 28): Puzzle Num (Left), Difficulty Badge (Center), Stars (Right)
    pnum_text = f"PUZZLE #{puzzle_num:03d}"
    draw.text((36, 28), pnum_text, font=get_font(24, bold=True), fill=accent, anchor="lm")

    diff_colors = {"EASY": (80, 200, 80), "MEDIUM": (255, 180, 0),
                   "HARD": (255, 80, 80), "EXTREME": (200, 0, 255)}
    diff_c = diff_colors.get(diff, (255, 80, 80))
    diff_text = f" {diff} "
    dw = text_w(diff_text, fn_badge) + 16
    draw.rounded_rectangle([WIDTH // 2 - dw // 2, 12, WIDTH // 2 + dw // 2, 44],
                            radius=6, fill=lerp_c(diff_c, (0, 0, 0), 0.75), outline=diff_c, width=2)
    draw.text((WIDTH // 2, 28), diff_text, font=fn_badge, fill=diff_c, anchor="mm")

    filled_stars = min(3, 1 + step_idx // max(total_steps // 3, 1))
    star_x = WIDTH - 36
    for si in range(3, 0, -1):
        s_text = "★" if si <= filled_stars else "☆"
        s_col  = (255, 210, 0) if si <= filled_stars else (60, 65, 90)
        draw.text((star_x, 28), s_text, font=fn_star, fill=s_col, anchor="rm")
        star_x -= 34

    # Row 2 (Y = 66): Game Tag Pill (Left) & Series Chapter Badge (Right)
    fn_tag = get_font(20, bold=True)
    tag_text = f" {game_tag} "
    tw = text_w(tag_text, fn_tag) + 10
    draw.rounded_rectangle([36, 54, 36 + tw, 84], radius=6,
                            fill=lerp_c(accent, (0, 0, 0), 0.8), outline=accent, width=1)
    draw.text((36 + tw // 2, 69), tag_text, font=fn_tag, fill=accent, anchor="mm")

    badge_text = f"{series} › {chapter}" if chapter else series
    if len(badge_text) > 30:
        badge_text = badge_text[:27] + "..."
    fn_series  = get_font(19, bold=False)
    draw.text((WIDTH - 36, 69), badge_text, font=fn_series,
              fill=(120, 135, 170), anchor="rm")

    # Row 3 (Y = 100-240): Wrapped Title & Subtitle (Strict Non-Overlapping Padding)
    fn_title = get_font(32, bold=True)
    fn_sub   = get_font(21, bold=False)
    title_lines = _wrap(title, fn_title, WIDTH - 100)[:2]
    
    title_y = 116
    for ln in title_lines:
        draw.text((WIDTH // 2, title_y), ln, font=fn_title, fill=(235, 240, 250), anchor="mm")
        title_y += 40

    if subtitle:
        if len(subtitle) > 55:
            subtitle = subtitle[:52] + "..."
        draw.text((WIDTH // 2, min(title_y + 4, HEADER_BOT - 20)), subtitle, font=fn_sub,
                  fill=(110, 125, 160), anchor="mm")



# ─────────────────────────────────────────────────────────────────────────────
# SECTION: TEST CASES PANEL
# ─────────────────────────────────────────────────────────────────────────────

def draw_test_panel(draw: ImageDraw.Draw, scene: dict, step_idx: int,
                    total_steps: int, accent: tuple):
    tests = scene.get("test_cases", [])
    if not tests:
        return

    draw.rectangle([0, TESTS_TOP, WIDTH, TESTS_BOT], fill=(14, 16, 24))
    draw.line([0, TESTS_TOP, WIDTH, TESTS_TOP], fill=EDITOR_BORDER, width=2)

    fn_head = get_font(20, bold=True)
    fn_test = get_font(20, mono=True)
    fn_icon = get_font(24, bold=True)

    draw.text((36, TESTS_TOP + 20), "TEST CASES", font=fn_head, fill=accent, anchor="lm")

    pass_ratio = (step_idx + 1) / max(total_steps, 1)
    n_pass     = int(len(tests) * pass_ratio)
    draw.text((WIDTH - 36, TESTS_TOP + 20),
              f"{n_pass}/{len(tests)} passing", font=fn_head,
              fill=(80, 200, 80) if n_pass == len(tests) else (200, 200, 80),
              anchor="rm")

    col_w = (WIDTH - 72) // min(len(tests), 4)
    for ti, test in enumerate(tests[:4]):
        passing = ti < n_pass
        tx      = 36 + ti * col_w
        ty      = TESTS_TOP + 44

        box_c   = (20, 42, 24) if passing else (32, 20, 24)
        brd_c   = (60, 180, 70) if passing else (90, 50, 50)
        icon    = "✓ PASS" if passing else "○ TEST"
        icon_c  = (90, 230, 90) if passing else (90, 90, 100)

        draw.rounded_rectangle([tx, ty, tx + col_w - 8, ty + (TESTS_BOT - TESTS_TOP - 54)],
                                radius=6, fill=box_c, outline=brd_c, width=2)

        draw.text((tx + col_w // 2, ty + 18), icon, font=fn_icon, fill=icon_c, anchor="mm")

        in_text  = f"in: {str(test.get('input', '?'))[:12]}"
        exp_text = f"→ {str(test.get('expected', '?'))[:12]}"
        draw.text((tx + 10, ty + 46), in_text,  font=fn_test, fill=(150, 160, 190))
        draw.text((tx + 10, ty + 72), exp_text, font=fn_test,
                  fill=(90, 210, 90) if passing else (150, 160, 190))

        label = test.get("label", f"test_{ti+1}")
        draw.text((tx + col_w // 2, ty + 108), label, font=get_font(16),
                  fill=(80, 95, 130), anchor="mm")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: STEP / SCORE FOOTER (0 Text Overlap)
# ─────────────────────────────────────────────────────────────────────────────

def draw_footer(draw: ImageDraw.Draw, step_idx: int, total_steps: int,
                scene: dict, accent: tuple, global_frame: int):
    draw.rectangle([0, FOOTER_TOP, WIDTH, FOOTER_BOT], fill=(10, 12, 20))
    draw.line([0, FOOTER_TOP, WIDTH, FOOTER_TOP], fill=EDITOR_BORDER, width=1)

    # Step dots in middle
    dot_r, gap = 8, 24
    dots_cx    = WIDTH // 2
    total_w    = total_steps * gap
    start_x    = dots_cx - total_w // 2 + dot_r
    dot_y      = FOOTER_TOP + 42
    for i in range(total_steps):
        cx = start_x + i * gap
        if i < step_idx:
            draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r], fill=accent)
        elif i == step_idx:
            # Pulsing current dot
            pulse = int(2 * math.sin(global_frame * 0.2))
            draw.ellipse([cx - dot_r - pulse, dot_y - dot_r - pulse, cx + dot_r + pulse, dot_y + dot_r + pulse],
                         fill=(255, 255, 255), outline=accent, width=2)
        else:
            draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r],
                         fill=(30, 35, 50), outline=(50, 55, 80), width=2)

    # Complexity badges (left) — truncated if long to prevent dot overlap
    time_c = scene.get("time_complexity", "O(?)")[:22]
    space_c = scene.get("space_complexity", "O(?)")[:22]
    fn_cmplx = get_font(20, bold=True, mono=True)
    draw.text((36, FOOTER_TOP + 36), f"⏱ {time_c}", font=fn_cmplx, fill=(80, 180, 255), anchor="lm")
    draw.text((36, FOOTER_TOP + 72), f"💾 {space_c}", font=fn_cmplx, fill=(180, 130, 255), anchor="lm")

    # Speedrun Timer (right)
    elapsed   = global_frame / FPS
    m, s = int(elapsed // 60), int(elapsed % 60)
    fn_timer  = get_font(26, bold=True, mono=True)
    draw.text((WIDTH - 36, FOOTER_TOP + 54), f"{m:02d}:{s:02d}",
              font=fn_timer, fill=(90, 105, 140), anchor="rm")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: HIGH-ANIMATION EXECUTION VISUALIZER (Cyber Grid + Neon Aura + Floating Badges)
# ─────────────────────────────────────────────────────────────────────────────

def _draw_cyber_grid(draw: ImageDraw.Draw, x0: int, y0: int, x1: int, y1: int,
                     frame: int, accent: tuple):
    """Render moving background cybernetic grid and animated energy particles."""
    grid_size = 40
    offset_y  = int((frame * 1.5) % grid_size)
    grid_col  = (18, 24, 38)

    # Vertical grid lines
    for gx in range(x0, x1, grid_size):
        draw.line([gx, y0, gx, y1], fill=grid_col, width=1)
    # Moving horizontal grid lines
    for gy in range(y0 + offset_y, y1, grid_size):
        draw.line([x0, gy, x1, gy], fill=grid_col, width=1)

    # Animated Energy Particles (Rising up)
    rng = random.Random(42)
    for p in range(12):
        px = rng.randint(x0 + 20, x1 - 20)
        base_py = rng.randint(y0 + 20, y1 - 20)
        py = y0 + ((base_py - y0 - frame * (2 + p % 3)) % (y1 - y0))
        pr = 2 + (p % 3)
        alpha_c = lerp_c(accent, (10, 12, 20), 0.6 + 0.03 * (p % 10))
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=alpha_c)


def draw_visualization(draw: ImageDraw.Draw, scene: dict, step_idx: int,
                       step_progress: float, global_frame: int, accent: tuple):
    x0, y0, x1, y1 = 28, VIZ_TOP + 12, WIDTH - 28, VIZ_BOT - 12
    draw.rectangle([0, VIZ_TOP, WIDTH, VIZ_BOT], fill=(10, 12, 20))
    draw.line([0, VIZ_TOP, WIDTH, VIZ_TOP], fill=EDITOR_BORDER, width=2)

    # 1. Background Cyber Grid Animation
    _draw_cyber_grid(draw, x0, VIZ_TOP, x1, VIZ_BOT, global_frame, accent)

    # Header label
    fn_label = get_font(22, bold=True)
    draw.text((x0 + 4, VIZ_TOP + 20), "▶ LIVE EXECUTION VISUALIZER", font=fn_label, fill=accent, anchor="lm")

    label_right = scene.get("viz_label", "")
    if label_right:
        draw.text((x1 - 4, VIZ_TOP + 20), f"[ {label_right} ]", font=fn_label,
                  fill=(100, 115, 150), anchor="rm")

    viz_y0 = VIZ_TOP + 48
    viz_type = scene.get("viz_type", "bars")

    # Render target visualization engine
    if   viz_type == "bars":       _viz_bars(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "grid":       _viz_grid(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "graph":      _viz_graph(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "stack":      _viz_stack(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "tree":       _viz_tree(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "memory":     _viz_memory(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "maze":       _viz_maze(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    else:                          _viz_bars(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)

    # 2. Animated Floating XP / Status Skill Badge (Positioned safely at bottom-right of viz)
    _draw_floating_skill_badge(draw, step_idx, global_frame, accent, x1 - 140, y1 - 24)


def _draw_floating_skill_badge(draw: ImageDraw.Draw, step_idx: int, frame: int,
                                accent: tuple, x: int, y: int):
    """Render animated floating XP particle and skill notification badge."""
    badges = ["⚡ +250 XP", "🔥 CACHE HIT", "💎 O(1) SPEED", "🛡 ACCURACY 99%", "⚔ STRIKE ✓"]
    badge_text = badges[step_idx % len(badges)]
    
    # Float Y-offset animation
    float_y = int(5 * math.sin(frame * 0.12))
    fn_badge = get_font(19, bold=True)
    
    bw = text_w(badge_text, fn_badge) + 16
    draw.rounded_rectangle([x - bw // 2, y + float_y - 12, x + bw // 2, y + float_y + 12],
                            radius=6, fill=lerp_c(accent, (0, 0, 0), 0.8), outline=accent, width=2)
    draw.text((x, y + float_y), badge_text, font=fn_badge, fill=(255, 255, 255), anchor="mm")


# ── BARS — animated array visualizer ─────────────────────────────────────────
def _viz_bars(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    values = scene.get("viz_data", {}).get("values", [64, 34, 25, 12, 22, 11, 90, 53, 43, 78])
    steps_data = scene.get("viz_data", {}).get("steps", [])

    if steps_data and step_idx < len(steps_data):
        current = steps_data[step_idx]
    else:
        sorted_v = sorted(values)
        current  = [sorted_v[i] if i <= step_idx * len(values) // 8 else values[i]
                    for i in range(len(values))]

    n       = len(current)
    max_v   = max(current) if current else 100
    bar_w   = max(18, (x1 - x0 - (n - 1) * 6) // n)
    gap     = 6
    chart_h = y1 - y0 - 48

    hi_indices = scene.get("viz_data", {}).get("highlight", {})
    hi_step    = hi_indices.get(str(step_idx), [])

    font_v = get_font(20, mono=True)
    font_i = get_font(18, mono=True)

    pulse = int(3 * math.sin(frame * 0.2))

    for i, v in enumerate(current):
        bx   = x0 + i * (bar_w + gap)
        bh   = int(chart_h * v / max_v)
        by   = y1 - 36 - bh

        is_hi   = i in hi_step
        is_comp = i in hi_step[1:] if len(hi_step) > 1 else False

        if is_hi and i == hi_step[0]:
            bar_c = (255, 80, 80)   # current element — red
        elif is_comp:
            bar_c = (255, 200, 0)   # comparing — yellow
        else:
            sorted_frac = step_idx / max(8, len(current))
            if i / len(current) < sorted_frac:
                bar_c = (80, 210, 90)
            else:
                bar_c = accent

        draw.rounded_rectangle([bx, by, bx + bar_w, y1 - 36], radius=4, fill=bar_c)

        if is_hi: # Animated Neon Glow Aura
            draw.rounded_rectangle([bx - 2 - pulse, by - 2 - pulse, bx + bar_w + 2 + pulse, y1 - 34],
                                    radius=5, outline=(255, 255, 255), fill=None, width=2)

        if bar_w >= 22:
            draw.text((bx + bar_w // 2, by - 12), str(v), font=font_v, fill=bar_c, anchor="mm")
            draw.text((bx + bar_w // 2, y1 - 20), str(i), font=font_i, fill=(70, 85, 120), anchor="mm")

    ops = scene.get("viz_data", {}).get("operations", [])
    if ops and step_idx < len(ops):
        op_str = ops[step_idx]
        if len(op_str) > 28:
            op_str = op_str[:25] + "..."
        fn_op = get_font(22, bold=True, mono=True)
        draw.text((x0, y0 + 16), op_str, font=fn_op, fill=(255, 200, 60), anchor="lm")



# ── GRID — DP table visualizer ───────────────────────────────────────────────
def _viz_grid(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    rows = scene.get("viz_data", {}).get("rows", 5)
    cols = scene.get("viz_data", {}).get("cols", 7)
    grid_vals = scene.get("viz_data", {}).get("grid", [])

    avail_w = x1 - x0 - 20
    avail_h = y1 - y0 - 20
    cell_w  = min(100, avail_w // cols)
    cell_h  = min(76,  avail_h // rows)
    start_x = x0 + (avail_w - cols * cell_w) // 2 + 10
    start_y = y0 + (avail_h - rows * cell_h) // 2 + 10

    fn_cell  = get_font(24, bold=True, mono=True)
    fn_label = get_font(18, mono=True)

    total_cells = rows * cols
    filled_up   = int(total_cells * (step_idx + 1) / 9)

    for r in range(rows):
        for c in range(cols):
            cell_idx = r * cols + c
            cx = start_x + c * cell_w
            cy = start_y + r * cell_h
            is_filled = cell_idx < filled_up
            is_current = cell_idx == filled_up - 1

            if is_current:
                bg = lerp_c(accent, (0, 0, 0), 0.4)
                bd = (255, 255, 255)
            elif is_filled:
                bg = (20, 38, 28)
                bd = (40, 110, 60)
            else:
                bg = (18, 20, 28)
                bd = (35, 40, 60)

            draw.rectangle([cx + 2, cy + 2, cx + cell_w - 2, cy + cell_h - 2], fill=bg, outline=bd, width=2 if is_current else 1)

            if is_filled and grid_vals:
                flat_idx = cell_idx % len(grid_vals)
                v = str(grid_vals[flat_idx]) if flat_idx < len(grid_vals) else "?"
            elif is_filled:
                v = "✓"
            else:
                v = ""
            if v:
                col = accent if is_current else (90, 210, 90) if is_filled else (60, 70, 100)
                draw.text((cx + cell_w // 2, cy + cell_h // 2), v, font=fn_cell, fill=col, anchor="mm")

    col_headers = scene.get("viz_data", {}).get("col_headers", [])
    row_headers = scene.get("viz_data", {}).get("row_headers", [])
    for ci, lbl in enumerate(col_headers[:cols]):
        draw.text((start_x + ci * cell_w + cell_w // 2, start_y - 16), str(lbl), font=fn_label, fill=(90, 105, 140), anchor="mm")
    for ri, lbl in enumerate(row_headers[:rows]):
        draw.text((start_x - 14, start_y + ri * cell_h + cell_h // 2), str(lbl), font=fn_label, fill=(90, 105, 140), anchor="rm")


# ── GRAPH — node traversal ───────────────────────────────────────────────────
def _viz_graph(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    nodes = scene.get("viz_data", {}).get("nodes", [])
    edges = scene.get("viz_data", {}).get("edges", [])
    visited_by_step = scene.get("viz_data", {}).get("visited", [])

    if not nodes:
        cx_avg, cy_avg = (x0 + x1) // 2, (y0 + y1) // 2
        radius = min((x1 - x0), (y1 - y0)) // 2 - 60
        n = 6
        nodes = [{"id": i, "label": str(i),
                  "x": cx_avg + int(radius * math.cos(math.radians(-90 + i * 360 / n))),
                  "y": cy_avg + int(radius * math.sin(math.radians(-90 + i * 360 / n)))}
                 for i in range(n)]
        edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (4, 5), (2, 5)]

    visited = set()
    if visited_by_step and step_idx < len(visited_by_step):
        visited = set(visited_by_step[:step_idx + 1])

    fn_node = get_font(26, bold=True)

    for (a, b) in edges:
        if a < len(nodes) and b < len(nodes):
            n1, n2 = nodes[a], nodes[b]
            both_visited = a in visited and b in visited
            edge_c = lerp_c(accent, (40, 45, 65), 0.5) if both_visited else (35, 40, 60)
            draw.line([n1["x"], n1["y"], n2["x"], n2["y"]], fill=edge_c, width=3 if both_visited else 2)

    pulse = int(4 * math.sin(frame * 0.25))

    for ni, node in enumerate(nodes):
        nx, ny = node["x"], node["y"]
        is_visited = ni in visited
        is_current = ni == (visited_by_step[step_idx] if visited_by_step and step_idx < len(visited_by_step) else -1)
        r = 34

        if is_current:
            for g in range(4, 0, -1):
                draw.ellipse([nx - r - g * 5 - pulse, ny - r - g * 5 - pulse, nx + r + g * 5 + pulse, ny + r + g * 5 + pulse],
                             fill=lerp_c(accent, (10, 12, 20), 0.75 + g * 0.05))

        bg_c = lerp_c(accent, (20, 25, 40), 0.3) if is_current else (25, 55, 35) if is_visited else (18, 22, 35)
        bd_c = (255, 255, 255) if is_current else (60, 160, 90) if is_visited else (40, 48, 70)

        draw.ellipse([nx - r, ny - r, nx + r, ny + r], fill=bg_c, outline=bd_c, width=3)
        lbl = str(node.get("label", ni))
        draw.text((nx, ny), lbl, font=fn_node, fill=(255, 255, 255) if is_current or is_visited else (80, 95, 130), anchor="mm")


# ── STACK — call stack visualizer ─────────────────────────────────────────────
def _viz_stack(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    frame_states = scene.get("viz_data", {}).get("frame_states", [])
    if frame_states and step_idx < len(frame_states):
        current_frames = frame_states[step_idx]
    else:
        all_frames = ["main()", "solve(n)", "solve(n-1)", "solve(n-2)", "solve(0) → base"]
        depth = min(step_idx + 1, len(all_frames))
        current_frames = all_frames[:depth]

    fn_frame = get_font(24, bold=True, mono=True)
    fn_var   = get_font(20, mono=True)

    frame_h = 62
    frame_w = x1 - x0 - 20
    stack_y  = y1 - 12

    for fi, fr in enumerate(reversed(current_frames)):
        is_top = fi == 0
        fy     = stack_y - (fi + 1) * (frame_h + 4)

        bd_c = accent if is_top else (40, 50, 75)
        draw.rounded_rectangle([x0 + 10, fy, x0 + 10 + frame_w, fy + frame_h],
                                radius=6, fill=(14, 18, 28), outline=bd_c, width=3 if is_top else 1)

        draw.text((x0 + 26, fy + frame_h // 2), str(fr), font=fn_frame,
                  fill=(235, 240, 250) if is_top else (100, 115, 160), anchor="lm")
        if is_top:
            draw.text((x0 + 10 + frame_w - 12, fy + frame_h // 2), "← active", font=fn_var, fill=accent, anchor="rm")


# ── TREE — BST visualizer ────────────────────────────────────────────────────
def _viz_tree(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    tree_vals = scene.get("viz_data", {}).get("tree", [50, 30, 70, 15, 35, 60, 80])
    visited_nodes = scene.get("viz_data", {}).get("visited", [])
    pointer_by_step = scene.get("viz_data", {}).get("pointer", [])

    n      = len(tree_vals)
    levels = int(math.log2(n + 1)) + 1
    level_h = max(76, (y1 - y0 - 20) // max(levels, 1))
    node_r  = 30
    fn_node = get_font(22, bold=True)

    visited  = set(visited_nodes[:step_idx + 1]) if visited_nodes else set()
    pointer  = pointer_by_step[step_idx] if pointer_by_step and step_idx < len(pointer_by_step) else -1

    positions = {}
    def get_pos(idx, depth, left, right):
        if idx >= n:
            return
        cx = (left + right) // 2
        cy = y0 + 30 + depth * level_h
        positions[idx] = (cx, cy)
        get_pos(idx * 2 + 1, depth + 1, left, cx)
        get_pos(idx * 2 + 2, depth + 1, cx, right)

    get_pos(0, 0, x0 + 20, x1 - 20)

    for idx in range(n):
        if idx in positions:
            px, py = positions[idx]
            for child in [idx * 2 + 1, idx * 2 + 2]:
                if child < n and child in positions:
                    cx_pos, cy_pos = positions[child]
                    both = idx in visited and child in visited
                    ec = lerp_c(accent, (40, 48, 70), 0.4) if both else (35, 40, 60)
                    draw.line([px, py + node_r, cx_pos, cy_pos - node_r], fill=ec, width=2)

    for idx, (nx, ny) in positions.items():
        is_pointer = idx == pointer
        is_visited = idx in visited
        if is_pointer:
            for g in range(3, 0, -1):
                draw.ellipse([nx - node_r - g * 5, ny - node_r - g * 5, nx + node_r + g * 5, ny + node_r + g * 5],
                             fill=lerp_c(accent, (10, 12, 20), 0.7 + g * 0.08))
        bg_c = lerp_c(accent, (15, 20, 35), 0.25) if is_pointer else (20, 48, 32) if is_visited else (15, 18, 30)
        bd_c = accent if is_pointer else (50, 140, 70) if is_visited else (38, 45, 70)
        draw.ellipse([nx - node_r, ny - node_r, nx + node_r, ny + node_r], fill=bg_c, outline=bd_c, width=3)
        draw.text((nx, ny), str(tree_vals[idx]), font=fn_node,
                  fill=(240, 245, 255) if is_pointer else (100, 190, 120) if is_visited else (80, 95, 130), anchor="mm")


# ── MEMORY — heap/stack diagram ─────────────────────────────────────────────
def _viz_memory(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    mem_rows = scene.get("viz_data", {}).get("memory", [
        {"addr": "0x00A0", "label": "arr[0]", "value": "42"},
        {"addr": "0x00A8", "label": "arr[1]", "value": "17"},
        {"addr": "0x00B0", "label": "ptr",    "value": "→ 0x00A0"},
        {"addr": "0x00B8", "label": "size",   "value": "2"},
    ])

    row_h  = 54
    col_addr = 150
    col_lbl  = 120
    col_val  = (x1 - x0 - col_addr - col_lbl - 20)
    rx       = x0 + 10

    fn_addr = get_font(20, mono=True)
    fn_lbl  = get_font(20, bold=True, mono=True)
    fn_val  = get_font(22, mono=True)

    draw.text((rx + col_addr // 2, y0 + 14), "ADDRESS", font=fn_addr, fill=(60, 70, 100), anchor="mm")
    draw.text((rx + col_addr + col_lbl // 2, y0 + 14), "NAME", font=fn_addr, fill=(60, 70, 100), anchor="mm")
    draw.text((rx + col_addr + col_lbl + col_val // 2, y0 + 14), "VALUE", font=fn_addr, fill=(60, 70, 100), anchor="mm")
    draw.line([rx, y0 + 26, x1 - 10, y0 + 26], fill=(38, 45, 70), width=1)

    active_rows = min(step_idx + 1, len(mem_rows))
    for ri, row in enumerate(mem_rows[:active_rows]):
        ry = y0 + 32 + ri * row_h
        is_active = ri == active_rows - 1
        bg_c = lerp_c(accent, (12, 14, 22), 0.82) if is_active else (14, 16, 24)
        draw.rectangle([rx, ry, x1 - 10, ry + row_h - 4], fill=bg_c)

        draw.text((rx + col_addr // 2, ry + row_h // 2), str(row.get("addr", "")), font=fn_addr,
                  fill=(140, 150, 210) if is_active else (60, 70, 100), anchor="mm")
        draw.text((rx + col_addr + 10, ry + row_h // 2), str(row.get("label", "")), font=fn_lbl,
                  fill=accent if is_active else (100, 120, 170), anchor="lm")
        draw.text((rx + col_addr + col_lbl + 10, ry + row_h // 2), str(row.get("value", "")), font=fn_val,
                  fill=(90, 230, 110) if is_active else (140, 160, 210), anchor="lm")


# ── MAZE — grid path visualizer ──────────────────────────────────────────────
def _viz_maze(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    grid = scene.get("viz_data", {}).get("maze", [
        [0,0,1,0,0,0,0], [0,1,1,0,1,0,1], [0,0,0,0,1,0,0],
        [1,1,0,1,0,0,1], [0,0,0,0,0,1,0], [0,1,1,1,0,1,0], [0,0,0,0,0,0,0],
    ])
    path_by_step = scene.get("viz_data", {}).get("path", [])

    rows = len(grid)
    cols = max(len(r) for r in grid)
    cell_size = min((x1 - x0 - 20) // cols, (y1 - y0 - 20) // rows, 76)
    ox = x0 + 10 + (x1 - x0 - 20 - cols * cell_size) // 2
    oy = y0 + 10 + (y1 - y0 - 20 - rows * cell_size) // 2

    visited_cells = set()
    if path_by_step and step_idx < len(path_by_step):
        for p in path_by_step[:step_idx + 1]:
            visited_cells.add(tuple(p))

    fn_cell = get_font(max(18, cell_size // 3), bold=True)

    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            cx = ox + c * cell_size
            cy = oy + r * cell_size
            is_visited = (r, c) in visited_cells
            is_current = path_by_step and step_idx < len(path_by_step) and list(path_by_step[step_idx]) == [r, c]

            if cell == 1:
                draw.rectangle([cx + 1, cy + 1, cx + cell_size - 1, cy + cell_size - 1], fill=(30, 35, 52))
            else:
                bg_c = lerp_c(accent, (10, 12, 20), 0.5) if is_current else (15, 42, 28) if is_visited else (14, 16, 24)
                draw.rectangle([cx + 1, cy + 1, cx + cell_size - 1, cy + cell_size - 1], fill=bg_c, outline=(30, 36, 55))
                if is_current:
                    pc, pr = cx + cell_size // 2, cy + cell_size // 2
                    draw.ellipse([pc - 11, pr - 11, pc + 11, pr + 11], fill=accent)
                    draw.text((pc, pr), "●", font=fn_cell, fill=(255, 255, 255), anchor="mm")
                elif is_visited:
                    draw.text((cx + cell_size // 2, cy + cell_size // 2), "·", font=fn_cell, fill=(50, 130, 75), anchor="mm")


def _wrap(text, font, max_w):
    words = text.split()
    lines, cur = [], []
    for w in words:
        trial = " ".join(cur + [w])
        if text_w(trial, font) <= max_w or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENGINE CLASS
# ─────────────────────────────────────────────────────────────────────────────

class PuzzleEngine:
    def __init__(self, series: str = "Algorithms"):
        self.series = series

    def _get_accent(self, scene: dict) -> tuple:
        pnum = scene.get("puzzle_num", 1)
        return DYNAMIC_PALETTES[(pnum - 1) % len(DYNAMIC_PALETTES)]

    def render_frame(self, scene: dict, step_idx: int, step_progress: float,
                     global_frame: int, total_steps: int) -> Image.Image:
        img  = Image.new("RGB", (WIDTH, HEIGHT), color=(10, 12, 20))
        draw = ImageDraw.Draw(img)
        accent = self._get_accent(scene)

        draw_game_header(draw, scene, accent, step_idx, total_steps)

        code_lines   = scene.get("code", ["# code loading..."])
        active_lines = scene.get("active_lines", list(range(len(code_lines))))
        active_line  = active_lines[step_idx] if step_idx < len(active_lines) else 0
        draw_code_editor(draw, code_lines, active_line, accent, step_progress)

        draw_visualization(draw, scene, step_idx, step_progress, global_frame, accent)

        draw_test_panel(draw, scene, step_idx, total_steps, accent)

        draw_footer(draw, step_idx, total_steps, scene, accent, global_frame)

        return img

    def render_thumbnail(self, scene: dict) -> Image.Image:
        img  = Image.new("RGB", (WIDTH, HEIGHT), color=(10, 12, 20))
        draw = ImageDraw.Draw(img)
        accent = self._get_accent(scene)
        draw_game_header(draw, scene, accent, 3, 9)
        code_lines = scene.get("code", ["# code loading..."])
        draw_code_editor(draw, code_lines, 0, accent, 0.0)
        return img

