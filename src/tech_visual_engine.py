"""
Tech Visual Engine — Game-Style Dark Neon Renderer
Renders animated frames for tech concept videos.
Objects: fish, rocket, car, robot, crystal, etc. animate through scenes.
Style: Dark background, neon glow, game UI, counters, captions.
"""

import math, random, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH  = 1080
HEIGHT = 1920
FPS    = 30

# ── Palette ─────────────────────────────────────────────────────────────────
BG        = (8,  12,  26)      # near-black deep navy
GRID      = (20, 30,  55)      # subtle grid
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

def rgb2hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

def glow_color(rgb, alpha=80):
    return rgb + (alpha,)

# ── Fonts ────────────────────────────────────────────────────────────────────
def get_font(size, bold=False):
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "assets/fonts/Montserrat-Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "assets/fonts/Montserrat-Regular.ttf",
        ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except:
            pass
    return ImageFont.load_default()


# ══════════════════════════════════════════════════════════════════════════════
# OBJECT DRAWING — 30+ unique animated shapes
# ══════════════════════════════════════════════════════════════════════════════

def draw_object(draw, obj_type, cx, cy, size, color_rgb, frame_idx=0, alpha_layer=None):
    """Draw any object type at (cx,cy). size≈40-80px."""
    s  = size
    s2 = size // 2
    t  = frame_idx * 0.1  # time for wobble

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
    fn = funcs.get(obj_type, _draw_packet)
    try:
        fn(draw, cx, cy, s, color_rgb, t)
    except:
        _draw_packet(draw, cx, cy, s, color_rgb, t)

# ── Individual object renderers ───────────────────────────────────────────────

def _draw_fish(draw, cx, cy, s, c, t):
    wobble = int(math.sin(t * 2) * s * 0.15)
    # Body
    draw.ellipse([cx-s, cy-s//2+wobble, cx+s//3, cy+s//2+wobble], fill=c, outline=TEXT_W, width=2)
    # Tail
    pts = [cx-s, cy+wobble, cx-s-s//2, cy-s//2+wobble, cx-s-s//2, cy+s//2+wobble]
    draw.polygon(pts, fill=c)
    # Eye
    draw.ellipse([cx+s//6-6, cy-8+wobble, cx+s//6+6, cy+4+wobble], fill=TEXT_W)
    draw.ellipse([cx+s//6-3, cy-6+wobble, cx+s//6+3, cy+2+wobble], fill=(0,0,0))
    # Fin
    draw.polygon([cx-s//3, cy-s//2+wobble, cx, cy+wobble, cx-s//3, cy+wobble], fill=lerp_color(c,(255,255,255),0.4))

def _draw_rocket(draw, cx, cy, s, c, t):
    # Body
    draw.ellipse([cx-s//3, cy-s, cx+s//3, cy+s//2], fill=c, outline=TEXT_W, width=2)
    # Nose
    pts = [cx-s//3, cy-s, cx+s//3, cy-s, cx, cy-s-s//2]
    draw.polygon(pts, fill=lerp_color(c, TEXT_W, 0.5))
    # Fins
    draw.polygon([cx-s//3, cy+s//4, cx-s//3-s//2, cy+s//2, cx-s//3, cy+s//2], fill=c)
    draw.polygon([cx+s//3, cy+s//4, cx+s//3+s//2, cy+s//2, cx+s//3, cy+s//2], fill=c)
    # Exhaust glow
    glow = NEON["gold"]
    for r in range(3):
        alpha = 80 - r*25
        ey = cy + s//2 + r*6
        draw.ellipse([cx-s//4+r*2, ey, cx+s//4-r*2, ey+s//3], fill=glow+(alpha,) if len(glow)==3 else glow)

def _draw_car(draw, cx, cy, s, c, t):
    # Body
    draw.rounded_rectangle([cx-s, cy-s//3, cx+s, cy+s//3], radius=s//5, fill=c, outline=TEXT_W, width=2)
    # Roof
    draw.rounded_rectangle([cx-s//2, cy-s//3-s//3, cx+s//2, cy-s//3], radius=s//8, fill=lerp_color(c,TEXT_W,0.3))
    # Wheels
    for wx in [cx-s//2, cx+s//2]:
        draw.ellipse([wx-s//4, cy+s//4, wx+s//4, cy+s//4+s//2], fill=(30,30,30), outline=TEXT_W, width=2)
        draw.ellipse([wx-s//8, cy+s//4+s//8, wx+s//8, cy+s//4+s//2-s//8], fill=TEXT_DIM)
    # Headlight
    draw.ellipse([cx+s-8, cy-s//8, cx+s+4, cy+s//8], fill=NEON["gold"])

def _draw_robot(draw, cx, cy, s, c, t):
    blink = int(t * 3) % 4 == 0
    # Body
    draw.rounded_rectangle([cx-s//2, cy, cx+s//2, cy+s], radius=8, fill=c, outline=TEXT_W, width=2)
    # Head
    draw.rounded_rectangle([cx-s//3, cy-s//2, cx+s//3, cy], radius=6, fill=lerp_color(c,BG,0.3), outline=TEXT_W, width=2)
    # Eyes
    eye_c = NEON["gold"] if not blink else NEON["red"]
    draw.ellipse([cx-s//5-6, cy-s//3-6, cx-s//5+6, cy-s//3+6], fill=eye_c)
    draw.ellipse([cx+s//5-6, cy-s//3-6, cx+s//5+6, cy-s//3+6], fill=eye_c)
    # Antenna
    draw.line([cx, cy-s//2, cx, cy-s//2-s//3], fill=TEXT_W, width=3)
    draw.ellipse([cx-6, cy-s//2-s//3-6, cx+6, cy-s//2-s//3+6], fill=NEON["red"])
    # Arms
    draw.rectangle([cx-s//2-s//4, cy+s//6, cx-s//2, cy+s//2], fill=c, outline=TEXT_W, width=1)
    draw.rectangle([cx+s//2, cy+s//6, cx+s//2+s//4, cy+s//2], fill=c, outline=TEXT_W, width=1)

def _draw_crystal(draw, cx, cy, s, c, t):
    glow = lerp_color(c, TEXT_W, 0.4)
    pts = [cx, cy-s, cx+s//2, cy-s//3, cx+s//2, cy+s//2, cx, cy+s, cx-s//2, cy+s//2, cx-s//2, cy-s//3]
    draw.polygon(pts, fill=glow, outline=TEXT_W, width=2)
    inner = [cx, cy-s//2, cx+s//4, cy, cx, cy+s//2, cx-s//4, cy]
    draw.polygon(inner, fill=c)
    # Sparkle
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle + t*20)
        px, py = cx + int(math.cos(rad)*s*0.8), cy + int(math.sin(rad)*s*0.8)
        draw.ellipse([px-4, py-4, px+4, py+4], fill=TEXT_W)

def _draw_satellite(draw, cx, cy, s, c, t):
    # Body
    draw.rounded_rectangle([cx-s//3, cy-s//4, cx+s//3, cy+s//4], radius=6, fill=c, outline=TEXT_W, width=2)
    # Solar panels
    draw.rectangle([cx-s-s//3, cy-s//8, cx-s//3, cy+s//8], fill=NEON["blue"], outline=TEXT_W, width=1)
    draw.rectangle([cx+s//3, cy-s//8, cx+s+s//3, cy+s//8], fill=NEON["blue"], outline=TEXT_W, width=1)
    # Dish
    draw.arc([cx-s//4, cy-s, cx+s//4, cy-s//2], 180, 0, fill=TEXT_W, width=3)
    draw.line([cx, cy-s//2, cx, cy-s//4], fill=TEXT_W, width=2)
    # Blink
    if int(t*2) % 2:
        draw.ellipse([cx-5, cy-5, cx+5, cy+5], fill=NEON["red"])

def _draw_packet(draw, cx, cy, s, c, t):
    pulse = int(math.sin(t*3)*4)
    r = s // 2 + pulse
    draw.rounded_rectangle([cx-r, cy-r, cx+r, cy+r], radius=8, fill=lerp_color(c, BG, 0.2), outline=c, width=3)
    # Data lines inside
    for i in range(3):
        y = cy - r//2 + i*(r//2)
        w = r - 10 - i*6
        draw.rectangle([cx-w, y, cx+w, y+4], fill=lerp_color(c, TEXT_W, 0.4))

def _draw_bird(draw, cx, cy, s, c, t):
    flap = math.sin(t * 4) * s * 0.5
    # Wings
    draw.arc([cx-s-int(flap), cy-int(flap), cx, cy], 200, 340, fill=c, width=4)
    draw.arc([cx, cy-int(flap), cx+s+int(flap), cy], 200, 340, fill=c, width=4)
    # Body
    draw.ellipse([cx-s//4, cy-s//6, cx+s//4, cy+s//4], fill=c)
    # Tail
    draw.polygon([cx-s//4, cy+s//4, cx-s//3, cy+s//2, cx+s//4, cy+s//4], fill=c)

def _draw_dragon(draw, cx, cy, s, c, t):
    # Body
    draw.ellipse([cx-s//2, cy-s//3, cx+s//2, cy+s//2], fill=c, outline=TEXT_W, width=2)
    # Head
    draw.ellipse([cx+s//4, cy-s//2, cx+s//4+s//2, cy], fill=c, outline=TEXT_W, width=2)
    # Wing
    pts = [cx-s//4, cy-s//4, cx-s, cy-s, cx, cy-s//3]
    draw.polygon(pts, fill=lerp_color(c, (80,0,200), 0.5), outline=TEXT_W, width=1)
    # Fire breath
    fire_x = cx + s//2 + s//4
    for i in range(4):
        fi = NEON["gold"] if i%2==0 else NEON["orange"]
        draw.ellipse([fire_x+i*10-8, cy-s//4-8, fire_x+i*10+8, cy-s//4+8], fill=fi)
    # Eye
    draw.ellipse([cx+s//4+s//4-5, cy-s//3-5, cx+s//4+s//4+5, cy-s//3+5], fill=NEON["gold"])

def _draw_submarine(draw, cx, cy, s, c, t):
    # Body
    draw.ellipse([cx-s, cy-s//3, cx+s, cy+s//3], fill=c, outline=TEXT_W, width=2)
    # Conning tower
    draw.rectangle([cx-s//6, cy-s//3-s//3, cx+s//6, cy-s//3], fill=lerp_color(c,TEXT_W,0.3), outline=TEXT_W, width=1)
    # Periscope
    draw.line([cx+s//8, cy-s//3-s//3, cx+s//8, cy-s//3-s//2], fill=TEXT_W, width=3)
    draw.line([cx+s//8, cy-s//3-s//2, cx+s//4, cy-s//3-s//2], fill=TEXT_W, width=3)
    # Propeller
    draw.ellipse([cx+s-8, cy-s//4, cx+s+8, cy+s//4], fill=NEON["gold"])
    # Bubble trail
    for i in range(3):
        bx = cx - s - i*18
        by = cy - s//4 - i*15
        r2 = 8 - i*2
        draw.ellipse([bx-r2, by-r2, bx+r2, by+r2], outline=NEON["cyan"], width=2)

def _draw_gear(draw, cx, cy, s, c, t):
    teeth = 8
    rot = t * 30
    for i in range(teeth*2):
        angle = math.radians(i * 180/teeth + rot)
        r = s if i%2==0 else s*0.75
        x1 = cx + int(math.cos(angle)*r*0.85)
        y1 = cy + int(math.sin(angle)*r*0.85)
        x2 = cx + int(math.cos(angle)*r)
        y2 = cy + int(math.sin(angle)*r)
        draw.line([x1, y1, x2, y2], fill=c, width=6)
    draw.ellipse([cx-s*0.7, cy-s*0.7, cx+s*0.7, cy+s*0.7], outline=c, width=4)
    draw.ellipse([cx-s*0.3, cy-s*0.3, cx+s*0.3, cy+s*0.3], fill=lerp_color(c,BG,0.5), outline=TEXT_W, width=2)

def _draw_lightning(draw, cx, cy, s, c, t):
    pts = [cx+s//4, cy-s, cx-s//8, cy, cx+s//4, cy, cx-s//4, cy+s]
    draw.polygon(pts, fill=NEON["gold"], outline=TEXT_W, width=2)

def _draw_diamond(draw, cx, cy, s, c, t):
    shine = lerp_color(c, TEXT_W, 0.5)
    pts = [cx, cy-s, cx+s//2, cy, cx, cy+s, cx-s//2, cy]
    draw.polygon(pts, fill=shine, outline=TEXT_W, width=3)
    draw.polygon([cx, cy-s//2, cx+s//4, cy, cx, cy+s//2, cx-s//4, cy], fill=c)

def _draw_comet(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s//3, cy-s//3, cx+s//3, cy+s//3], fill=c, outline=TEXT_W, width=2)
    for i in range(5):
        alpha = 150 - i*28
        tx = cx + (i+1)*s//3
        ty = cy + (i+1)*s//4
        r2 = s//3 - i*3
        if r2 > 2:
            draw.ellipse([tx-r2, ty-r2, tx+r2, ty+r2], fill=lerp_color(c, BG, i*0.2))

def _draw_ufo(draw, cx, cy, s, c, t):
    pulse = math.sin(t*3)*0.1
    # Saucer
    draw.ellipse([cx-s, cy-s//4, cx+s, cy+s//4], fill=c, outline=TEXT_W, width=2)
    # Dome
    draw.arc([cx-s//2, cy-s//2, cx+s//2, cy+s//4], 180, 0, fill=NEON["cyan"], width=3)
    # Lights
    colors = [NEON["red"], NEON["gold"], NEON["green"]]
    for i, lc in enumerate(colors):
        lx = cx - s//2 + (i+1)*s//2
        draw.ellipse([lx-7, cy+s//6-7, lx+7, cy+s//6+7], fill=lc)
    # Beam
    if int(t*2)%2 == 0:
        pts = [cx-s//4, cy+s//4, cx+s//4, cy+s//4, cx+s//2, cy+s, cx-s//2, cy+s]
        draw.polygon(pts, fill=(34,211,238,40))

def _draw_bug(draw, cx, cy, s, c, t):
    # Body segments
    draw.ellipse([cx-s//3, cy, cx+s//3, cy+s//2], fill=c, outline=TEXT_W, width=2)
    draw.ellipse([cx-s//4, cy-s//2, cx+s//4, cy+s//8], fill=lerp_color(c,TEXT_W,0.3), outline=TEXT_W, width=2)
    # Eyes
    draw.ellipse([cx-s//5-5, cy-s//3-5, cx-s//5+5, cy-s//3+5], fill=NEON["red"])
    draw.ellipse([cx+s//5-5, cy-s//3-5, cx+s//5+5, cy-s//3+5], fill=NEON["red"])
    # Legs
    for i in range(3):
        y = cy + i*s//6
        draw.line([cx-s//3, y, cx-s//3-s//2, y-s//6], fill=c, width=3)
        draw.line([cx+s//3, y, cx+s//3+s//2, y-s//6], fill=c, width=3)
    # Antennae
    draw.line([cx-s//6, cy-s//2, cx-s//2, cy-s], fill=c, width=2)
    draw.line([cx+s//6, cy-s//2, cx+s//2, cy-s], fill=c, width=2)
    draw.ellipse([cx-s//2-5, cy-s-5, cx-s//2+5, cy-s+5], fill=NEON["gold"])
    draw.ellipse([cx+s//2-5, cy-s-5, cx+s//2+5, cy-s+5], fill=NEON["gold"])

def _draw_train(draw, cx, cy, s, c, t):
    draw.rounded_rectangle([cx-s, cy-s//3, cx+s//2, cy+s//3], radius=8, fill=c, outline=TEXT_W, width=2)
    draw.rounded_rectangle([cx-s+s//6, cy-s//3-s//4, cx+s//6, cy-s//3], radius=4, fill=lerp_color(c,TEXT_W,0.3))
    for wx in [cx-s//2, cx]:
        draw.ellipse([wx-s//5, cy+s//4, wx+s//5, cy+s//4+s//3], fill=(40,40,40), outline=TEXT_W, width=2)
    draw.rectangle([cx+s//2, cy-s//6, cx+s//2+s//3, cy+s//6], fill=c, outline=TEXT_W, width=2)
    draw.ellipse([cx-s+6, cy-s//5, cx-s+6+16, cy+s//5], fill=NEON["gold"])

def _draw_airplane(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s, cy-s//4, cx+s//2, cy+s//4], fill=c, outline=TEXT_W, width=2)
    draw.polygon([cx-s, cy, cx-s-s//3, cy-s//3, cx-s//2, cy], fill=c)
    draw.polygon([cx-s//3, cy-s//4, cx+s//4, cy-s//4, cx+s//4, cy-s//4-s//3, cx-s//3, cy-s//4-s//6], fill=lerp_color(c,TEXT_W,0.4))
    draw.polygon([cx+s//4, cy, cx+s//2, cy-s//4, cx+s//2, cy+s//4], fill=c)

def _draw_bubble(draw, cx, cy, s, c, t):
    wobble = int(math.sin(t*2)*4)
    draw.ellipse([cx-s, cy-s+wobble, cx+s, cy+s+wobble], outline=c, width=4)
    draw.ellipse([cx-s+4, cy-s+4+wobble, cx+s-4, cy+s-4+wobble], outline=lerp_color(c,TEXT_W,0.3), width=2)
    draw.ellipse([cx-s//3, cy-s*0.6+wobble, cx-s//6, cy-s*0.4+wobble], fill=lerp_color(c,TEXT_W,0.6))

def _draw_star(draw, cx, cy, s, c, t):
    rot = t * 15
    n, r_out, r_in = 5, s, s*0.4
    pts = []
    for i in range(n*2):
        angle = math.radians(i*180/n + rot - 90)
        r = r_out if i%2==0 else r_in
        pts.extend([cx+int(math.cos(angle)*r), cy+int(math.sin(angle)*r)])
    draw.polygon(pts, fill=c, outline=TEXT_W, width=2)

def _draw_turtle(draw, cx, cy, s, c, t):
    draw.ellipse([cx-s//2, cy-s//3, cx+s//2, cy+s//3], fill=c, outline=TEXT_W, width=2)
    # Shell pattern
    draw.arc([cx-s//3, cy-s//4, cx+s//3, cy+s//4], 0, 180, fill=lerp_color(c,TEXT_W,0.4), width=3)
    # Head
    draw.ellipse([cx+s//2-s//4, cy-s//6, cx+s//2+s//4, cy+s//6], fill=c, outline=TEXT_W, width=2)
    # Legs
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
    draw.ellipse([cx-s-pulse, cy-s-pulse, cx+s+pulse, cy+s+pulse], fill=lerp_color(c, BG, 0.3), outline=c, width=4)
    draw.ellipse([cx-s+8, cy-s+8, cx+s-8, cy+s-8], outline=lerp_color(c, TEXT_W, 0.5), width=2)
    fnt = get_font(s, bold=True)
    draw.text((cx, cy), "$", font=fnt, fill=TEXT_W, anchor="mm")

def _draw_hexagon(draw, cx, cy, s, c, t):
    rot = t * 10
    pts = []
    for i in range(6):
        a = math.radians(60*i + rot)
        pts.extend([cx+int(math.cos(a)*s), cy+int(math.sin(a)*s)])
    draw.polygon(pts, fill=lerp_color(c, BG, 0.3), outline=c, width=4)

def _draw_molecule(draw, cx, cy, s, c, t):
    rot = t * 20
    atoms = [(0, 0, c, s//3), (s, -s//2, NEON["red"], s//4), (s, s//2, NEON["green"], s//4), (-s, 0, NEON["gold"], s//4)]
    for ax, ay, ac, ar in atoms:
        r = math.radians(rot)
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
        fs = s - i*s//5 + int(flicker)
        draw.ellipse([cx-fs//2, cy-fs*2+i*s//2, cx+fs//2, cy+i*s//4], fill=fc)

def _draw_snowflake(draw, cx, cy, s, c, t):
    rot = t * 15
    for i in range(6):
        a = math.radians(60*i + rot)
        ex = cx + int(math.cos(a)*s)
        ey = cy + int(math.sin(a)*s)
        draw.line([cx, cy, ex, ey], fill=c, width=3)
        for j in [0.4, 0.7]:
            bx = cx + int(math.cos(a)*s*j)
            by = cy + int(math.sin(a)*s*j)
            for d in [45, -45]:
                ba = math.radians(60*i + rot + d)
                draw.line([bx, by, bx+int(math.cos(ba)*s*0.25), by+int(math.sin(ba)*s*0.25)], fill=c, width=2)

def _draw_leaf(draw, cx, cy, s, c, t):
    sway = math.sin(t*2)*s*0.2
    pts = [cx, cy-s, cx+s//2+int(sway), cy, cx, cy+s//2, cx-s//2+int(sway), cy]
    draw.polygon(pts, fill=c, outline=lerp_color(c, TEXT_W, 0.3), width=2)
    draw.line([cx, cy-s, cx, cy+s//2], fill=lerp_color(c, TEXT_W, 0.4), width=2)

def _draw_virus(draw, cx, cy, s, c, t):
    rot = t * 20
    draw.ellipse([cx-s//2, cy-s//2, cx+s//2, cy+s//2], fill=c, outline=TEXT_W, width=2)
    for i in range(8):
        a = math.radians(45*i + rot)
        px = cx + int(math.cos(a)*s*0.8)
        py = cy + int(math.sin(a)*s*0.8)
        draw.line([cx+int(math.cos(a)*s//2), cy+int(math.sin(a)*s//2), px, py], fill=c, width=3)
        draw.ellipse([px-6, py-6, px+6, py+6], fill=NEON["red"])

def _draw_drop(draw, cx, cy, s, c, t):
    pts = [cx, cy-s, cx+s//2, cy, cx+s//2, cy+s//2, cx, cy+s, cx-s//2, cy+s//2, cx-s//2, cy]
    draw.polygon(pts, fill=c, outline=TEXT_W, width=2)
    draw.ellipse([cx-s//5, cy-s//3, cx+s//5, cy+s//6], fill=lerp_color(c, TEXT_W, 0.5))

def _draw_crown(draw, cx, cy, s, c, t):
    pts = [cx-s, cy+s//3, cx-s, cy-s//3, cx-s//2, cy+s//6, cx, cy-s, cx+s//2, cy+s//6, cx+s, cy-s//3, cx+s, cy+s//3]
    draw.polygon(pts, fill=NEON["gold"], outline=TEXT_W, width=2)
    for px, py in [(cx-s+s//5, cy-s//6), (cx, cy-s//4), (cx+s-s//5, cy-s//6)]:
        draw.ellipse([px-6, py-6, px+6, py+6], fill=c)

def _draw_shield(draw, cx, cy, s, c, t):
    pts = [cx-s, cy-s, cx+s, cy-s, cx+s, cy+s//3, cx, cy+s, cx-s, cy+s//3]
    draw.polygon(pts, fill=lerp_color(c, BG, 0.3), outline=c, width=4)
    draw.polygon([cx-s//2, cy-s//2, cx+s//2, cy-s//2, cx+s//2, cy, cx, cy+s//2, cx-s//2, cy], outline=lerp_color(c, TEXT_W, 0.4), width=2)

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
# NODE DRAWING — different box types
# ══════════════════════════════════════════════════════════════════════════════

def draw_node(draw, node, highlight=False, frame_idx=0):
    x, y  = node["x"], node["y"]
    label = node.get("label", "")
    ntype = node.get("type", "box")
    c     = hex2rgb(node.get("color", "#38BDF8"))
    glow  = lerp_color(c, BG, 0.3)
    pulse = math.sin(frame_idx * 0.15) * 5 if highlight else 0

    w, h = 160, 80
    if ntype in ("gate", "server"):
        w, h = 200, 70

    # Glow behind box
    if highlight:
        for ex in range(1, 5):
            draw.rounded_rectangle(
                [x-w//2-ex*3, y-h//2-ex*3, x+w//2+ex*3, y+h//2+ex*3],
                radius=18, outline=c+(60-ex*12,), width=2)

    # Box
    draw.rounded_rectangle(
        [x-w//2+int(pulse)//2, y-h//2+int(pulse)//2,
         x+w//2-int(pulse)//2, y+h//2-int(pulse)//2],
        radius=14, fill=lerp_color(glow, BG, 0.5),
        outline=c if not highlight else TEXT_W, width=3 if highlight else 2)

    # Type icon
    icon_map = {
        "gate":     "⬡",
        "database": "🗄",
        "cloud":    "☁",
        "brain":    "◉",
        "chip":     "▦",
        "server":   "▤",
        "user":     "◎",
        "module":   "⬛",
        "box":      "□",
    }
    icon = icon_map.get(ntype, "□")
    fnt_icon = get_font(22)
    fnt_lbl  = get_font(20, bold=True)

    draw.text((x, y-10), icon, font=fnt_icon, fill=c, anchor="mm")
    draw.text((x, y+16), label, font=fnt_lbl, fill=TEXT_W if highlight else TEXT_DIM, anchor="mm")


# ══════════════════════════════════════════════════════════════════════════════
# CONNECTION LINE with animated object
# ══════════════════════════════════════════════════════════════════════════════

def draw_connection(draw, n1, n2, progress, obj_type, c, frame_idx=0):
    """Draw a glowing connection line with an animated object moving along it."""
    x1, y1 = n1["x"], n1["y"]
    x2, y2 = n2["x"], n2["y"]
    rgb    = hex2rgb(c)

    # Glow line (thick + translucent)
    _draw_glow_line(draw, x1, y1, x2, y2, rgb, width=6, alpha=60)
    # Core line
    draw.line([x1, y1, x2, y2], fill=rgb, width=2)

    # Animated dots (packets) along line
    for dot_offset in [0.0, 0.33, 0.66]:
        p = (progress + dot_offset) % 1.0
        dx = int(x1 + (x2-x1)*p)
        dy = int(y1 + (y2-y1)*p)
        draw.ellipse([dx-5, dy-5, dx+5, dy+5], fill=rgb)

    # Main animated object
    p2 = progress % 1.0
    ox = int(x1 + (x2-x1)*p2)
    oy = int(y1 + (y2-y1)*p2)
    draw_object(draw, obj_type, ox, oy, 32, rgb, frame_idx=frame_idx)


def _draw_glow_line(draw, x1, y1, x2, y2, rgb, width=8, alpha=50):
    """Draw a thick semi-transparent glow along a line (approximated with thick line)."""
    # PIL doesn't support alpha on lines directly, so we overdraw with color
    gc = lerp_color(rgb, BG, 0.5)
    draw.line([x1, y1, x2, y2], fill=gc, width=width+4)
    draw.line([x1, y1, x2, y2], fill=rgb, width=width)


# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND
# ══════════════════════════════════════════════════════════════════════════════

def draw_background(draw, accent_rgb, frame_idx=0):
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=BG)
    # Subtle grid
    for gx in range(0, WIDTH, 80):
        draw.line([gx, 0, gx, HEIGHT], fill=GRID, width=1)
    for gy in range(0, HEIGHT, 80):
        draw.line([0, gy, WIDTH, gy], fill=GRID, width=1)
    # Subtle diagonal gradient streak
    streak_x = int((frame_idx * 8) % (WIDTH + HEIGHT))
    for i in range(3):
        sx = streak_x - i*6
        sc = lerp_color(accent_rgb, BG, 0.9 + i*0.03)
        draw.line([sx, 0, sx-HEIGHT, HEIGHT], fill=sc, width=3-i)


# ══════════════════════════════════════════════════════════════════════════════
# UI ELEMENTS
# ══════════════════════════════════════════════════════════════════════════════

def draw_header(draw, scene):
    series  = scene.get("series", "Tech")
    chapter = scene.get("chapter", "")
    title   = scene.get("title", "Topic")
    accent  = hex2rgb(scene.get("accent", "#38BDF8"))

    # Series badge
    fnt_s = get_font(22, bold=True)
    badge_text = f"  {series} › {chapter}  "
    bbox = fnt_s.getbbox(badge_text)
    bw = bbox[2]-bbox[0]+20
    draw.rounded_rectangle([WIDTH//2-bw//2, 60, WIDTH//2+bw//2, 100], radius=10,
                            fill=lerp_color(accent, BG, 0.8), outline=accent, width=1)
    draw.text((WIDTH//2, 80), badge_text, font=fnt_s, fill=accent, anchor="mm")

    # Title
    fnt_t = get_font(72, bold=True)
    words = title.split()
    if len(words) >= 2:
        part1 = " ".join(words[:-1])
        part2 = words[-1]
        draw.text((WIDTH//2, 140), part1 + " ", font=fnt_t, fill=TEXT_W, anchor="rm")
        x_off = fnt_t.getlength(part1+" ")
        draw.text((WIDTH//2, 140), part2, font=fnt_t, fill=accent, anchor="lm")
    else:
        draw.text((WIDTH//2, 140), title, font=fnt_t, fill=accent, anchor="mm")

    # Subtitle
    fnt_sub = get_font(30)
    draw.text((WIDTH//2, 195), scene.get("subtitle",""), font=fnt_sub, fill=TEXT_DIM, anchor="mm")


def draw_hook(draw, hook_text):
    fnt = get_font(28)
    # Pill badge
    bbox = fnt.getbbox(hook_text)
    bw = min(bbox[2]-bbox[0]+40, WIDTH-80)
    x1 = WIDTH//2 - bw//2
    draw.rounded_rectangle([x1, 220, x1+bw, 265], radius=20,
                            fill=(255,255,255,15), outline=TEXT_DIM, width=1)
    # Truncate if needed
    draw.text((WIDTH//2, 242), hook_text[:60], font=fnt, fill=TEXT_W, anchor="mm")


def draw_counters(draw, scene, frame_idx, total_frames):
    ca = scene.get("counter_a", {"label":"PROCESSED","max":20})
    cb = scene.get("counter_b", {"label":"FAILED","max":3})

    prog = min(1.0, frame_idx / max(total_frames-1, 1))
    val_a = int(ca["max"] * prog)
    val_b = int(cb["max"] * prog)

    y_c = HEIGHT - 340
    # Counter A
    _draw_counter_badge(draw, 180, y_c, ca["label"], val_a, NEON["green"])
    # Counter B
    _draw_counter_badge(draw, WIDTH-180, y_c, cb["label"], val_b, NEON["red"])


def _draw_counter_badge(draw, cx, cy, label, value, color):
    bw, bh = 200, 70
    draw.rounded_rectangle([cx-bw//2, cy-bh//2, cx+bw//2, cy+bh//2],
                            radius=35, fill=lerp_color(color, BG, 0.85),
                            outline=color, width=2)
    # Checkmark or X icon
    icon = "✓" if color == NEON["green"] else "✗"
    fnt_icon = get_font(24, bold=True)
    fnt_num  = get_font(38, bold=True)
    fnt_lbl  = get_font(18)
    draw.text((cx-bw//2+24, cy), icon, font=fnt_icon, fill=color, anchor="mm")
    draw.text((cx+10, cy-8), str(value), font=fnt_num, fill=TEXT_W, anchor="mm")
    draw.text((cx+10, cy+20), label, font=fnt_lbl, fill=TEXT_DIM, anchor="mm")


def draw_caption(draw, text, step_progress=1.0):
    """Draw narration caption at bottom in a pill."""
    if not text:
        return
    # Word wrap
    words = text.split()
    lines = []
    line  = []
    fnt   = get_font(34)
    max_w = WIDTH - 100
    for w in words:
        test = " ".join(line + [w])
        if fnt.getlength(test) > max_w and line:
            lines.append(" ".join(line))
            line = [w]
        else:
            line.append(w)
    if line:
        lines.append(" ".join(line))

    line_h = 44
    total_h = len(lines) * line_h + 40
    y1 = HEIGHT - 120 - total_h
    draw.rounded_rectangle([40, y1, WIDTH-40, HEIGHT-100],
                            radius=20, fill=(10,15,35,200), outline=TEXT_DIM, width=1)
    for i, l in enumerate(lines):
        alpha_color = TEXT_W if step_progress > 0.2 else lerp_color(TEXT_DIM, TEXT_W, step_progress*5)
        draw.text((WIDTH//2, y1+25+i*line_h), l, font=fnt, fill=alpha_color, anchor="mm")


def draw_step_indicator(draw, step_idx, total_steps):
    """Small dots showing which step we're on."""
    dot_r = 6
    spacing = 20
    total_w = total_steps * spacing
    x0 = WIDTH//2 - total_w//2
    y  = HEIGHT - 75
    for i in range(total_steps):
        c = TEXT_W if i == step_idx else TEXT_DIM
        r = dot_r if i == step_idx else dot_r-2
        draw.ellipse([x0+i*spacing-r, y-r, x0+i*spacing+r, y+r], fill=c)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE CLASS
# ══════════════════════════════════════════════════════════════════════════════

class TechVisualEngine:
    FRAMES_PER_STEP = 60   # 2s per step at 30fps; actual duration set by audio

    def __init__(self, obj_a: str, obj_b: str):
        self.obj_a = obj_a
        self.obj_b = obj_b

    def render_all_frames(self, scene: dict, frame_dir: str) -> list:
        """Render all frames for the full video."""
        steps       = scene.get("steps", ["Loading..."])
        total_steps = len(steps)
        frame_paths = []
        frame_dir   = Path(frame_dir)
        frame_dir.mkdir(parents=True, exist_ok=True)

        global_frame = 0
        for step_idx, caption in enumerate(steps):
            n_frames = self.FRAMES_PER_STEP
            for f in range(n_frames):
                img  = Image.new("RGBA", (WIDTH, HEIGHT), BG)
                draw = ImageDraw.Draw(img)
                self._render_frame(draw, scene, step_idx, total_steps, caption, f, n_frames, global_frame)
                # Convert RGBA → RGB for PNG saving
                rgb_img = Image.new("RGB", (WIDTH, HEIGHT), BG)
                rgb_img.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
                path = str(frame_dir / f"frame_{global_frame:05d}.png")
                rgb_img.save(path)
                frame_paths.append(path)
                global_frame += 1

        print(f"  Rendered {global_frame} frames ({total_steps} steps × {self.FRAMES_PER_STEP} frames)")
        return frame_paths

    def _render_frame(self, draw, scene, step_idx, total_steps, caption, f, n_frames, global_frame):
        accent  = hex2rgb(scene.get("accent", "#38BDF8"))
        nodes   = scene.get("nodes", [])
        paths   = scene.get("paths", [])
        node_map = {n["id"]: n for n in nodes}
        step_progress = f / max(n_frames-1, 1)

        # ── Background ────────────────────────────────────────────────────────
        draw_background(draw, accent, global_frame)

        # ── Header ────────────────────────────────────────────────────────────
        draw_header(draw, scene)
        draw_hook(draw, scene.get("hook", ""))

        # ── Which paths are active this step ──────────────────────────────────
        active_paths = self._active_paths_for_step(paths, step_idx, total_steps)

        # ── Draw connections ──────────────────────────────────────────────────
        for p_idx, path in enumerate(paths):
            n1 = node_map.get(path["from"])
            n2 = node_map.get(path["to"])
            if n1 and n2:
                if p_idx in active_paths:
                    obj = self.obj_a if p_idx % 2 == 0 else self.obj_b
                    progress = (step_progress + p_idx * 0.37) % 1.0
                    clr = n1.get("color", scene.get("accent", "#38BDF8"))
                    draw_connection(draw, n1, n2, progress, obj, clr, global_frame)
                else:
                    # Inactive: dim line only
                    c = hex2rgb(n1.get("color", "#334155"))
                    gc = lerp_color(c, BG, 0.7)
                    draw.line([n1["x"], n1["y"], n2["x"], n2["y"]], fill=gc, width=2)

        # ── Draw nodes ────────────────────────────────────────────────────────
        highlighted = self._highlighted_nodes(active_paths, paths, step_idx)
        for node in nodes:
            hl = node["id"] in highlighted
            draw_node(draw, node, highlight=hl, frame_idx=global_frame)

        # ── Extra roaming objects (random positions, not on paths) ────────────
        self._draw_roaming_objects(draw, scene, step_idx, step_progress, global_frame)

        # ── Counters ─────────────────────────────────────────────────────────
        total_frames = total_steps * n_frames
        draw_counters(draw, scene, global_frame, total_frames)

        # ── Caption ──────────────────────────────────────────────────────────
        draw_caption(draw, caption, step_progress)

        # ── Step indicators ──────────────────────────────────────────────────
        draw_step_indicator(draw, step_idx, total_steps)

    def _active_paths_for_step(self, paths, step_idx, total_steps):
        """Return indices of active paths for this step."""
        if not paths:
            return set()
        n = len(paths)
        # Progressive reveal: each step activates one more path
        active_count = max(1, (step_idx + 1) * n // total_steps)
        return set(range(min(active_count, n)))

    def _highlighted_nodes(self, active_path_indices, paths, step_idx):
        """Nodes involved in active paths."""
        highlighted = set()
        for i in active_path_indices:
            if i < len(paths):
                highlighted.add(paths[i]["from"])
                highlighted.add(paths[i]["to"])
        return highlighted

    def _draw_roaming_objects(self, draw, scene, step_idx, step_progress, global_frame):
        """Draw extra animated objects floating around the diagram area."""
        random.seed(step_idx * 17 + 42)
        n_roamers = random.randint(2, 4)
        nodes = scene.get("nodes", [])
        accent = hex2rgb(scene.get("accent", "#38BDF8"))

        for i in range(n_roamers):
            obj = [self.obj_a, self.obj_b][i % 2]
            # Circular orbit around center of diagram
            center_x = sum(n["x"] for n in nodes) // max(len(nodes), 1) if nodes else WIDTH//2
            center_y = sum(n["y"] for n in nodes) // max(len(nodes), 1) if nodes else HEIGHT//2
            orbit_r  = 80 + i * 60
            angle    = math.radians((global_frame * (3 + i) + i * 120) % 360)
            ox = center_x + int(math.cos(angle) * orbit_r)
            oy = center_y + int(math.sin(angle) * orbit_r)
            # Keep in diagram area
            ox = max(50, min(WIDTH-50, ox))
            oy = max(300, min(HEIGHT-400, oy))
            c  = lerp_color(accent, NEON["purple"], i * 0.3)
            draw_object(draw, obj, ox, oy, 28, c, frame_idx=global_frame)

    def render_thumbnail(self, scene: dict) -> Image.Image:
        """Render a single thumbnail frame."""
        img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)
        accent = hex2rgb(scene.get("accent", "#38BDF8"))
        draw_background(draw, accent, 0)
        draw_header(draw, scene)
        draw_hook(draw, scene.get("hook", ""))

        # Draw all nodes highlighted
        nodes = scene.get("nodes", [])
        for node in nodes:
            draw_node(draw, node, highlight=True, frame_idx=0)

        # Draw objects at interesting positions
        if nodes:
            cx = WIDTH // 2
            cy = HEIGHT // 2
            draw_object(draw, self.obj_a, cx-150, cy, 60, accent, frame_idx=0)
            draw_object(draw, self.obj_b, cx+150, cy, 60, NEON["purple"], frame_idx=0)

        # Big caption: first step
        steps = scene.get("steps", [])
        if steps:
            draw_caption(draw, steps[0], step_progress=1.0)

        return img
