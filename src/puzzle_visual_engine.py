"""
Puzzle Visual Engine — Coding Game Style Renderer
Looks like a real coding puzzle game (Human Resource Machine / Zachtronics / CodeCombat).
Layout:
  [0   – 220]  Game header: puzzle# + stars + topic title
  [220 – 960]  Python code editor panel (syntax highlighted, line cursor)
  [960 – 1550] Execution visualization (bars, graph, grid, stack, tree)
  [1550– 1760] Test cases panel
  [1760– 1920] Step dots + score footer
"""

import math, random, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH  = 1080
HEIGHT = 1920
FPS    = 30

# ── Zone constants ────────────────────────────────────────────────────────────
HEADER_TOP   = 0
HEADER_BOT   = 220
CODE_TOP     = 220
CODE_BOT     = 960
VIZ_TOP      = 960
VIZ_BOT      = 1555
TESTS_TOP    = 1555
TESTS_BOT    = 1765
FOOTER_TOP   = 1765
FOOTER_BOT   = 1920

CODE_PAD_L   = 28
CODE_PAD_R   = 28
LINE_H       = 46          # pixels per code line
MAX_VISIBLE  = 16          # max code lines visible at once

# ── Color palette (VS Code Dark+ inspired) ───────────────────────────────────
EDITOR_BG     = (18,  20,  28)
EDITOR_BORDER = (50,  55,  75)
GUTTER_BG     = (22,  24,  32)
GUTTER_FG     = (70,  80, 110)
LINE_HL       = (40,  48,  72)   # active line highlight
CURSOR_COL    = (220, 220, 80)   # cursor color

# Syntax colors
SYN = {
    "keyword":   (197, 120, 221),  # purple  – def, for, if, return, class
    "builtin":   ( 86, 182, 194),  # cyan    – range, len, print, enumerate
    "string":    (152, 195, 121),  # green   – "text", 'text'
    "number":    (209, 154,  98),  # orange  – 42, 3.14
    "comment":   ( 92, 100, 125),  # dim     – # comment
    "decorator": (224, 108,  78),  # red-ish – @property
    "operator":  ( 86, 182, 194),  # cyan    – == != <= >=
    "class_name":(229, 192, 123),  # yellow  – ClassName
    "func_name": ( 97, 175, 239),  # blue    – function name after def
    "default":   (171, 178, 191),  # light   – everything else
    "self_kw":   (224, 108,  78),  # reddish – self
    "bracket":   (229, 192, 123),  # yellow  – ( ) [ ] { }
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
    # Monospace candidates for code editor
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
# PYTHON SYNTAX TOKENIZER
# ─────────────────────────────────────────────────────────────────────────────

def tokenize_python_line(line: str) -> list[tuple[str, tuple]]:
    """
    Returns list of (text_fragment, color_rgb) for one code line.
    Simple but effective — covers the most visible cases.
    """
    if not line.strip():
        return [(" ", SYN["default"])]

    tokens = []

    # Full-line comment
    stripped = line.lstrip()
    if stripped.startswith("#"):
        tokens.append((line, SYN["comment"]))
        return tokens

    # Inline comment split
    comment = ""
    code_part = line
    # Find # not inside a string
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

    # Process code part token by token
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
    """
    Render VS Code-style Python code editor in CODE_TOP → CODE_BOT zone.
    active_line: 0-indexed line that is highlighted (currently executing).
    """
    GUTTER_W    = 52          # line number gutter width
    CODE_LEFT   = CODE_PAD_L + GUTTER_W
    AVAIL_W     = WIDTH - CODE_LEFT - CODE_PAD_R
    font        = get_font(26, mono=True)
    font_lnum   = get_font(20, mono=True)

    # ── Editor background ──
    draw.rectangle([0, CODE_TOP, WIDTH, CODE_BOT], fill=EDITOR_BG)
    # Top border line
    draw.line([0, CODE_TOP, WIDTH, CODE_TOP], fill=accent, width=3)
    # Bottom border
    draw.line([0, CODE_BOT, WIDTH, CODE_BOT], fill=EDITOR_BORDER, width=2)
    # Gutter
    draw.rectangle([0, CODE_TOP, CODE_PAD_L + GUTTER_W, CODE_BOT], fill=GUTTER_BG)
    draw.line([CODE_PAD_L + GUTTER_W, CODE_TOP, CODE_PAD_L + GUTTER_W, CODE_BOT],
              fill=EDITOR_BORDER, width=1)

    # ── File tab ──
    tab_text = "  puzzle.py  "
    tab_font = get_font(22, bold=True)
    tab_w    = text_w(tab_text, tab_font) + 4
    draw.rectangle([0, CODE_TOP, tab_w, CODE_TOP + 36], fill=accent)
    draw.text((tab_w // 2, CODE_TOP + 18), tab_text, font=tab_font, fill=(0, 0, 0), anchor="mm")

    # ── Scroll so active line stays in view ──
    scroll_start = max(0, active_line - MAX_VISIBLE // 2)
    visible_lines = code_lines[scroll_start: scroll_start + MAX_VISIBLE]

    for i, line in enumerate(visible_lines):
        abs_line = scroll_start + i
        y_top    = CODE_TOP + 44 + i * LINE_H

        # Active line background
        is_active = (abs_line == active_line)
        if is_active:
            draw.rectangle([0, y_top, WIDTH, y_top + LINE_H], fill=LINE_HL)
            # Accent left border
            draw.rectangle([0, y_top, 4, y_top + LINE_H], fill=accent)

        # Line number
        lnum_str = str(abs_line + 1)
        lnum_x   = CODE_PAD_L + GUTTER_W - 8
        lnum_col = accent if is_active else GUTTER_FG
        draw.text((lnum_x, y_top + LINE_H // 2), lnum_str,
                  font=font_lnum, fill=lnum_col, anchor="rm")

        # Syntax-highlighted code
        tokens = tokenize_python_line(line)
        x = CODE_LEFT + 8
        for token_text, color in tokens:
            if x > WIDTH - CODE_PAD_R:
                break
            draw.text((x, y_top + LINE_H // 2 - 1), token_text,
                      font=font, fill=color, anchor="lm")
            x += text_w(token_text, font)

        # Blinking cursor on active line
        if is_active:
            cursor_blink = step_progress % 0.5 < 0.25 or step_progress > 0.8
            if cursor_blink:
                cursor_x = x + 2
                cursor_x = max(CODE_LEFT + 10, min(cursor_x, WIDTH - CODE_PAD_R - 6))
                draw.rectangle([cursor_x, y_top + 8, cursor_x + 3, y_top + LINE_H - 8],
                               fill=CURSOR_COL)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: GAME HEADER
# ─────────────────────────────────────────────────────────────────────────────

def draw_game_header(draw: ImageDraw.Draw, scene: dict, accent: tuple,
                     step_idx: int, total_steps: int):
    """Render puzzle game header: puzzle#, stars, title, series badge."""
    puzzle_num = scene.get("puzzle_num", 1)
    title      = scene.get("title", "Algorithm")
    subtitle   = scene.get("subtitle", "")
    series     = scene.get("series", "Algorithms")
    chapter    = scene.get("chapter", "")
    stars      = scene.get("puzzle_stars", 3)
    diff       = scene.get("difficulty", "HARD")
    game_tag   = scene.get("game_tag", "⚔ BOSS FIGHT")

    # ── Background ──
    draw.rectangle([0, HEADER_TOP, WIDTH, HEADER_BOT], fill=(12, 14, 22))
    draw.line([0, HEADER_BOT, WIDTH, HEADER_BOT], fill=EDITOR_BORDER, width=2)

    # ── Top row: puzzle number + difficulty badge + stars ──
    fn_badge = get_font(24, bold=True)
    fn_star  = get_font(30, bold=True)

    # Puzzle number (left)
    pnum_text = f"PUZZLE #{puzzle_num:03d}"
    draw.text((36, 36), pnum_text, font=get_font(26, bold=True),
              fill=accent, anchor="lm")

    # Difficulty badge (center)
    diff_colors = {"EASY": (80, 200, 80), "MEDIUM": (255, 180, 0),
                   "HARD": (255, 80, 80), "EXTREME": (200, 0, 255)}
    diff_c = diff_colors.get(diff, (255, 80, 80))
    diff_text = f" {diff} "
    dw = text_w(diff_text, fn_badge) + 16
    draw.rounded_rectangle([WIDTH // 2 - dw // 2, 16, WIDTH // 2 + dw // 2, 58],
                            radius=8, fill=lerp_c(diff_c, (0, 0, 0), 0.7), outline=diff_c, width=2)
    draw.text((WIDTH // 2, 37), diff_text, font=fn_badge, fill=diff_c, anchor="mm")

    # Stars (right) — filled based on step progress
    filled_stars = min(3, 1 + step_idx // max(total_steps // 3, 1))
    star_x = WIDTH - 36
    for si in range(3, 0, -1):
        s_text = "★" if si <= filled_stars else "☆"
        s_col  = (255, 210, 0) if si <= filled_stars else (60, 65, 90)
        draw.text((star_x, 37), s_text, font=fn_star, fill=s_col, anchor="rm")
        star_x -= 38

    # ── Game tag pill ──
    fn_tag = get_font(22, bold=True)
    tag_text = f" {game_tag} "
    tw = text_w(tag_text, fn_tag) + 12
    draw.rounded_rectangle([36, 68, 36 + tw, 106], radius=8,
                            fill=lerp_c(accent, (0, 0, 0), 0.8), outline=accent, width=1)
    draw.text((36 + tw // 2, 87), tag_text, font=fn_tag, fill=accent, anchor="mm")

    # ── Series badge (right side) ──
    badge_text = f"{series} › {chapter}" if chapter else series
    fn_series  = get_font(20, bold=False)
    sw = text_w(badge_text, fn_series)
    draw.text((WIDTH - 36, 87), badge_text, font=fn_series,
              fill=(100, 110, 150), anchor="rm")

    # ── Title ──
    fn_title = get_font(44, bold=True)
    fn_sub   = get_font(26, bold=False)
    title_lines = _wrap(title, fn_title, WIDTH - 72)[:2]
    title_y = 118
    for ln in title_lines:
        draw.text((WIDTH // 2, title_y), ln, font=fn_title,
                  fill=(230, 235, 245), anchor="mm")
        title_y += 50

    if subtitle:
        draw.text((WIDTH // 2, title_y + 2), subtitle, font=fn_sub,
                  fill=(100, 110, 150), anchor="mm")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: TEST CASES PANEL
# ─────────────────────────────────────────────────────────────────────────────

def draw_test_panel(draw: ImageDraw.Draw, scene: dict, step_idx: int,
                    total_steps: int, accent: tuple):
    """Render test cases panel: inputs → expected → actual → ✓/✗."""
    tests = scene.get("test_cases", [])
    if not tests:
        return

    draw.rectangle([0, TESTS_TOP, WIDTH, TESTS_BOT], fill=(14, 16, 24))
    draw.line([0, TESTS_TOP, WIDTH, TESTS_TOP], fill=EDITOR_BORDER, width=2)

    fn_head = get_font(22, bold=True)
    fn_test = get_font(22, mono=True)
    fn_icon = get_font(26, bold=True)

    draw.text((36, TESTS_TOP + 24), "TEST CASES", font=fn_head, fill=accent, anchor="lm")

    # Progress bar
    pass_ratio = (step_idx + 1) / max(total_steps, 1)
    n_pass     = int(len(tests) * pass_ratio)
    draw.text((WIDTH - 36, TESTS_TOP + 24),
              f"{n_pass}/{len(tests)} passing", font=fn_head,
              fill=(80, 200, 80) if n_pass == len(tests) else (200, 200, 80),
              anchor="rm")

    col_w = (WIDTH - 72) // min(len(tests), 4)
    for ti, test in enumerate(tests[:4]):
        passing = ti < n_pass
        tx      = 36 + ti * col_w
        ty      = TESTS_TOP + 52

        box_c   = (20, 40, 20) if passing else (30, 20, 20)
        brd_c   = (60, 180, 60) if passing else (80, 50, 50)
        icon    = "✓" if passing else "○"
        icon_c  = (80, 220, 80) if passing else (80, 80, 80)

        draw.rounded_rectangle([tx, ty, tx + col_w - 8, ty + (TESTS_BOT - TESTS_TOP - 62)],
                                radius=8, fill=box_c, outline=brd_c, width=2)

        draw.text((tx + col_w // 2, ty + 20), icon, font=fn_icon, fill=icon_c, anchor="mm")

        in_text  = f"in: {str(test.get('input', '?'))[:14]}"
        exp_text = f"→ {str(test.get('expected', '?'))[:14]}"
        draw.text((tx + 10, ty + 50), in_text,  font=fn_test, fill=(150, 160, 190))
        draw.text((tx + 10, ty + 80), exp_text, font=fn_test,
                  fill=(80, 200, 80) if passing else (150, 160, 190))

        label = test.get("label", f"test_{ti+1}")
        draw.text((tx + col_w // 2, ty + 118), label, font=get_font(18),
                  fill=(80, 90, 120), anchor="mm")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: STEP / SCORE FOOTER
# ─────────────────────────────────────────────────────────────────────────────

def draw_footer(draw: ImageDraw.Draw, step_idx: int, total_steps: int,
                scene: dict, accent: tuple, global_frame: int):
    """Step dots + complexity badge + frame counter."""
    draw.rectangle([0, FOOTER_TOP, WIDTH, FOOTER_BOT], fill=(10, 12, 20))
    draw.line([0, FOOTER_TOP, WIDTH, FOOTER_TOP], fill=EDITOR_BORDER, width=1)

    # Step dots
    dot_r, gap = 9, 26
    dots_cx    = WIDTH // 2
    total_w    = total_steps * gap
    start_x    = dots_cx - total_w // 2 + dot_r
    dot_y      = FOOTER_TOP + 40
    for i in range(total_steps):
        cx = start_x + i * gap
        if i < step_idx:
            draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r], fill=accent)
        elif i == step_idx:
            draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r],
                         fill=(255, 255, 255), outline=accent, width=2)
        else:
            draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r],
                         fill=(30, 35, 50), outline=(50, 55, 80), width=2)

    # Complexity badge (left)
    time_c = scene.get("time_complexity", "O(?)")
    space_c = scene.get("space_complexity", "O(?)")
    fn_cmplx = get_font(22, bold=True, mono=True)
    draw.text((36, FOOTER_TOP + 40), f"⏱ {time_c}", font=fn_cmplx, fill=(80, 180, 255), anchor="lm")
    draw.text((36, FOOTER_TOP + 76), f"💾 {space_c}", font=fn_cmplx, fill=(180, 130, 255), anchor="lm")

    # Frame counter / timer (right) — like a speedrun timer
    elapsed   = global_frame / FPS
    m, s = int(elapsed // 60), int(elapsed % 60)
    fn_timer  = get_font(28, bold=True, mono=True)
    draw.text((WIDTH - 36, FOOTER_TOP + 58), f"{m:02d}:{s:02d}",
              font=fn_timer, fill=(80, 90, 120), anchor="rm")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: EXECUTION VISUALIZATIONS
# ─────────────────────────────────────────────────────────────────────────────

def _viz_bounds():
    """Return (x0, y0, x1, y1) for the visualization zone with padding."""
    return 28, VIZ_TOP + 16, WIDTH - 28, VIZ_BOT - 16

def draw_visualization(draw: ImageDraw.Draw, scene: dict, step_idx: int,
                       step_progress: float, global_frame: int, accent: tuple):
    """Dispatch to the correct visualization renderer."""
    x0, y0, x1, y1 = _viz_bounds()
    draw.rectangle([0, VIZ_TOP, WIDTH, VIZ_BOT], fill=(10, 12, 20))
    draw.line([0, VIZ_TOP, WIDTH, VIZ_TOP], fill=EDITOR_BORDER, width=2)

    viz_type = scene.get("viz_type", "bars")
    fn_label = get_font(22, bold=True)
    draw.text((x0 + 4, VIZ_TOP + 20), "▶ EXECUTION", font=fn_label, fill=accent, anchor="lm")

    label_right = scene.get("viz_label", "")
    if label_right:
        draw.text((x1, VIZ_TOP + 20), label_right, font=fn_label,
                  fill=(80, 90, 120), anchor="rm")

    viz_y0 = VIZ_TOP + 48

    if   viz_type == "bars":       _viz_bars(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "grid":       _viz_grid(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "graph":      _viz_graph(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "stack":      _viz_stack(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "tree":       _viz_tree(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "memory":     _viz_memory(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "maze":       _viz_maze(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    else:                          _viz_bars(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)


# ── BARS — sorting algorithm visualization ────────────────────────────────────
def _viz_bars(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    values = scene.get("viz_data", {}).get("values", [64, 34, 25, 12, 22, 11, 90, 53, 43, 78])
    steps_data = scene.get("viz_data", {}).get("steps", [])

    # Get current array state based on step
    if steps_data and step_idx < len(steps_data):
        current = steps_data[step_idx]
    else:
        # Default: show values progressively sorted
        sorted_v = sorted(values)
        current  = [sorted_v[i] if i <= step_idx * len(values) // 8 else values[i]
                    for i in range(len(values))]

    n       = len(current)
    max_v   = max(current) if current else 100
    bar_w   = max(18, (x1 - x0 - (n - 1) * 6) // n)
    gap     = 6
    chart_h = y1 - y0 - 48

    # Highlight indices
    hi_indices = scene.get("viz_data", {}).get("highlight", {})
    hi_step    = hi_indices.get(str(step_idx), [])

    font_v = get_font(20, mono=True)
    font_i = get_font(18, mono=True)

    for i, v in enumerate(current):
        bx   = x0 + i * (bar_w + gap)
        bh   = int(chart_h * v / max_v)
        by   = y1 - 36 - bh

        is_hi  = i in hi_step
        is_comp = i in hi_step[1:] if len(hi_step) > 1 else False

        if is_hi and i == hi_step[0]:
            bar_c = (255, 80, 80)   # current element — red
        elif is_comp:
            bar_c = (255, 200, 0)   # comparing — yellow
        else:
            # Gradient: green for sorted portion, blue for unsorted
            sorted_frac = step_idx / max(8, len(current))
            if i / len(current) < sorted_frac:
                bar_c = (80, 200, 80)
            else:
                bar_c = accent

        # Bar
        draw.rounded_rectangle([bx, by, bx + bar_w, y1 - 36],
                                radius=4, fill=bar_c)
        # Glow on highlighted
        if is_hi:
            draw.rounded_rectangle([bx - 2, by - 2, bx + bar_w + 2, y1 - 34],
                                    radius=5, outline=lerp_c(bar_c, (255, 255, 255), 0.5), fill=None)

        # Value label on top
        if bar_w >= 22:
            draw.text((bx + bar_w // 2, by - 12), str(v), font=font_v,
                      fill=bar_c, anchor="mm")
        # Index label at bottom
        if bar_w >= 22:
            draw.text((bx + bar_w // 2, y1 - 20), str(i), font=font_i,
                      fill=(60, 70, 100), anchor="mm")

    # Operation label
    ops = scene.get("viz_data", {}).get("operations", [])
    if ops and step_idx < len(ops):
        fn_op = get_font(26, bold=True, mono=True)
        draw.text((x0, y0 + 18), ops[step_idx], font=fn_op, fill=(255, 200, 60), anchor="lm")


# ── GRID — DP table / matrix visualization ────────────────────────────────────
def _viz_grid(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    rows = scene.get("viz_data", {}).get("rows", 5)
    cols = scene.get("viz_data", {}).get("cols", 7)
    grid_vals = scene.get("viz_data", {}).get("grid", [])
    cell_labels = scene.get("viz_data", {}).get("labels", {})

    avail_w = x1 - x0 - 20
    avail_h = y1 - y0 - 20
    cell_w  = min(100, avail_w // cols)
    cell_h  = min(80,  avail_h // rows)
    start_x = x0 + (avail_w - cols * cell_w) // 2 + 10
    start_y = y0 + (avail_h - rows * cell_h) // 2 + 10

    fn_cell  = get_font(24, bold=True, mono=True)
    fn_label = get_font(18, mono=True)

    # Cells filled up to current step
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
                bd = accent
            elif is_filled:
                bg = (20, 35, 28)
                bd = (40, 100, 60)
            else:
                bg = (18, 20, 28)
                bd = (35, 40, 60)

            draw.rectangle([cx + 2, cy + 2, cx + cell_w - 2, cy + cell_h - 2], fill=bg, outline=bd)

            if is_filled and grid_vals:
                flat_idx = cell_idx % len(grid_vals)
                v = str(grid_vals[flat_idx]) if flat_idx < len(grid_vals) else "?"
            elif is_filled:
                v = "✓"
            else:
                v = ""
            if v:
                col = accent if is_current else (80, 180, 80) if is_filled else (60, 70, 100)
                draw.text((cx + cell_w // 2, cy + cell_h // 2), v, font=fn_cell,
                          fill=col, anchor="mm")

    # Row/col header labels
    col_headers = scene.get("viz_data", {}).get("col_headers", [])
    row_headers = scene.get("viz_data", {}).get("row_headers", [])
    for ci, lbl in enumerate(col_headers[:cols]):
        draw.text((start_x + ci * cell_w + cell_w // 2, start_y - 18),
                  str(lbl), font=fn_label, fill=(80, 90, 120), anchor="mm")
    for ri, lbl in enumerate(row_headers[:rows]):
        draw.text((start_x - 14, start_y + ri * cell_h + cell_h // 2),
                  str(lbl), font=fn_label, fill=(80, 90, 120), anchor="rm")


# ── GRAPH — node + edge traversal ─────────────────────────────────────────────
def _viz_graph(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    nodes = scene.get("viz_data", {}).get("nodes", [])
    edges = scene.get("viz_data", {}).get("edges", [])
    visited_by_step = scene.get("viz_data", {}).get("visited", [])

    if not nodes:
        # Generate a default graph layout
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

    # Draw edges
    for (a, b) in edges:
        if a < len(nodes) and b < len(nodes):
            n1, n2 = nodes[a], nodes[b]
            both_visited = a in visited and b in visited
            edge_c = lerp_c(accent, (40, 45, 65), 0.5) if both_visited else (35, 40, 60)
            draw.line([n1["x"], n1["y"], n2["x"], n2["y"]], fill=edge_c, width=3 if both_visited else 2)
            # Arrow head
            if both_visited:
                dx = n2["x"] - n1["x"]
                dy = n2["y"] - n1["y"]
                d  = max(1, int(math.sqrt(dx * dx + dy * dy)))
                mx = n1["x"] + dx * 2 // 3
                my = n1["y"] + dy * 2 // 3
                pdx, pdy = -dy / d * 10, dx / d * 10
                draw.polygon([(mx + dx // d * 14, my + dy // d * 14),
                               (mx + int(pdx), my + int(pdy)),
                               (mx - int(pdx), my - int(pdy))], fill=edge_c)

    # Draw nodes
    for ni, node in enumerate(nodes):
        nx, ny = node["x"], node["y"]
        is_visited = ni in visited
        is_current = ni == (visited_by_step[step_idx] if visited_by_step and step_idx < len(visited_by_step) else -1)
        r = 36

        if is_current:
            # Glow ring
            for g in range(4, 0, -1):
                draw.ellipse([nx - r - g * 5, ny - r - g * 5, nx + r + g * 5, ny + r + g * 5],
                             fill=lerp_c(accent, (10, 12, 20), 0.75 + g * 0.05))

        bg_c = lerp_c(accent, (20, 25, 40), 0.3) if is_current else \
               (25, 50, 35) if is_visited else (18, 22, 35)
        bd_c = accent if is_current else (50, 150, 80) if is_visited else (40, 48, 70)

        draw.ellipse([nx - r, ny - r, nx + r, ny + r], fill=bg_c, outline=bd_c, width=3)
        lbl = str(node.get("label", ni))
        draw.text((nx, ny), lbl, font=fn_node,
                  fill=(255, 255, 255) if is_current or is_visited else (80, 90, 120),
                  anchor="mm")

    # Queue/stack display
    queue = scene.get("viz_data", {}).get("queue_by_step", [])
    if queue and step_idx < len(queue):
        fn_q = get_font(22, mono=True)
        q_str = "queue: " + str(queue[step_idx])
        draw.text((x0 + 8, y1 - 16), q_str, font=fn_q, fill=(130, 150, 200), anchor="lm")


# ── STACK — recursion / call stack ───────────────────────────────────────────
def _viz_stack(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    frames_data = scene.get("viz_data", {}).get("frames", [])
    frame_states = scene.get("viz_data", {}).get("frame_states", [])

    # Current frames visible
    if frame_states and step_idx < len(frame_states):
        current_frames = frame_states[step_idx]
    else:
        # Build progressive stack
        all_frames = ["main()", "solve(n)", "solve(n-1)", "solve(n-2)", "solve(0) → base"]
        depth = min(step_idx + 1, len(all_frames))
        current_frames = all_frames[:depth]

    fn_frame = get_font(26, bold=True, mono=True)
    fn_var   = get_font(22, mono=True)

    frame_h = 68
    frame_w = x1 - x0 - 20
    stack_y  = y1 - 12  # grow upward

    for fi, fr in enumerate(reversed(current_frames)):
        is_top = fi == 0
        fy     = stack_y - (fi + 1) * (frame_h + 4)

        depth_ratio = fi / max(len(current_frames), 1)
        bg_c = lerp_c(accent, (14, 18, 28), 0.7 - depth_ratio * 0.2)
        bd_c = accent if is_top else lerp_c(accent, (40, 50, 80), depth_ratio * 0.6)

        draw.rounded_rectangle([x0 + 10, fy, x0 + 10 + frame_w, fy + frame_h],
                                radius=6, fill=(14, 18, 28), outline=bd_c, width=3 if is_top else 1)

        # Frame label
        draw.text((x0 + 26, fy + frame_h // 2), str(fr), font=fn_frame,
                  fill=(230, 235, 245) if is_top else (100, 115, 160), anchor="lm")

        # Return address arrow (right side)
        if is_top:
            draw.text((x0 + 10 + frame_w - 12, fy + frame_h // 2), "← active",
                      font=fn_var, fill=accent, anchor="rm")
        elif fi == len(current_frames) - 1:
            draw.text((x0 + 10 + frame_w - 12, fy + frame_h // 2), "← bottom",
                      font=fn_var, fill=(60, 70, 100), anchor="rm")

    # Stack pointer label
    fn_sp = get_font(22, bold=True)
    draw.text((x0 + 10 + frame_w // 2, y0 + 12),
              f"Call Stack  (depth: {len(current_frames)})", font=fn_sp,
              fill=(80, 90, 120), anchor="mm")


# ── TREE — binary tree / BST traversal ───────────────────────────────────────
def _viz_tree(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    tree_vals = scene.get("viz_data", {}).get("tree", [])
    visited_nodes = scene.get("viz_data", {}).get("visited", [])
    pointer_by_step = scene.get("viz_data", {}).get("pointer", [])

    if not tree_vals:
        tree_vals = [50, 30, 70, 15, 35, 60, 80]

    n      = len(tree_vals)
    levels = int(math.log2(n + 1)) + 1
    cx_c   = (x0 + x1) // 2
    level_h = max(80, (y1 - y0 - 20) // max(levels, 1))
    node_r  = 32
    fn_node = get_font(24, bold=True)

    visited  = set(visited_nodes[:step_idx + 1]) if visited_nodes else set()
    pointer  = pointer_by_step[step_idx] if pointer_by_step and step_idx < len(pointer_by_step) else -1

    # Compute positions
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

    # Draw edges
    for idx in range(n):
        if idx in positions:
            px, py = positions[idx]
            for child in [idx * 2 + 1, idx * 2 + 2]:
                if child < n and child in positions:
                    cx_pos, cy_pos = positions[child]
                    both = idx in visited and child in visited
                    ec = lerp_c(accent, (40, 48, 70), 0.4) if both else (35, 40, 60)
                    draw.line([px, py + node_r, cx_pos, cy_pos - node_r], fill=ec, width=2)

    # Draw nodes
    for idx, (nx, ny) in positions.items():
        is_pointer = idx == pointer
        is_visited = idx in visited
        if is_pointer:
            for g in range(3, 0, -1):
                draw.ellipse([nx - node_r - g * 6, ny - node_r - g * 6,
                               nx + node_r + g * 6, ny + node_r + g * 6],
                             fill=lerp_c(accent, (10, 12, 20), 0.7 + g * 0.08))
        bg_c = lerp_c(accent, (15, 20, 35), 0.25) if is_pointer else \
               (20, 45, 30) if is_visited else (15, 18, 30)
        bd_c = accent if is_pointer else (50, 140, 70) if is_visited else (38, 45, 70)
        draw.ellipse([nx - node_r, ny - node_r, nx + node_r, ny + node_r],
                     fill=bg_c, outline=bd_c, width=3)
        draw.text((nx, ny), str(tree_vals[idx]), font=fn_node,
                  fill=(240, 245, 255) if is_pointer else (100, 180, 120) if is_visited else (80, 90, 120),
                  anchor="mm")


# ── MEMORY — pointer/heap/stack memory diagram ───────────────────────────────
def _viz_memory(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    mem_rows = scene.get("viz_data", {}).get("memory", [])
    if not mem_rows:
        mem_rows = [
            {"addr": "0x00A0", "label": "arr[0]", "value": "42"},
            {"addr": "0x00A8", "label": "arr[1]", "value": "17"},
            {"addr": "0x00B0", "label": "ptr",    "value": "→ 0x00A0"},
            {"addr": "0x00B8", "label": "size",   "value": "2"},
        ]

    row_h  = 58
    col_addr = 160
    col_lbl  = 120
    col_val  = (x1 - x0 - col_addr - col_lbl - 20)
    rx       = x0 + 10

    fn_addr = get_font(22, mono=True)
    fn_lbl  = get_font(22, bold=True, mono=True)
    fn_val  = get_font(24, mono=True)

    # Header
    draw.text((rx + col_addr // 2, y0 + 16), "ADDRESS", font=fn_addr, fill=(60, 70, 100), anchor="mm")
    draw.text((rx + col_addr + col_lbl // 2, y0 + 16), "NAME", font=fn_addr, fill=(60, 70, 100), anchor="mm")
    draw.text((rx + col_addr + col_lbl + col_val // 2, y0 + 16), "VALUE", font=fn_addr, fill=(60, 70, 100), anchor="mm")
    draw.line([rx, y0 + 30, x1 - 10, y0 + 30], fill=(38, 45, 70), width=1)

    active_rows = min(step_idx + 1, len(mem_rows))
    for ri, row in enumerate(mem_rows[:active_rows]):
        ry = y0 + 36 + ri * row_h
        is_active = ri == active_rows - 1
        bg_c = lerp_c(accent, (12, 14, 22), 0.82) if is_active else (14, 16, 24)
        draw.rectangle([rx, ry, x1 - 10, ry + row_h - 4], fill=bg_c)
        draw.line([rx, ry + row_h - 4, x1 - 10, ry + row_h - 4], fill=(28, 32, 50), width=1)

        draw.text((rx + col_addr // 2, ry + row_h // 2),
                  str(row.get("addr", "")), font=fn_addr,
                  fill=(130, 140, 200) if is_active else (60, 70, 100), anchor="mm")
        draw.text((rx + col_addr + 10, ry + row_h // 2),
                  str(row.get("label", "")), font=fn_lbl,
                  fill=accent if is_active else (100, 120, 170), anchor="lm")
        draw.text((rx + col_addr + col_lbl + 10, ry + row_h // 2),
                  str(row.get("value", "")), font=fn_val,
                  fill=(80, 220, 100) if is_active else (140, 160, 210), anchor="lm")


# ── MAZE — character moving through grid ─────────────────────────────────────
def _viz_maze(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    grid = scene.get("viz_data", {}).get("maze", [])
    path_by_step = scene.get("viz_data", {}).get("path", [])

    if not grid:
        # Default: 7×7 maze with walls
        grid = [
            [0,0,1,0,0,0,0],
            [0,1,1,0,1,0,1],
            [0,0,0,0,1,0,0],
            [1,1,0,1,0,0,1],
            [0,0,0,0,0,1,0],
            [0,1,1,1,0,1,0],
            [0,0,0,0,0,0,0],
        ]

    rows = len(grid)
    cols = max(len(r) for r in grid)
    cell_size = min((x1 - x0 - 20) // cols, (y1 - y0 - 20) // rows, 80)
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
            is_current = path_by_step and step_idx < len(path_by_step) and \
                         list(path_by_step[step_idx]) == [r, c]

            if cell == 1:  # wall
                draw.rectangle([cx + 1, cy + 1, cx + cell_size - 1, cy + cell_size - 1],
                               fill=(30, 35, 50))
                # Brick pattern
                draw.rectangle([cx + 2, cy + 2, cx + cell_size - 2, cy + cell_size - 2],
                               fill=(35, 40, 55))
            else:
                bg_c = lerp_c(accent, (10, 12, 20), 0.5) if is_current else \
                       (15, 40, 25) if is_visited else (14, 16, 24)
                draw.rectangle([cx + 1, cy + 1, cx + cell_size - 1, cy + cell_size - 1],
                               fill=bg_c, outline=(30, 36, 55))
                if is_current:
                    # Draw player character
                    pc = cx + cell_size // 2
                    pr = cy + cell_size // 2
                    draw.ellipse([pc - 12, pr - 12, pc + 12, pr + 12], fill=accent)
                    draw.text((pc, pr), "●", font=fn_cell, fill=(255, 255, 255), anchor="mm")
                elif is_visited:
                    draw.text((cx + cell_size // 2, cy + cell_size // 2), "·",
                              font=fn_cell, fill=(50, 120, 70), anchor="mm")

    # Start / End markers
    if grid and grid[0]:
        draw.text((ox + cell_size // 2, oy + cell_size // 2), "S",
                  font=fn_cell, fill=(80, 220, 80), anchor="mm")
    draw.text((ox + (cols - 1) * cell_size + cell_size // 2,
               oy + (rows - 1) * cell_size + cell_size // 2),
              "E", font=fn_cell, fill=(255, 80, 80), anchor="mm")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

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
        self.accent = SERIES_COLORS.get(series, (80, 180, 255))

    def render_frame(self, scene: dict, step_idx: int, step_progress: float,
                     global_frame: int, total_steps: int) -> Image.Image:
        img  = Image.new("RGB", (WIDTH, HEIGHT), color=(10, 12, 20))
        draw = ImageDraw.Draw(img)
        accent = self.accent

        # 1. Game header (puzzle#, stars, title)
        draw_game_header(draw, scene, accent, step_idx, total_steps)

        # 2. Python code editor
        code_lines   = scene.get("code", ["# code loading..."])
        active_lines = scene.get("active_lines", list(range(len(code_lines))))
        active_line  = active_lines[step_idx] if step_idx < len(active_lines) else 0
        draw_code_editor(draw, code_lines, active_line, accent, step_progress)

        # 3. Execution visualization
        draw_visualization(draw, scene, step_idx, step_progress, global_frame, accent)

        # 4. Test cases panel
        draw_test_panel(draw, scene, step_idx, total_steps, accent)

        # 5. Footer (step dots, complexity)
        draw_footer(draw, step_idx, total_steps, scene, accent, global_frame)

        return img

    def render_thumbnail(self, scene: dict) -> Image.Image:
        img  = Image.new("RGB", (WIDTH, HEIGHT), color=(10, 12, 20))
        draw = ImageDraw.Draw(img)
        accent = self.accent
        draw_game_header(draw, scene, accent, 3, 9)
        code_lines = scene.get("code", ["# code loading..."])
        draw_code_editor(draw, code_lines, 0, accent, 0.0)
        return img
