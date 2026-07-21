"""
Tech Visual Engine v2 — Multi-Theme Game-World Renderer
Each video lives in a completely unique visual universe.
2-minute videos, game-mechanic explanations, expert-level content.
"""

import math, random, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from src.visual_themes import THEMES

WIDTH  = 1080
HEIGHT = 1920
FPS    = 30

# ── Layout zones ─────────────────────────────────────────────────────────────
HEADER_TOP    = 0
BADGE_CY      = 72
BADGE_H       = 44
TITLE_TOP     = 108
TITLE_MAX_BOT = 230
SUBTITLE_CY   = 255
HOOK_TOP      = 275
HOOK_BOT      = 328
DIAGRAM_TOP   = 338
DIAGRAM_BOT   = 1420
COUNTER_CY    = 1478
COUNTER_H     = 78
CAPTION_TOP   = 1568
CAPTION_BOT   = 1855
DOTS_Y        = 1882
FOOTER_BOT    = 1920


# ── Font helpers ──────────────────────────────────────────────────────────────
_FONT_CACHE = {}
def get_font(size, bold=False):
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    candidates = []
    if bold:
        candidates = [
            "assets/fonts/Montserrat-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/nix/store/fonts/Montserrat-Bold.ttf",
        ]
    else:
        candidates = [
            "assets/fonts/Montserrat-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for p in candidates:
        try:
            fnt = ImageFont.truetype(p, size)
            _FONT_CACHE[key] = fnt
            return fnt
        except:
            pass
    _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


def fit_font(text, max_width, max_size=64, min_size=20, bold=False):
    for size in range(max_size, min_size - 1, -2):
        fnt = get_font(size, bold)
        try:
            w = fnt.getlength(text)
        except:
            w = len(text) * size * 0.6
        if w <= max_width:
            return fnt, size
    return get_font(min_size, bold), min_size


def wrap_text(text, font, max_width):
    words = text.split()
    lines, cur = [], []
    for w in words:
        trial = " ".join(cur + [w])
        try:
            tw = font.getlength(trial)
        except:
            tw = len(trial) * 12
        if tw <= max_width or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


def draw_text_shadow(draw, pos, text, font, fill, shadow_color=None, offset=3):
    if shadow_color is None:
        shadow_color = (0, 0, 0)
    x, y = pos
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill)


# ── Color helpers ─────────────────────────────────────────────────────────────
def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def glow_color(base, strength=0.5):
    """Brighten color for glow effect."""
    return tuple(min(255, int(c + (255 - c) * strength)) for c in base)


def alpha_composite_color(bg, fg, alpha):
    """Simple alpha composite without PIL Image."""
    a = alpha / 255.0
    return tuple(int(bg[i] * (1 - a) + fg[i] * a) for i in range(3))


# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND RENDERERS — one per grid_style
# ══════════════════════════════════════════════════════════════════════════════

def _bg_lines(draw, theme, frame_idx):
    """Classic scan-line grid — sharp and techy."""
    g = theme["grid"]
    scroll = (frame_idx * 2) % 80
    for gx in range(0, WIDTH + 80, 80):
        draw.line([gx - scroll, 0, gx - scroll, HEIGHT], fill=g, width=1)
    for gy in range(0, HEIGHT + 80, 80):
        draw.line([0, gy, WIDTH, gy], fill=g, width=1)


def _bg_diagonal(draw, theme, frame_idx):
    """Diagonal streaks — cyberpunk city feel."""
    g = theme["grid"]
    p = theme["primary"]
    for i in range(0, WIDTH + HEIGHT, 90):
        draw.line([i, 0, i - HEIGHT, HEIGHT], fill=g, width=1)
    # Moving accent streak
    t = frame_idx * 5
    sx = int(t % (WIDTH + HEIGHT))
    streak = lerp_color(p, theme["bg"], 0.85)
    draw.line([sx, 0, sx - HEIGHT, HEIGHT], fill=streak, width=3)
    draw.line([sx - 6, 0, sx - 6 - HEIGHT, HEIGHT], fill=lerp_color(p, theme["bg"], 0.94), width=1)


def _bg_dots(draw, theme, frame_idx):
    """Dot grid — deep space / quantum feel."""
    g = theme["grid"]
    p = theme["primary"]
    pulse = 0.5 + 0.5 * math.sin(frame_idx * 0.04)
    dot_c = lerp_color(g, p, pulse * 0.15)
    for gx in range(40, WIDTH, 80):
        for gy in range(40, HEIGHT, 80):
            draw.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=dot_c)


def _bg_hex(draw, theme, frame_idx):
    """Hexagonal grid — biomech / organic tech."""
    g = theme["grid"]
    hex_r = 52
    hex_h = int(hex_r * math.sqrt(3))
    offset_x = int((frame_idx * 0.3) % hex_r)

    col = 0
    x = -hex_r + offset_x
    while x < WIDTH + hex_r:
        y_offset = 0 if col % 2 == 0 else hex_h // 2
        y = -hex_h + y_offset
        while y < HEIGHT + hex_h:
            pts = []
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                pts.append((x + int(hex_r * 0.85 * math.cos(rad)),
                             y + int(hex_r * 0.85 * math.sin(rad))))
            draw.polygon(pts, outline=g, fill=None)
            y += hex_h
        x += int(hex_r * 1.5)
        col += 1


def _bg_circuit(draw, theme, frame_idx):
    """PCB circuit trace style — circuit board feel."""
    g = theme["grid"]
    p = theme["primary"]
    rng = random.Random(42)
    pulse_t = frame_idx * 0.06

    # Horizontal traces
    for row in range(60, HEIGHT, 120):
        draw.line([0, row, WIDTH, row], fill=g, width=1)
        # Random via dots
        for _ in range(6):
            vx = rng.randint(80, WIDTH - 80)
            # Pulse along trace
            t_frac = (pulse_t % (2 * math.pi)) / (2 * math.pi)
            if abs(vx / WIDTH - t_frac) < 0.04:
                dot_c = lerp_color(p, theme["bg"], 0.5)
            else:
                dot_c = lerp_color(g, theme["bg"], 0.3)
            draw.ellipse([vx - 5, row - 5, vx + 5, row + 5], fill=dot_c, outline=g)

    # Vertical traces
    for col in range(80, WIDTH, 160):
        draw.line([col, 0, col, HEIGHT], fill=g, width=1)


def _bg_none(draw, theme, frame_idx):
    """Clean background — only subtle radial vignette."""
    # Subtle scanlines
    g = theme["grid"]
    for gy in range(0, HEIGHT, 4):
        draw.line([0, gy, WIDTH, gy], fill=lerp_color(theme["bg"], g, 0.3), width=1)


def _draw_background(draw, theme, frame_idx):
    style = theme.get("grid_style", "lines")
    {
        "lines":    _bg_lines,
        "diagonal": _bg_diagonal,
        "dots":     _bg_dots,
        "hex":      _bg_hex,
        "circuit":  _bg_circuit,
        "none":     _bg_none,
    }.get(style, _bg_lines)(draw, theme, frame_idx)


# ══════════════════════════════════════════════════════════════════════════════
# PARTICLE SYSTEMS
# ══════════════════════════════════════════════════════════════════════════════

def _draw_particles(draw, theme, frame_idx, zone_top=DIAGRAM_TOP, zone_bot=DIAGRAM_BOT):
    style   = theme.get("particle", "sparks")
    p       = theme["primary"]
    s       = theme["secondary"]
    rng_seed = frame_idx // 3  # slow update

    if style == "rain":
        rng = random.Random(rng_seed)
        for _ in range(18):
            rx = rng.randint(0, WIDTH)
            ry = ((frame_idx * (rng.randint(4, 12))) % (zone_bot - zone_top)) + zone_top
            alpha = rng.random()
            rc = lerp_color(p, theme["bg"], 0.6 + alpha * 0.3)
            length = rng.randint(20, 60)
            draw.line([rx, ry, rx + 2, ry + length], fill=rc, width=1)

    elif style == "stars":
        rng = random.Random(42)
        for _ in range(50):
            sx = rng.randint(0, WIDTH)
            sy = rng.randint(zone_top, zone_bot)
            twinkle = 0.5 + 0.5 * math.sin(frame_idx * 0.1 + rng.random() * 10)
            sc = lerp_color(theme["bg"], p, twinkle * 0.6)
            r = 1 if twinkle < 0.7 else 2
            draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=sc)

    elif style == "sparks":
        rng = random.Random(rng_seed * 13)
        for _ in range(12):
            px = rng.randint(100, WIDTH - 100)
            py = rng.randint(zone_top + 50, zone_bot - 50)
            life = rng.random()
            pc = lerp_color(p, s, life)
            size = int(2 + life * 5)
            angle = rng.random() * 2 * math.pi
            ex = px + int(math.cos(angle) * size * 8)
            ey = py + int(math.sin(angle) * size * 8)
            draw.line([px, py, ex, ey], fill=lerp_color(pc, theme["bg"], 0.4), width=1)

    elif style == "bubbles":
        rng = random.Random(rng_seed)
        for _ in range(14):
            bx = rng.randint(60, WIDTH - 60)
            by_base = rng.randint(zone_top + 30, zone_bot - 30)
            drift = int(math.sin(frame_idx * 0.05 + rng.random() * 6) * 12)
            by = by_base + drift
            if by < zone_top or by > zone_bot:
                continue
            r = rng.randint(4, 14)
            bc = lerp_color(p, theme["bg"], 0.72)
            draw.ellipse([bx - r, by - r, bx + r, by + r], outline=bc, fill=None)

    elif style == "pixels":
        rng = random.Random(rng_seed)
        for _ in range(20):
            px = rng.randint(0, WIDTH // 8) * 8
            py = rng.randint(zone_top // 8, zone_bot // 8) * 8
            pc = lerp_color(p, s, rng.random())
            pc = lerp_color(pc, theme["bg"], 0.5)
            draw.rectangle([px, py, px + 7, py + 7], fill=pc)

    elif style == "dust":
        rng = random.Random(42)
        for _ in range(35):
            dx = rng.randint(0, WIDTH)
            dy = rng.randint(zone_top, zone_bot)
            drift_x = int(math.sin(frame_idx * 0.02 + rng.random() * 4) * 15)
            drift_y = int((frame_idx * (rng.random() * 0.5 + 0.2)) % (zone_bot - zone_top))
            fx = (dx + drift_x) % WIDTH
            fy = ((dy + drift_y - zone_top) % (zone_bot - zone_top)) + zone_top
            dc = lerp_color(p, theme["bg"], 0.78)
            draw.ellipse([fx - 1, fy - 1, fx + 1, fy + 1], fill=dc)


# ══════════════════════════════════════════════════════════════════════════════
# GAME UI ELEMENTS
# ══════════════════════════════════════════════════════════════════════════════

def draw_xp_bar(draw, theme, x, y, width, height, pct, label="XP"):
    """Horizontal progress/XP bar with glow."""
    p = theme["primary"]
    bg_fill = lerp_color(theme["bg"], p, 0.08)
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height // 2,
                            fill=bg_fill, outline=lerp_color(p, theme["bg"], 0.4), width=2)
    if pct > 0.01:
        fill_w = int((width - 4) * min(pct, 1.0))
        if fill_w > height:
            fill_c = lerp_color(p, theme["secondary"], pct)
            draw.rounded_rectangle([x + 2, y + 2, x + 2 + fill_w, y + height - 2],
                                    radius=height // 2 - 2, fill=fill_c)
    # Label
    fnt = get_font(max(18, height - 8), bold=True)
    pct_text = f"{label}  {int(pct * 100)}%"
    try:
        tw = fnt.getlength(pct_text)
    except:
        tw = len(pct_text) * 10
    draw.text((x + width // 2 - tw // 2, y + (height - fnt.size) // 2 - 1 if hasattr(fnt, 'size') else y + 2),
              pct_text, font=fnt, fill=theme["text_bright"])


def draw_stat_badge(draw, theme, cx, cy, label, value, color=None):
    """Floating stat chip — like game HUD element."""
    if color is None:
        color = theme["primary"]
    fnt_lbl = get_font(20, bold=False)
    fnt_val = get_font(28, bold=True)
    try:
        vw = fnt_val.getlength(str(value))
        lw = fnt_lbl.getlength(label)
    except:
        vw = len(str(value)) * 16
        lw = len(label) * 11
    w = max(int(vw), int(lw)) + 28
    h = 72
    bg = lerp_color(theme["bg"], color, 0.12)
    draw.rounded_rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2],
                            radius=10, fill=bg, outline=color, width=2)
    draw.text((cx, cy - 14), label, font=fnt_lbl, fill=theme["text_dim"], anchor="mm")
    draw.text((cx, cy + 16), str(value), font=fnt_val, fill=color, anchor="mm")


def draw_damage_number(draw, theme, x, y, text, color=None, size=38):
    """Floating damage/info popup — game style."""
    if color is None:
        color = theme["secondary"]
    fnt = get_font(size, bold=True)
    # Shadow
    draw.text((x + 2, y + 2), text, font=fnt, fill=(0, 0, 0), anchor="mm")
    draw.text((x, y), text, font=fnt, fill=color, anchor="mm")


def draw_node_glow(draw, theme, cx, cy, r, intensity=1.0):
    """Multi-layer glow halo around a node."""
    glow = theme["glow"]
    for i in range(4, 0, -1):
        radius = r + i * 8 * intensity
        alpha_t = (5 - i) / 5 * 0.25 * intensity
        gc = lerp_color(theme["bg"], glow, alpha_t)
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=gc)


def draw_connection_beam(draw, theme, x1, y1, x2, y2, active=True, progress=1.0):
    """Animated beam between nodes — energy transfer look."""
    p = theme["primary"] if active else theme["grid"]
    s = theme["secondary"]

    # Draw the full path dimly
    draw.line([x1, y1, x2, y2], fill=lerp_color(p, theme["bg"], 0.65), width=2)

    if active and progress > 0:
        # Animated segment
        mx = int(x1 + (x2 - x1) * progress)
        my = int(y1 + (y2 - y1) * progress)
        draw.line([x1, y1, mx, my], fill=p, width=3)
        # Head glow dot
        draw.ellipse([mx - 6, my - 6, mx + 6, my + 6], fill=s)
        draw.ellipse([mx - 3, my - 3, mx + 3, my + 3], fill=(255, 255, 255))


def draw_node(draw, theme, cx, cy, r, label, color=None, is_active=False, sublabel=""):
    """Draw a themed node (hexagonal or circular based on theme)."""
    if color is None:
        color = theme["primary"]
    bg_node = theme["node_fill"]
    border  = color if is_active else lerp_color(color, theme["bg"], 0.4)

    if is_active:
        draw_node_glow(draw, theme, cx, cy, r, intensity=1.2)

    # Node shape: hexagonal for hex-style themes, circular otherwise
    grid_style = theme.get("grid_style", "lines")
    if grid_style == "hex":
        pts = []
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            pts.append((cx + int(r * math.cos(rad)), cy + int(r * math.sin(rad))))
        draw.polygon(pts, fill=bg_node, outline=border)
        if is_active:
            inner_pts = [(cx + int((r - 6) * math.cos(math.radians(a))),
                          cy + int((r - 6) * math.sin(math.radians(a)))) for a in range(0, 360, 60)]
            draw.polygon(inner_pts, outline=lerp_color(border, (255, 255, 255), 0.4), fill=None)
    else:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg_node, outline=border, width=3)
        if is_active:
            draw.ellipse([cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5],
                         outline=lerp_color(border, (255, 255, 255), 0.4), fill=None)

    # Inner label
    fnt_size = max(18, min(32, int(r * 0.55)))
    fnt = get_font(fnt_size, bold=True)
    lbl_color = color if is_active else theme["text_dim"]
    if label:
        lines = wrap_text(label, fnt, r * 1.7)[:3]
        line_h = fnt_size + 3
        total_h = len(lines) * line_h
        start_y = cy - total_h // 2 + line_h // 2
        for i, ln in enumerate(lines):
            draw.text((cx, start_y + i * line_h), ln, font=fnt, fill=lbl_color, anchor="mm")

    # Sublabel below node
    if sublabel:
        fnt_sub = get_font(18, bold=False)
        draw.text((cx, cy + r + 14), sublabel, font=fnt_sub,
                  fill=theme["text_dim"], anchor="mm")


# ══════════════════════════════════════════════════════════════════════════════
# HEADER / FOOTER ZONE RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

def draw_header(draw, scene, theme):
    series   = scene.get("series", "")
    chapter  = scene.get("chapter", "")
    title    = scene.get("title", "Topic")
    subtitle = scene.get("subtitle", "")
    hook     = scene.get("hook", "")
    game_tag = scene.get("game_tag", "")  # e.g. "⚔ BOSS FIGHT", "🧪 LAB MODE"
    p        = theme["primary"]
    s        = theme["secondary"]

    SIDE_PAD = 55
    MAX_W    = WIDTH - SIDE_PAD * 2

    # ── Theme name watermark ──
    theme_fnt = get_font(20, bold=False)
    draw.text((WIDTH - SIDE_PAD, BADGE_CY - BADGE_H // 2 + 6),
              theme.get("name", ""), font=theme_fnt,
              fill=lerp_color(p, theme["bg"], 0.55), anchor="rm")

    # ── Series badge ──
    badge_text = f"  {series}  ›  {chapter}  " if chapter else f"  {series}  "
    fnt_badge  = get_font(22, bold=True)
    try:
        bw = int(fnt_badge.getlength(badge_text)) + 24
    except:
        bw = len(badge_text) * 13 + 24
    bw  = min(bw, MAX_W)
    bx1 = SIDE_PAD
    by1 = BADGE_CY - BADGE_H // 2
    by2 = BADGE_CY + BADGE_H // 2
    draw.rounded_rectangle([bx1, by1, bx1 + bw, by2], radius=10,
                            fill=lerp_color(p, theme["bg"], 0.85), outline=p, width=2)
    draw.text((bx1 + bw // 2, BADGE_CY), badge_text, font=fnt_badge, fill=p, anchor="mm")

    # ── Game tag pill (right side) ──
    if game_tag:
        gtag_fnt = get_font(22, bold=True)
        try:
            gtw = int(gtag_fnt.getlength(game_tag)) + 24
        except:
            gtw = len(game_tag) * 13 + 24
        gx1 = WIDTH - SIDE_PAD - gtw
        draw.rounded_rectangle([gx1, by1, gx1 + gtw, by2], radius=10,
                                fill=lerp_color(s, theme["bg"], 0.8), outline=s, width=2)
        draw.text((gx1 + gtw // 2, BADGE_CY), game_tag, font=gtag_fnt, fill=s, anchor="mm")

    # ── Title ──
    title_zone_h = TITLE_MAX_BOT - TITLE_TOP
    chosen_fnt, chosen_lines = None, [title]
    for size in range(64, 22, -2):
        fnt_t = get_font(size, bold=True)
        lines = wrap_text(title, fnt_t, MAX_W)
        if len(lines) <= 2:
            line_h = size + 8
            if len(lines) * line_h <= title_zone_h:
                chosen_fnt   = fnt_t
                chosen_lines = lines
                break
    if chosen_fnt is None:
        chosen_fnt   = get_font(24, bold=True)
        chosen_lines = wrap_text(chosen_fnt, MAX_W)[:2]

    line_h  = (chosen_fnt.size if hasattr(chosen_fnt, 'size') else 30) + 8
    total_h = len(chosen_lines) * line_h
    title_cy = TITLE_TOP + (title_zone_h - total_h) // 2 + line_h // 2

    for i, line in enumerate(chosen_lines):
        y_pos = title_cy + i * line_h
        if ' ' in line and i == len(chosen_lines) - 1:
            idx       = line.rfind(' ')
            part_main = line[:idx]
            part_hl   = line[idx:]
            try:
                main_w = int(chosen_fnt.getlength(part_main))
                hl_w   = int(chosen_fnt.getlength(part_hl))
            except:
                main_w = len(part_main) * 18
                hl_w   = len(part_hl) * 18
            total_tw  = main_w + hl_w
            start_x   = (WIDTH - total_tw) // 2
            draw_text_shadow(draw, (start_x, y_pos), part_main, chosen_fnt, theme["text_bright"])
            draw_text_shadow(draw, (start_x + main_w, y_pos), part_hl, chosen_fnt, p)
        else:
            try:
                tw = chosen_fnt.getlength(line)
            except:
                tw = len(line) * 18
            draw_text_shadow(draw, ((WIDTH - tw) // 2, y_pos), line, chosen_fnt, theme["text_bright"])

    # ── Subtitle ──
    if subtitle:
        fnt_sub, _ = fit_font(subtitle, MAX_W, max_size=30, min_size=18, bold=False)
        try:
            sw = fnt_sub.getlength(subtitle)
        except:
            sw = len(subtitle) * 14
        draw.text(((WIDTH - sw) // 2, SUBTITLE_CY), subtitle, font=fnt_sub,
                  fill=theme["text_dim"], anchor="lm")

    # ── Hook pill ──
    if hook:
        hook_h = HOOK_BOT - HOOK_TOP
        fnt_hook, _ = fit_font(hook, MAX_W - 40, max_size=26, min_size=16, bold=True)
        draw.rounded_rectangle([SIDE_PAD, HOOK_TOP, WIDTH - SIDE_PAD, HOOK_BOT],
                                radius=hook_h // 2,
                                fill=lerp_color(s, theme["bg"], 0.82),
                                outline=s, width=2)
        draw.text((WIDTH // 2, (HOOK_TOP + HOOK_BOT) // 2), hook,
                  font=fnt_hook, fill=s, anchor="mm")


def draw_caption(draw, caption, theme, step_progress):
    if not caption:
        return
    p = theme["primary"]
    MAX_W = WIDTH - 80
    fnt, _ = fit_font(caption, MAX_W - 40, max_size=30, min_size=18, bold=False)
    lines = wrap_text(caption, fnt, MAX_W - 40)[:4]
    line_h = (fnt.size if hasattr(fnt, 'size') else 24) + 6
    total_h = len(lines) * line_h

    cap_h   = CAPTION_BOT - CAPTION_TOP
    pad_top = (cap_h - total_h) // 2

    draw.rounded_rectangle([40, CAPTION_TOP, WIDTH - 40, CAPTION_BOT],
                            radius=18, fill=lerp_color(theme["bg"], p, 0.07),
                            outline=lerp_color(p, theme["bg"], 0.55), width=2)

    # Progress bar under caption
    bar_y = CAPTION_BOT - 8
    bar_w = int((WIDTH - 80 - 4) * min(step_progress, 1.0))
    if bar_w > 0:
        draw.rounded_rectangle([42, bar_y, 42 + bar_w, CAPTION_BOT - 4],
                                radius=3, fill=lerp_color(p, theme["secondary"], step_progress))

    for i, line in enumerate(lines):
        yt = CAPTION_TOP + pad_top + i * line_h + line_h // 2
        draw.text((WIDTH // 2, yt), line, font=fnt, fill=theme["text_bright"], anchor="mm")


def draw_step_indicator(draw, step_idx, total_steps, theme):
    p = theme["primary"]
    s = theme["secondary"]
    dot_r, gap = 8, 22
    total_w = total_steps * (dot_r * 2) + (total_steps - 1) * (gap - dot_r * 2)
    start_x = WIDTH // 2 - total_w // 2 + dot_r
    for i in range(total_steps):
        cx = start_x + i * gap
        if i < step_idx:
            draw.ellipse([cx - dot_r, DOTS_Y - dot_r, cx + dot_r, DOTS_Y + dot_r], fill=p)
        elif i == step_idx:
            draw.ellipse([cx - dot_r, DOTS_Y - dot_r, cx + dot_r, DOTS_Y + dot_r],
                         fill=s, outline=(255, 255, 255), width=2)
        else:
            draw.ellipse([cx - dot_r, DOTS_Y - dot_r, cx + dot_r, DOTS_Y + dot_r],
                         fill=theme["bg"], outline=theme["grid"], width=2)


def draw_counters(draw, scene, theme, global_frame, total_frames):
    counters = scene.get("counters", [])
    if not counters:
        return
    n = len(counters)
    pad = 60
    spacing = (WIDTH - 2 * pad) // max(n, 1)
    for i, c in enumerate(counters[:4]):
        cx = pad + spacing // 2 + i * spacing
        val_str = str(c.get("value", ""))
        lbl_str = str(c.get("label", ""))

        # Animated value (count up during first half of video)
        if isinstance(c.get("value"), (int, float)):
            progress = min(global_frame / (total_frames * 0.6), 1.0)
            animated_val = int(c["value"] * progress)
            val_str = f"{animated_val:,}"

        color = theme["primary"] if i % 2 == 0 else theme["secondary"]
        draw_stat_badge(draw, theme, cx, COUNTER_CY, lbl_str, val_str, color=color)


# ══════════════════════════════════════════════════════════════════════════════
# ANIMATED OBJECTS — themed creatures/icons that roam the diagram
# ══════════════════════════════════════════════════════════════════════════════

def draw_object(draw, obj_type, cx, cy, size, color, frame_idx=0):
    funcs = {
        "packet":     _draw_packet,
        "fish":       _draw_fish,
        "rocket":     _draw_rocket,
        "car":        _draw_car,
        "robot":      _draw_robot,
        "crystal":    _draw_crystal,
        "satellite":  _draw_satellite,
        "bird":       _draw_bird,
        "dragon":     _draw_dragon,
        "submarine":  _draw_submarine,
        "gear":       _draw_gear,
        "lightning":  _draw_lightning,
        "diamond":    _draw_diamond,
        "comet":      _draw_comet,
        "ufo":        _draw_ufo,
        "bug":        _draw_bug,
        "train":      _draw_train,
        "airplane":   _draw_airplane,
        "bubble":     _draw_bubble,
        "star":       _draw_star,
        "turtle":     _draw_turtle,
        "cat":        _draw_cat,
        "token":      _draw_token,
        "hexagon":    _draw_hexagon,
        "molecule":   _draw_molecule,
        "flame":      _draw_flame,
        "snowflake":  _draw_snowflake,
        "virus":      _draw_virus,
        "crown":      _draw_crown,
        "shield":     _draw_shield,
        "key":        _draw_key,
        "bolt":       _draw_bolt,
        "wave":       _draw_wave,
        "skull":      _draw_skull,
        "eye":        _draw_eye,
        "arrow":      _draw_arrow_obj,
    }
    t = frame_idx * 0.1
    fn = funcs.get(obj_type, _draw_packet)
    try:
        fn(draw, cx, cy, size, color, t)
    except Exception:
        _draw_packet(draw, cx, cy, size, color, t)


# ── Object renderers ──────────────────────────────────────────────────────────

def _draw_packet(draw, cx, cy, s, c, t):
    draw.rectangle([cx - s, cy - s // 2, cx + s, cy + s // 2], fill=c)
    draw.line([cx - s, cy - s // 2, cx + s // 2, cy], fill=(255, 255, 255), width=1)

def _draw_fish(draw, cx, cy, s, c, t):
    wobble = int(math.sin(t * 2) * s * 0.15)
    draw.ellipse([cx - s, cy - s // 2 + wobble, cx + s // 3, cy + s // 2 + wobble], fill=c)
    pts = [cx - s, cy + wobble, cx - s - s // 2, cy - s // 2 + wobble, cx - s - s // 2, cy + s // 2 + wobble]
    draw.polygon(pts, fill=c)
    draw.ellipse([cx + s // 6 - 5, cy - 6 + wobble, cx + s // 6 + 5, cy + 4 + wobble], fill=(255, 255, 255))
    draw.ellipse([cx + s // 6 - 2, cy - 4 + wobble, cx + s // 6 + 2, cy + 2 + wobble], fill=(0, 0, 0))

def _draw_rocket(draw, cx, cy, s, c, t):
    bob = int(math.sin(t) * 4)
    pts = [(cx, cy - s - bob), (cx - s // 2, cy + s // 2 - bob), (cx + s // 2, cy + s // 2 - bob)]
    draw.polygon(pts, fill=c)
    flame_c = (255, 200, 50)
    draw.ellipse([cx - s // 4, cy + s // 2 - bob, cx + s // 4, cy + s - bob], fill=flame_c)

def _draw_car(draw, cx, cy, s, c, t):
    draw.rectangle([cx - s, cy - s // 3, cx + s, cy + s // 3], fill=c)
    draw.rectangle([cx - s // 2, cy - s // 2, cx + s // 2, cy - s // 3 + 2], fill=lerp_color(c, (180, 230, 255), 0.5))
    for wx in [cx - s // 2, cx + s // 2]:
        draw.ellipse([wx - s // 4, cy + s // 3 - s // 4, wx + s // 4, cy + s // 3 + s // 4], fill=(30, 30, 30))

def _draw_robot(draw, cx, cy, s, c, t):
    bob = int(math.sin(t) * 3)
    draw.rectangle([cx - s // 2, cy - s + bob, cx + s // 2, cy - s // 3 + bob], fill=c)
    draw.rectangle([cx - s // 2, cy - s // 3 + bob, cx + s // 2, cy + s // 2 + bob], fill=lerp_color(c, (80, 80, 80), 0.4))
    pulse = int((math.sin(t * 3) + 1) * 127)
    draw.ellipse([cx - 8, cy - s + 10 + bob, cx + 8, cy - s + 26 + bob], fill=(pulse, 255 - pulse, 100))

def _draw_crystal(draw, cx, cy, s, c, t):
    spin = t * 0.5
    pts = []
    for i in range(6):
        angle = spin + i * math.pi / 3
        r = s if i % 2 == 0 else s // 2
        pts.append((cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle))))
    draw.polygon(pts, fill=lerp_color(c, (255, 255, 255), 0.3), outline=c)

def _draw_satellite(draw, cx, cy, s, c, t):
    draw.rectangle([cx - 4, cy - 4, cx + 4, cy + 4], fill=c)
    draw.rectangle([cx - s, cy - 3, cx - 5, cy + 3], fill=lerp_color(c, (80, 80, 80), 0.3))
    draw.rectangle([cx + 5, cy - 3, cx + s, cy + 3], fill=lerp_color(c, (80, 80, 80), 0.3))

def _draw_bird(draw, cx, cy, s, c, t):
    flap = int(math.sin(t * 4) * s // 3)
    draw.arc([cx - s, cy - flap, cx, cy + flap], 200, 340, fill=c, width=3)
    draw.arc([cx, cy - flap, cx + s, cy + flap], 200, 340, fill=c, width=3)

def _draw_dragon(draw, cx, cy, s, c, t):
    body_pts = [(cx, cy - s), (cx - s, cy + s // 2), (cx + s, cy + s // 2)]
    draw.polygon(body_pts, fill=c)
    draw.polygon([(cx - s // 2, cy - s // 2), (cx - s, cy - s), (cx, cy - s // 4)],
                 fill=lerp_color(c, (255, 100, 0), 0.5))
    draw.polygon([(cx + s // 2, cy - s // 2), (cx + s, cy - s), (cx, cy - s // 4)],
                 fill=lerp_color(c, (255, 100, 0), 0.5))

def _draw_submarine(draw, cx, cy, s, c, t):
    draw.ellipse([cx - s, cy - s // 3, cx + s, cy + s // 3], fill=c)
    draw.rectangle([cx + s // 3, cy - 8, cx + s + s // 3, cy + 8], fill=lerp_color(c, (60, 60, 60), 0.5))
    draw.ellipse([cx - s // 3 - 8, cy - 8, cx - s // 3 + 8, cy + 8], fill=(180, 230, 255))

def _draw_gear(draw, cx, cy, s, c, t):
    angle = t * 0.5
    teeth = 8
    for i in range(teeth):
        a = angle + i * 2 * math.pi / teeth
        ox1 = cx + int((s - 8) * math.cos(a))
        oy1 = cy + int((s - 8) * math.sin(a))
        ox2 = cx + int((s + 6) * math.cos(a + math.pi / teeth))
        oy2 = cy + int((s + 6) * math.sin(a + math.pi / teeth))
        draw.line([ox1, oy1, ox2, oy2], fill=c, width=6)
    draw.ellipse([cx - s + 8, cy - s + 8, cx + s - 8, cy + s - 8], fill=lerp_color(c, (20, 20, 20), 0.6), outline=c)

def _draw_lightning(draw, cx, cy, s, c, t):
    pts = [(cx + s // 3, cy - s), (cx - s // 4, cy), (cx + s // 4, cy), (cx - s // 3, cy + s)]
    draw.line(pts, fill=c, width=5)
    draw.line(pts, fill=(255, 255, 200), width=2)

def _draw_diamond(draw, cx, cy, s, c, t):
    pts = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
    draw.polygon(pts, fill=lerp_color(c, (255, 255, 255), 0.4), outline=c)
    draw.line([(cx, cy - s), (cx, cy + s)], fill=lerp_color(c, (255, 255, 255), 0.6), width=2)

def _draw_comet(draw, cx, cy, s, c, t):
    drift = int(math.sin(t) * 10)
    draw.ellipse([cx - s // 3, cy - s // 3 + drift, cx + s // 3, cy + s // 3 + drift], fill=c)
    for i in range(1, 5):
        tail_c = lerp_color(c, (0, 0, 0), i * 0.22)
        draw.line([cx - i * 14, cy + i * 8 + drift, cx, cy + drift], fill=tail_c, width=max(1, 5 - i))

def _draw_ufo(draw, cx, cy, s, c, t):
    hover = int(math.sin(t * 0.8) * 6)
    draw.ellipse([cx - s, cy - s // 4 + hover, cx + s, cy + s // 4 + hover], fill=c)
    draw.ellipse([cx - s // 2, cy - s // 2 + hover, cx + s // 2, cy + hover], fill=lerp_color(c, (200, 240, 255), 0.5))
    beam_c = lerp_color(c, (255, 255, 100), 0.5)
    draw.polygon([(cx - s // 2, cy + s // 4 + hover), (cx + s // 2, cy + s // 4 + hover),
                  (cx + s // 3, cy + s + hover), (cx - s // 3, cy + s + hover)], fill=(*beam_c[:3],))

def _draw_bug(draw, cx, cy, s, c, t):
    draw.ellipse([cx - s // 2, cy - s, cx + s // 2, cy], fill=c)
    draw.ellipse([cx - s // 2, cy - s // 4, cx + s // 2, cy + s // 2], fill=lerp_color(c, (40, 40, 40), 0.4))
    for i, (ox, oy) in enumerate([(-s, -s // 4), (-s + 8, s // 4), (s, -s // 4), (s - 8, s // 4)]):
        draw.line([cx, cy, cx + ox, cy + oy], fill=c, width=2)

def _draw_train(draw, cx, cy, s, c, t):
    draw.rectangle([cx - s, cy - s // 3, cx + s, cy + s // 3], fill=c)
    draw.rectangle([cx + s // 2, cy - s // 2, cx + s, cy - s // 3 + 2], fill=lerp_color(c, (60, 60, 60), 0.5))
    for wx in [cx - s // 2, cx + s // 2]:
        draw.ellipse([wx - 8, cy + s // 3 - 8, wx + 8, cy + s // 3 + 8], fill=(30, 30, 30))

def _draw_airplane(draw, cx, cy, s, c, t):
    pts = [(cx, cy - s // 3), (cx + s, cy), (cx, cy + s // 4), (cx - s // 2, cy)]
    draw.polygon(pts, fill=c)
    draw.polygon([(cx - s // 4, cy - s // 8), (cx - s // 2, cy - s // 2),
                  (cx + s // 4, cy - s // 8)], fill=lerp_color(c, (80, 80, 80), 0.3))

def _draw_bubble(draw, cx, cy, s, c, t):
    r = s + int(math.sin(t) * 4)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, fill=None, width=3)
    draw.ellipse([cx - r // 3, cy - r // 2, cx, cy - r // 4], outline=lerp_color(c, (255, 255, 255), 0.6), fill=None)

def _draw_star(draw, cx, cy, s, c, t):
    spin = t * 0.3
    for i in range(5):
        a_out = spin + i * 2 * math.pi / 5 - math.pi / 2
        a_in  = spin + (i + 0.5) * 2 * math.pi / 5 - math.pi / 2
        ox = cx + int(s * math.cos(a_out))
        oy = cy + int(s * math.sin(a_out))
        ix = cx + int(s // 2 * math.cos(a_in))
        iy = cy + int(s // 2 * math.sin(a_in))
        next_a = spin + (i + 1) * 2 * math.pi / 5 - math.pi / 2
        nx = cx + int(s * math.cos(next_a))
        ny = cy + int(s * math.sin(next_a))
        draw.polygon([(cx, cy), (ox, oy), (ix, iy)], fill=c)
        draw.polygon([(cx, cy), (ix, iy), (nx, ny)], fill=c)

def _draw_turtle(draw, cx, cy, s, c, t):
    draw.ellipse([cx - s // 2, cy - s // 3, cx + s // 2, cy + s // 3], fill=c)
    draw.ellipse([cx - s // 2 + 4, cy - s // 3 + 4, cx + s // 2 - 4, cy + s // 3 - 4],
                 fill=lerp_color(c, (40, 80, 40), 0.4))
    draw.ellipse([cx - 8, cy - s // 2 - 8, cx + 8, cy - s // 2 + 8], fill=lerp_color(c, (200, 200, 0), 0.4))

def _draw_cat(draw, cx, cy, s, c, t):
    draw.ellipse([cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2], fill=c)
    draw.polygon([(cx - s // 2, cy - s // 2), (cx - s // 2 - 10, cy - s), (cx - s // 4, cy - s // 2)], fill=c)
    draw.polygon([(cx + s // 2, cy - s // 2), (cx + s // 2 + 10, cy - s), (cx + s // 4, cy - s // 2)], fill=c)

def _draw_token(draw, cx, cy, s, c, t):
    spin = t * 0.4
    pts = [(cx + int(s * math.cos(spin + i * 2 * math.pi / 6)),
            cy + int(s * math.sin(spin + i * 2 * math.pi / 6))) for i in range(6)]
    draw.polygon(pts, fill=lerp_color(c, (255, 200, 0), 0.3), outline=c)
    draw.ellipse([cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2], fill=c)

def _draw_hexagon(draw, cx, cy, s, c, t):
    spin = t * 0.2
    pts = [(cx + int(s * math.cos(spin + i * math.pi / 3)),
            cy + int(s * math.sin(spin + i * math.pi / 3))) for i in range(6)]
    draw.polygon(pts, outline=c, fill=lerp_color(c, (0, 0, 0), 0.7))

def _draw_molecule(draw, cx, cy, s, c, t):
    spin = t * 0.3
    for i in range(3):
        a = spin + i * 2 * math.pi / 3
        ax = cx + int(s * math.cos(a))
        ay = cy + int(s * math.sin(a))
        draw.ellipse([ax - 8, ay - 8, ax + 8, ay + 8], fill=c)
        draw.line([cx, cy, ax, ay], fill=lerp_color(c, (80, 80, 80), 0.4), width=3)
    draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=lerp_color(c, (255, 255, 255), 0.4))

def _draw_flame(draw, cx, cy, s, c, t):
    flicker = int(math.sin(t * 4) * 8)
    pts = [(cx, cy - s - flicker), (cx - s // 2, cy), (cx + s // 2, cy)]
    draw.polygon(pts, fill=c)
    inner = lerp_color(c, (255, 255, 200), 0.5)
    pts2 = [(cx, cy - s // 2 - flicker), (cx - s // 4, cy), (cx + s // 4, cy)]
    draw.polygon(pts2, fill=inner)

def _draw_snowflake(draw, cx, cy, s, c, t):
    spin = t * 0.2
    for i in range(6):
        a = spin + i * math.pi / 3
        ex = cx + int(s * math.cos(a))
        ey = cy + int(s * math.sin(a))
        draw.line([cx, cy, ex, ey], fill=c, width=2)

def _draw_virus(draw, cx, cy, s, c, t):
    draw.ellipse([cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2], fill=c)
    for i in range(8):
        a = t * 0.2 + i * math.pi / 4
        sx = cx + int(s // 2 * math.cos(a))
        sy = cy + int(s // 2 * math.sin(a))
        ex = cx + int(s * math.cos(a))
        ey = cy + int(s * math.sin(a))
        draw.line([sx, sy, ex, ey], fill=c, width=3)
        draw.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill=lerp_color(c, (255, 100, 100), 0.4))

def _draw_crown(draw, cx, cy, s, c, t):
    pts = [(cx - s, cy + s // 3), (cx - s, cy - s // 2), (cx - s // 3, cy - s // 6),
           (cx, cy - s), (cx + s // 3, cy - s // 6), (cx + s, cy - s // 2), (cx + s, cy + s // 3)]
    draw.polygon(pts, fill=c)

def _draw_shield(draw, cx, cy, s, c, t):
    pts = [(cx, cy + s), (cx - s, cy - s // 3), (cx - s, cy - s), (cx + s, cy - s), (cx + s, cy - s // 3)]
    draw.polygon(pts, fill=lerp_color(c, (30, 30, 30), 0.5), outline=c)

def _draw_key(draw, cx, cy, s, c, t):
    spin = t * 0.3
    draw.ellipse([cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2], outline=c, fill=None, width=4)
    draw.line([cx, cy + s // 2, cx, cy + s], fill=c, width=5)
    draw.line([cx, cy + s * 3 // 4, cx + s // 4, cy + s * 3 // 4], fill=c, width=4)

def _draw_bolt(draw, cx, cy, s, c, t):
    pts = [(cx + s // 3, cy - s), (cx - s // 3, cy - s // 10),
           (cx + s // 5, cy - s // 10), (cx - s // 3, cy + s)]
    draw.polygon(pts, fill=c)
    draw.polygon(pts, outline=lerp_color(c, (255, 255, 255), 0.5))

def _draw_wave(draw, cx, cy, s, c, t):
    pts = []
    for px in range(-s, s + 1, 4):
        wave_y = cy + int(math.sin((px * 0.12) + t) * s // 3)
        pts.append((cx + px, wave_y))
    if len(pts) >= 2:
        draw.line(pts, fill=c, width=4)

def _draw_skull(draw, cx, cy, s, c, t):
    draw.ellipse([cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 5], fill=c)
    eye_c = (20, 20, 20)
    draw.ellipse([cx - s // 3 - 6, cy - s // 4 - 6, cx - s // 3 + 6, cy - s // 4 + 6], fill=eye_c)
    draw.ellipse([cx + s // 3 - 6, cy - s // 4 - 6, cx + s // 3 + 6, cy - s // 4 + 6], fill=eye_c)
    draw.rectangle([cx - s // 3, cy + s // 5, cx + s // 3, cy + s // 2], fill=c)
    for tx in range(cx - s // 3 + 8, cx + s // 3, 18):
        draw.line([tx, cy + s // 5, tx, cy + s // 2], fill=eye_c, width=3)

def _draw_eye(draw, cx, cy, s, c, t):
    draw.ellipse([cx - s, cy - s // 3, cx + s, cy + s // 3], fill=(20, 20, 20), outline=c, width=3)
    pupil_x = cx + int(math.sin(t * 0.5) * s // 3)
    draw.ellipse([pupil_x - s // 3, cy - s // 3, pupil_x + s // 3, cy + s // 3], fill=c)
    draw.ellipse([pupil_x - s // 6, cy - s // 6, pupil_x + s // 6, cy + s // 6], fill=(0, 0, 0))

def _draw_arrow_obj(draw, cx, cy, s, c, t):
    bob = int(math.sin(t * 2) * 6)
    pts = [(cx - s, cy + 8 + bob), (cx + s // 3, cy + 8 + bob),
           (cx + s // 3, cy - s // 2 + bob), (cx + s, cy + bob), (cx + s // 3, cy + s // 2 + bob),
           (cx + s // 3, cy - 8 + bob), (cx - s, cy - 8 + bob)]
    draw.polygon(pts, fill=c)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE CLASS
# ══════════════════════════════════════════════════════════════════════════════

class TechVisualEngine:
    def __init__(self, obj_a: str, obj_b: str, theme: dict = None):
        self.obj_a = obj_a
        self.obj_b = obj_b
        self.theme = theme or THEMES.get("QUANTUM", list(THEMES.values())[0])

    # ── render_frame ─────────────────────────────────────────────────────────
    def render_frame(self, scene: dict, step_idx: int, step_progress: float,
                     global_frame: int, total_steps: int) -> Image.Image:
        img  = Image.new("RGB", (WIDTH, HEIGHT), color=self.theme["bg"])
        draw = ImageDraw.Draw(img)
        theme = self.theme

        # 1. Background (grid / pattern)
        _draw_background(draw, theme, global_frame)

        # 2. Particles (behind everything)
        _draw_particles(draw, theme, global_frame)

        # 3. Connections between nodes
        nodes = scene.get("nodes", [])
        paths = scene.get("paths", [])
        n_frames_per_step = 360  # 12 s per step
        active_paths = self._active_paths_for_step(paths, step_idx, total_steps)
        for pi, path in enumerate(paths):
            from_idx = path.get("from", 0)
            to_idx   = path.get("to", 1)
            if from_idx < len(nodes) and to_idx < len(nodes):
                n1 = nodes[from_idx]
                n2 = nodes[to_idx]
                is_active = pi in active_paths
                beam_progress = step_progress if is_active else 0.0
                draw_connection_beam(draw, theme, n1["x"], n1["y"], n2["x"], n2["y"],
                                     active=is_active, progress=beam_progress)

        # 4. Nodes
        highlighted = self._highlighted_nodes(active_paths, paths)
        for ni, node in enumerate(nodes):
            color = theme["primary"] if ni % 2 == 0 else theme["secondary"]
            if ni % 3 == 2:
                color = theme["tertiary"]
            is_active = ni in highlighted
            draw_node(draw, theme, node["x"], node["y"],
                      node.get("r", 58), node.get("label", ""),
                      color=color, is_active=is_active,
                      sublabel=node.get("sublabel", ""))

        # 5. Roaming objects
        self._draw_roaming_objects(draw, scene, step_idx, step_progress, global_frame)

        # 6. Game mechanic overlay (boss health bar, XP meter, damage numbers)
        self._draw_game_overlay(draw, scene, step_idx, step_progress, global_frame, total_steps)

        # 7. Counters
        total_frames = total_steps * n_frames_per_step
        draw_counters(draw, scene, theme, global_frame, total_frames)

        # 8. Header
        draw_header(draw, scene, theme)

        # 9. Caption
        captions = scene.get("captions", scene.get("caption_steps", []))
        if captions and step_idx < len(captions):
            caption = captions[step_idx]
        else:
            caption = scene.get("hook", "")
        draw_caption(draw, caption, theme, step_progress)

        # 10. Step dots
        draw_step_indicator(draw, step_idx, total_steps, theme)

        return img

    def _draw_game_overlay(self, draw, scene, step_idx, step_progress, global_frame, total_steps):
        """Render game-mechanic UI elements: boss bar, XP, damage pops."""
        theme  = self.theme
        mech   = scene.get("game_mechanic", "")  # "boss_fight", "skill_tree", "xp_grind", "quest", "raid"

        if mech == "boss_fight":
            # Boss HP bar at top of diagram zone
            boss_hp_pct = max(0.0, 1.0 - step_idx / max(total_steps - 1, 1))
            boss_hp_pct = boss_hp_pct * (1.0 - step_progress / total_steps)
            color = lerp_color((220, 30, 30), (50, 200, 50), boss_hp_pct)
            # Draw boss HP bar
            bar_x, bar_y = 60, DIAGRAM_TOP + 12
            bar_w, bar_h = WIDTH - 120, 36
            draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                                    radius=8, fill=lerp_color(theme["bg"], (200, 0, 0), 0.1),
                                    outline=(180, 0, 0), width=2)
            fill_w = int((bar_w - 4) * boss_hp_pct)
            if fill_w > 0:
                draw.rounded_rectangle([bar_x + 2, bar_y + 2, bar_x + 2 + fill_w, bar_y + bar_h - 2],
                                        radius=6, fill=color)
            fnt = get_font(20, bold=True)
            boss_label = scene.get("boss_name", "BOSS") + f"  HP: {int(boss_hp_pct * 100)}%"
            draw.text((WIDTH // 2, bar_y + bar_h // 2), boss_label, font=fnt,
                      fill=(255, 220, 220), anchor="mm")
            # Damage number popup on active steps
            if step_progress > 0.3 and step_idx > 0:
                dmg_val = scene.get("damage_values", ["−25 DMG"])[min(step_idx - 1, 4)]
                dmg_x = 300 + (step_idx * 87) % (WIDTH - 400)
                dmg_y = DIAGRAM_TOP + 80 + (step_idx * 43) % 200
                draw_damage_number(draw, theme, dmg_x, dmg_y, dmg_val,
                                   color=lerp_color((255, 80, 80), (255, 200, 0), step_progress))

        elif mech == "skill_tree":
            # XP bar showing mastery accumulation
            mastery = (step_idx + step_progress) / total_steps
            draw_xp_bar(draw, theme, 60, DIAGRAM_TOP + 8, WIDTH - 120, 34, mastery,
                        label="MASTERY")

        elif mech == "xp_grind":
            # Show XP gaining with each step
            xp_gained = step_idx * 250 + int(step_progress * 250)
            total_xp  = total_steps * 250
            pct = xp_gained / total_xp
            draw_xp_bar(draw, theme, 60, DIAGRAM_TOP + 8, WIDTH - 120, 34, pct,
                        label=f"+{xp_gained} XP")

        elif mech == "quest":
            # Quest progress checkboxes
            fnt = get_font(22, bold=True)
            quest_steps = scene.get("quest_steps", [])[:6]
            y_start = DIAGRAM_TOP + 14
            for qi, qstep in enumerate(quest_steps[:min(step_idx + 1, len(quest_steps))]):
                done = qi < step_idx
                color = theme["primary"] if done else theme["text_dim"]
                mark = "✓ " if done else "▶ "
                draw.text((80, y_start + qi * 38), mark + qstep, font=fnt, fill=color)

        elif mech == "raid":
            # Raid timer countdown
            total_secs = 120  # 2-minute video
            elapsed = global_frame / FPS
            remaining = max(0, total_secs - elapsed)
            m = int(remaining // 60)
            s = int(remaining % 60)
            timer_text = f"⏱ {m:02d}:{s:02d}"
            fnt = get_font(26, bold=True)
            draw.text((WIDTH - 80, DIAGRAM_TOP + 28), timer_text, font=fnt,
                      fill=lerp_color(theme["secondary"], (255, 60, 60), max(0, 1 - remaining / 30)),
                      anchor="rm")

    def _draw_roaming_objects(self, draw, scene, step_idx, step_progress, global_frame):
        random.seed(step_idx * 17 + 42)
        n_roamers = 3
        nodes = scene.get("nodes", [])
        theme = self.theme

        if nodes:
            cx_avg = sum(n["x"] for n in nodes) // len(nodes)
            cy_avg = sum(n["y"] for n in nodes) // len(nodes)
        else:
            cx_avg = WIDTH // 2
            cy_avg = (DIAGRAM_TOP + DIAGRAM_BOT) // 2

        for i in range(n_roamers):
            obj     = self.obj_a if i % 2 == 0 else self.obj_b
            orbit_r = 110 + i * 65
            speed   = 3 + i * 1.5
            angle   = math.radians((global_frame * speed + i * 120) % 360)
            ox = cx_avg + int(math.cos(angle) * orbit_r)
            oy = cy_avg + int(math.sin(angle) * orbit_r * 0.6)
            ox = max(60, min(WIDTH - 60, ox))
            oy = max(DIAGRAM_TOP + 55, min(DIAGRAM_BOT - 55, oy))
            c  = lerp_color(theme["primary"], theme["secondary"], i * 0.45)
            draw_object(draw, obj, ox, oy, 30, c, frame_idx=global_frame)

    def _active_paths_for_step(self, paths, step_idx, total_steps):
        if not paths:
            return set()
        n = len(paths)
        active_count = max(1, (step_idx + 1) * n // max(total_steps, 1))
        return set(range(min(active_count, n)))

    def _highlighted_nodes(self, active_path_indices, paths):
        highlighted = set()
        for i in active_path_indices:
            if i < len(paths):
                highlighted.add(paths[i]["from"])
                highlighted.add(paths[i]["to"])
        return highlighted

    # ── render_thumbnail ─────────────────────────────────────────────────────
    def render_thumbnail(self, scene: dict) -> Image.Image:
        img  = Image.new("RGB", (WIDTH, HEIGHT), color=self.theme["bg"])
        draw = ImageDraw.Draw(img)
        _draw_background(draw, self.theme, 60)
        _draw_particles(draw, self.theme, 60)
        draw_header(draw, scene, self.theme)
        nodes = scene.get("nodes", [])
        for ni, node in enumerate(nodes[:5]):
            color = self.theme["primary"] if ni % 2 == 0 else self.theme["secondary"]
            draw_node(draw, self.theme, node["x"], node["y"],
                      node.get("r", 58) + 8, node.get("label", ""),
                      color=color, is_active=(ni == 0))
        return img
