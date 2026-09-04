"""
Bio Bone & Anatomy Renderer
============================
Renders distinct, anatomically accurate biological creatures for Code Reels.
Provides unique skeletons, heads, tails, and surface patterns for:
- Quadrupeds: Lion, Tiger, Giraffe, Rhinoceros, Elephant, Bear, Cheetah/Leopard, Wolf, Fox, Canine
- Serpents: Cobra (flared hood), Viper (triangular head & rattle), Sea Snake
- Arachnids: Spider (bulbous abdomen, fangs), Scorpion (chelae, stinger tail)
"""
from __future__ import annotations

import math
from PIL import ImageDraw

def _clamp(v, low=0, high=255):
    return max(low, min(high, int(v)))

def _brighten(rgb: tuple[int, int, int], amount: int = 30) -> tuple[int, int, int]:
    return (_clamp(rgb[0] + amount), _clamp(rgb[1] + amount), _clamp(rgb[2] + amount))

def _darken(rgb: tuple[int, int, int], amount: int = 30) -> tuple[int, int, int]:
    return (_clamp(rgb[0] - amount), _clamp(rgb[1] - amount), _clamp(rgb[2] - amount))

def solve_forelimb_ik(shoulder, paw, l1, l2, side):
    dx = paw[0] - shoulder[0]
    dy = paw[1] - shoulder[1]
    dist = math.hypot(dx, dy)
    clamped = min(dist, l1 + l2 - 0.001)
    base = math.atan2(dy, dx)
    cos_a = (l1 * l1 + clamped * clamped - l2 * l2) / (2 * l1 * clamped)
    ang = base - math.acos(max(-1.0, min(1.0, cos_a))) * side * 0.92
    elbow = (shoulder[0] + math.cos(ang) * l1, shoulder[1] + math.sin(ang) * l1)
    return shoulder, elbow, paw

def draw_bio_quadruped(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    sp_id = species.get("id", "").lower()
    name = species.get("name", "").upper()
    
    fur_dark   = tuple(species.get("fur_dark",      [120, 60,  5]))
    fur_mid    = tuple(species.get("fur_mid",       [190, 110, 20]))
    fur_gold   = tuple(species.get("fur_gold",      [230, 160, 45]))
    fur_light  = tuple(species.get("fur_light",     [255, 210, 100]))
    fur_cream  = tuple(species.get("fur_cream",     [255, 235, 170]))
    accent     = tuple(species.get("accent",        [245, 158, 11]))

    is_lion     = "lion" in sp_id or "lion" in name
    is_tiger    = "tiger" in sp_id or "tiger" in name
    is_giraffe  = "giraffe" in sp_id or "giraffe" in name
    is_rhino    = "rhino" in sp_id or "rhino" in name
    is_elephant = "elephant" in sp_id or "elephant" in name
    is_bear     = "bear" in sp_id or "panda" in sp_id or "bear" in name
    is_cheetah  = "cheetah" in sp_id or "leopard" in sp_id or "jaguar" in sp_id or "ocelot" in sp_id or "serval" in sp_id
    is_wolf     = "wolf" in sp_id or "coyote" in sp_id or "hyena" in sp_id
    is_fox      = "fox" in sp_id

    def draw_limb(p1, p2, base_w, dark_col, mid_col):
        dx = p2[0] - p1[0]; dy = p2[1] - p1[1]
        ln = math.hypot(dx, dy)
        if ln < 1: return
        nx = -dy / ln; ny = dx / ln
        draw.line([p1, p2], fill=dark_col, width=base_w + 6)
        draw.line([p1, p2], fill=mid_col, width=base_w)
        hi = _brighten(mid_col, 35)
        draw.line([(p1[0]+nx*2.5, p1[1]+ny*2.5), (p2[0]+nx*2.5, p2[1]+ny*2.5)], fill=hi, width=max(2, base_w // 3))

    leg_width = 32 if (is_rhino or is_elephant or is_bear) else (18 if is_giraffe else 24)

    # A. HINDLEGS
    for leg in [l for l in sim.legs4 if not l["is_front"]]:
        paw_pos = (leg["cur"][0], leg["cur"][1])
        sock = leg["socket"]
        side = leg["side"]
        thigh_end = (sock[0] + cos_a * 36 + perp_x * (24 * side), sock[1] + sin_a * 36 + perp_y * (24 * side))
        draw_limb(sock, thigh_end, leg_width + 4, fur_dark, fur_mid)
        shin_end = (thigh_end[0] - cos_a * 34 + perp_x * (16 * side), thigh_end[1] - sin_a * 34 + perp_y * (16 * side))
        draw_limb(thigh_end, shin_end, leg_width, fur_dark, fur_gold)
        draw.ellipse([thigh_end[0]-10, thigh_end[1]-10, thigh_end[0]+10, thigh_end[1]+10], fill=fur_dark)
        hock = (shin_end[0] - cos_a * 10 + perp_x * (12 * side), shin_end[1] - sin_a * 10 + perp_y * (12 * side))
        draw_limb(shin_end, hock, max(12, leg_width - 4), fur_dark, fur_mid)
        draw_limb(hock, paw_pos, max(12, leg_width - 6), fur_dark, fur_mid)
        if is_giraffe or is_rhino:
            draw.ellipse([paw_pos[0]-14, paw_pos[1]-9, paw_pos[0]+14, paw_pos[1]+9], fill=(25, 20, 18), outline=(60, 50, 45), width=2)
        else:
            draw.ellipse([paw_pos[0]-14, paw_pos[1]-10, paw_pos[0]+14, paw_pos[1]+10], fill=(30, 22, 16), outline=fur_dark, width=2)

    # B. FORELEGS
    for leg in [l for l in sim.legs4 if l["is_front"]]:
        paw_pos = (leg["cur"][0], leg["cur"][1])
        sock = leg["socket"]
        side = leg["side"]
        _, elbow, _ = solve_forelimb_ik(sock, paw_pos, leg["l1"], leg["l2"], side)
        draw_limb(sock, elbow, leg_width + 2, fur_dark, fur_mid)
        draw.ellipse([elbow[0]-10, elbow[1]-10, elbow[0]+10, elbow[1]+10], fill=fur_dark)
        draw_limb(elbow, paw_pos, leg_width, fur_dark, fur_gold)
        if is_giraffe or is_rhino:
            draw.ellipse([paw_pos[0]-14, paw_pos[1]-9, paw_pos[0]+14, paw_pos[1]+9], fill=(25, 20, 18), outline=(60, 50, 45), width=2)
        else:
            draw.ellipse([paw_pos[0]-14, paw_pos[1]-10, paw_pos[0]+14, paw_pos[1]+10], fill=(30, 22, 16), outline=fur_dark, width=2)

    # C. BODY SILHOUETTE
    spine_pts = [(seg["x"], seg["y"]) for seg in sim.spine[:16]]
    left_out, right_out = [], []
    
    if is_rhino or is_elephant or is_bear:
        body_widths = [36, 48, 62, 70, 68, 66, 64, 62, 58, 60, 62, 56, 48, 38, 28, 20]
    elif is_giraffe:
        body_widths = [22, 28, 38, 44, 42, 40, 38, 36, 34, 38, 40, 36, 30, 24, 18, 12]
    elif is_cheetah:
        body_widths = [24, 30, 40, 46, 42, 38, 36, 34, 32, 36, 42, 38, 30, 22, 16, 12]
    else:
        body_widths = [28, 36, 46, 54, 52, 50, 48, 44, 40, 44, 48, 44, 36, 28, 20, 14]

    for i, seg in enumerate(sim.spine[:16]):
        s_px = -math.sin(seg["angle"]); s_py = math.cos(seg["angle"])
        hw = max(10, body_widths[i] if i < len(body_widths) else 14)
        left_out.append((seg["x"] + s_px * (hw + 4), seg["y"] + s_py * (hw + 4)))
        right_out.append((seg["x"] - s_px * (hw + 4), seg["y"] - s_py * (hw + 4)))

    shadow_pts = [(x+6, y+6) for x,y in left_out] + list(reversed([(x+6, y+6) for x,y in right_out]))
    if len(shadow_pts) >= 3: draw.polygon(shadow_pts, fill=(35, 20, 10))

    body_poly = left_out + list(reversed(right_out))
    if len(body_poly) >= 3:
        draw.polygon(body_poly, fill=fur_mid, outline=fur_dark, width=3)

    mid_poly = [(x*0.5 + spine_pts[min(i, len(spine_pts)-1)][0]*0.5,
                 y*0.5 + spine_pts[min(i, len(spine_pts)-1)][1]*0.5)
                for i, (x, y) in enumerate(left_out[:14])] +                list(reversed([(x*0.5 + spine_pts[min(i, len(spine_pts)-1)][0]*0.5,
                               y*0.5 + spine_pts[min(i, len(spine_pts)-1)][1]*0.5)
                              for i, (x, y) in enumerate(right_out[:14])]))
    if len(mid_poly) >= 3:
        draw.polygon(mid_poly, fill=fur_gold)

    # D. SURFACE TEXTURES & PATTERNS
    if is_tiger:
        for i in range(2, 14, 2):
            sp = spine_pts[i]
            s_px = -math.sin(sim.spine[i]["angle"]); s_py = math.cos(sim.spine[i]["angle"])
            w = body_widths[i] * 0.88
            draw.line([(sp[0] - s_px * w, sp[1] - s_py * w), (sp[0] + s_px * w, sp[1] + s_py * w)], fill=(20, 15, 12), width=5)
    elif is_giraffe:
        for i in range(2, 14):
            sp = spine_pts[i]
            s_px = -math.sin(sim.spine[i]["angle"]); s_py = math.cos(sim.spine[i]["angle"])
            for offset_f in [-0.5, 0.5]:
                px = sp[0] + s_px * (body_widths[i] * offset_f)
                py = sp[1] + s_py * (body_widths[i] * offset_f)
                pw, ph = 12, 10
                patch = [(px - pw, py - ph), (px + pw + 2, py - ph + 3), (px + pw - 2, py + ph), (px - pw + 1, py + ph - 2)]
                draw.polygon(patch, fill=fur_dark, outline=(180, 120, 40), width=1)
    elif is_cheetah:
        for i in range(2, 14):
            sp = spine_pts[i]
            s_px = -math.sin(sim.spine[i]["angle"]); s_py = math.cos(sim.spine[i]["angle"])
            for off in [-0.6, -0.2, 0.2, 0.6]:
                sx = sp[0] + s_px * (body_widths[i] * off)
                sy = sp[1] + s_py * (body_widths[i] * off)
                draw.ellipse([sx-4, sy-4, sx+4, sy+4], fill=(25, 20, 15), outline=fur_dark, width=1)
    elif is_rhino:
        for i in [3, 7, 11]:
            sp = spine_pts[i]
            s_px = -math.sin(sim.spine[i]["angle"]); s_py = math.cos(sim.spine[i]["angle"])
            w = body_widths[i] + 4
            draw.arc([sp[0] - w, sp[1] - w, sp[0] + w, sp[1] + w], 0, 360, fill=(40, 35, 30), width=3)

    # E. TAIL
    tail_prev = spine_pts[-1]
    wag = math.sin(sim_time * 6.5) * (0.3 if is_bear or is_rhino else 0.7)
    
    if is_bear:
        tx = tail_prev[0] - cos_a * 14 + wag * 5
        ty = tail_prev[1] - sin_a * 14 + wag * 5
        draw.ellipse([tx-10, ty-10, tx+10, ty+10], fill=fur_dark, outline=fur_mid, width=2)
    elif is_rhino:
        t_mid = (tail_prev[0] - cos_a * 25 + wag * 8, tail_prev[1] - sin_a * 25 + wag * 8)
        draw.line([tail_prev, t_mid], fill=fur_dark, width=5)
        draw.ellipse([t_mid[0]-4, t_mid[1]-4, t_mid[0]+4, t_mid[1]+4], fill=(20, 15, 10))
    elif is_lion or is_giraffe:
        for i in range(10):
            t_ang = sim.angle + math.pi + wag * ((i + 1) / 10)
            tx = tail_prev[0] + math.cos(t_ang) * 16
            ty = tail_prev[1] + math.sin(t_ang) * 16
            draw.line([tail_prev, (tx, ty)], fill=fur_mid, width=max(3, 8 - i // 2))
            tail_prev = (tx, ty)
        draw.ellipse([tail_prev[0]-12, tail_prev[1]-12, tail_prev[0]+12, tail_prev[1]+12], fill=(25, 18, 10), outline=fur_dark, width=2)
    elif is_fox or is_wolf:
        for i in range(12):
            t_ang = sim.angle + math.pi + wag * ((i + 1) / 12)
            tx = tail_prev[0] + math.cos(t_ang) * 18
            ty = tail_prev[1] + math.sin(t_ang) * 18
            bw = int(14 + math.sin(i / 12 * math.pi) * 16)
            draw.line([tail_prev, (tx, ty)], fill=fur_dark, width=bw + 4)
            draw.line([tail_prev, (tx, ty)], fill=fur_gold, width=bw)
            tail_prev = (tx, ty)
        if is_fox:
            draw.ellipse([tail_prev[0]-9, tail_prev[1]-9, tail_prev[0]+9, tail_prev[1]+9], fill=(250, 245, 235))
    else:
        for i in range(12):
            t_ang = sim.angle + math.pi + wag * ((i + 1) / 12)
            tx = tail_prev[0] + math.cos(t_ang) * 18
            ty = tail_prev[1] + math.sin(t_ang) * 18
            w = max(4, int(20 - i * 1.4))
            draw.line([tail_prev, (tx, ty)], fill=fur_dark, width=w + 3)
            draw.line([tail_prev, (tx, ty)], fill=fur_gold, width=w)
            tail_prev = (tx, ty)

    # F. DISTINCT HEAD ANATOMY
    if is_giraffe:
        neck_len = 80
        hx = sim.x + cos_a * neck_len
        hy = sim.y + sin_a * neck_len
        draw.line([(sim.x, sim.y), (hx, hy)], fill=fur_dark, width=28)
        draw.line([(sim.x, sim.y), (hx, hy)], fill=fur_mid, width=22)
        draw.line([(sim.x, sim.y), (hx, hy)], fill=fur_gold, width=14)
        draw.ellipse([hx-20, hy-18, hx+20, hy+18], fill=fur_mid, outline=fur_dark, width=2)
        sn_x, sn_y = hx + cos_a * 24, hy + sin_a * 24
        draw.ellipse([sn_x-12, sn_y-10, sn_x+12, sn_y+10], fill=fur_dark, outline=(30, 25, 20), width=2)
        for s in [-1, 1]:
            ox = hx - cos_a * 6 + perp_x * (14 * s)
            oy = hy - sin_a * 6 + perp_y * (14 * s)
            ot_x = ox + cos_a * 20 + perp_x * (10 * s)
            ot_y = oy + sin_a * 20 + perp_y * (10 * s)
            draw.line([(ox, oy), (ot_x, ot_y)], fill=fur_dark, width=5)
            draw.ellipse([ot_x-6, ot_y-6, ot_x+6, ot_y+6], fill=(25, 18, 12))
        for s in [-1, 1]:
            ex = hx - cos_a * 10 + perp_x * (22 * s)
            ey = hy - sin_a * 10 + perp_y * (22 * s)
            draw.ellipse([ex-6, ey-4, ex+6, ey+4], fill=fur_mid, outline=fur_dark, width=1)
        for s in [-1, 1]:
            eye_pt = (hx + cos_a * 6 + perp_x * (14 * s), hy + sin_a * 6 + perp_y * (14 * s))
            draw.ellipse([eye_pt[0]-5, eye_pt[1]-5, eye_pt[0]+5, eye_pt[1]+5], fill=(20, 15, 10))
            draw.ellipse([eye_pt[0]+1, eye_pt[1]-1, eye_pt[0]+3, eye_pt[1]+1], fill=(255, 255, 255))

    elif is_lion:
        hx = sim.x + cos_a * 44
        hy = sim.y + sin_a * 44
        mane_col = _darken(fur_dark, 20)
        draw.ellipse([hx-46, hy-46, hx+46, hy+46], fill=mane_col, outline=(30, 15, 5), width=3)
        draw.ellipse([hx-38, hy-38, hx+38, hy+38], fill=fur_dark)
        draw.ellipse([hx-30, hy-30, hx+30, hy+30], fill=fur_mid)
        draw.ellipse([hx-24, hy-22, hx+24, hy+22], fill=fur_gold)
        for s in [-1, 1]:
            ex = hx - cos_a * 14 + perp_x * (30 * s)
            ey = hy - sin_a * 14 + perp_y * (30 * s)
            draw.ellipse([ex-9, ey-9, ex+9, ey+9], fill=mane_col, outline=(20, 10, 5), width=2)
            draw.ellipse([ex-5, ey-5, ex+5, ey+5], fill=(210, 140, 130))
        sn_x, sn_y = hx + cos_a * 22, hy + sin_a * 22
        draw.ellipse([sn_x-15, sn_y-12, sn_x+15, sn_y+12], fill=fur_cream, outline=fur_mid, width=2)
        nose_x, nose_y = sn_x + cos_a * 8, sn_y + sin_a * 8
        draw.polygon([(nose_x - perp_x * 8, nose_y - perp_y * 8),
                      (nose_x + perp_x * 8, nose_y + perp_y * 8),
                      (nose_x + cos_a * 6, nose_y + sin_a * 6)], fill=(50, 30, 25))
        for s in [-1, 1]:
            eye_pt = (hx + cos_a * 6 + perp_x * (15 * s), hy + sin_a * 6 + perp_y * (15 * s))
            draw.ellipse([eye_pt[0]-7, eye_pt[1]-6, eye_pt[0]+7, eye_pt[1]+6], fill=(30, 20, 5))
            draw.ellipse([eye_pt[0]-5, eye_pt[1]-5, eye_pt[0]+5, eye_pt[1]+5], fill=(245, 175, 20))
            draw.line([(eye_pt[0], eye_pt[1]-4), (eye_pt[0], eye_pt[1]+4)], fill=(10, 5, 2), width=2)

    elif is_rhino:
        hx = sim.x + cos_a * 44
        hy = sim.y + sin_a * 44
        draw.ellipse([hx-26, hy-24, hx+26, hy+24], fill=fur_mid, outline=fur_dark, width=3)
        sn_x, sn_y = hx + cos_a * 26, hy + sin_a * 26
        draw.ellipse([sn_x-18, sn_y-15, sn_x+18, sn_y+15], fill=fur_dark, outline=(30, 25, 20), width=2)
        horn_tip = (sn_x + cos_a * 46, sn_y + sin_a * 46)
        horn_b1 = (sn_x + cos_a * 8 + perp_x * 8, sn_y + sin_a * 8 + perp_y * 8)
        horn_b2 = (sn_x + cos_a * 8 - perp_x * 8, sn_y + sin_a * 8 - perp_y * 8)
        draw.polygon([horn_b1, horn_tip, horn_b2], fill=(220, 210, 190), outline=(50, 45, 40), width=2)
        horn2_tip = (sn_x + cos_a * 20, sn_y + sin_a * 20)
        horn2_b1 = (sn_x - cos_a * 4 + perp_x * 6, sn_y - sin_a * 4 + perp_y * 6)
        horn2_b2 = (sn_x - cos_a * 4 - perp_x * 6, sn_y - sin_a * 4 - perp_y * 6)
        draw.polygon([horn2_b1, horn2_tip, horn2_b2], fill=(180, 170, 150), outline=(40, 35, 30), width=2)
        for s in [-1, 1]:
            ex = hx - cos_a * 16 + perp_x * (24 * s)
            ey = hy - sin_a * 16 + perp_y * (24 * s)
            draw.ellipse([ex-6, ey-6, ex+6, ey+6], fill=fur_dark)
        for s in [-1, 1]:
            eye_pt = (hx + cos_a * 2 + perp_x * (18 * s), hy + sin_a * 2 + perp_y * (18 * s))
            draw.ellipse([eye_pt[0]-4, eye_pt[1]-4, eye_pt[0]+4, eye_pt[1]+4], fill=(15, 12, 10))

    elif is_elephant:
        hx = sim.x + cos_a * 44
        hy = sim.y + sin_a * 44
        for s in [-1, 1]:
            ex = hx - cos_a * 8 + perp_x * (45 * s)
            ey = hy - sin_a * 8 + perp_y * (45 * s)
            draw.ellipse([ex-24, ey-24, ex+24, ey+24], fill=fur_dark, outline=(50, 45, 40), width=2)
            draw.ellipse([ex-16, ey-16, ex+16, ey+16], fill=fur_mid)
        draw.ellipse([hx-32, hy-30, hx+32, hy+30], fill=fur_mid, outline=fur_dark, width=3)
        for s in [-1, 1]:
            tb = (hx + cos_a * 18 + perp_x * (18 * s), hy + sin_a * 18 + perp_y * (18 * s))
            tt = (hx + cos_a * 44 + perp_x * (28 * s), hy + sin_a * 44 + perp_y * (28 * s))
            draw.line([tb, tt], fill=(245, 240, 220), width=6)
        t_prev = (hx + cos_a * 24, hy + sin_a * 24)
        trunk_wave = math.sin(sim_time * 5.0) * 0.4
        for i in range(8):
            t_ang = sim.angle + trunk_wave * ((i + 1) / 8)
            tx = t_prev[0] + math.cos(t_ang) * 12
            ty = t_prev[1] + math.sin(t_ang) * 12
            draw.line([t_prev, (tx, ty)], fill=fur_dark, width=max(4, 18 - i * 1.8))
            draw.line([t_prev, (tx, ty)], fill=fur_mid, width=max(2, 14 - i * 1.8))
            t_prev = (tx, ty)

    elif is_bear:
        hx = sim.x + cos_a * 40
        hy = sim.y + sin_a * 40
        draw.ellipse([hx-30, hy-28, hx+30, hy+28], fill=fur_dark, outline=(30, 20, 10), width=3)
        draw.ellipse([hx-22, hy-20, hx+22, hy+20], fill=fur_mid)
        for s in [-1, 1]:
            ex = hx - cos_a * 16 + perp_x * (26 * s)
            ey = hy - sin_a * 16 + perp_y * (26 * s)
            draw.ellipse([ex-10, ey-10, ex+10, ey+10], fill=fur_dark, outline=(25, 18, 12), width=2)
            draw.ellipse([ex-6, ey-6, ex+6, ey+6], fill=fur_gold)
        sn_x, sn_y = hx + cos_a * 20, hy + sin_a * 20
        draw.ellipse([sn_x-16, sn_y-13, sn_x+16, sn_y+13], fill=fur_gold, outline=fur_dark, width=2)
        draw.ellipse([sn_x+cos_a*6-7, sn_y+sin_a*6-6, sn_x+cos_a*6+7, sn_y+sin_a*6+6], fill=(20, 15, 10))
        for s in [-1, 1]:
            eye_pt = (hx + cos_a * 4 + perp_x * (15 * s), hy + sin_a * 4 + perp_y * (15 * s))
            draw.ellipse([eye_pt[0]-5, eye_pt[1]-5, eye_pt[0]+5, eye_pt[1]+5], fill=(15, 10, 5))

    elif is_wolf or is_fox:
        hx = sim.x + cos_a * 44
        hy = sim.y + sin_a * 44
        draw.ellipse([hx-24, hy-22, hx+24, hy+22], fill=fur_mid, outline=fur_dark, width=2)
        for s in [-1, 1]:
            eb1 = (hx - cos_a * 4 + perp_x * (12 * s), hy - sin_a * 4 + perp_y * (12 * s))
            eb2 = (hx - cos_a * 18 + perp_x * (24 * s), hy - sin_a * 18 + perp_y * (24 * s))
            etip = (hx + cos_a * 8 + perp_x * (32 * s), hy + sin_a * 8 + perp_y * (32 * s))
            draw.polygon([eb1, eb2, etip], fill=fur_dark, outline=(20, 15, 10), width=2)
            draw.polygon([eb1, eb2, (etip[0]-perp_x*(4*s), etip[1]-perp_y*(4*s))], fill=fur_cream)
        sn_x, sn_y = hx + cos_a * 28, hy + sin_a * 28
        draw.ellipse([sn_x-12, sn_y-10, sn_x+12, sn_y+10], fill=fur_cream, outline=fur_dark, width=2)
        draw.ellipse([sn_x+cos_a*8-6, sn_y+sin_a*8-5, sn_x+cos_a*8+6, sn_y+sin_a*8+5], fill=(20, 15, 10))
        for s in [-1, 1]:
            eye_pt = (hx + cos_a * 6 + perp_x * (14 * s), hy + sin_a * 6 + perp_y * (14 * s))
            draw.ellipse([eye_pt[0]-6, eye_pt[1]-5, eye_pt[0]+6, eye_pt[1]+5], fill=(20, 10, 5))
            draw.ellipse([eye_pt[0]-4, eye_pt[1]-3.5, eye_pt[0]+4, eye_pt[1]+3.5], fill=(235, 180, 20))
            draw.ellipse([eye_pt[0]-1.5, eye_pt[1]-2, eye_pt[0]+1.5, eye_pt[1]+2], fill=(5, 3, 1))

    else:
        hx = sim.x + cos_a * 44
        hy = sim.y + sin_a * 44
        draw.ellipse([hx-26, hy-24, hx+26, hy+24], fill=fur_mid, outline=fur_dark, width=2)
        draw.ellipse([hx+cos_a*4-10, hy+sin_a*4-10, hx+cos_a*4+10, hy+sin_a*4+10], fill=fur_gold)
        for s in [-1, 1]:
            eb = (hx - cos_a * 12 + perp_x * (20 * s), hy - sin_a * 12 + perp_y * (20 * s))
            etip = (eb[0] - cos_a * 24 + perp_x * (12 * s), eb[1] - sin_a * 24 + perp_y * (12 * s))
            draw.line([eb, etip], fill=fur_dark, width=12)
        sn_x, sn_y = hx + cos_a * 28, hy + sin_a * 28
        draw.ellipse([sn_x-14, sn_y-11, sn_x+14, sn_y+11], fill=fur_cream, outline=fur_mid, width=2)
        draw.ellipse([sn_x+cos_a*8-7, sn_y+sin_a*8-5, sn_x+cos_a*8+7, sn_y+sin_a*8+5], fill=(20, 15, 10))
        for s in [-1, 1]:
            eye_pt = (hx + cos_a * 8 + perp_x * (15 * s), hy + sin_a * 8 + perp_y * (15 * s))
            draw.ellipse([eye_pt[0]-6, eye_pt[1]-5, eye_pt[0]+6, eye_pt[1]+5], fill=(235, 170, 30))

def draw_bio_serpent(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    sp_id = species.get("id", "").lower()
    accent = tuple(species.get("accent", [16, 185, 129]))
    is_cobra = "cobra" in sp_id or "naja" in sp_id
    is_rattlesnake = "rattle" in sp_id or "viper" in sp_id

    spine = sim.spine[:18]
    left_pts, right_pts = [], []
    for i, seg in enumerate(spine):
        s_px = -math.sin(seg["angle"]); s_py = math.cos(seg["angle"])
        if is_cobra and 1 <= i <= 4:
            hw = 48 - (i - 2)**2 * 6
        else:
            hw = max(8, 28 - i * 1.3)
        left_pts.append((seg["x"] + s_px * hw, seg["y"] + s_py * hw))
        right_pts.append((seg["x"] - s_px * hw, seg["y"] - s_py * hw))

    shadow_pts = [(x+5, y+5) for x,y in left_pts] + list(reversed([(x+5, y+5) for x,y in right_pts]))
    if len(shadow_pts) >= 3: draw.polygon(shadow_pts, fill=(15, 20, 25))

    body_poly = left_pts + list(reversed(right_pts))
    if len(body_poly) >= 3:
        draw.polygon(body_poly, fill=(20, 35, 30), outline=accent, width=2)

    for i in range(1, len(spine)-1, 2):
        sp = spine[i]
        draw.ellipse([sp["x"]-6, sp["y"]-6, sp["x"]+6, sp["y"]+6], fill=accent)

    if is_cobra:
        h_seg = spine[2]
        draw.ellipse([h_seg["x"]-14, h_seg["y"]-14, h_seg["x"]+14, h_seg["y"]+14], outline=(255, 255, 255), width=2)
        draw.ellipse([h_seg["x"]-5, h_seg["y"]-5, h_seg["x"]+5, h_seg["y"]+5], fill=accent)

    t_end = (spine[-1]["x"], spine[-1]["y"])
    if is_rattlesnake:
        for r in range(4):
            rx = t_end[0] - cos_a * (r * 7)
            ry = t_end[1] - sin_a * (r * 7)
            draw.ellipse([rx-6, ry-6, rx+6, ry+6], fill=(210, 180, 130), outline=(50, 40, 30), width=1)

    hx = sim.x + cos_a * 35
    hy = sim.y + sin_a * 35
    if is_rattlesnake or "viper" in sp_id:
        h_front = (hx + cos_a * 22, hy + sin_a * 22)
        h_l = (hx - cos_a * 12 + perp_x * 24, hy - sin_a * 12 + perp_y * 24)
        h_r = (hx - cos_a * 12 - perp_x * 24, hy - sin_a * 12 - perp_y * 24)
        draw.polygon([h_front, h_l, h_r], fill=(25, 45, 35), outline=accent, width=2)
    else:
        draw.ellipse([hx-18, hy-14, hx+18, hy+14], fill=(25, 45, 35), outline=accent, width=2)

    for s in [-1, 1]:
        ep = (hx + cos_a * 8 + perp_x * (14 * s), hy + sin_a * 8 + perp_y * (14 * s))
        draw.ellipse([ep[0]-5, ep[1]-5, ep[0]+5, ep[1]+5], fill=(245, 180, 20))
        draw.line([(ep[0], ep[1]-3), (ep[0], ep[1]+3)], fill=(0, 0, 0), width=2)

    tongue_f = math.sin(sim_time * 12)
    if tongue_f > 0.4:
        tb = (hx + cos_a * 20, hy + sin_a * 20)
        tm = (tb[0] + cos_a * 18, tb[1] + sin_a * 18)
        draw.line([tb, tm], fill=(230, 40, 60), width=2)
        draw.line([tm, (tm[0] + cos_a * 8 + perp_x * 6, tm[1] + sin_a * 8 + perp_y * 6)], fill=(230, 40, 60), width=2)
        draw.line([tm, (tm[0] + cos_a * 8 - perp_x * 6, tm[1] - sin_a * 8 - perp_y * 6)], fill=(230, 40, 60), width=2)

def draw_bio_arachnid(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    sp_id = species.get("id", "").lower()
    accent = tuple(species.get("accent", [239, 68, 68]))
    is_spider = "spider" in sp_id or "tarantula" in sp_id or "widow" in sp_id

    if is_spider:
        for leg in sim.legs8:
            hp = leg["hip"]
            foot = (leg["cur"][0], leg["cur"][1])
            knee = ((hp[0] + foot[0]) / 2 + perp_x * (20 * leg["side"]),
                    (hp[1] + foot[1]) / 2 + perp_y * (20 * leg["side"]))
            draw.line([hp, knee], fill=(25, 20, 25), width=7)
            draw.line([knee, foot], fill=(35, 28, 35), width=5)
            draw.ellipse([knee[0]-4, knee[1]-4, knee[0]+4, knee[1]+4], fill=accent)
            draw.ellipse([foot[0]-3, foot[1]-3, foot[0]+3, foot[1]+3], fill=(10, 10, 10))

        ab_x = sim.x - cos_a * 46
        ab_y = sim.y - sin_a * 46
        draw.ellipse([ab_x-36, ab_y-36, ab_x+36, ab_y+36], fill=(18, 14, 20), outline=(40, 30, 45), width=3)
        draw.polygon([(ab_x - 10, ab_y - 12), (ab_x + 10, ab_y - 12), (ab_x, ab_y),
                      (ab_x + 10, ab_y + 12), (ab_x - 10, ab_y + 12)], fill=accent)

        draw.ellipse([sim.x-24, sim.y-22, sim.x+24, sim.y+22], fill=(25, 20, 28), outline=accent, width=2)
        f_l = (sim.x + cos_a * 24 + perp_x * 8, sim.y + sin_a * 24 + perp_y * 8)
        f_r = (sim.x + cos_a * 24 - perp_x * 8, sim.y + sin_a * 24 - perp_y * 8)
        draw.line([f_l, (f_l[0] + cos_a * 10 - perp_x * 4, f_l[1] + sin_a * 10 - perp_y * 4)], fill=accent, width=3)
        draw.line([f_r, (f_r[0] + cos_a * 10 + perp_x * 4, f_r[1] + sin_a * 10 + perp_y * 4)], fill=accent, width=3)

        for ex, ey in [(-6, -4), (0, -6), (6, -4), (-4, 2), (4, 2), (-8, 0), (8, 0), (0, 0)]:
            ep = (sim.x + cos_a * 12 + perp_x * ex, sim.y + sin_a * 12 + perp_y * ey)
            draw.ellipse([ep[0]-2, ep[1]-2, ep[0]+2, ep[1]+2], fill=accent)
    else:
        for leg in sim.legs8:
            hp = leg["hip"]
            foot = (leg["cur"][0], leg["cur"][1])
            knee = ((hp[0] + foot[0]) / 2 + perp_x * (18 * leg["side"]),
                    (hp[1] + foot[1]) / 2 + perp_y * (18 * leg["side"]))
            draw.line([hp, knee], fill=(30, 25, 30), width=6)
            draw.line([knee, foot], fill=(40, 35, 40), width=4)

        for side in [-1, 1]:
            arm_sock = (sim.x + cos_a * 25 + perp_x * (22 * side), sim.y + sin_a * 25 + perp_y * (22 * side))
            elbow_p = (sim.x + cos_a * 55 + perp_x * (45 * side), sim.y + sin_a * 55 + perp_y * (45 * side))
            palm_p = (sim.x + cos_a * 85 + perp_x * (35 * side), sim.y + sin_a * 85 + perp_y * (35 * side))
            draw.line([arm_sock, elbow_p], fill=(30, 25, 30), width=10)
            draw.line([elbow_p, palm_p], fill=(35, 30, 35), width=12)
            draw.ellipse([palm_p[0]-10, palm_p[1]-10, palm_p[0]+10, palm_p[1]+10], fill=(20, 15, 20), outline=accent, width=2)
            draw.line([palm_p, (palm_p[0] + cos_a * 22 + perp_x * (8 * side), palm_p[1] + sin_a * 22 + perp_y * (8 * side))], fill=accent, width=4)
            draw.line([palm_p, (palm_p[0] + cos_a * 22 - perp_x * (8 * side), palm_p[1] + sin_a * 22 - perp_y * (8 * side))], fill=accent, width=4)

        for i in range(1, 8):
            seg = sim.spine[i]
            w = max(16, 45 - i * 4)
            draw.ellipse([seg["x"] - w, seg["y"] - 12, seg["x"] + w, seg["y"] + 12], fill=(20, 18, 24), outline=accent, width=2)

        t_prev = (sim.spine[7]["x"], sim.spine[7]["y"])
        t_wag = math.sin(sim_time * 4) * 0.4
        for i in range(6):
            t_ang = sim.angle + math.pi + t_wag * ((i + 1) / 6)
            tx = t_prev[0] + math.cos(t_ang) * 16
            ty = t_prev[1] + math.sin(t_ang) * 16
            draw.line([t_prev, (tx, ty)], fill=(25, 20, 25), width=max(4, 14 - i * 1.8))
            t_prev = (tx, ty)
        draw.ellipse([t_prev[0]-8, t_prev[1]-8, t_prev[0]+8, t_prev[1]+8], fill=accent)
        draw.line([t_prev, (t_prev[0] - cos_a * 14 + perp_x * 8, t_prev[1] - sin_a * 14 + perp_y * 8)], fill=(255, 255, 255), width=3)