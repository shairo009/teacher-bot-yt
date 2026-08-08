"""
Puzzle Visual Engine — Coding Game Style Renderer v5 (Fixed Layout & Vector Icons)
Looks like a real high-end coding puzzle game (Human Resource Machine / Zachtronics / CodeCombat).
Layout:
  [0   – 220]  Game header: puzzle# + vector stars + topic title + difficulty badge
  [220 – 820]  Python code editor panel (auto-scaled syntax highlighted code, line cursor)
  [820 – 1540] Execution visualization (720px height, 0 bleed, perfect node/bar positioning)
  [1540– 1760] Test cases panel (vector badges)
  [1760– 1920] Step dots + complexity stats + speedrun timer footer
"""

import math, random, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH  = 1080
HEIGHT = 1920
FPS    = 30

# ── Zone constants (Strict Non-Overlapping Boundaries) ──────────────────────
HEADER_TOP   = 0
HEADER_BOT   = 220
CODE_TOP     = 220
CODE_BOT     = 820
VIZ_TOP      = 820
VIZ_BOT      = 1540
TESTS_TOP    = 1540
TESTS_BOT    = 1760
FOOTER_TOP   = 1760
FOOTER_BOT   = 1920

CODE_PAD_L   = 28
CODE_PAD_R   = 28
MAX_VISIBLE  = 14          # max code lines visible at once

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


# ── Color Helpers ────────────────────────────────────────────────────────────
def lerp_c(c1: tuple, c2: tuple, t: float) -> tuple:
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ── Font Helpers ─────────────────────────────────────────────────────────────
_FONT_CACHE = {}
def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.ImageFont:
    key = (size, bold, mono)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    
    candidates = []
    if bold:
        candidates = ["assets/fonts/Montserrat-Bold.ttf", "assets/fonts/hindi_font_bold.ttf"]
    else:
        candidates = ["assets/fonts/Montserrat-Regular.ttf", "assets/fonts/hindi_font.ttf"]
    
    for p in candidates:
        try:
            fnt = ImageFont.truetype(p, size)
            _FONT_CACHE[key] = fnt
            return fnt
        except:
            pass
    
    fnt = ImageFont.load_default()
    _FONT_CACHE[key] = fnt
    return fnt


def text_w(text: str, font: ImageFont.ImageFont) -> int:
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]
    except:
        return len(text) * 12


# ── Vector Drawing Helpers (Replaces missing font glyphs) ────────────────────
def draw_vector_star(draw: ImageDraw.Draw, cx: float, cy: float, r_outer: float = 12,
                     r_inner: float = 5, fill: tuple = (255, 210, 0), outline: tuple = None):
    pts = []
    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        angle = math.radians(-90 + i * 36)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(pts, fill=fill, outline=outline)


def draw_play_icon(draw: ImageDraw.Draw, x: float, y: float, size: float = 14, fill: tuple = (80, 220, 160)):
    h = size
    w = size * 0.866
    pts = [(x, y - h / 2), (x + w, y), (x, y + h / 2)]
    draw.polygon(pts, fill=fill)


def draw_check_icon(draw: ImageDraw.Draw, x: float, y: float, size: float = 14, color: tuple = (90, 230, 90)):
    pts = [(x - size * 0.4, y), (x - size * 0.1, y + size * 0.3), (x + size * 0.4, y - size * 0.3)]
    draw.line(pts, fill=color, width=3)


def draw_circle_icon(draw: ImageDraw.Draw, x: float, y: float, r: float = 6, color: tuple = (90, 90, 110)):
    draw.ellipse([x - r, y - r, x + r, y + r], outline=color, width=2)


# ── Syntax Tokenizer ──────────────────────────────────────────────────────────
def tokenize_python_line(line: str) -> list[tuple[str, tuple]]:
    tokens = []
    comment_idx = -1
    in_str = False
    str_char = ''
    
    for i, ch in enumerate(line):
        if ch in ('"', "'") and (i == 0 or line[i-1] != '\\'):
            if not in_str:
                in_str = True
                str_char = ch
            elif ch == str_char:
                in_str = False
        elif ch == '#' and not in_str:
            comment_idx = i
            break

    comment = ""
    code_part = line
    if comment_idx != -1:
        code_part = line[:comment_idx]
        comment   = line[comment_idx:]

    pattern = r'(@\w+)|("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(\b\d+\.?\d*\b)|(\b[a-zA-Z_]\w*\b)|(==|!=|<=|>=|=>|\+|\-|\*|/|%|=|:)|([()[\]{}])'
    
    pos = 0
    after_def = False

    for m in re.finditer(pattern, code_part):
        start, end = m.span()
        if start > pos:
            tokens.append((code_part[pos:start], SYN["default"]))
        pos = end

        dec, string, num, word, op, brk = m.groups()
        if string:
            tokens.append((string, SYN["string"]))
        elif num:
            tokens.append((num, SYN["number"]))
        elif dec:
            tokens.append((dec, SYN["decorator"]))
        elif brk:
            tokens.append((brk, SYN["bracket"]))
        elif word:
            if word in PY_KEYWORDS:
                tokens.append((word, SYN["keyword"]))
                after_def = (word == "def")
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

    if pos < len(code_part):
        tokens.append((code_part[pos:], SYN["default"]))

    if comment:
        tokens.append((comment, SYN["comment"]))

    return tokens or [(line, SYN["default"])]


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: CODE EDITOR (Auto-Scaled & Balanced)
# ─────────────────────────────────────────────────────────────────────────────

def draw_code_editor(draw: ImageDraw.Draw, code_lines: list[str],
                     active_line: int, accent: tuple, step_progress: float):
    GUTTER_W  = 56
    CODE_LEFT = CODE_PAD_L + GUTTER_W
    
    n_lines = len(code_lines)
    avail_h = CODE_BOT - CODE_TOP - 44
    
    if n_lines <= 8:
        line_h    = max(48, min(62, avail_h // max(1, n_lines)))
        font_size = max(26, min(32, line_h - 18))
    else:
        line_h    = max(38, min(46, avail_h // min(n_lines, MAX_VISIBLE)))
        font_size = max(22, min(26, line_h - 16))

    font      = get_font(font_size, mono=True)
    font_lnum = get_font(max(18, font_size - 6), mono=True)

    # Panel backgrounds
    draw.rectangle([0, CODE_TOP, WIDTH, CODE_BOT], fill=EDITOR_BG)
    draw.line([0, CODE_TOP, WIDTH, CODE_TOP], fill=accent, width=3)
    draw.line([0, CODE_BOT, WIDTH, CODE_BOT], fill=EDITOR_BORDER, width=2)
    draw.rectangle([0, CODE_TOP, CODE_PAD_L + GUTTER_W, CODE_BOT], fill=GUTTER_BG)
    draw.line([CODE_PAD_L + GUTTER_W, CODE_TOP, CODE_PAD_L + GUTTER_W, CODE_BOT],
              fill=EDITOR_BORDER, width=1)

    # File Tab
    tab_text = "  puzzle.py  "
    tab_font = get_font(20, bold=True)
    tab_w    = text_w(tab_text, tab_font) + 4
    draw.rectangle([0, CODE_TOP, tab_w, CODE_TOP + 32], fill=accent)
    draw.text((tab_w // 2, CODE_TOP + 16), tab_text, font=tab_font, fill=(0, 0, 0), anchor="mm")

    scroll_start  = max(0, active_line - MAX_VISIBLE // 2)
    visible_lines = code_lines[scroll_start: scroll_start + MAX_VISIBLE]

    # Vertical centering offset if few lines
    total_code_h = len(visible_lines) * line_h
    start_y_offset = CODE_TOP + 40
    if n_lines <= 8 and total_code_h < avail_h - 20:
        start_y_offset += (avail_h - total_code_h - 20) // 2

    for i, line in enumerate(visible_lines):
        abs_line = scroll_start + i
        y_top    = start_y_offset + i * line_h

        is_active = (abs_line == active_line)
        if is_active:
            draw.rectangle([0, y_top, WIDTH, y_top + line_h], fill=LINE_HL)
            draw.rectangle([0, y_top, 5, y_top + line_h], fill=accent)

        lnum_str = str(abs_line + 1)
        lnum_x   = CODE_PAD_L + GUTTER_W - 10
        lnum_col = accent if is_active else GUTTER_FG
        draw.text((lnum_x, y_top + line_h // 2), lnum_str,
                  font=font_lnum, fill=lnum_col, anchor="rm")

        tokens = tokenize_python_line(line)
        x = CODE_LEFT + 10
        max_x = WIDTH - CODE_PAD_R - 10
        for token_text, color in tokens:
            if x >= max_x:
                break
            tw_val = text_w(token_text, font)
            if x + tw_val > max_x:
                avail_chars = max(1, int(len(token_text) * (max_x - x) / max(1, tw_val)))
                token_text = token_text[:avail_chars]
                draw.text((x, y_top + line_h // 2 - 1), token_text,
                          font=font, fill=color, anchor="lm")
                break
            draw.text((x, y_top + line_h // 2 - 1), token_text,
                      font=font, fill=color, anchor="lm")
            x += tw_val

        if is_active:
            cursor_blink = step_progress % 0.5 < 0.25 or step_progress > 0.8
            if cursor_blink:
                cursor_x = max(CODE_LEFT + 12, min(x + 2, max_x))
                draw.rectangle([cursor_x, y_top + 4, cursor_x + 3, y_top + line_h - 4],
                               fill=CURSOR_COL)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: GAME HEADER (Vector Stars & Sleek Badges)
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
    raw_tag    = scene.get("game_tag", "BOSS FIGHT")
    game_tag   = raw_tag.replace("⚔", "").replace("⚡", "").replace("📜", "").replace("💀", "").replace("🌲", "").strip()

    draw.rectangle([0, HEADER_TOP, WIDTH, HEADER_BOT], fill=(12, 14, 22))
    draw.line([0, HEADER_BOT, WIDTH, HEADER_BOT], fill=EDITOR_BORDER, width=2)

    fn_badge = get_font(20, bold=True)

    # Row 1 (Y = 24): Puzzle Num (Left), Difficulty Badge (Center), Vector Stars (Right)
    pnum_text = f"PUZZLE #{puzzle_num:03d}"
    draw.text((36, 24), pnum_text, font=get_font(24, bold=True), fill=accent, anchor="lm")

    diff_colors = {"EASY": (80, 200, 80), "MEDIUM": (255, 180, 0),
                   "HARD": (255, 80, 80), "EXTREME": (200, 0, 255)}
    diff_c = diff_colors.get(diff, (255, 80, 80))
    diff_text = f" {diff} "
    dw = text_w(diff_text, fn_badge) + 16
    draw.rounded_rectangle([WIDTH // 2 - dw // 2, 10, WIDTH // 2 + dw // 2, 38],
                            radius=6, fill=lerp_c(diff_c, (0, 0, 0), 0.75), outline=diff_c, width=2)
    draw.text((WIDTH // 2, 24), diff_text, font=fn_badge, fill=diff_c, anchor="mm")

    # Vector 5-pointed Stars (Right side)
    filled_stars = min(3, 1 + step_idx // max(total_steps // 3, 1))
    star_x = WIDTH - 40
    for si in range(3, 0, -1):
        s_fill = (255, 210, 0) if si <= filled_stars else (35, 40, 55)
        s_out  = (255, 210, 0) if si <= filled_stars else (70, 75, 95)
        draw_vector_star(draw, star_x, 24, r_outer=11, r_inner=4.5, fill=s_fill, outline=s_out)
        star_x -= 30

    # Row 2 (Y = 62): Game Tag Pill (Left) & Series Chapter Badge (Right)
    fn_tag = get_font(18, bold=True)
    tag_text = f" {game_tag} "
    tw = text_w(tag_text, fn_tag) + 12
    draw.rounded_rectangle([36, 50, 36 + tw, 76], radius=5,
                            fill=lerp_c(accent, (0, 0, 0), 0.8), outline=accent, width=1)
    draw.text((36 + tw // 2, 63), tag_text, font=fn_tag, fill=accent, anchor="mm")

    badge_text = f"{series} > {chapter}" if chapter else series
    if len(badge_text) > 35:
        badge_text = badge_text[:32] + "..."
    fn_series  = get_font(18, bold=False)
    draw.text((WIDTH - 36, 63), badge_text, font=fn_series,
              fill=(120, 135, 170), anchor="rm")

    # Row 3 (Y = 96-210): Wrapped Title & Subtitle
    fn_title = get_font(30, bold=True)
    fn_sub   = get_font(20, bold=False)
    title_lines = _wrap(title, fn_title, WIDTH - 100)[:2]
    
    title_y = 110
    for ln in title_lines:
        draw.text((WIDTH // 2, title_y), ln, font=fn_title, fill=(235, 240, 250), anchor="mm")
        title_y += 36

    if subtitle:
        if len(subtitle) > 60:
            subtitle = subtitle[:57] + "..."
        draw.text((WIDTH // 2, min(title_y + 2, HEADER_BOT - 16)), subtitle, font=fn_sub,
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
    fn_test = get_font(19, mono=True)
    fn_badge = get_font(18, bold=True)

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
        lbl_text= "PASS" if passing else "TEST"
        lbl_c   = (90, 230, 90) if passing else (120, 120, 140)

        draw.rounded_rectangle([tx, ty, tx + col_w - 8, ty + (TESTS_BOT - TESTS_TOP - 54)],
                                radius=6, fill=box_c, outline=brd_c, width=2)

        # Vector Icon + Badge Text
        icon_cx = tx + 24
        icon_cy = ty + 20
        if passing:
            draw_check_icon(draw, icon_cx, icon_cy, size=14, color=(90, 230, 90))
        else:
            draw_circle_icon(draw, icon_cx, icon_cy, r=6, color=(90, 90, 110))

        draw.text((tx + 42, ty + 20), lbl_text, font=fn_badge, fill=lbl_c, anchor="lm")

        in_str  = str(test.get('input', '?')).replace('\n', '')[:11]
        exp_str = str(test.get('expected', '?')).replace('\n', '')[:11]

        draw.text((tx + 10, ty + 46), f"in: {in_str}", font=fn_test, fill=(150, 160, 190))
        draw.text((tx + 10, ty + 72), f"> {exp_str}",  font=fn_test,
                  fill=(90, 210, 90) if passing else (150, 160, 190))

        label = test.get("label", f"test_{ti+1}")
        draw.text((tx + col_w // 2, ty + 106), label, font=get_font(16),
                  fill=(80, 95, 130), anchor="mm")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: STEP / SCORE FOOTER
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
    dot_y      = FOOTER_TOP + 40
    for i in range(total_steps):
        cx = start_x + i * gap
        if i < step_idx:
            draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r], fill=accent)
        elif i == step_idx:
            pulse = int(2 * math.sin(global_frame * 0.2))
            draw.ellipse([cx - dot_r - pulse, dot_y - dot_r - pulse, cx + dot_r + pulse, dot_y + dot_r + pulse],
                         fill=(255, 255, 255), outline=accent, width=2)
        else:
            draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r],
                         fill=(30, 35, 50), outline=(50, 55, 80), width=2)

    # Complexity badges (left)
    tc_val = scene.get("time_complexity", "O(?)")
    sc_val = scene.get("space_complexity", "O(?)")
    tc_clean = re.sub(r"[^\w\(\)\+\*\^/, -]", "", tc_val)[:20]
    sc_clean = re.sub(r"[^\w\(\)\+\*\^/, -]", "", sc_val)[:20]
    
    fn_cmplx = get_font(20, bold=True, mono=True)
    draw.text((36, FOOTER_TOP + 36), f"TIME: {tc_clean}", font=fn_cmplx, fill=(80, 180, 255), anchor="lm")
    draw.text((36, FOOTER_TOP + 72), f"MEM : {sc_clean}", font=fn_cmplx, fill=(180, 130, 255), anchor="lm")

    # Speedrun Timer (right)
    elapsed  = global_frame / FPS
    m, s     = int(elapsed // 60), int(elapsed % 60)
    fn_timer = get_font(26, bold=True, mono=True)
    draw.text((WIDTH - 36, FOOTER_TOP + 54), f"{m:02d}:{s:02d}",
              font=fn_timer, fill=(90, 105, 140), anchor="rm")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: EXECUTION VISUALIZER (Cyber Grid + 0-Bleed Canvas + Safe Badges)
# ─────────────────────────────────────────────────────────────────────────────

def _draw_cyber_grid(draw: ImageDraw.Draw, x0: int, y0: int, x1: int, y1: int,
                     frame: int, accent: tuple):
    grid_size = 40
    offset_y  = int((frame * 1.5) % grid_size)
    grid_col  = (18, 24, 38)

    for gx in range(x0, x1, grid_size):
        draw.line([gx, y0, gx, y1], fill=grid_col, width=1)
    for gy in range(y0 + offset_y, y1, grid_size):
        draw.line([x0, gy, x1, gy], fill=grid_col, width=1)

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

    # 2. Header Vector Play Icon + Text
    draw_play_icon(draw, x0 + 6, VIZ_TOP + 20, size=14, fill=accent)
    fn_label = get_font(22, bold=True)
    draw.text((x0 + 26, VIZ_TOP + 20), "LIVE EXECUTION VISUALIZER", font=fn_label, fill=accent, anchor="lm")

    # Floating Badge in Header (Zero Overlap with Graphics)
    _draw_floating_skill_badge(draw, step_idx, global_frame, accent, x1 - 120, VIZ_TOP + 20)

    viz_y0 = VIZ_TOP + 52
    viz_type = scene.get("viz_type", "bars")

    # Render target visualization engine
    if   viz_type == "bars":   _viz_bars(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "grid":   _viz_grid(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "graph":  _viz_graph(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "stack":  _viz_stack(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "tree":   _viz_tree(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "memory": _viz_memory(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    elif viz_type == "maze":   _viz_maze(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)
    else:                      _viz_bars(draw, scene, step_idx, step_progress, global_frame, accent, x0, viz_y0, x1, y1)


def _draw_floating_skill_badge(draw: ImageDraw.Draw, step_idx: int, frame: int,
                                accent: tuple, x: int, y: int):
    badges = ["+250 XP", "CACHE HIT", "O(1) SPEED", "ACCURACY 99%", "STRIKE PASS"]
    badge_text = badges[step_idx % len(badges)]
    
    float_y = int(3 * math.sin(frame * 0.12))
    fn_badge = get_font(18, bold=True)
    
    bw = text_w(badge_text, fn_badge) + 16
    draw.rounded_rectangle([x - bw // 2, y + float_y - 12, x + bw // 2, y + float_y + 12],
                            radius=6, fill=lerp_c(accent, (0, 0, 0), 0.82), outline=accent, width=2)
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
    bar_w   = max(18, (x1 - x0 - (n - 1) * 8) // n)
    gap     = 8
    chart_h = y1 - y0 - 90

    hi_indices = scene.get("viz_data", {}).get("highlight", {})
    hi_step    = hi_indices.get(str(step_idx), [])

    font_v = get_font(20, mono=True)
    font_i = get_font(18, mono=True)

    pulse = int(3 * math.sin(frame * 0.2))

    for i, v in enumerate(current):
        bx   = x0 + i * (bar_w + gap)
        bh   = int(chart_h * v / max_v)
        by   = y1 - 40 - bh

        is_hi   = i in hi_step
        is_comp = i in hi_step[1:] if len(hi_step) > 1 else False

        if is_hi and i == hi_step[0]:
            bar_c = (255, 80, 80)   # current element – red
        elif is_comp:
            bar_c = (255, 200, 0)   # comparing – yellow
        else:
            sorted_frac = step_idx / max(8, len(current))
            if i / len(current) < sorted_frac:
                bar_c = (80, 210, 90)
            else:
                bar_c = accent

        draw.rounded_rectangle([bx, by, bx + bar_w, y1 - 40], radius=4, fill=bar_c)

        if is_hi:
            draw.rounded_rectangle([bx - 2 - pulse, by - 2 - pulse, bx + bar_w + 2 + pulse, y1 - 38],
                                    radius=5, outline=(255, 255, 255), fill=None, width=2)

        if bar_w >= 20:
            draw.text((bx + bar_w // 2, by - 14), str(v), font=font_v, fill=bar_c, anchor="mm")
            draw.text((bx + bar_w // 2, y1 - 20), str(i), font=font_i, fill=(70, 85, 120), anchor="mm")

    ops = scene.get("viz_data", {}).get("operations", [])
    if ops and step_idx < len(ops):
        op_str = ops[step_idx]
        if len(op_str) > 35:
            op_str = op_str[:32] + "..."
        fn_op = get_font(22, bold=True, mono=True)
        draw.text((x0, y0 + 10), op_str, font=fn_op, fill=(255, 200, 60), anchor="lm")


# ── GRID — DP table visualizer ───────────────────────────────────────────────
def _viz_grid(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    rows = scene.get("viz_data", {}).get("rows", 5)
    cols = scene.get("viz_data", {}).get("cols", 7)
    grid_vals = scene.get("viz_data", {}).get("grid", [])

    avail_w = x1 - x0 - 80
    avail_h = y1 - y0 - 80
    cell_w  = min(110, avail_w // max(1, cols))
    cell_h  = min(80,  avail_h // max(1, rows))
    start_x = x0 + 50 + (avail_w - cols * cell_w) // 2
    start_y = y0 + 40 + (avail_h - rows * cell_h) // 2

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
                v = "OK"
            else:
                v = ""
            if v:
                col = accent if is_current else (90, 210, 90) if is_filled else (60, 70, 100)
                draw.text((cx + cell_w // 2, cy + cell_h // 2), v, font=fn_cell, fill=col, anchor="mm")

    col_headers = scene.get("viz_data", {}).get("col_headers", [])
    row_headers = scene.get("viz_data", {}).get("row_headers", [])
    for ci, lbl in enumerate(col_headers[:cols]):
        draw.text((start_x + ci * cell_w + cell_w // 2, start_y - 18), str(lbl), font=fn_label, fill=(90, 105, 140), anchor="mm")
    for ri, lbl in enumerate(row_headers[:rows]):
        draw.text((start_x - 16, start_y + ri * cell_h + cell_h // 2), str(lbl), font=fn_label, fill=(90, 105, 140), anchor="rm")


# ── GRAPH — node traversal (Coordinate Fixed) ──────────────────────────────
def _viz_graph(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    nodes = scene.get("viz_data", {}).get("nodes", [])
    edges = scene.get("viz_data", {}).get("edges", [])
    visited_by_step = scene.get("viz_data", {}).get("visited", [])

    # Map raw nodes into [x0+50, x1-50] and [y0+50, y1-50]
    mapped_nodes = []
    if not nodes:
        cx_avg, cy_avg = (x0 + x1) // 2, (y0 + y1) // 2
        radius = min((x1 - x0), (y1 - y0)) // 2 - 60
        n = 6
        for i in range(n):
            angle = math.radians(-90 + i * 360 / n)
            mapped_nodes.append({
                "id": i, "label": str(i),
                "x": cx_avg + int(radius * math.cos(angle)),
                "y": cy_avg + int(radius * math.sin(angle))
            })
        edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (4, 5), (2, 5)]
    else:
        for node in nodes:
            rx = node.get("x", 500)
            ry = node.get("y", 250)
            # Check if ry is out of panel range (e.g. 50-450)
            if ry < y0 or ry > y1:
                ny = y0 + 60 + int((ry / 450.0) * (y1 - y0 - 120))
            else:
                ny = ry
            
            if rx < x0 or rx > x1:
                nx = x0 + 60 + int((rx / 1000.0) * (x1 - x0 - 120))
            else:
                nx = rx

            mapped_nodes.append({
                "id": node.get("id", len(mapped_nodes)),
                "label": str(node.get("label", node.get("id", ""))),
                "x": nx, "y": ny
            })

    visited = set()
    if visited_by_step and step_idx < len(visited_by_step):
        visited = set(visited_by_step[:step_idx + 1])

    fn_node = get_font(26, bold=True)

    for edge in edges:
        if isinstance(edge, (list, tuple)) and len(edge) >= 2:
            a, b = edge[0], edge[1]
            if a < len(mapped_nodes) and b < len(mapped_nodes):
                n1, n2 = mapped_nodes[a], mapped_nodes[b]
                both_visited = a in visited and b in visited
                edge_c = lerp_c(accent, (40, 45, 65), 0.5) if both_visited else (35, 40, 60)
                draw.line([n1["x"], n1["y"], n2["x"], n2["y"]], fill=edge_c, width=3 if both_visited else 2)

    pulse = int(4 * math.sin(frame * 0.25))

    for ni, node in enumerate(mapped_nodes):
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
        all_frames = ["main()", "solve(n)", "solve(n-1)", "solve(n-2)", "solve(0) -> base"]
        depth = min(step_idx + 1, len(all_frames))
        current_frames = all_frames[:depth]

    fn_frame = get_font(24, bold=True, mono=True)
    fn_var   = get_font(20, mono=True)

    n_frames = max(1, len(current_frames))
    frame_h  = min(64, (y1 - y0 - 40) // n_frames - 6)
    frame_w  = x1 - x0 - 20
    stack_y  = y1 - 16

    for fi, fr in enumerate(reversed(current_frames)):
        is_top = fi == 0
        fy     = stack_y - (fi + 1) * (frame_h + 6)

        bd_c = accent if is_top else (40, 50, 75)
        draw.rounded_rectangle([x0 + 10, fy, x0 + 10 + frame_w, fy + frame_h],
                                radius=6, fill=(14, 18, 28), outline=bd_c, width=3 if is_top else 1)

        draw.text((x0 + 26, fy + frame_h // 2), str(fr), font=fn_frame,
                  fill=(235, 240, 250) if is_top else (100, 115, 160), anchor="lm")
        if is_top:
            draw.text((x0 + 10 + frame_w - 16, fy + frame_h // 2), "ACTIVE", font=fn_var, fill=accent, anchor="rm")


# ── TREE — BST visualizer ────────────────────────────────────────────────────
def _viz_tree(draw, scene, step_idx, progress, frame, accent, x0, y0, x1, y1):
    tree_vals = scene.get("viz_data", {}).get("tree", [50, 30, 70, 15, 35, 60, 80])
    visited_nodes = scene.get("viz_data", {}).get("visited", [])
    pointer_by_step = scene.get("viz_data", {}).get("pointer", [])

    n       = len(tree_vals)
    levels  = int(math.log2(n + 1)) + 1
    level_h = max(70, (y1 - y0 - 60) // max(levels, 1))
    node_r  = 28
    fn_node = get_font(22, bold=True)

    visited = set(visited_nodes[:step_idx + 1]) if visited_nodes else set()
    if isinstance(pointer_by_step, list):
        pointer = pointer_by_step[step_idx] if step_idx < len(pointer_by_step) else -1
    elif isinstance(pointer_by_step, int):
        pointer = pointer_by_step
    else:
        pointer = -1

    positions = {}
    def get_pos(idx, depth, left, right):
        if idx >= n:
            return
        cx = (left + right) // 2
        cy = y0 + 40 + depth * level_h
        positions[idx] = (cx, cy)
        get_pos(idx * 2 + 1, depth + 1, left, cx)
        get_pos(idx * 2 + 2, depth + 1, cx, right)

    get_pos(0, 0, x0 + 30, x1 - 30)

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
        {"addr": "0x00B0", "label": "ptr",    "value": "-> 0x00A0"},
        {"addr": "0x00B8", "label": "size",   "value": "2"},
    ])

    active_rows = min(step_idx + 1, len(mem_rows))
    row_h    = min(54, (y1 - y0 - 50) // max(active_rows, 1))
    col_addr = 160
    col_lbl  = 140
    col_val  = (x1 - x0 - col_addr - col_lbl - 20)
    rx       = x0 + 10

    fn_addr = get_font(20, mono=True)
    fn_lbl  = get_font(20, bold=True, mono=True)
    fn_val  = get_font(22, mono=True)

    draw.text((rx + col_addr // 2, y0 + 14), "ADDRESS", font=fn_addr, fill=(60, 70, 100), anchor="mm")
    draw.text((rx + col_addr + col_lbl // 2, y0 + 14), "NAME", font=fn_addr, fill=(60, 70, 100), anchor="mm")
    draw.text((rx + col_addr + col_lbl + col_val // 2, y0 + 14), "VALUE", font=fn_addr, fill=(60, 70, 100), anchor="mm")
    draw.line([rx, y0 + 28, x1 - 10, y0 + 28], fill=(38, 45, 70), width=1)

    for ri, row in enumerate(mem_rows[:active_rows]):
        ry = y0 + 34 + ri * row_h
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
    cell_size = min((x1 - x0 - 20) // cols, (y1 - y0 - 20) // rows, 80)
    ox = x0 + 10 + (x1 - x0 - 20 - cols * cell_size) // 2
    oy = y0 + 10 + (y1 - y0 - 20 - rows * cell_size) // 2

    visited_cells = set()
    if path_by_step and step_idx < len(path_by_step):
        for p in path_by_step[:step_idx + 1]:
            visited_cells.add(tuple(p))

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
                elif is_visited:
                    pc, pr = cx + cell_size // 2, cy + cell_size // 2
                    draw.ellipse([pc - 4, pr - 4, pc + 4, pr + 4], fill=(50, 160, 85))


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
        draw_visualization(draw, scene, 3, 0.5, 90, accent)
        draw_test_panel(draw, scene, 3, 9, accent)
        draw_footer(draw, 3, 9, scene, accent, 90)
        return img
