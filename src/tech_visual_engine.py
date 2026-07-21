"""
Tech Visual Engine — Game-Style Dark Neon Renderer
Renders animated frames for tech concept videos.
Objects: fish, rocket, car, robot, crystal, etc. animate through scenes.
Style: Dark background, neon glow, game UI, counters, captions.

LAYOUT ZONES (1080 × 1920):
  Header  :  y = 0   → 295   (badge + title + subtitle + hook)
  Diagram :  y = 295 → 1435  (nodes, connections, roaming objects)
  Footer  :  y = 1435→ 1920  (counters + caption + step-dots)
All elements are strictly clamped to their zones — no overlaps possible.
"""

import math, random, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH  = 1080
HEIGHT = 1920
FPS    = 30

# ── Layout constants — change here, changes everywhere ───────────────────────
HEADER_TOP    = 0
BADGE_CY      = 68       # series badge center-y
BADGE_H       = 38       # badge pill height
TITLE_TOP     = 100      # title block top (auto-size fits here)
TITLE_MAX_BOT = 208      # title block max bottom (2 lines max)
SUBTITLE_CY   = 235      # subtitle center-y
HOOK_TOP      = 258      # hook pill top
HOOK_BOT      = 302      # hook pill bottom  → always 44px tall
DIAGRAM_TOP   = 310      # diagram zone top  (nodes clamped ≥ this)
DIAGRAM_BOT   = 1430     # diagram zone bottom (nodes clamped ≤ this)
COUNTER_CY    = 1490     # counter badges center-y
COUNTER_H     = 72       # counter badge height
CAPTION_TOP   = 1572     # caption pill top
CAPTION_BOT   = 1845     # caption pill bottom (≤ 273px = max 4 lines)
DOTS_Y        = 1872     # step-indicator dots center-y
FOOTER_BOT    = 1920

# ── Palette ──────────────────────────────────────────────────────────────────
BG        = (8,  12,  26)
GRID      = (20, 30,  55)
TEXT_W    = (245,250,255)
TEXT_DIM  = (100,120,160)
NEON = {
    "blue":   (56,  189, 248),
    "purple": (192, 132, 252),
    "green":  (52,  211, 153),
    "gold":   (251, 191,  36),
    "red":    (248,  113, 113),
    "cyan":   (34,  211, 238),
    "orange": (251, 146,  60),
    "pink":   (244, 114, 182),
}

def hex2rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (56, 189, 248)

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ── Font helpers ─────────────────────────────────────────────────────────────
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
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
    else:
        candidates = [
            "assets/fonts/Montserrat-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
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


def fit_font(text, max_width, max_size=64, min_size=20, bold=False):
    """Return the largest font that fits `text` in `max_width` pixels."""
    for size in range(max_size, min_size - 1, -2):
        fnt = get_font(size, bold)
        try:
            w = fnt.getlength(text)
        except:
            w = len(text) * size * 0.6
        if w <= max_width:
            return fnt, size
    return get_font(min_size, bold), min_size


def wrap_text(text, fnt, max_width):
    """Word-wrap text into lines that each fit max_width. Returns list of strings."""
    words  = text.split()
    lines  = []
    line   = []
    for word in words:
        candidate = " ".join(line + [word])
        try:
            w = fnt.getlength(candidate)
        except:
            w = len(candidate) * 12
        if w > max_width and line:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))
    return lines or [""]


# ══════════════════════════════════════════════════════════════════════════════
# OBJECT DRAWING — 30+ unique animated shapes
# ══════════════════════════════════════════════════════════════════════════════

def draw_object(draw, obj_type, cx, cy, size, color_rgb, frame_idx=0):
    """Draw any object type at (cx,cy). size ≈ 28-60px."""
    funcs = {
        "fish":       _draw_fish,
        "rocket":     _draw_rocket,
        "car":        _draw_car,
        "robot":      _draw_robot,
        "crystal":    _draw_crystal,
        "satellite":  _draw_satellite,
        "packet":     _draw_packet,
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
        "arrow":      _draw_arrow_obj,
        "flame":      _draw_flame,
        "snowflake":  _draw_snowflake,
        "leaf":       _draw_leaf,
        "virus":      _draw_virus,
        "drop":       _draw_drop,
        "crown":      _draw_crown,
        "shield":     _draw_shield,
        "key":        _draw_key,
        "lock":       _draw_lock,
        "eye":        _draw_eye,
        "bolt":       _draw_bolt,
        "wave":       _draw_wave,
    }
    t  = frame_idx * 0.1
    fn = funcs.get(obj_type, _draw_packet)
    try:
        fn(draw, cx, cy, size, color_rgb, t)
    except Exception:
        _draw_packet(draw, cx, cy, size, color_rgb, t)


# ── Individual object renderers ───────────────────────────────────────────────

def _draw_fish(draw, cx, cy, s, c, t):
    wobble = int(math.sin(t * 2) * s * 0.15)
    draw.ellipse([cx-s, cy-s//2+wobble, cx+s//3, cy+s//2+wobble], fill=c, outline=TEXT_W, width=2)
    pts = [cx-s, cy+wobble, cx-s-s//2, cy-s//2+wobble, cx-s-s//2, cy+s//2+wobble]
    draw.polygon(pts, fill=c)
    draw.ellipse([cx+s//6-6, cy-8+wobble, cx+s//6+6, cy+4+wobble], fill=TEXT_W)
    draw.ellipse([cx+s//6-3, cy-6+wobble, cx+s//6+3, cy+2+wobble], fill=(0,0,0))
    draw.polygon([cx-s//3, cy-s//2+wobble, cx, cy+wobble, cx-s//3, cy+wobble],
                 fill=lerp_color(c,(255,255,255),0.4))

def _draw_rocket(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s//3, cy-s, cx+s//3, cy+s//2], fill=c, outline=TEXT_W, width=2)
    pts = [cx-s//3, cy-s, cx+s//3, cy-s, cx, cy-s-s//2]
    draw.polygon(pts, fill=lerp_color(c, TEXT_W, 0.5))
    draw.polygon([cx-s//3, cy+s//4, cx-s//3-s//2, cy+s//2, cx-s//3, cy+s//2], fill=c)
    draw.polygon([cx+s//3, cy+s//4, cx+s//3+s//2, cy+s//2, cx+s//3, cy+s//2], fill=c)
    glow = NEON["gold"]
    for r in range(3):
        ey = cy + s//2 + r*6
        w2 = max(2, s//4 - r*2)
        draw.ellipse([cx-w2, ey, cx+w2, ey+s//3], fill=lerp_color(glow, BG, r*0.3))

def _draw_car(draw, cx, cy, s, c, t):
    draw.rounded_rectangle([cx-s, cy-s//3, cx+s, cy+s//3], radius=s//5,
                            fill=c, outline=TEXT_W, width=2)
    draw.rounded_rectangle([cx-s//2, cy-s//3-s//3, cx+s//2, cy-s//3],
                            radius=s//8, fill=lerp_color(c,TEXT_W,0.3))
    for wx in [cx-s//2, cx+s//2]:
        draw.ellipse([wx-s//4, cy+s//4, wx+s//4, cy+s//4+s//2],
                     fill=(30,30,30), outline=TEXT_W, width=2)
        draw.ellipse([wx-s//8, cy+s//4+s//8, wx+s//8, cy+s//4+s//2-s//8], fill=TEXT_DIM)
    draw.ellipse([cx+s-8, cy-s//8, cx+s+4, cy+s//8], fill=NEON["gold"])

def _draw_robot(draw, cx, cy, s, c, t):
    blink = int(t * 3) % 4 == 0
    draw.rounded_rectangle([cx-s//2, cy, cx+s//2, cy+s], radius=8,
                            fill=c, outline=TEXT_W, width=2)
    draw.rounded_rectangle([cx-s//3, cy-s//2, cx+s//3, cy], radius=6,
                            fill=lerp_color(c,BG,0.3), outline=TEXT_W, width=2)
    eye_c = NEON["gold"] if not blink else NEON["red"]
    draw.ellipse([cx-s//5-6, cy-s//3-6, cx-s//5+6, cy-s//3+6], fill=eye_c)
    draw.ellipse([cx+s//5-6, cy-s//3-6, cx+s//5+6, cy-s//3+6], fill=eye_c)
    draw.line([cx, cy-s//2, cx, cy-s//2-s//3], fill=TEXT_W, width=3)
    draw.ellipse([cx-6, cy-s//2-s//3-6, cx+6, cy-s//2-s//3+6], fill=NEON["red"])
    draw.rectangle([cx-s//2-s//4, cy+s//6, cx-s//2, cy+s//2], fill=c, outline=TEXT_W, width=1)
    draw.rectangle([cx+s//2, cy+s//6, cx+s//2+s//4, cy+s//2], fill=c, outline=TEXT_W, width=1)

def _draw_crystal(draw, cx, cy, s, c, t):
    glow = lerp_color(c, TEXT_W, 0.4)
    pts  = [cx, cy-s, cx+s//2, cy-s//3, cx+s//2, cy+s//2,
            cx, cy+s, cx-s//2, cy+s//2, cx-s//2, cy-s//3]
    draw.polygon(pts, fill=glow, outline=TEXT_W, width=2)
    inner = [cx, cy-s//2, cx+s//4, cy, cx, cy+s//2, cx-s//4, cy]
    draw.polygon(inner, fill=c)
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle + t*20)
        px, py = cx + int(math.cos(rad)*s*0.8), cy + int(math.sin(rad)*s*0.8)
        draw.ellipse([px-4, py-4, px+4, py+4], fill=TEXT_W)

def _draw_satellite(draw, cx, cy, s, c, t):
    draw.rounded_rectangle([cx-s//3, cy-s//4, cx+s//3, cy+s//4],
                            radius=6, fill=c, outline=TEXT_W, width=2)
    draw.rectangle([cx-s-s//3, cy-s//8, cx-s//3, cy+s//8], fill=NEON["blue"], outline=TEXT_W, width=1)
    draw.rectangle([cx+s//3, cy-s//8, cx+s+s//3, cy+s//8], fill=NEON["blue"], outline=TEXT_W, width=1)
    draw.arc([cx-s//4, cy-s, cx+s//4, cy-s//2], 180, 0, fill=TEXT_W, width=3)
    draw.line([cx, cy-s//2, cx, cy-s//4], fill=TEXT_W, width=2)
    if int(t*2) % 2:
        draw.ellipse([cx-5, cy-5, cx+5, cy+5], fill=NEON["red"])

def _draw_packet(draw, cx, cy, s, c, t):
    pulse = int(math.sin(t*3)*4)
    r = s // 2 + pulse
    draw.rounded_rectangle([cx-r, cy-r, cx+r, cy+r], radius=8,
                            fill=lerp_color(c, BG, 0.2), outline=c, width=3)
    for i in range(3):
        y = cy - r//2 + i*(r//2)
        w = r - 10 - i*6
        if w > 0:
            draw.rectangle([cx-w, y, cx+w, y+4], fill=lerp_color(c, TEXT_W, 0.4))

def _draw_bird(draw, cx, cy, s, c, t):
    flap = math.sin(t * 4) * s * 0.5
    draw.arc([cx-s-int(flap), cy-int(flap), cx, cy], 200, 340, fill=c, width=4)
    draw.arc([cx, cy-int(flap), cx+s+int(flap), cy], 200, 340, fill=c, width=4)
    draw.ellipse([cx-s//4, cy-s//6, cx+s//4, cy+s//4], fill=c)
    draw.polygon([cx-s//4, cy+s//4, cx-s//3, cy+s//2, cx+s//4, cy+s//4], fill=c)

def _draw_dragon(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s//2, cy-s//3, cx+s//2, cy+s//2], fill=c, outline=TEXT_W, width=2)
    draw.ellipse([cx+s//4, cy-s//2, cx+s//4+s//2, cy], fill=c, outline=TEXT_W, width=2)
    pts = [cx-s//4, cy-s//4, cx-s, cy-s, cx, cy-s//3]
    draw.polygon(pts, fill=lerp_color(c, (80,0,200), 0.5), outline=TEXT_W, width=1)
    fire_x = cx + s//2 + s//4
    for i in range(4):
        fi = NEON["gold"] if i%2==0 else NEON["orange"]
        draw.ellipse([fire_x+i*10-8, cy-s//4-8, fire_x+i*10+8, cy-s//4+8], fill=fi)
    draw.ellipse([cx+s//4+s//4-5, cy-s//3-5, cx+s//4+s//4+5, cy-s//3+5], fill=NEON["gold"])

def _draw_submarine(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s, cy-s//3, cx+s, cy+s//3], fill=c, outline=TEXT_W, width=2)
    draw.rectangle([cx-s//6, cy-s//3-s//3, cx+s//6, cy-s//3],
                   fill=lerp_color(c,TEXT_W,0.3), outline=TEXT_W, width=1)
    draw.line([cx+s//8, cy-s//3-s//3, cx+s//8, cy-s//3-s//2], fill=TEXT_W, width=3)
    draw.line([cx+s//8, cy-s//3-s//2, cx+s//4, cy-s//3-s//2], fill=TEXT_W, width=3)
    draw.ellipse([cx+s-8, cy-s//4, cx+s+8, cy+s//4], fill=NEON["gold"])
    for i in range(3):
        bx, by = cx - s - i*18, cy - s//4 - i*15
        r2 = 8 - i*2
        if r2 > 0:
            draw.ellipse([bx-r2, by-r2, bx+r2, by+r2], outline=NEON["cyan"], width=2)

def _draw_gear(draw, cx, cy, s, c, t):
    teeth = 8
    rot   = t * 30
    for i in range(teeth*2):
        angle = math.radians(i * 180/teeth + rot)
        r = s if i%2==0 else s*0.75
        x1 = cx + int(math.cos(angle)*r*0.85)
        y1 = cy + int(math.sin(angle)*r*0.85)
        x2 = cx + int(math.cos(angle)*r)
        y2 = cy + int(math.sin(angle)*r)
        draw.line([x1, y1, x2, y2], fill=c, width=6)
    draw.ellipse([cx-s*0.7, cy-s*0.7, cx+s*0.7, cy+s*0.7], outline=c, width=4)
    draw.ellipse([cx-s*0.3, cy-s*0.3, cx+s*0.3, cy+s*0.3],
                 fill=lerp_color(c,BG,0.5), outline=TEXT_W, width=2)

def _draw_lightning(draw, cx, cy, s, c, t):
    pts = [cx+s//4, cy-s, cx-s//8, cy, cx+s//4, cy, cx-s//4, cy+s]
    draw.polygon(pts, fill=NEON["gold"], outline=TEXT_W, width=2)

def _draw_diamond(draw, cx, cy, s, c, t):
    shine = lerp_color(c, TEXT_W, 0.5)
    pts   = [cx, cy-s, cx+s//2, cy, cx, cy+s, cx-s//2, cy]
    draw.polygon(pts, fill=shine, outline=TEXT_W, width=3)
    draw.polygon([cx, cy-s//2, cx+s//4, cy, cx, cy+s//2, cx-s//4, cy], fill=c)

def _draw_comet(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s//3, cy-s//3, cx+s//3, cy+s//3], fill=c, outline=TEXT_W, width=2)
    for i in range(5):
        tx = cx + (i+1)*s//3
        ty = cy + (i+1)*s//4
        r2 = s//3 - i*3
        if r2 > 2:
            draw.ellipse([tx-r2, ty-r2, tx+r2, ty+r2], fill=lerp_color(c, BG, i*0.2))

def _draw_ufo(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s, cy-s//4, cx+s, cy+s//4], fill=c, outline=TEXT_W, width=2)
    draw.arc([cx-s//2, cy-s//2, cx+s//2, cy+s//4], 180, 0, fill=NEON["cyan"], width=3)
    colors = [NEON["red"], NEON["gold"], NEON["green"]]
    for i, lc in enumerate(colors):
        lx = cx - s//2 + (i+1)*s//2
        draw.ellipse([lx-7, cy+s//6-7, lx+7, cy+s//6+7], fill=lc)
    if int(t*2)%2 == 0:
        pts = [cx-s//4, cy+s//4, cx+s//4, cy+s//4, cx+s//2, cy+s, cx-s//2, cy+s]
        try:
            draw.polygon(pts, fill=(34,211,238,40))
        except:
            draw.polygon(pts, fill=(34,211,238))

def _draw_bug(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s//3, cy, cx+s//3, cy+s//2], fill=c, outline=TEXT_W, width=2)
    draw.ellipse([cx-s//4, cy-s//2, cx+s//4, cy+s//8],
                 fill=lerp_color(c,TEXT_W,0.3), outline=TEXT_W, width=2)
    draw.ellipse([cx-s//5-5, cy-s//3-5, cx-s//5+5, cy-s//3+5], fill=NEON["red"])
    draw.ellipse([cx+s//5-5, cy-s//3-5, cx+s//5+5, cy-s//3+5], fill=NEON["red"])
    for i in range(3):
        y = cy + i*s//6
        draw.line([cx-s//3, y, cx-s//3-s//2, y-s//6], fill=c, width=3)
        draw.line([cx+s//3, y, cx+s//3+s//2, y-s//6], fill=c, width=3)
    draw.line([cx-s//6, cy-s//2, cx-s//2, cy-s], fill=c, width=2)
    draw.line([cx+s//6, cy-s//2, cx+s//2, cy-s], fill=c, width=2)
    draw.ellipse([cx-s//2-5, cy-s-5, cx-s//2+5, cy-s+5], fill=NEON["gold"])
    draw.ellipse([cx+s//2-5, cy-s-5, cx+s//2+5, cy-s+5], fill=NEON["gold"])

def _draw_train(draw, cx, cy, s, c, t):
    draw.rounded_rectangle([cx-s, cy-s//3, cx+s//2, cy+s//3], radius=8, fill=c, outline=TEXT_W, width=2)
    draw.rounded_rectangle([cx-s+s//6, cy-s//3-s//4, cx+s//6, cy-s//3], radius=4,
                            fill=lerp_color(c,TEXT_W,0.3))
    for wx in [cx-s//2, cx]:
        draw.ellipse([wx-s//5, cy+s//4, wx+s//5, cy+s//4+s//3],
                     fill=(40,40,40), outline=TEXT_W, width=2)
    draw.rectangle([cx+s//2, cy-s//6, cx+s//2+s//3, cy+s//6], fill=c, outline=TEXT_W, width=2)
    draw.ellipse([cx-s+6, cy-s//5, cx-s+22, cy+s//5], fill=NEON["gold"])

def _draw_airplane(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s, cy-s//4, cx+s//2, cy+s//4], fill=c, outline=TEXT_W, width=2)
    draw.polygon([cx-s, cy, cx-s-s//3, cy-s//3, cx-s//2, cy], fill=c)
    draw.polygon([cx-s//3, cy-s//4, cx+s//4, cy-s//4, cx+s//4, cy-s//4-s//3, cx-s//3, cy-s//4-s//6],
                 fill=lerp_color(c,TEXT_W,0.4))
    draw.polygon([cx+s//4, cy, cx+s//2, cy-s//4, cx+s//2, cy+s//4], fill=c)

def _draw_bubble(draw, cx, cy, s, c, t):
    wobble = int(math.sin(t*2)*4)
    draw.ellipse([cx-s, cy-s+wobble, cx+s, cy+s+wobble], outline=c, width=4)
    draw.ellipse([cx-s+4, cy-s+4+wobble, cx+s-4, cy+s-4+wobble],
                 outline=lerp_color(c,TEXT_W,0.3), width=2)
    draw.ellipse([cx-s//3, cy-s*0.6+wobble, cx-s//6, cy-s*0.4+wobble],
                 fill=lerp_color(c,TEXT_W,0.6))

def _draw_star(draw, cx, cy, s, c, t):
    rot   = t * 15
    n, r_out, r_in = 5, s, s*0.4
    pts   = []
    for i in range(n*2):
        angle = math.radians(i*180/n + rot - 90)
        r = r_out if i%2==0 else r_in
        pts.extend([cx+int(math.cos(angle)*r), cy+int(math.sin(angle)*r)])
    draw.polygon(pts, fill=c, outline=TEXT_W, width=2)

def _draw_turtle(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s//2, cy-s//3, cx+s//2, cy+s//3], fill=c, outline=TEXT_W, width=2)
    draw.arc([cx-s//3, cy-s//4, cx+s//3, cy+s//4], 0, 180, fill=lerp_color(c,TEXT_W,0.4), width=3)
    draw.ellipse([cx+s//2-s//4, cy-s//6, cx+s//2+s//4, cy+s//6], fill=c, outline=TEXT_W, width=2)
    for lx, ly in [(cx-s//3, cy+s//3), (cx+s//3, cy+s//3), (cx-s//3, cy-s//3), (cx+s//3, cy-s//3)]:
        draw.ellipse([lx-10, ly-8, lx+10, ly+8], fill=c)

def _draw_cat(draw, cx, cy, s, c, t):
    tail_w = math.sin(t*2)*s*0.3
    draw.ellipse([cx-s//2, cy-s//4, cx+s//2, cy+s//2], fill=c, outline=TEXT_W, width=2)
    draw.ellipse([cx-s//3, cy-s//3-s//2, cx+s//3, cy-s//3], fill=c, outline=TEXT_W, width=2)
    draw.polygon([cx-s//3, cy-s//3-s//2, cx-s//3-s//4, cy-s//3-s], fill=c)
    draw.polygon([cx+s//3, cy-s//3-s//2, cx+s//3+s//4, cy-s//3-s], fill=c)
    draw.ellipse([cx-s//5-5, cy-s//3-s//4-5, cx-s//5+5, cy-s//3-s//4+5], fill=NEON["green"])
    draw.ellipse([cx+s//5-5, cy-s//3-s//4-5, cx+s//5+5, cy-s//3-s//4+5], fill=NEON["green"])
    draw.line([cx-s//2, cy+s//4, cx-s//2+int(tail_w), cy+s], fill=c, width=5)

def _draw_token(draw, cx, cy, s, c, t):
    pulse = int(math.sin(t*3)*3)
    draw.ellipse([cx-s-pulse, cy-s-pulse, cx+s+pulse, cy+s+pulse],
                 fill=lerp_color(c, BG, 0.3), outline=c, width=4)
    draw.ellipse([cx-s+8, cy-s+8, cx+s-8, cy+s-8], outline=lerp_color(c, TEXT_W, 0.5), width=2)
    fnt = get_font(max(10, s), bold=True)
    draw.text((cx, cy), "$", font=fnt, fill=TEXT_W, anchor="mm")

def _draw_hexagon(draw, cx, cy, s, c, t):
    rot = t * 10
    pts = []
    for i in range(6):
        a = math.radians(60*i + rot)
        pts.extend([cx+int(math.cos(a)*s), cy+int(math.sin(a)*s)])
    draw.polygon(pts, fill=lerp_color(c, BG, 0.3), outline=c, width=4)

def _draw_molecule(draw, cx, cy, s, c, t):
    rot   = t * 20
    atoms = [(0,0,c,s//3),(s,-s//2,NEON["red"],s//4),(s,s//2,NEON["green"],s//4),(-s,0,NEON["gold"],s//4)]
    for ax, ay, ac, ar in atoms:
        r  = math.radians(rot)
        rx = int(ax*math.cos(r) - ay*math.sin(r))
        ry = int(ax*math.sin(r) + ay*math.cos(r))
        draw.line([cx, cy, cx+rx, cy+ry], fill=TEXT_DIM, width=3)
        draw.ellipse([cx+rx-ar, cy+ry-ar, cx+rx+ar, cy+ry+ar], fill=ac, outline=TEXT_W, width=2)

def _draw_arrow_obj(draw, cx, cy, s, c, t):
    pts = [cx-s, cy-s//3, cx, cy-s//3, cx, cy-s//2, cx+s, cy, cx, cy+s//2, cx, cy+s//3, cx-s, cy+s//3]
    draw.polygon(pts, fill=c, outline=TEXT_W, width=2)

def _draw_flame(draw, cx, cy, s, c, t):
    flicker = math.sin(t*5)*s*0.2
    for i in range(4):
        fc = [NEON["red"], NEON["orange"], NEON["gold"], TEXT_W][i]
        fs = max(4, s - i*s//5 + int(flicker))
        draw.ellipse([cx-fs//2, cy-fs*2+i*s//2, cx+fs//2, cy+i*s//4], fill=fc)

def _draw_snowflake(draw, cx, cy, s, c, t):
    rot = t * 15
    for i in range(6):
        a  = math.radians(60*i + rot)
        ex = cx + int(math.cos(a)*s)
        ey = cy + int(math.sin(a)*s)
        draw.line([cx, cy, ex, ey], fill=c, width=3)
        for j in [0.4, 0.7]:
            bx = cx + int(math.cos(a)*s*j)
            by = cy + int(math.sin(a)*s*j)
            for d in [45, -45]:
                ba = math.radians(60*i + rot + d)
                draw.line([bx, by, bx+int(math.cos(ba)*s*0.25), by+int(math.sin(ba)*s*0.25)],
                          fill=c, width=2)

def _draw_leaf(draw, cx, cy, s, c, t):
    sway = math.sin(t*2)*s*0.2
    pts  = [cx, cy-s, cx+s//2+int(sway), cy, cx, cy+s//2, cx-s//2+int(sway), cy]
    draw.polygon(pts, fill=c, outline=lerp_color(c, TEXT_W, 0.3), width=2)
    draw.line([cx, cy-s, cx, cy+s//2], fill=lerp_color(c, TEXT_W, 0.4), width=2)

def _draw_virus(draw, cx, cy, s, c, t):
    rot = t * 20
    draw.ellipse([cx-s//2, cy-s//2, cx+s//2, cy+s//2], fill=c, outline=TEXT_W, width=2)
    for i in range(8):
        a  = math.radians(45*i + rot)
        px = cx + int(math.cos(a)*s*0.8)
        py = cy + int(math.sin(a)*s*0.8)
        draw.line([cx+int(math.cos(a)*s//2), cy+int(math.sin(a)*s//2), px, py], fill=c, width=3)
        draw.ellipse([px-6, py-6, px+6, py+6], fill=NEON["red"])

def _draw_drop(draw, cx, cy, s, c, t):
    pts = [cx, cy-s, cx+s//2, cy, cx+s//2, cy+s//2, cx, cy+s, cx-s//2, cy+s//2, cx-s//2, cy]
    draw.polygon(pts, fill=c, outline=TEXT_W, width=2)
    draw.ellipse([cx-s//5, cy-s//3, cx+s//5, cy+s//6], fill=lerp_color(c, TEXT_W, 0.5))

def _draw_crown(draw, cx, cy, s, c, t):
    pts = [cx-s, cy+s//3, cx-s, cy-s//3, cx-s//2, cy+s//6,
           cx, cy-s, cx+s//2, cy+s//6, cx+s, cy-s//3, cx+s, cy+s//3]
    draw.polygon(pts, fill=NEON["gold"], outline=TEXT_W, width=2)
    for px, py in [(cx-s+s//5, cy-s//6), (cx, cy-s//4), (cx+s-s//5, cy-s//6)]:
        draw.ellipse([px-6, py-6, px+6, py+6], fill=c)

def _draw_shield(draw, cx, cy, s, c, t):
    pts = [cx-s, cy-s, cx+s, cy-s, cx+s, cy+s//3, cx, cy+s, cx-s, cy+s//3]
    draw.polygon(pts, fill=lerp_color(c, BG, 0.3), outline=c, width=4)
    draw.polygon([cx-s//2, cy-s//2, cx+s//2, cy-s//2, cx+s//2, cy, cx, cy+s//2, cx-s//2, cy],
                 outline=lerp_color(c, TEXT_W, 0.4), width=2)

def _draw_key(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s//2, cy-s//2, cx+s//2, cy+s//2], outline=c, width=5)
    draw.line([cx+s//2, cy, cx+s, cy], fill=c, width=5)
    draw.line([cx+s*0.7, cy, cx+s*0.7, cy+s//4], fill=c, width=4)
    draw.line([cx+s*0.9, cy, cx+s*0.9, cy+s//4], fill=c, width=4)

def _draw_lock(draw, cx, cy, s, c, t):
    draw.rounded_rectangle([cx-s//2, cy, cx+s//2, cy+s], radius=8, fill=c, outline=TEXT_W, width=2)
    draw.arc([cx-s//3, cy-s//2, cx+s//3, cy+s//4], 180, 0, fill=c, width=5)
    draw.ellipse([cx-8, cy+s//3, cx+8, cy+s*0.7], fill=BG, outline=TEXT_W, width=2)

def _draw_eye(draw, cx, cy, s, c, t):
    blink = max(2, int((1 - abs(math.sin(t*0.3)))*s//2))
    draw.ellipse([cx-s, cy-blink, cx+s, cy+blink], fill=(20,15,35), outline=c, width=3)
    draw.ellipse([cx-blink//2, cy-blink//2, cx+blink//2, cy+blink//2], fill=c)
    draw.ellipse([cx-blink//4, cy-blink//4, cx+blink//4, cy+blink//4], fill=(0,0,0))
    if blink > 6:
        draw.ellipse([cx-blink//6, cy-blink//2+4, cx+blink//6-4, cy-blink//4+4], fill=TEXT_W)

def _draw_bolt(draw, cx, cy, s, c, t):
    pts = [cx, cy-s, cx-s//3, cy, cx+s//4, cy, cx, cy+s]
    draw.polygon(pts, fill=NEON["gold"], outline=TEXT_W, width=2)

def _draw_wave(draw, cx, cy, s, c, t):
    pts = []
    for x in range(-s, s+1, 4):
        y = int(math.sin((x/s)*math.pi*2 + t*3)*s*0.5)
        pts.append((cx+x, cy+y))
    if len(pts) > 1:
        draw.line(pts, fill=c, width=5)


# ══════════════════════════════════════════════════════════════════════════════
# NODE DRAWING
# ══════════════════════════════════════════════════════════════════════════════

def draw_node(draw, node, highlight=False, frame_idx=0):
    # Clamp to diagram zone — never draws over header or footer
    x = max(100, min(WIDTH - 100, node["x"]))
    y = max(DIAGRAM_TOP + 50, min(DIAGRAM_BOT - 50, node["y"]))

    label = node.get("label", "")
    ntype = node.get("type", "box")
    c     = hex2rgb(node.get("color", "#38BDF8"))
    glow  = lerp_color(c, BG, 0.3)
    pulse = math.sin(frame_idx * 0.15) * 4 if highlight else 0

    w, h = 170, 76

    # Glow halo behind box when highlighted
    if highlight:
        for ex in range(1, 5):
            oc = lerp_color(c, BG, 0.4 + ex*0.12)
            draw.rounded_rectangle(
                [x-w//2-ex*4, y-h//2-ex*4, x+w//2+ex*4, y+h//2+ex*4],
                radius=20, outline=oc, width=2)

    # Box body
    draw.rounded_rectangle(
        [x-w//2+int(pulse)//2, y-h//2+int(pulse)//2,
         x+w//2-int(pulse)//2, y+h//2-int(pulse)//2],
        radius=14,
        fill=lerp_color(glow, BG, 0.5),
        outline=c if not highlight else TEXT_W,
        width=3 if highlight else 2)

    # Icon + label — both fit inside the box (box is 76px tall → icon at -12, label at +16)
    icon_map = {
        "gate":     "⬡", "database": "▣", "cloud": "☁",
        "brain":    "◉", "chip":     "▦", "server": "▤",
        "user":     "◎", "module":   "⬛", "box":   "□",
    }
    icon = icon_map.get(ntype, "□")
    fnt_icon = get_font(20)

    # Auto-shrink label to fit inside box width
    label_max_w = w - 16
    fnt_lbl, _ = fit_font(label, label_max_w, max_size=18, min_size=12, bold=True)

    draw.text((x, y - 12), icon,  font=fnt_icon, fill=c,                               anchor="mm")
    draw.text((x, y + 18), label, font=fnt_lbl,  fill=TEXT_W if highlight else TEXT_DIM, anchor="mm")


# ══════════════════════════════════════════════════════════════════════════════
# CONNECTION LINE with animated object
# ══════════════════════════════════════════════════════════════════════════════

def draw_connection(draw, n1, n2, progress, obj_type, c, frame_idx=0):
    x1 = max(80, min(WIDTH-80, n1["x"]))
    y1 = max(DIAGRAM_TOP+40, min(DIAGRAM_BOT-40, n1["y"]))
    x2 = max(80, min(WIDTH-80, n2["x"]))
    y2 = max(DIAGRAM_TOP+40, min(DIAGRAM_BOT-40, n2["y"]))
    rgb = hex2rgb(c)

    # Glow line
    gc = lerp_color(rgb, BG, 0.5)
    draw.line([x1, y1, x2, y2], fill=gc,  width=10)
    draw.line([x1, y1, x2, y2], fill=rgb, width=3)

    # Travelling dots
    for dot_offset in [0.0, 0.33, 0.66]:
        p  = (progress + dot_offset) % 1.0
        dx = int(x1 + (x2-x1)*p)
        dy = int(y1 + (y2-y1)*p)
        draw.ellipse([dx-5, dy-5, dx+5, dy+5], fill=rgb)

    # Main animated object on line
    p2 = progress % 1.0
    ox = int(x1 + (x2-x1)*p2)
    oy = int(y1 + (y2-y1)*p2)
    draw_object(draw, obj_type, ox, oy, 30, rgb, frame_idx=frame_idx)


# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND
# ══════════════════════════════════════════════════════════════════════════════

def draw_background(draw, accent_rgb, frame_idx=0):
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=BG)
    # Grid
    for gx in range(0, WIDTH, 80):
        draw.line([gx, 0, gx, HEIGHT], fill=GRID, width=1)
    for gy in range(0, HEIGHT, 80):
        draw.line([0, gy, WIDTH, gy], fill=GRID, width=1)
    # Diagonal streak
    streak_x = int((frame_idx * 8) % (WIDTH + HEIGHT))
    for i in range(3):
        sx = streak_x - i*6
        sc = lerp_color(accent_rgb, BG, 0.9 + i*0.03)
        draw.line([sx, 0, sx-HEIGHT, HEIGHT], fill=sc, width=3-i)
    # Vignette edges (top and bottom gradient bars to frame the zones)
    for alpha_step, y_start, y_end in [(0.6, 0, 20), (0.6, HEIGHT-20, HEIGHT)]:
        vc = lerp_color(BG, (0,0,0), alpha_step)
        draw.rectangle([0, y_start, WIDTH, y_end], fill=vc)


# ══════════════════════════════════════════════════════════════════════════════
# UI ELEMENTS — all strictly inside their layout zones
# ══════════════════════════════════════════════════════════════════════════════

def draw_header(draw, scene):
    """
    Renders into the top zone (y=0 → DIAGRAM_TOP).
    Layout (fixed, no overlaps):
      y=45-90  : Series › Chapter badge
      y=100-208: Title (auto-size + wrap, max 2 lines)
      y=218-252: Subtitle (single line, auto-shrink)
      y=258-302: Hook pill (single line, auto-shrink)
    """
    series   = scene.get("series", "Tech")
    chapter  = scene.get("chapter", "")
    title    = scene.get("title", "Topic")
    subtitle = scene.get("subtitle", "")
    hook     = scene.get("hook", "")
    accent   = hex2rgb(scene.get("accent", "#38BDF8"))

    SIDE_PAD  = 60         # left+right padding from canvas edge
    MAX_W     = WIDTH - SIDE_PAD * 2

    # ── 1. Series › Chapter badge ────────────────────────────────────────────
    badge_text = f"  {series}  ›  {chapter}  " if chapter else f"  {series}  "
    fnt_badge  = get_font(22, bold=True)
    try:
        bw = int(fnt_badge.getlength(badge_text)) + 20
    except:
        bw = len(badge_text) * 13 + 20
    bw    = min(bw, MAX_W)
    bx1   = WIDTH//2 - bw//2
    badge_y1 = BADGE_CY - BADGE_H//2
    badge_y2 = BADGE_CY + BADGE_H//2
    draw.rounded_rectangle([bx1, badge_y1, bx1+bw, badge_y2],
                            radius=10,
                            fill=lerp_color(accent, BG, 0.82),
                            outline=accent, width=1)
    draw.text((WIDTH//2, BADGE_CY), badge_text, font=fnt_badge, fill=accent, anchor="mm")

    # ── 2. Title — auto-size + word-wrap (max 2 lines) ───────────────────────
    title_zone_h = TITLE_MAX_BOT - TITLE_TOP          # 108 px
    max_lines    = 2
    line_spacing = 8

    # Find the largest font where title fits in 2 lines inside title_zone_h
    chosen_fnt   = None
    chosen_lines = [title]
    for size in range(62, 22, -2):
        fnt_t = get_font(size, bold=True)
        lines = wrap_text(title, fnt_t, MAX_W)
        if len(lines) <= max_lines:
            line_h = size + line_spacing
            total  = len(lines) * line_h
            if total <= title_zone_h:
                chosen_fnt   = fnt_t
                chosen_lines = lines
                break
    if chosen_fnt is None:
        chosen_fnt   = get_font(24, bold=True)
        chosen_lines = wrap_text(title, chosen_fnt, MAX_W)[:max_lines]

    line_h      = chosen_fnt.size + line_spacing if hasattr(chosen_fnt, 'size') else 34
    total_h     = len(chosen_lines) * line_h
    title_cy    = TITLE_TOP + (title_zone_h - total_h) // 2 + line_h // 2

    for i, line in enumerate(chosen_lines):
        y_pos = title_cy + i * line_h
        # Last word in accent color — split at last space
        if ' ' in line and i == len(chosen_lines) - 1:
            idx       = line.rfind(' ')
            part_main = line[:idx]
            part_hl   = line[idx:]   # includes leading space
            try:
                main_w = int(chosen_fnt.getlength(part_main))
                hl_w   = int(chosen_fnt.getlength(part_hl))
                total_line_w = main_w + hl_w
                x_start = WIDTH//2 - total_line_w//2
                draw.text((x_start, y_pos), part_main, font=chosen_fnt, fill=TEXT_W, anchor="lm")
                draw.text((x_start + main_w, y_pos), part_hl, font=chosen_fnt, fill=accent, anchor="lm")
            except:
                draw.text((WIDTH//2, y_pos), line, font=chosen_fnt, fill=accent, anchor="mm")
        else:
            draw.text((WIDTH//2, y_pos), line, font=chosen_fnt, fill=TEXT_W, anchor="mm")

    # ── 3. Subtitle — single line, auto-shrink ───────────────────────────────
    if subtitle:
        fnt_sub, _ = fit_font(subtitle, MAX_W, max_size=28, min_size=18)
        draw.text((WIDTH//2, SUBTITLE_CY), subtitle, font=fnt_sub, fill=TEXT_DIM, anchor="mm")

    # ── 4. Hook pill — single line, auto-shrink ──────────────────────────────
    if hook:
        _draw_hook_pill(draw, hook, HOOK_TOP, HOOK_BOT, accent)


def _draw_hook_pill(draw, text, y_top, y_bot, accent):
    """Render hook text inside a pill between y_top and y_bot."""
    pill_h   = y_bot - y_top
    pill_cx  = WIDTH // 2
    pill_cy  = (y_top + y_bot) // 2
    MAX_W    = WIDTH - 120

    fnt, _   = fit_font(text, MAX_W - 40, max_size=28, min_size=16)
    try:
        text_w = int(fnt.getlength(text))
    except:
        text_w = len(text) * 16
    pill_w   = min(text_w + 48, WIDTH - 80)

    x1 = pill_cx - pill_w//2
    x2 = pill_cx + pill_w//2
    draw.rounded_rectangle([x1, y_top+2, x2, y_bot-2],
                            radius=pill_h//2,
                            fill=lerp_color(accent, BG, 0.88),
                            outline=lerp_color(accent, TEXT_DIM, 0.4),
                            width=1)
    draw.text((pill_cx, pill_cy), text, font=fnt, fill=TEXT_W, anchor="mm")


def draw_counters(draw, scene, frame_idx, total_frames):
    """Render two counter badges, always at COUNTER_CY — never overlaps caption."""
    ca = scene.get("counter_a", {"label": "PROCESSED", "max": 20})
    cb = scene.get("counter_b", {"label": "FAILED",    "max": 3})

    prog  = min(1.0, frame_idx / max(total_frames - 1, 1))
    val_a = int(ca["max"] * prog)
    val_b = int(cb["max"] * prog)

    _draw_counter_badge(draw, WIDTH//4,       COUNTER_CY, ca["label"], val_a, NEON["green"])
    _draw_counter_badge(draw, WIDTH*3//4,     COUNTER_CY, cb["label"], val_b, NEON["red"])


def _draw_counter_badge(draw, cx, cy, label, value, color):
    bw, bh = 210, COUNTER_H
    # Background pill
    draw.rounded_rectangle([cx-bw//2, cy-bh//2, cx+bw//2, cy+bh//2],
                            radius=bh//2,
                            fill=lerp_color(color, BG, 0.88),
                            outline=color, width=2)

    # Icon
    icon     = "✓" if color == NEON["green"] else "✗"
    fnt_icon = get_font(22, bold=True)
    fnt_num  = get_font(36, bold=True)
    fnt_lbl  = get_font(17)

    icon_x = cx - bw//2 + 28
    num_x  = cx + 12
    draw.text((icon_x, cy - 6),  icon,        font=fnt_icon, fill=color,   anchor="mm")
    draw.text((num_x,  cy - 8),  str(value),  font=fnt_num,  fill=TEXT_W,  anchor="mm")
    draw.text((num_x,  cy + 18), label,       font=fnt_lbl,  fill=TEXT_DIM, anchor="mm")


def draw_caption(draw, text, step_progress=1.0):
    """
    Render narration caption in the fixed zone CAPTION_TOP → CAPTION_BOT.
    Max 3 lines. Never overlaps counters (above) or step dots (below).
    """
    if not text:
        return

    SIDE_PAD = 48
    MAX_W    = WIDTH - SIDE_PAD * 2
    zone_h   = CAPTION_BOT - CAPTION_TOP   # 273px

    # Auto-size font: largest that fits ≤3 lines in zone
    chosen_fnt   = None
    chosen_lines = [text]
    MAX_LINES    = 3
    for size in range(34, 20, -2):
        fnt   = get_font(size)
        lines = wrap_text(text, fnt, MAX_W)
        if len(lines) <= MAX_LINES:
            line_h = size + 10
            if len(lines) * line_h + 36 <= zone_h:
                chosen_fnt   = fnt
                chosen_lines = lines
                break
    if chosen_fnt is None:
        chosen_fnt   = get_font(22)
        chosen_lines = wrap_text(text, chosen_fnt, MAX_W)[:MAX_LINES]

    line_h  = (chosen_fnt.size if hasattr(chosen_fnt, 'size') else 24) + 10
    total_h = len(chosen_lines) * line_h + 36

    # Center pill vertically inside caption zone
    pill_top = CAPTION_TOP + (zone_h - total_h) // 2
    pill_bot = pill_top + total_h

    # Pill background
    draw.rounded_rectangle([SIDE_PAD - 12, pill_top, WIDTH - SIDE_PAD + 12, pill_bot],
                            radius=18,
                            fill=(10, 14, 34),
                            outline=TEXT_DIM, width=1)

    # Text lines
    y_text = pill_top + 18
    fade   = min(1.0, step_progress * 5)
    txt_c  = lerp_color(TEXT_DIM, TEXT_W, fade)
    for line in chosen_lines:
        draw.text((WIDTH//2, y_text), line, font=chosen_fnt, fill=txt_c, anchor="mm")
        y_text += line_h


def draw_step_indicator(draw, step_idx, total_steps):
    """Dots showing progress, at the very bottom of the footer zone."""
    dot_r   = 5
    spacing = 18
    total_w = total_steps * spacing
    x0      = WIDTH//2 - total_w//2
    for i in range(total_steps):
        c = TEXT_W  if i == step_idx else TEXT_DIM
        r = dot_r   if i == step_idx else dot_r - 2
        draw.ellipse([x0+i*spacing-r, DOTS_Y-r, x0+i*spacing+r, DOTS_Y+r], fill=c)


def draw_zone_separators(draw):
    """Subtle separator lines between header and diagram, diagram and footer."""
    sep_c = lerp_color(GRID, BG, 0.2)
    draw.line([40, DIAGRAM_TOP - 8, WIDTH-40, DIAGRAM_TOP - 8], fill=sep_c, width=1)
    draw.line([40, DIAGRAM_BOT + 8, WIDTH-40, DIAGRAM_BOT + 8], fill=sep_c, width=1)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE CLASS
# ══════════════════════════════════════════════════════════════════════════════

class TechVisualEngine:
    FRAMES_PER_STEP = 60   # 2s per step at 30fps

    def __init__(self, obj_a: str, obj_b: str):
        self.obj_a = obj_a
        self.obj_b = obj_b

    # ── Public API ────────────────────────────────────────────────────────────

    def render_all_frames(self, scene: dict, frame_dir: str) -> list:
        steps       = scene.get("steps", ["Loading..."])
        total_steps = len(steps)
        frame_paths = []
        frame_dir   = Path(frame_dir)
        frame_dir.mkdir(parents=True, exist_ok=True)

        global_frame = 0
        for step_idx, caption in enumerate(steps):
            n_frames = self.FRAMES_PER_STEP
            for f in range(n_frames):
                img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
                draw = ImageDraw.Draw(img)
                self._render_frame(draw, scene, step_idx, total_steps,
                                   caption, f, n_frames, global_frame)
                path = str(frame_dir / f"frame_{global_frame:05d}.png")
                img.save(path, optimize=False)
                frame_paths.append(path)
                global_frame += 1

        print(f"  Rendered {global_frame} frames ({total_steps} steps × {self.FRAMES_PER_STEP}f)")
        return frame_paths

    def render_thumbnail(self, scene: dict) -> Image.Image:
        img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)
        accent = hex2rgb(scene.get("accent", "#38BDF8"))

        draw_background(draw, accent, 0)
        draw_zone_separators(draw)
        draw_header(draw, scene)

        nodes = scene.get("nodes", [])
        for node in nodes:
            draw_node(draw, node, highlight=True, frame_idx=0)

        if nodes:
            cx = WIDTH // 2
            cy = (DIAGRAM_TOP + DIAGRAM_BOT) // 2
            draw_object(draw, self.obj_a, cx - 170, cy, 55, accent, frame_idx=0)
            draw_object(draw, self.obj_b, cx + 170, cy, 55, NEON["purple"], frame_idx=0)

        steps = scene.get("steps", [])
        if steps:
            draw_caption(draw, steps[0], step_progress=1.0)

        total_frames = len(steps) * self.FRAMES_PER_STEP
        draw_counters(draw, scene, 0, max(total_frames, 1))
        draw_step_indicator(draw, 0, max(len(steps), 1))
        return img

    # ── Internal rendering ────────────────────────────────────────────────────

    def _render_frame(self, draw, scene, step_idx, total_steps,
                      caption, f, n_frames, global_frame):
        accent        = hex2rgb(scene.get("accent", "#38BDF8"))
        nodes         = scene.get("nodes", [])
        paths         = scene.get("paths", [])
        node_map      = {n["id"]: n for n in nodes}
        step_progress = f / max(n_frames - 1, 1)

        # 1. Background + zone separators
        draw_background(draw, accent, global_frame)
        draw_zone_separators(draw)

        # 2. Header (badge + title + subtitle + hook)
        draw_header(draw, scene)

        # 3. Connections (within diagram zone)
        active_paths = self._active_paths_for_step(paths, step_idx, total_steps)
        for p_idx, path in enumerate(paths):
            n1 = node_map.get(path["from"])
            n2 = node_map.get(path["to"])
            if not (n1 and n2):
                continue
            if p_idx in active_paths:
                obj      = self.obj_a if p_idx % 2 == 0 else self.obj_b
                progress = (step_progress + p_idx * 0.37) % 1.0
                clr      = n1.get("color", scene.get("accent", "#38BDF8"))
                draw_connection(draw, n1, n2, progress, obj, clr, global_frame)
            else:
                c  = hex2rgb(n1.get("color", "#334155"))
                gc = lerp_color(c, BG, 0.72)
                x1 = max(80, min(WIDTH-80, n1["x"]))
                y1 = max(DIAGRAM_TOP+40, min(DIAGRAM_BOT-40, n1["y"]))
                x2 = max(80, min(WIDTH-80, n2["x"]))
                y2 = max(DIAGRAM_TOP+40, min(DIAGRAM_BOT-40, n2["y"]))
                draw.line([x1, y1, x2, y2], fill=gc, width=2)

        # 4. Nodes
        highlighted = self._highlighted_nodes(active_paths, paths)
        for node in nodes:
            draw_node(draw, node, highlight=node["id"] in highlighted, frame_idx=global_frame)

        # 5. Roaming objects (within diagram zone)
        self._draw_roaming_objects(draw, scene, step_idx, step_progress, global_frame)

        # 6. Footer: counters
        total_frames = total_steps * n_frames
        draw_counters(draw, scene, global_frame, total_frames)

        # 7. Footer: caption
        draw_caption(draw, caption, step_progress)

        # 8. Footer: step dots
        draw_step_indicator(draw, step_idx, total_steps)

    def _active_paths_for_step(self, paths, step_idx, total_steps):
        if not paths:
            return set()
        n            = len(paths)
        active_count = max(1, (step_idx + 1) * n // total_steps)
        return set(range(min(active_count, n)))

    def _highlighted_nodes(self, active_path_indices, paths):
        highlighted = set()
        for i in active_path_indices:
            if i < len(paths):
                highlighted.add(paths[i]["from"])
                highlighted.add(paths[i]["to"])
        return highlighted

    def _draw_roaming_objects(self, draw, scene, step_idx, step_progress, global_frame):
        """Orbit objects in diagram zone only."""
        random.seed(step_idx * 17 + 42)
        n_roamers = random.randint(2, 3)
        nodes     = scene.get("nodes", [])
        accent    = hex2rgb(scene.get("accent", "#38BDF8"))

        if nodes:
            center_x = sum(n["x"] for n in nodes) // len(nodes)
            center_y = sum(n["y"] for n in nodes) // len(nodes)
        else:
            center_x = WIDTH // 2
            center_y = (DIAGRAM_TOP + DIAGRAM_BOT) // 2

        for i in range(n_roamers):
            obj      = self.obj_a if i % 2 == 0 else self.obj_b
            orbit_r  = 90 + i * 55
            angle    = math.radians((global_frame * (3 + i) + i * 120) % 360)
            ox = center_x + int(math.cos(angle) * orbit_r)
            oy = center_y + int(math.sin(angle) * orbit_r)
            # Hard-clamp to diagram zone with margin
            ox = max(60, min(WIDTH - 60, ox))
            oy = max(DIAGRAM_TOP + 50, min(DIAGRAM_BOT - 50, oy))
            c  = lerp_color(accent, NEON["purple"], i * 0.35)
            draw_object(draw, obj, ox, oy, 26, c, frame_idx=global_frame)
