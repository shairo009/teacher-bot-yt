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
            draw.line([t_prev, (tx, ty)], fill=fur_dark, width=int(max(4, 18 - i * 1.8)))
            draw.line([t_prev, (tx, ty)], fill=fur_mid, width=int(max(2, 14 - i * 1.8)))
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
            draw.line([t_prev, (tx, ty)], fill=(25, 20, 25), width=int(max(4, 14 - i * 1.8)))
            t_prev = (tx, ty)
        draw.ellipse([t_prev[0]-8, t_prev[1]-8, t_prev[0]+8, t_prev[1]+8], fill=accent)
        draw.line([t_prev, (t_prev[0] - cos_a * 14 + perp_x * 8, t_prev[1] - sin_a * 14 + perp_y * 8)], fill=(255, 255, 255), width=3)

# ─────────────────────────────────────────────────────────────────────────────
# 4. REPTILES: TURTLE / TORTOISE
# ─────────────────────────────────────────────────────────────────────────────
def draw_turtle(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [180, 83, 9]))
    shell_dark = _darken(accent, 45)
    shell_mid = accent
    shell_light = _brighten(accent, 35)

    # 4 Paddling Flippers / Legs
    swim_phase = math.sin(sim_time * 5.0)
    for leg in sim.legs4:
        side = leg["side"]
        is_front = leg["is_front"]
        sock = leg["socket"]
        if is_front:
            f_len = 55
            f_ang = sim.angle + (math.pi / 3) * side + swim_phase * 0.35 * side
            f_tip = (sock[0] + math.cos(f_ang) * f_len, sock[1] + math.sin(f_ang) * f_len)
            f_mid = (sock[0] + math.cos(f_ang + 0.2 * side) * (f_len * 0.6), sock[1] + math.sin(f_ang + 0.2 * side) * (f_len * 0.6))
            draw.polygon([sock, f_mid, f_tip, (sock[0] + perp_x * (12 * side), sock[1] + perp_y * (12 * side))], fill=shell_dark, outline=shell_mid, width=2)
        else:
            r_ang = sim.angle + math.pi - (math.pi / 4) * side - swim_phase * 0.25 * side
            r_tip = (sock[0] + math.cos(r_ang) * 40, sock[1] + math.sin(r_ang) * 40)
            draw.polygon([sock, r_tip, (sock[0] + perp_x * (10 * side), sock[1] + perp_y * (10 * side))], fill=shell_dark, outline=shell_mid, width=2)

    # Tail
    t_end = (sim.x - cos_a * 58, sim.y - sin_a * 58)
    draw.polygon([(sim.x - cos_a * 45 + perp_x * 8, sim.y - sin_a * 45 + perp_y * 8),
                  (sim.x - cos_a * 45 - perp_x * 8, sim.y - sin_a * 45 - perp_y * 8), t_end], fill=shell_dark)

    # Domed Carapace (Oval Shell)
    cx, cy = sim.x - cos_a * 4, sim.y - sin_a * 4
    # Shadow
    draw.ellipse([cx - 66 + 6, cy - 54 + 6, cx + 66 + 6, cy + 54 + 6], fill=(20, 20, 20))
    # Outer Rim
    draw.ellipse([cx - 68, cy - 56, cx + 68, cy + 56], fill=_darken(shell_dark, 20), outline=shell_light, width=3)
    # Main Dome
    draw.ellipse([cx - 62, cy - 50, cx + 62, cy + 50], fill=shell_mid, outline=shell_dark, width=2)
    # Inner polygonal scutes
    for sc_x, sc_y, sc_r in [(0, 0, 22), (0, -26, 16), (0, 26, 16), (-32, -14, 18), (-32, 14, 18), (32, -14, 18), (32, 14, 18)]:
        px = cx + cos_a * sc_x - perp_x * sc_y
        py = cy + sin_a * sc_x - perp_y * sc_y
        draw.ellipse([px - sc_r, py - sc_r * 0.75, px + sc_r, py + sc_r * 0.75], outline=_brighten(shell_light, 20), width=2, fill=shell_dark)

    # Neck & Head (Extendable with beak)
    hx = sim.x + cos_a * 62
    hy = sim.y + sin_a * 62
    draw.line([(sim.x + cos_a * 35, sim.y + sin_a * 35), (hx, hy)], fill=shell_dark, width=22)
    draw.line([(sim.x + cos_a * 35, sim.y + sin_a * 35), (hx, hy)], fill=shell_mid, width=16)
    draw.ellipse([hx - 16, hy - 14, hx + 16, hy + 14], fill=shell_mid, outline=shell_dark, width=2)
    # Beak tip
    sn_tip = (hx + cos_a * 16, hy + sin_a * 16)
    draw.polygon([(hx + perp_x * 8, hy + perp_y * 8), (hx - perp_x * 8, hy - perp_y * 8), sn_tip], fill=shell_dark)
    # Eyes
    for s in [-1, 1]:
        ep = (hx + cos_a * 4 + perp_x * (10 * s), hy + sin_a * 4 + perp_y * (10 * s))
        draw.ellipse([ep[0]-4, ep[1]-4, ep[0]+4, ep[1]+4], fill=(15, 23, 42))
        draw.ellipse([ep[0]+1, ep[1]-1, ep[0]+2.5, ep[1]+0.5], fill=(255, 255, 255))


# ─────────────────────────────────────────────────────────────────────────────
# 5. CRUSTACEANS: CRAB
# ─────────────────────────────────────────────────────────────────────────────
def draw_crab(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [239, 68, 68]))
    crab_dark = _darken(accent, 40)
    crab_mid = accent
    crab_light = _brighten(accent, 40)

    # 8 Walking Legs splayed sideways
    leg_steps = [-28, -10, 8, 26]
    for i, offset in enumerate(leg_steps):
        crawl = math.sin(sim_time * 7.0 + i * 0.8) * 14
        for side in [-1, 1]:
            h_p = (sim.x + cos_a * offset + perp_x * (38 * side), sim.y + sin_a * offset + perp_y * (38 * side))
            knee_p = (h_p[0] + perp_x * ((55 + crawl) * side) - cos_a * (10 - i * 4),
                      h_p[1] + perp_y * ((55 + crawl) * side) - sin_a * (10 - i * 4))
            claw_p = (knee_p[0] + perp_x * (32 * side) + cos_a * (i * 6),
                      knee_p[1] + perp_y * (32 * side) + sin_a * (i * 6))
            draw.line([h_p, knee_p], fill=crab_dark, width=9)
            draw.line([h_p, knee_p], fill=crab_mid, width=6)
            draw.line([knee_p, claw_p], fill=crab_dark, width=6)
            draw.line([knee_p, claw_p], fill=crab_light, width=3)
            draw.ellipse([claw_p[0]-3, claw_p[1]-3, claw_p[0]+3, claw_p[1]+3], fill=(15, 23, 42))

    # 2 Massive Front Chelae (Pincers)
    pincer_open = 0.22 + math.sin(sim_time * 4.0) * 0.12
    for side in [-1, 1]:
        c_sock = (sim.x + cos_a * 28 + perp_x * (30 * side), sim.y + sin_a * 28 + perp_y * (30 * side))
        c_elbow = (sim.x + cos_a * 68 + perp_x * (55 * side), sim.y + sin_a * 68 + perp_y * (55 * side))
        c_palm = (sim.x + cos_a * 96 + perp_x * (36 * side), sim.y + sin_a * 96 + perp_y * (36 * side))
        draw.line([c_sock, c_elbow], fill=crab_dark, width=15)
        draw.line([c_sock, c_elbow], fill=crab_mid, width=10)
        draw.line([c_elbow, c_palm], fill=crab_dark, width=18)
        draw.line([c_elbow, c_palm], fill=crab_mid, width=13)
        draw.ellipse([c_palm[0]-16, c_palm[1]-14, c_palm[0]+16, c_palm[1]+14], fill=crab_mid, outline=crab_dark, width=2)
        ang_p = math.atan2(c_palm[1] - c_elbow[1], c_palm[0] - c_elbow[0])
        f1 = (c_palm[0] + math.cos(ang_p - pincer_open) * 32, c_palm[1] + math.sin(ang_p - pincer_open) * 32)
        f2 = (c_palm[0] + math.cos(ang_p + pincer_open) * 32, c_palm[1] + math.sin(ang_p + pincer_open) * 32)
        draw.line([c_palm, f1], fill=crab_light, width=6)
        draw.line([c_palm, f2], fill=crab_light, width=6)

    # Broad Hexagonal Carapace
    c_pts = [
        (sim.x + cos_a * 44, sim.y + sin_a * 44),
        (sim.x + cos_a * 24 + perp_x * 58, sim.y + sin_a * 24 + perp_y * 58),
        (sim.x - cos_a * 28 + perp_x * 52, sim.y - sin_a * 28 + perp_y * 52),
        (sim.x - cos_a * 42, sim.y - sin_a * 42),
        (sim.x - cos_a * 28 - perp_x * 52, sim.y - sin_a * 28 - perp_y * 52),
        (sim.x + cos_a * 24 - perp_x * 58, sim.y + sin_a * 24 - perp_y * 58),
    ]
    # Carapace Shadow & Body
    draw.polygon([(x+6, y+6) for x, y in c_pts], fill=(20, 20, 20))
    draw.polygon(c_pts, fill=crab_mid, outline=crab_dark, width=3)
    # Dorsal Carapace grooves
    draw.arc([sim.x - 30, sim.y - 20, sim.x + 30, sim.y + 20], 0, 180, fill=crab_dark, width=2)
    draw.line([(sim.x, sim.y - 18), (sim.x, sim.y + 18)], fill=crab_dark, width=2)

    # Eyestalks & Eyes
    for s in [-1, 1]:
        st_b = (sim.x + cos_a * 38 + perp_x * (12 * s), sim.y + sin_a * 38 + perp_y * (12 * s))
        st_t = (st_b[0] + cos_a * 14 + perp_x * (4 * s), st_b[1] + sin_a * 14 + perp_y * (4 * s))
        draw.line([st_b, st_t], fill=crab_dark, width=4)
        draw.ellipse([st_t[0]-5, st_t[1]-5, st_t[0]+5, st_t[1]+5], fill=(15, 23, 42), outline=crab_light, width=1)
        draw.ellipse([st_t[0]+1, st_t[1]-1, st_t[0]+2.5, st_t[1]+0.5], fill=(255, 255, 255))


# ─────────────────────────────────────────────────────────────────────────────
# 6. CRUSTACEANS: LOBSTER / CRAYFISH
# ─────────────────────────────────────────────────────────────────────────────
def draw_lobster(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [55, 65, 81]))
    lob_dark = _darken(accent, 35)
    lob_mid = accent
    lob_light = _brighten(accent, 40)

    # Long Sweeping Sensory Antennae
    ant_wave = math.sin(sim_time * 6.0) * 0.2
    for s in [-1, 1]:
        a_root = (sim.x + cos_a * 44 + perp_x * (14 * s), sim.y + sin_a * 44 + perp_y * (14 * s))
        a_ang = sim.angle + 0.35 * s + ant_wave * s
        a_prev = a_root
        for j in range(8):
            a_cur = (a_prev[0] + math.cos(a_ang + j * 0.08 * s) * 18, a_prev[1] + math.sin(a_ang + j * 0.08 * s) * 18)
            draw.line([a_prev, a_cur], fill=lob_light, width=max(1, 3 - j // 3))
            a_prev = a_cur

    # 2 Big Front Claws
    for side in [-1, 1]:
        sock = (sim.x + cos_a * 32 + perp_x * (22 * side), sim.y + sin_a * 32 + perp_y * (22 * side))
        elbow = (sim.x + cos_a * 75 + perp_x * (45 * side), sim.y + sin_a * 75 + perp_y * (45 * side))
        palm = (sim.x + cos_a * 115 + perp_x * (32 * side), sim.y + sin_a * 115 + perp_y * (32 * side))
        draw.line([sock, elbow], fill=lob_dark, width=14)
        draw.line([elbow, palm], fill=lob_mid, width=16)
        # Giant Crushing/Cutting Claw
        draw.ellipse([palm[0]-16, palm[1]-14, palm[0]+16, palm[1]+14], fill=lob_mid, outline=lob_dark, width=2)
        p_ang = math.atan2(palm[1] - elbow[1], palm[0] - elbow[0])
        p1 = (palm[0] + math.cos(p_ang - 0.25) * 36, palm[1] + math.sin(p_ang - 0.25) * 36)
        p2 = (palm[0] + math.cos(p_ang + 0.25) * 36, palm[1] + math.sin(p_ang + 0.25) * 36)
        draw.line([palm, p1], fill=lob_light, width=6)
        draw.line([palm, p2], fill=lob_light, width=6)

    # Walking Legs
    for i in range(4):
        crawl = math.sin(sim_time * 6.0 + i * 0.7) * 10
        for s in [-1, 1]:
            h_p = (sim.x - cos_a * (i * 12) + perp_x * (25 * s), sim.y - sin_a * (i * 12) + perp_y * (25 * s))
            k_p = (h_p[0] + perp_x * ((38 + crawl) * s), h_p[1] + perp_y * ((38 + crawl) * s))
            f_p = (k_p[0] + perp_x * (20 * s) + cos_a * 8, k_p[1] + perp_y * (20 * s) + sin_a * 8)
            draw.line([h_p, k_p], fill=lob_dark, width=6)
            draw.line([k_p, f_p], fill=lob_mid, width=4)

    # Segmented Abdomen (Tail)
    for i in range(7, 0, -1):
        seg_x = sim.x - cos_a * (i * 14 + 10)
        seg_y = sim.y - sin_a * (i * 14 + 10)
        hw = max(14, 38 - i * 3)
        draw.ellipse([seg_x - hw, seg_y - 12, seg_x + hw, seg_y + 12], fill=lob_mid, outline=lob_dark, width=2)

    # Fan Tail (Uropods & Telson)
    t_base = (sim.x - cos_a * 115, sim.y - sin_a * 115)
    for f_ang_off in [-0.5, -0.25, 0.0, 0.25, 0.5]:
        fan_t = (t_base[0] - cos_a * 28 + perp_x * (f_ang_off * 45), t_base[1] - sin_a * 28 + perp_y * (f_ang_off * 45))
        draw.polygon([t_base, fan_t, (t_base[0] - cos_a * 20, t_base[1] - sin_a * 20)], fill=lob_light, outline=lob_dark, width=1)

    # Cephalothorax (Main Body)
    draw.ellipse([sim.x - 34, sim.y - 28, sim.x + 34, sim.y + 28], fill=lob_mid, outline=lob_dark, width=3)
    # Rostrum spine
    sn_tip = (sim.x + cos_a * 46, sim.y + sin_a * 46)
    draw.polygon([(sim.x + cos_a * 26 + perp_x * 12, sim.y + sin_a * 26 + perp_y * 12),
                  (sim.x + cos_a * 26 - perp_x * 12, sim.y + sin_a * 26 - perp_y * 12), sn_tip], fill=lob_dark)


# ─────────────────────────────────────────────────────────────────────────────
# 7. AQUATIC: SEAHORSE / SEADRAGON
# ─────────────────────────────────────────────────────────────────────────────
def draw_seahorse(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [245, 158, 11]))
    s_dark = _darken(accent, 40)
    s_mid = accent
    s_light = _brighten(accent, 45)

    # Fluttering Translucent Dorsal Fin
    flutter = math.sin(sim_time * 24.0) * 8
    df_base = (sim.x - cos_a * 15, sim.y - sin_a * 15)
    draw.polygon([df_base,
                  (df_base[0] - cos_a * 32 + perp_x * (16 + flutter), df_base[1] - sin_a * 32 + perp_y * (16 + flutter)),
                  (df_base[0] - cos_a * 36, df_base[1] - sin_a * 36),
                  (df_base[0] - cos_a * 32 - perp_x * (16 - flutter), df_base[1] - sin_a * 32 - perp_y * (16 - flutter))],
                 fill=(245, 245, 250), outline=s_light, width=1)

    # Segmented Prehensile Curled Tail (Tight Spiral)
    t_prev = (sim.x - cos_a * 25, sim.y - sin_a * 25)
    curl_f = math.sin(sim_time * 3.0) * 0.25
    for i in range(12):
        curl_ang = sim.angle + math.pi + (i * 0.45 + curl_f)
        rad = max(4, 22 - i * 1.5)
        t_next = (t_prev[0] + math.cos(curl_ang) * rad, t_prev[1] + math.sin(curl_ang) * rad)
        w = max(3, 16 - i)
        draw.line([t_prev, t_next], fill=s_dark, width=w + 3)
        draw.line([t_prev, t_next], fill=s_mid, width=w)
        draw.ellipse([t_next[0]-w//2, t_next[1]-w//2, t_next[0]+w//2, t_next[1]+w//2], fill=s_light)
        t_prev = t_next

    # Puffed Armored Chest & Torso
    draw.ellipse([sim.x - 28, sim.y - 24, sim.x + 28, sim.y + 24], fill=s_mid, outline=s_dark, width=3)
    # Armor plates ridges
    for r in range(-16, 20, 8):
        draw.line([(sim.x + r + perp_x * 16, sim.y + perp_y * 16), (sim.x + r - perp_x * 16, sim.y - perp_y * 16)], fill=s_light, width=2)

    # Arched Neck & Head with Coronet
    hx = sim.x + cos_a * 45
    hy = sim.y + sin_a * 45
    draw.ellipse([hx - 20, hy - 18, hx + 20, hy + 18], fill=s_mid, outline=s_dark, width=2)
    # Coronet Spines
    for c_i in [-0.4, 0.0, 0.4]:
        c_p = (hx - cos_a * 16 + perp_x * (c_i * 24), hy - sin_a * 16 + perp_y * (c_i * 24))
        draw.line([(hx, hy), c_p], fill=s_light, width=3)

    # Tubular Snout
    sn_tip = (hx + cos_a * 35, hy + sin_a * 35)
    draw.line([(hx, hy), sn_tip], fill=s_mid, width=10)
    draw.line([(hx, hy), sn_tip], fill=s_light, width=6)
    draw.ellipse([sn_tip[0]-4, sn_tip[1]-4, sn_tip[0]+4, sn_tip[1]+4], fill=s_dark)

    # Round Eyes
    for s in [-1, 1]:
        ep = (hx + cos_a * 4 + perp_x * (12 * s), hy + sin_a * 4 + perp_y * (12 * s))
        draw.ellipse([ep[0]-5, ep[1]-5, ep[0]+5, ep[1]+5], fill=(15, 23, 42), outline=s_light, width=1)
        draw.ellipse([ep[0]+1, ep[1]-1, ep[0]+2.5, ep[1]+0.5], fill=(255, 255, 255))


# ─────────────────────────────────────────────────────────────────────────────
# 8. AQUATIC: JELLYFISH
# ─────────────────────────────────────────────────────────────────────────────
def draw_jellyfish(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [147, 197, 253]))
    j_dark = _darken(accent, 40)
    j_mid = accent
    j_light = _brighten(accent, 45)

    # Rhythmic Bell Pulsing (Contract & Expand)
    pulse = (math.sin(sim_time * 4.0) + 1.0) * 0.5
    bell_w = int(55 + pulse * 18)
    bell_h = int(45 - pulse * 10)

    # Trailing Stinging Tentacles Streaming Behind
    for t_i in range(-5, 6):
        t_root = (sim.x - cos_a * 20 + perp_x * (t_i * 10), sim.y - sin_a * 20 + perp_y * (t_i * 10))
        t_prev = t_root
        t_wave_freq = 4.0 + abs(t_i) * 0.3
        for seg in range(12):
            sway = math.sin(sim_time * t_wave_freq - seg * 0.5) * (seg * 3.5)
            t_cur = (t_prev[0] - cos_a * 18 + perp_x * sway, t_prev[1] - sin_a * 18 + perp_y * sway)
            draw.line([t_prev, t_cur], fill=j_light, width=max(1, 3 - seg // 4))
            t_prev = t_cur

    # Central Frilled Oral Arms
    for arm_s in [-1, 1]:
        o_prev = (sim.x - cos_a * 10 + perp_x * (12 * arm_s), sim.y - sin_a * 10 + perp_y * (12 * arm_s))
        for seg in range(8):
            frill = math.sin(sim_time * 5.0 + seg * 0.7) * 14
            o_cur = (o_prev[0] - cos_a * 16 + perp_x * frill, o_prev[1] - sin_a * 16 + perp_y * frill)
            draw.line([o_prev, o_cur], fill=j_mid, width=max(2, 8 - seg))
            o_prev = o_cur

    # Translucent Umbrella Bell Dome
    bx, by = sim.x + cos_a * 15, sim.y + sin_a * 15
    draw.ellipse([bx - bell_w, by - bell_h, bx + bell_w, by + bell_h], fill=j_dark, outline=j_light, width=3)
    draw.ellipse([bx - bell_w * 0.75, by - bell_h * 0.75, bx + bell_w * 0.75, by + bell_h * 0.75], fill=j_mid)
    # Bell Margin Lobe Rim
    for m in range(-bell_w + 8, bell_w - 8, 12):
        draw.ellipse([bx + m - 4, by + bell_h - 6, bx + m + 4, by + bell_h + 2], fill=j_light)


# ─────────────────────────────────────────────────────────────────────────────
# 9. INSECTS: BUTTERFLY / MOTH
# ─────────────────────────────────────────────────────────────────────────────
def draw_butterfly(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [37, 99, 235]))
    b_dark = _darken(accent, 45)
    b_mid = accent
    b_light = _brighten(accent, 40)

    # Flapping Wing Angle
    flap = math.sin(sim_time * 12.0)
    w_scale = 0.65 + 0.35 * abs(flap)

    # Large Expansive Forewings & Hindwings
    for side in [-1, 1]:
        # Forewing
        w_root = (sim.x + cos_a * 10 + perp_x * (8 * side), sim.y + sin_a * 10 + perp_y * (8 * side))
        fw_tip = (sim.x + cos_a * 75 + perp_x * ((95 * w_scale) * side), sim.y + sin_a * 75 + perp_y * ((95 * w_scale) * side))
        fw_mid = (sim.x - cos_a * 15 + perp_x * ((85 * w_scale) * side), sim.y - sin_a * 15 + perp_y * ((85 * w_scale) * side))
        fw_poly = [w_root, fw_tip, fw_mid, (sim.x - cos_a * 5, sim.y - sin_a * 5)]
        draw.polygon(fw_poly, fill=b_mid, outline=b_dark, width=2)
        # Inner Wing Spot
        sp_x = (w_root[0] + fw_tip[0] + fw_mid[0]) / 3
        sp_y = (w_root[1] + fw_tip[1] + fw_mid[1]) / 3
        draw.ellipse([sp_x - 12, sp_y - 12, sp_x + 12, sp_y + 12], fill=(15, 23, 42), outline=b_light, width=2)
        draw.ellipse([sp_x - 5, sp_y - 5, sp_x + 5, sp_y + 5], fill=b_light)

        # Hindwing
        hw_tip = (sim.x - cos_a * 55 + perp_x * ((65 * w_scale) * side), sim.y - sin_a * 55 + perp_y * ((65 * w_scale) * side))
        hw_mid = (sim.x - cos_a * 75 + perp_x * ((35 * w_scale) * side), sim.y - sin_a * 75 + perp_y * ((35 * w_scale) * side))
        hw_poly = [(sim.x - cos_a * 5, sim.y - sin_a * 5), fw_mid, hw_tip, hw_mid, (sim.x - cos_a * 35, sim.y - sin_a * 35)]
        draw.polygon(hw_poly, fill=b_dark, outline=b_light, width=2)

    # Slender Segmented Torso & Abdomen
    for i in range(8):
        seg_x = sim.x - cos_a * (i * 8)
        seg_y = sim.y - sin_a * (i * 8)
        w = max(4, 12 - i)
        draw.ellipse([seg_x - w, seg_y - w, seg_x + w, seg_y + w], fill=(15, 23, 42), outline=b_light, width=1)

    # Head & Clubbed Antennae
    hx = sim.x + cos_a * 22
    hy = sim.y + sin_a * 22
    draw.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill=(15, 23, 42), outline=b_light, width=1)
    for s in [-1, 1]:
        ant_end = (hx + cos_a * 28 + perp_x * (18 * s), hy + sin_a * 28 + perp_y * (18 * s))
        draw.line([(hx, hy), ant_end], fill=(15, 23, 42), width=2)
        draw.ellipse([ant_end[0]-3, ant_end[1]-3, ant_end[0]+3, ant_end[1]+3], fill=b_light)


# ─────────────────────────────────────────────────────────────────────────────
# 10. INSECTS: BEETLE (STAG / HERCULES / SCARAB)
# ─────────────────────────────────────────────────────────────────────────────
def draw_beetle(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [120, 53, 15]))
    b_dark = _darken(accent, 40)
    b_mid = accent
    b_light = _brighten(accent, 40)
    name = species.get("name", "").upper()

    # 6 Jointed Insect Legs
    for i, offset in enumerate([-25, 0, 22]):
        crawl = math.sin(sim_time * 8.0 + i * 1.0) * 12
        for s in [-1, 1]:
            h_p = (sim.x + cos_a * offset + perp_x * (24 * s), sim.y + sin_a * offset + perp_y * (24 * s))
            k_p = (h_p[0] + perp_x * ((42 + crawl) * s) - cos_a * (i * 6), h_p[1] + perp_y * ((42 + crawl) * s) - sin_a * (i * 6))
            c_p = (k_p[0] + perp_x * (24 * s) + cos_a * 10, k_p[1] + perp_y * (24 * s) + sin_a * 10)
            draw.line([h_p, k_p], fill=b_dark, width=6)
            draw.line([k_p, c_p], fill=b_mid, width=4)
            draw.ellipse([c_p[0]-2, c_p[1]-2, c_p[0]+2, c_p[1]+2], fill=(10, 10, 10))

    # Shiny Convex Elytra (Wing Shell)
    draw.ellipse([sim.x - 38 - cos_a * 15, sim.y - 32 - sin_a * 15, sim.x + 38 - cos_a * 15, sim.y + 32 - sin_a * 15],
                 fill=b_mid, outline=b_dark, width=3)
    # Elytra central suture line
    draw.line([(sim.x + cos_a * 5, sim.y + sin_a * 5), (sim.x - cos_a * 50, sim.y - sin_a * 50)], fill=b_dark, width=3)

    # Pronotum Thorax Collar
    th_x, th_y = sim.x + cos_a * 18, sim.y + sin_a * 18
    draw.ellipse([th_x - 24, th_y - 18, th_x + 24, th_y + 18], fill=b_dark, outline=b_light, width=2)

    # Head & Horns / Pincers
    hx = sim.x + cos_a * 38
    hy = sim.y + sin_a * 38
    draw.ellipse([hx - 14, hy - 12, hx + 14, hy + 12], fill=b_dark)

    if "STAG" in name or "HERCULES" in name or "RHINOCEROS" in name:
        # Massive Pinching Antler Horns
        for s in [-1, 1]:
            h_b = (hx + perp_x * (8 * s), hy + perp_y * (8 * s))
            h_m = (h_b[0] + cos_a * 35 + perp_x * (18 * s), h_b[1] + sin_a * 35 + perp_y * (18 * s))
            h_t = (h_m[0] + cos_a * 25 - perp_x * (10 * s), h_m[1] + sin_a * 25 - perp_y * (10 * s))
            draw.line([h_b, h_m], fill=b_dark, width=6)
            draw.line([h_m, h_t], fill=b_light, width=4)
            # Horn tines
            draw.line([h_m, (h_m[0] + cos_a * 8 - perp_x * (6 * s), h_m[1] + sin_a * 8 - perp_y * (6 * s))], fill=b_light, width=3)
    else:
        # Pincer mandibles
        for s in [-1, 1]:
            m_t = (hx + cos_a * 18 + perp_x * (6 * s), hy + sin_a * 18 + perp_y * (6 * s))
            draw.line([(hx + perp_x * (6 * s), hy + perp_y * (6 * s)), m_t], fill=b_light, width=3)


# ─────────────────────────────────────────────────────────────────────────────
# 11. AMPHIBIANS: FROG / TOAD
# ─────────────────────────────────────────────────────────────────────────────
def draw_frog(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [234, 179, 8]))
    f_dark = _darken(accent, 40)
    f_mid = accent
    f_light = _brighten(accent, 35)

    # Long Folded Jumping Hindlegs (3-Joint: Thigh -> Shin -> Foot)
    for leg in [l for l in sim.legs4 if not l["is_front"]]:
        sock = leg["socket"]
        side = leg["side"]
        paw = (leg["cur"][0], leg["cur"][1])
        knee = (sock[0] - cos_a * 25 + perp_x * (35 * side), sock[1] - sin_a * 25 + perp_y * (35 * side))
        ankle = (knee[0] - cos_a * 30 - perp_x * (10 * side), knee[1] - sin_a * 30 - perp_y * (10 * side))
        draw.line([sock, knee], fill=f_dark, width=16)
        draw.line([sock, knee], fill=f_mid, width=11)
        draw.line([knee, ankle], fill=f_dark, width=12)
        draw.line([knee, ankle], fill=f_mid, width=8)
        draw.line([ankle, paw], fill=f_dark, width=7)
        draw.line([ankle, paw], fill=f_light, width=4)
        # Webbed Toes
        for toe_i in [-0.3, 0.0, 0.3]:
            toe_t = (paw[0] + cos_a * 12 + perp_x * (toe_i * 12), paw[1] + sin_a * 12 + perp_y * (toe_i * 12))
            draw.line([paw, toe_t], fill=f_light, width=2)

    # Forelegs
    for leg in [l for l in sim.legs4 if l["is_front"]]:
        sock = leg["socket"]
        paw = (leg["cur"][0], leg["cur"][1])
        draw.line([sock, paw], fill=f_dark, width=9)
        draw.line([sock, paw], fill=f_mid, width=6)
        draw.ellipse([paw[0]-4, paw[1]-4, paw[0]+4, paw[1]+4], fill=f_dark)

    # Squat Broad Body
    bx, by = sim.x - cos_a * 8, sim.y - sin_a * 8
    draw.ellipse([bx - 38, by - 34, bx + 38, by + 34], fill=f_mid, outline=f_dark, width=3)
    # Dorsal spots / warts
    for sp_x, sp_y in [(-12, -10), (10, -12), (0, 8), (-14, 12), (14, 10)]:
        draw.ellipse([bx + sp_x - 5, by + sp_y - 5, bx + sp_x + 5, by + sp_y + 5], fill=f_dark, outline=f_light, width=1)

    # Head with Bulging Eyes
    hx = sim.x + cos_a * 34
    hy = sim.y + sin_a * 34
    draw.ellipse([hx - 26, hy - 20, hx + 26, hy + 20], fill=f_mid, outline=f_dark, width=2)
    # Bulging Round Eyes
    for s in [-1, 1]:
        ep = (hx + cos_a * 6 + perp_x * (18 * s), hy + sin_a * 6 + perp_y * (18 * s))
        draw.ellipse([ep[0]-10, ep[1]-10, ep[0]+10, ep[1]+10], fill=f_dark, outline=f_light, width=2)
        draw.ellipse([ep[0]-7, ep[1]-7, ep[0]+7, ep[1]+7], fill=(234, 179, 8))
        # Horizontal Slit Pupil
        draw.line([(ep[0]-6, ep[1]), (ep[0]+6, ep[1])], fill=(0, 0, 0), width=3)
        draw.ellipse([ep[0]+2, ep[1]-3, ep[0]+4, ep[1]-1], fill=(255, 255, 255))


# ─────────────────────────────────────────────────────────────────────────────
# 12. BIRDS: RAPTOR / PASSERINE / WATERBIRD
# ─────────────────────────────────────────────────────────────────────────────
def draw_bird(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [245, 158, 11]))
    b_dark = _darken(accent, 40)
    b_mid = accent
    b_light = _brighten(accent, 40)
    name = species.get("name", "").upper()

    # Sweeping Feathered Wings
    wing_flap = math.sin(sim_time * 6.0) * 0.35
    for side in [-1, 1]:
        w_root = (sim.x + cos_a * 12 + perp_x * (14 * side), sim.y + sin_a * 12 + perp_y * (14 * side))
        w_joint = (sim.x + cos_a * 45 + perp_x * (55 * side), sim.y + sin_a * 45 + perp_y * (55 * side))
        w_tip = (sim.x - cos_a * 15 + perp_x * ((95 + wing_flap * 30) * side), sim.y - sin_a * 15 + perp_y * ((95 + wing_flap * 30) * side))
        draw.polygon([w_root, w_joint, w_tip, (sim.x - cos_a * 25 + perp_x * (30 * side), sim.y - sin_a * 25 + perp_y * (30 * side))],
                     fill=b_mid, outline=b_dark, width=2)
        # Wing feather primaries
        for f_i in range(5):
            fp = (w_joint[0] + (w_tip[0] - w_joint[0]) * (f_i / 5.0), w_joint[1] + (w_tip[1] - w_joint[1]) * (f_i / 5.0))
            draw.line([w_root, fp], fill=b_light, width=2)

    # Fan Tail Feathers
    t_base = (sim.x - cos_a * 35, sim.y - sin_a * 35)
    for t_i in range(-3, 4):
        t_tip = (t_base[0] - cos_a * 45 + perp_x * (t_i * 12), t_base[1] - sin_a * 45 + perp_y * (t_i * 12))
        draw.line([t_base, t_tip], fill=b_dark, width=6)
        draw.line([t_base, t_tip], fill=b_light, width=3)

    # Aerodynamic Torso
    draw.ellipse([sim.x - 24, sim.y - 18, sim.x + 24, sim.y + 18], fill=b_mid, outline=b_dark, width=3)

    # Head & Beak
    hx = sim.x + cos_a * 38
    hy = sim.y + sin_a * 38
    draw.ellipse([hx - 14, hy - 13, hx + 14, hy + 13], fill=b_dark, outline=b_light, width=2)

    # Beak (Hooked for raptors, straight for songbirds)
    is_raptor = any(k in name for k in ("EAGLE", "FALCON", "HAWK", "OWL", "KESTREL", "OSPREY", "VULTURE", "CONDOR"))
    beak_col = (234, 179, 8) if is_raptor else (180, 83, 9)
    bk_tip = (hx + cos_a * 22, hy + sin_a * 22)
    if is_raptor:
        bk_hook = (bk_tip[0] - perp_y * 4, bk_tip[1] + perp_x * 4)
        draw.polygon([(hx + perp_x * 6, hy + perp_y * 6), (hx - perp_x * 6, hy - perp_y * 6), bk_hook], fill=beak_col)
    else:
        draw.polygon([(hx + perp_x * 5, hy + perp_y * 5), (hx - perp_x * 5, hy - perp_y * 5), bk_tip], fill=beak_col)

    # Eyes
    for s in [-1, 1]:
        ep = (hx + cos_a * 4 + perp_x * (9 * s), hy + sin_a * 4 + perp_y * (9 * s))
        draw.ellipse([ep[0]-4, ep[1]-4, ep[0]+4, ep[1]+4], fill=(15, 23, 42), outline=beak_col, width=1)
        draw.ellipse([ep[0]+1, ep[1]-1, ep[0]+2.5, ep[1]+0.5], fill=(255, 255, 255))


# ─────────────────────────────────────────────────────────────────────────────
# 13. MAMMALS: KANGAROO / MARSUPIALS
# ─────────────────────────────────────────────────────────────────────────────
def draw_kangaroo(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [234, 88, 12]))
    k_dark = _darken(accent, 40)
    k_mid = accent
    k_light = _brighten(accent, 35)

    # Massive Muscular Jumping Hindlegs
    for leg in [l for l in sim.legs4 if not l["is_front"]]:
        sock = leg["socket"]
        side = leg["side"]
        paw = (leg["cur"][0], leg["cur"][1])
        knee = (sock[0] + cos_a * 35 + perp_x * (26 * side), sock[1] + sin_a * 35 + perp_y * (26 * side))
        hock = (knee[0] - cos_a * 42 + perp_x * (14 * side), knee[1] - sin_a * 42 + perp_y * (14 * side))
        draw.line([sock, knee], fill=k_dark, width=20)
        draw.line([sock, knee], fill=k_mid, width=14)
        draw.line([knee, hock], fill=k_dark, width=14)
        draw.line([knee, hock], fill=k_mid, width=10)
        draw.line([hock, paw], fill=k_dark, width=10)
        draw.line([hock, paw], fill=k_light, width=7)
        draw.line([paw, (paw[0] + cos_a * 18, paw[1] + sin_a * 18)], fill=k_dark, width=8)

    # Smaller Forepaws
    for leg in [l for l in sim.legs4 if l["is_front"]]:
        sock = leg["socket"]
        paw = (leg["cur"][0], leg["cur"][1])
        draw.line([sock, paw], fill=k_dark, width=10)
        draw.line([sock, paw], fill=k_mid, width=7)
        draw.ellipse([paw[0]-5, paw[1]-5, paw[0]+5, paw[1]+5], fill=k_dark)

    # Thick Heavy Muscular Balancing Tail
    t_prev = (sim.x - cos_a * 30, sim.y - sin_a * 30)
    wag = math.sin(sim_time * 5.0) * 0.3
    for i in range(12):
        t_ang = sim.angle + math.pi + wag * ((i + 1) / 12)
        tx = t_prev[0] + math.cos(t_ang) * 16
        ty = t_prev[1] + math.sin(t_ang) * 16
        w = max(4, int(26 - i * 1.8))
        draw.line([t_prev, (tx, ty)], fill=k_dark, width=w + 3)
        draw.line([t_prev, (tx, ty)], fill=k_mid, width=w)
        t_prev = (tx, ty)

    # Upright Torso
    draw.ellipse([sim.x - 26, sim.y - 20, sim.x + 26, sim.y + 20], fill=k_mid, outline=k_dark, width=3)

    # Head & Long Ears
    hx = sim.x + cos_a * 44
    hy = sim.y + sin_a * 44
    draw.ellipse([hx - 18, hy - 16, hx + 18, hy + 16], fill=k_mid, outline=k_dark, width=2)
    # Long Upright Ears
    for s in [-1, 1]:
        eb = (hx - cos_a * 6 + perp_x * (14 * s), hy - sin_a * 6 + perp_y * (14 * s))
        etip = (eb[0] + cos_a * 10 + perp_x * (32 * s), eb[1] + sin_a * 10 + perp_y * (32 * s))
        draw.line([eb, etip], fill=k_dark, width=10)
        draw.line([eb, etip], fill=k_light, width=6)
    # Muzzle & Eyes
    sn_x, sn_y = hx + cos_a * 20, hy + sin_a * 20
    draw.ellipse([sn_x - 8, sn_y - 7, sn_x + 8, sn_y + 7], fill=k_dark)
    for s in [-1, 1]:
        ep = (hx + cos_a * 4 + perp_x * (11 * s), hy + sin_a * 4 + perp_y * (11 * s))
        draw.ellipse([ep[0]-4, ep[1]-4, ep[0]+4, ep[1]+4], fill=(15, 23, 42), outline=k_light, width=1)


# ─────────────────────────────────────────────────────────────────────────────
# 14. MAMMALS: UNGULATES WITH ANTLERS / HORNS (CERVIDS & BOVIDS)
# ─────────────────────────────────────────────────────────────────────────────
def draw_cervid_bovid(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [160, 90, 45]))
    c_dark = _darken(accent, 40)
    c_mid = accent
    c_light = _brighten(accent, 35)
    name = species.get("name", "").upper()

    # Slender Hooved Legs
    for leg in sim.legs4:
        sock = leg["socket"]
        paw = (leg["cur"][0], leg["cur"][1])
        draw.line([sock, paw], fill=c_dark, width=12)
        draw.line([sock, paw], fill=c_mid, width=8)
        draw.ellipse([paw[0]-6, paw[1]-5, paw[0]+6, paw[1]+5], fill=(20, 20, 20), outline=c_dark, width=1)

    # Body
    draw.ellipse([sim.x - 36, sim.y - 24, sim.x + 36, sim.y + 24], fill=c_mid, outline=c_dark, width=3)

    # Arched Neck & Head
    hx = sim.x + cos_a * 46
    hy = sim.y + sin_a * 46
    draw.ellipse([hx - 18, hy - 16, hx + 18, hy + 16], fill=c_mid, outline=c_dark, width=2)
    # Muzzle
    sn_x, sn_y = hx + cos_a * 18, hy + sin_a * 18
    draw.ellipse([sn_x - 8, sn_y - 7, sn_x + 8, sn_y + 7], fill=c_dark)

    # Antlers / Horns
    is_antler = any(k in name for k in ("DEER", "MOOSE", "ELK", "REINDEER", "CARIBOU", "WAPITI"))
    horn_col = (235, 225, 205) if is_antler else (50, 45, 40)
    for s in [-1, 1]:
        h_b = (hx - cos_a * 4 + perp_x * (10 * s), hy - sin_a * 4 + perp_y * (10 * s))
        if is_antler:
            h_m = (h_b[0] + cos_a * 25 + perp_x * (28 * s), h_b[1] + sin_a * 25 + perp_y * (28 * s))
            h_t = (h_m[0] + cos_a * 18 + perp_x * (15 * s), h_m[1] + sin_a * 18 + perp_y * (15 * s))
            draw.line([h_b, h_m], fill=horn_col, width=5)
            draw.line([h_m, h_t], fill=horn_col, width=3)
            draw.line([h_m, (h_m[0] + cos_a * 14 - perp_x * (8 * s), h_m[1] + sin_a * 14 - perp_y * (8 * s))], fill=horn_col, width=3)
        else:
            h_t = (h_b[0] - cos_a * 15 + perp_x * (32 * s), h_b[1] - sin_a * 15 + perp_y * (32 * s))
            draw.line([h_b, h_t], fill=horn_col, width=6)
            draw.ellipse([h_t[0]-3, h_t[1]-3, h_t[0]+3, h_t[1]+3], fill=(20, 20, 20))

    # Eyes
    for s in [-1, 1]:
        ep = (hx + cos_a * 4 + perp_x * (11 * s), hy + sin_a * 4 + perp_y * (11 * s))
        draw.ellipse([ep[0]-4, ep[1]-4, ep[0]+4, ep[1]+4], fill=(15, 23, 42))


# ─────────────────────────────────────────────────────────────────────────────
# 15. MAMMALS: EQUINES (HORSE / ZEBRA)
# ─────────────────────────────────────────────────────────────────────────────
def draw_equine(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> None:
    accent = tuple(species.get("accent", [30, 30, 30]))
    name = species.get("name", "").upper()
    is_zebra = "ZEBRA" in name
    eq_dark = (20, 20, 20) if is_zebra else _darken(accent, 40)
    eq_mid = (245, 245, 245) if is_zebra else accent
    eq_light = (255, 255, 255) if is_zebra else _brighten(accent, 35)

    # Long Slender Legs with Hooves
    for leg in sim.legs4:
        sock = leg["socket"]
        paw = (leg["cur"][0], leg["cur"][1])
        draw.line([sock, paw], fill=eq_dark, width=14)
        draw.line([sock, paw], fill=eq_mid, width=9)
        draw.ellipse([paw[0]-6, paw[1]-5, paw[0]+6, paw[1]+5], fill=(15, 15, 15))

    # Muscular Body
    draw.ellipse([sim.x - 38, sim.y - 25, sim.x + 38, sim.y + 25], fill=eq_mid, outline=eq_dark, width=3)
    if is_zebra:
        # Zebra Stripes
        for r in range(-30, 30, 10):
            draw.line([(sim.x + r + perp_x * 20, sim.y + perp_y * 20), (sim.x + r - perp_x * 20, sim.y - perp_y * 20)], fill=(15, 15, 15), width=4)

    # Long Flowing Tail
    t_prev = (sim.x - cos_a * 35, sim.y - sin_a * 35)
    for i in range(8):
        tx = t_prev[0] - cos_a * 12
        ty = t_prev[1] - sin_a * 12
        draw.line([t_prev, (tx, ty)], fill=eq_dark, width=max(3, 8 - i))
        t_prev = (tx, ty)

    # Arched Neck with Mane & Head
    hx = sim.x + cos_a * 48
    hy = sim.y + sin_a * 48
    draw.ellipse([hx - 20, hy - 16, hx + 20, hy + 16], fill=eq_mid, outline=eq_dark, width=2)
    # Mane
    draw.line([(sim.x + cos_a * 20, sim.y + sin_a * 20), (hx, hy)], fill=eq_dark, width=8)
    # Muzzle & Ears
    sn_x, sn_y = hx + cos_a * 22, hy + sin_a * 22
    draw.ellipse([sn_x - 9, sn_y - 8, sn_x + 9, sn_y + 8], fill=eq_dark)
    for s in [-1, 1]:
        eb = (hx - cos_a * 8 + perp_x * (10 * s), hy - sin_a * 8 + perp_y * (10 * s))
        draw.line([eb, (eb[0] + cos_a * 8 + perp_x * (14 * s), eb[1] + sin_a * 8 + perp_y * (14 * s))], fill=eq_dark, width=4)


# ─────────────────────────────────────────────────────────────────────────────
# 16. MASTER UNIFIED BIOLOGICAL DISPATCHER
# ─────────────────────────────────────────────────────────────────────────────
def draw_bio_creature(draw: ImageDraw.ImageDraw, sim, species: dict, sim_time: float, cos_a: float, sin_a: float, perp_x: float, perp_y: float) -> bool:
    """
    Renders the exact biological silhouette and mechanics for 550+ animal species.
    Returns True if successfully rendered, False if falling back.
    """
    morphology = species.get("morphology", "").lower()
    class_type = species.get("class_type", "").lower()
    name = species.get("name", "").upper()
    sp_id = species.get("id", "").lower()

    # 1. Turtles & Tortoises
    if morphology == "turtle" or any(k in name for k in ("TURTLE", "TORTOISE", "TERRAPIN")):
        draw_turtle(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 2. Crabs
    if morphology == "crab" or any(k in name for k in ("CRAB",)):
        draw_crab(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 3. Lobsters & Crayfish
    if morphology == "lobster" or any(k in name for k in ("LOBSTER", "CRAYFISH", "YABBY", "SCAMPI")):
        draw_lobster(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 4. Seahorse & Seadragon
    if morphology == "seahorse" or any(k in name for k in ("SEAHORSE", "SEADRAGON", "PIPEFISH")):
        draw_seahorse(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 5. Jellyfish
    if morphology == "jellyfish" or any(k in name for k in ("JELLYFISH", "MAN O WAR")):
        draw_jellyfish(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 6. Butterflies & Moths
    if morphology in ("butterfly", "lepidoptera") or any(k in name for k in ("BUTTERFLY", "MOTH")):
        draw_butterfly(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 7. Beetles
    if morphology == "beetle" or any(k in name for k in ("BEETLE", "LADYBUG", "FIREFLY")):
        draw_beetle(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 8. Frogs & Toads
    if morphology == "frog" or class_type == "amphibian" or any(k in name for k in ("FROG", "TOAD", "AXOLOTL", "NEWT", "SALAMANDER")):
        draw_frog(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 9. Birds
    if morphology == "bird" or class_type == "bird" or any(k in name for k in ("EAGLE", "FALCON", "OWL", "HAWK", "PENGUIN", "TOUCAN", "MACAW", "FLAMINGO", "PEACOCK", "HERON", "STORK", "CRANE", "OSTRICH", "EMU", "KIWI", "DUCK", "GOOSE", "SWAN", "PARROT", "PUFFIN", "ALBATROSS")):
        draw_bird(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 10. Kangaroos & Marsupials
    if morphology == "kangaroo" or any(k in name for k in ("KANGAROO", "WALLABY", "QUOKKA")):
        draw_kangaroo(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 11. Cervids & Bovids (Deer, Bison, Antelope, Gazelle, Ibex)
    if morphology == "cervid_bovid" or any(k in name for k in ("DEER", "MOOSE", "ELK", "REINDEER", "CARIBOU", "BISON", "BUFFALO", "ANTELOPE", "GAZELLE", "IMPALA", "IBEX", "SHEEP", "GOAT", "ORYX", "KUDU", "WILDEBEEST")):
        draw_cervid_bovid(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 12. Equines (Horse, Zebra, Mustang)
    if morphology == "equine" or any(k in name for k in ("ZEBRA", "HORSE", "MUSTANG", "DONKEY", "ONAGER")):
        draw_equine(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 13. Serpents (Snakes, Cobras, Vipers, Boas, Pythons)
    if class_type == "serpent" or morphology == "serpent" or any(k in sp_id for k in ("snake", "cobra", "viper", "boa", "python", "mamba", "krait", "adder")):
        draw_bio_serpent(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 14. Arachnids (Spiders, Scorpions, Tarantulas)
    if class_type == "arachnid" or morphology in ("spider", "scorpion") or any(k in sp_id for k in ("spider", "scorpion", "tarantula")):
        draw_bio_arachnid(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    # 15. Bio Quadrupeds (Lion, Tiger, Giraffe, Elephant, Rhino, Bear, Cheetah, Wolf, Fox, Dog, etc.)
    if class_type == "quadruped" or any(k in sp_id for k in ("dog","wolf","tiger","lion","cat","leopard","cheetah","bear","fox","deer","horse","rabbit","hyena","panda","elephant","rhino","hippo","giraffe")):
        draw_bio_quadruped(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
        return True

    return False
