"""
Realistic Autonomous Emperor Scorpion & Creature Engine
Features:
- Full HD 1080 x 1920 Vertical format
- Authentic Emperor Scorpion (Pandinus imperator) with:
  1. Carapace with glowing median eyes
  2. Two Giant Front 3-Joint Pincer Arms (Crusher Claws / Hands) snapping & reaching
  3. 8 Articulated Walking Legs with realistic alternating tripod stepping gait
  4. 7 Segmented Overlapping Abdominal Tergite Plates
  5. 5-Segment Metasoma Stinger Tail curling upwards with venom bulb and sharp needle
- Autonomous self-crawling animation & interactive cursor tracking
- macOS Dark VS Code Card (Scorpion.js) with real inverse kinematics math
- Bottom species pill card & progress timeline
"""
from __future__ import annotations

import math
import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT, FPS = 1080, 1920, 30

def get_font(size: int, bold: bool = False, serif: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        candidates = [
            "/system/fonts/DroidSansMono.ttf",
            "/data/data/com.termux/files/home/teacher-bot-repo/assets/fonts/Montserrat-Regular.ttf"
        ]
    elif serif:
        candidates = [
            "/system/fonts/NotoSerif-Bold.ttf" if bold else "/system/fonts/NotoSerif-Regular.ttf",
            "/system/fonts/DroidSerif-Bold.ttf" if bold else "/system/fonts/DroidSerif-Regular.ttf",
            "/data/data/com.termux/files/home/teacher-bot-repo/assets/fonts/PlayfairDisplay-Bold.ttf"
        ]
    else:
        candidates = [
            "/data/data/com.termux/files/home/teacher-bot-repo/assets/fonts/Montserrat-Bold.ttf" if bold else "/data/data/com.termux/files/home/teacher-bot-repo/assets/fonts/Montserrat-Regular.ttf",
            "/system/fonts/Roboto-Bold.ttf" if bold else "/system/fonts/Roboto-Regular.ttf",
            "/system/fonts/DroidSans.ttf",
        ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

def solve_ik_2joint(origin: tuple[float, float], target: tuple[float, float], l1: float, l2: float, bend_side: float):
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    dist = math.hypot(dx, dy)
    clamped_dist = min(dist, l1 + l2 - 0.001)
    base_angle = math.atan2(dy, dx)
    cos_a = (l1 * l1 + clamped_dist * clamped_dist - l2 * l2) / (2 * l1 * clamped_dist)
    angle_a = math.acos(max(-1.0, min(1.0, cos_a)))
    knee_angle = base_angle + angle_a * bend_side
    knee = (origin[0] + math.cos(knee_angle) * l1, origin[1] + math.sin(knee_angle) * l1)
    return origin, knee, target

CREATURE_SPECIES = [
    {
        "id": "emperor_scorpion",
        "name": "EMPEROR SCORPION",
        "title": "Interactive Scorpion Cursor",
        "scientific": "Pandinus imperator",
        "comment_keyword": "Scorpion",
        "file_name": "Scorpion.js",
        "accent": (234, 179, 8),
        "code_lines": [
            "const animateScorpion = () => {",
            "  requestAnimationFrame(animateScorpion);",
            "  const p = getTargetCoordinates();",
            "  // 3-Joint Pincer Claws IK (Hands)",
            "  solvePincerIK(leftChela, p, 52, 60, -1);",
            "  solvePincerIK(rightChela, p, 52, 60, 1);",
            "  // 8-Legged Tripod Stepping Gait",
            "  legs.forEach(leg => stepTripodIK(leg, frm));",
            "  // 5-Segment 3D Curved Stinger Tail",
            "  curlStingerTail(tail, Math.sin(frm * 3) * 0.4);",
            "  renderChitinPlates(ctx, scorpion);",
            "};"
        ],
        "yt_title": "Realistic Emperor Scorpion Interactive Cursor in JS 🦂🔥 #JavaScript #Shorts #WebDev",
        "yt_desc": "🦂 Build an Emperor Scorpion interactive cursor with 8-legged tripod gait & articulated pincer claws in Vanilla JavaScript!\n\nSpecies: Pandinus imperator\nComment 'Scorpion' to get the full source code!\n\n#JavaScript #CreativeCoding #WebDev #Shorts #Coding #Frontend"
    },
    {
        "id": "komodo_dragon",
        "name": "KOMODO DRAGON",
        "title": "Interactive Dragon Cursor",
        "scientific": "Varanus komodoensis",
        "comment_keyword": "Dragon",
        "file_name": "Dragon.js",
        "accent": (255, 120, 40),
        "code_lines": [
            "const run = () => {",
            "  requestAnimationFrame(run);",
            "  let e = elems[0];",
            "  const ax = (Math.cos(3 * frm) * rad * width) / height;",
            "  const ay = (Math.sin(4 * frm) * rad * height) / width;",
            "  e.x += (ax + pointer.x - e.x) / 10;",
            "  e.y += (ay + pointer.y - e.y) / 10;",
            "  for (let i = 1; i < N; i++) {",
            "    let e = elems[i]; let ep = elems[i - 1];",
            "    const a = Math.atan2(e.y - ep.y, e.x - ep.x);",
            "    e.x += (ep.x - e.x + (Math.cos(a) * (100 - i)) / 5) / 4;",
            "    e.y += (ep.y - e.y + (Math.sin(a) * (100 - i)) / 5) / 4;",
            "  }",
            "};"
        ],
        "yt_title": "Realistic Interactive Dragon Cursor in JavaScript 🐉✨ #JavaScript #Coding #Shorts",
        "yt_desc": "🐉 Realistic Interactive Dragon Cursor in Vanilla JavaScript!\n\nSpecies: Varanus komodoensis\nComment 'Dragon' for code!\n\n#JavaScript #CreativeCoding #Shorts"
    }
]

def render_generative_frame(species: dict, frame_idx: int, total_frames: int) -> Image.Image:
    t = (frame_idx / total_frames) * 2 * math.pi
    progress = frame_idx / total_frames

    # 1. Deep Midnight Navy Background (#0B1B26 to #0E2331)
    img = Image.new("RGBA", (WIDTH, HEIGHT), (11, 27, 38, 255))
    draw = ImageDraw.Draw(img)

    # Vignette
    grad = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grad)
    g_draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(14, 35, 49, 255))
    g_draw.ellipse([WIDTH//2 - 500, HEIGHT//2 - 600, WIDTH//2 + 500, HEIGHT//2 + 600], fill=(22, 50, 70, 200))
    img = Image.alpha_composite(img, grad.filter(ImageFilter.GaussianBlur(80)))
    draw = ImageDraw.Draw(img)

    # 2. Top Header Black Bar
    draw.rectangle([0, 0, WIDTH, 170], fill=(15, 18, 22, 255))
    draw.line([(0, 170), (WIDTH, 170)], fill=(30, 36, 44), width=2)

    sp_font = get_font(52, bold=True)
    draw.text((WIDTH // 2, 45), species["name"], font=sp_font, fill=(255, 255, 255), anchor="mt")

    sub_font = get_font(25, bold=False)
    sci = species["scientific"]
    draw.text((WIDTH // 2, 115), f"Realistic interactive cursor • {sci}", font=sub_font, fill=(160, 176, 192), anchor="mt")

    # 3. Section Title (Serif Elegant Font)
    serif_font = get_font(68, bold=True, serif=True)
    draw.text((WIDTH // 2, 280), species["title"], font=serif_font, fill=(255, 255, 255), anchor="mt")

    # 4. Framed Canvas Box
    box_w, box_h = 860, 480
    box_x = (WIDTH - box_w) // 2
    box_y = 390

    # Drop Shadow
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rectangle([box_x - 10, box_y - 10, box_x + box_w + 10, box_y + box_h + 10], fill=(0, 0, 0, 140))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(25)))
    draw = ImageDraw.Draw(img)

    # Frame Outer Border (Cream Bevel)
    draw.rectangle([box_x - 14, box_y - 14, box_x + box_w + 14, box_y + box_h + 14], fill=(235, 230, 220), outline=(190, 185, 175), width=2)
    # Box Inner Background (Warm Parchment / Cream #EFECE4)
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=(239, 236, 228))

    # 5. REALISTIC EMPEROR SCORPION DRAWING ROUTINE
    cb_x = box_x + box_w // 2
    cb_y = box_y + box_h // 2

    # Autonomous Crawling Path (Figure-8 wandering loop)
    rad_x = box_w * 0.32
    rad_y = box_h * 0.28

    scorp_x = cb_x + math.cos(3 * t) * rad_x
    scorp_y = cb_y + math.sin(4 * t) * rad_y
    # Direction tangent
    dx_dt = -3 * math.sin(3 * t) * rad_x
    dy_dt =  4 * math.cos(4 * t) * rad_y
    scorp_angle = math.atan2(dy_dt, dx_dt)

    cos_a = math.cos(scorp_angle)
    sin_a = math.sin(scorp_angle)
    perp_x = -sin_a
    perp_y =  cos_a

    # 5.1 Draw 8 Walking Legs with Tripod Stepping Gait
    leg_offsets = [-0.8, -1.2, -1.6, -2.0, 0.8, 1.2, 1.6, 2.0]
    for idx in range(8):
        side = -1 if idx < 4 else 1
        leg_i = idx % 4
        hip_along = 12 - leg_i * 10
        hip = (scorp_x + cos_a * hip_along + perp_x * (20 * side),
               scorp_y + sin_a * hip_along + perp_y * (20 * side))

        # Tripod Gait phase
        group = (idx % 2)
        gait_clock = t * 12.0 + (math.pi if group == 1 else 0.0)
        is_swing = math.sin(gait_clock) > 0.0
        step_lead = math.cos(gait_clock) * 18 if is_swing else -10
        step_lift = math.sin(gait_clock) * 8 if is_swing else 0

        reach_ang = scorp_angle + leg_offsets[idx]
        rest_dist = 56 + (leg_i % 2) * 8
        foot_x = hip[0] + math.cos(reach_ang) * rest_dist + cos_a * step_lead
        foot_y = hip[1] + math.sin(reach_ang) * rest_dist + sin_a * step_lead - step_lift
        foot = (foot_x, foot_y)

        # 2-Joint IK
        hip_p, knee_p, foot_p = solve_ik_2joint(hip, foot, 30, 34, side)

        # Upper Limb (Coxa/Femur)
        draw.line([hip_p, knee_p], fill=(22, 28, 38), width=5)
        # Lower Limb (Tibia/Tarsus)
        draw.line([knee_p, foot_p], fill=(12, 16, 22), width=3)
        # Knee Joint Amber Node
        draw.ellipse([knee_p[0]-3, knee_p[1]-3, knee_p[0]+3, knee_p[1]+3], fill=(234, 179, 8))
        # Tarsus Claws
        draw.ellipse([foot_p[0]-2.5, foot_p[1]-2.5, foot_p[0]+2.5, foot_p[1]+2.5], fill=(10, 12, 16))

    # 5.2 Draw 7 Segmented Abdominal Tergite Plates (Mesosoma)
    prev_x, prev_y = scorp_x, scorp_y
    for b_idx in range(7):
        b_lag = (b_idx + 1) * 0.02
        bx = cb_x + math.cos(3 * (t - b_lag)) * rad_x
        by = cb_y + math.sin(4 * (t - b_lag)) * rad_y
        b_ang = math.atan2(prev_y - by, prev_x - bx)
        b_cos, b_sin = math.cos(b_ang), math.sin(b_ang)
        b_perp_x, b_perp_y = -b_sin, b_cos

        half_w = max(10, 28 - b_idx * 2.8)
        half_h = 7

        p1 = (bx - b_cos * half_h + b_perp_x * half_w, by - b_sin * half_h + b_perp_y * half_w)
        p2 = (bx + b_cos * half_h + b_perp_x * (half_w * 0.9), by + b_sin * half_h + b_perp_y * (half_w * 0.9))
        p3 = (bx + b_cos * half_h - b_perp_x * (half_w * 0.9), by + b_sin * half_h - b_perp_y * (half_w * 0.9))
        p4 = (bx - b_cos * half_h - b_perp_x * half_w, by - b_sin * half_h - b_perp_y * half_w)

        draw.polygon([p1, p2, p3, p4], fill=(16, 22, 32), outline=(30, 41, 59), width=1)
        prev_x, prev_y = bx, by

    # 5.3 Draw Carapace (Prosoma Head Shield)
    c_front = (scorp_x + cos_a * 24, scorp_y + sin_a * 24)
    c_r1 = (scorp_x + cos_a * 12 + perp_x * 24, scorp_y + sin_a * 12 + perp_y * 24)
    c_r2 = (scorp_x - cos_a * 14 + perp_x * 26, scorp_y - sin_a * 14 + perp_y * 26)
    c_l2 = (scorp_x - cos_a * 14 - perp_x * 26, scorp_y - sin_a * 14 - perp_y * 26)
    c_l1 = (scorp_x + cos_a * 12 - perp_x * 24, scorp_y + sin_a * 12 - perp_y * 24)

    draw.polygon([c_front, c_r1, c_r2, c_l2, c_l1], fill=(12, 16, 24), outline=(234, 179, 8), width=2)
    # Glowing Amber Center Eyes
    eye_pos = (scorp_x + cos_a * 10, scorp_y + sin_a * 10)
    draw.ellipse([eye_pos[0]-3, eye_pos[1]-3, eye_pos[0]+3, eye_pos[1]+3], fill=(234, 179, 8))

    # 5.4 Draw 2 Giant Front Pincer Arms (Hands / Chelae)
    for side in [-1, 1]:
        shoulder = (scorp_x + cos_a * 20 + perp_x * (18 * side),
                    scorp_y + sin_a * 20 + perp_y * (18 * side))
        
        # Snapping claw animation
        snap_open = math.sin(t * 6 + side) * 0.2 + 0.35
        pincer_ang = scorp_angle + side * 0.45
        p_target = (shoulder[0] + math.cos(pincer_ang) * 72,
                    shoulder[1] + math.sin(pincer_ang) * 72)

        sh_pt, elbow_pt, wrist_pt = solve_ik_2joint(shoulder, p_target, 40, 46, side * -1)

        # Bulky Arm Segments
        draw.line([sh_pt, elbow_pt], fill=(16, 22, 32), width=9)
        draw.line([elbow_pt, wrist_pt], fill=(24, 32, 46), width=7)
        draw.ellipse([elbow_pt[0]-4, elbow_pt[1]-4, elbow_pt[0]+4, elbow_pt[1]+4], fill=(234, 179, 8))

        # Massive Crusher Chela Pincer Bulb
        w_ang = math.atan2(wrist_pt[1] - elbow_pt[1], wrist_pt[0] - elbow_pt[0])
        w_cos, w_sin = math.cos(w_ang), math.sin(w_ang)
        w_perp_x, w_perp_y = -w_sin, w_cos

        chela_poly = [
            (wrist_pt[0] - w_cos * 6 + w_perp_x * 12, wrist_pt[1] - w_sin * 6 + w_perp_y * 12),
            (wrist_pt[0] + w_cos * 16 + w_perp_x * 8, wrist_pt[1] + w_sin * 16 + w_perp_y * 8),
            (wrist_pt[0] + w_cos * 16 - w_perp_x * 8, wrist_pt[1] + w_sin * 16 - w_perp_y * 8),
            (wrist_pt[0] - w_cos * 6 - w_perp_x * 12, wrist_pt[1] - w_sin * 6 - w_perp_y * 12)
        ]
        draw.polygon(chela_poly, fill=(10, 14, 20), outline=(234, 179, 8), width=2)

        # Fixed Finger (Curved Amber Blade)
        f_tip = (wrist_pt[0] + math.cos(w_ang + side * 0.3) * 32,
                 wrist_pt[1] + math.sin(w_ang + side * 0.3) * 32)
        draw.line([(wrist_pt[0] + w_cos * 14, wrist_pt[1] + w_sin * 14), f_tip], fill=(234, 179, 8), width=4)

        # Movable Finger (Snaps)
        m_tip = (wrist_pt[0] + math.cos(w_ang - side * snap_open) * 28,
                 wrist_pt[1] + math.sin(w_ang - side * snap_open) * 28)
        draw.line([(wrist_pt[0] + w_cos * 14, wrist_pt[1] + w_sin * 14), m_tip], fill=(202, 138, 4), width=3)

    # 5.5 Draw 5-Segment Stinger Tail (Metasoma Curving Arc)
    tail_prev = (prev_x, prev_y)
    t_angle_base = scorp_angle + math.pi
    for s_i in range(5):
        s_curl = math.sin(t * 4) * 0.2
        t_ang = t_angle_base + s_curl * (s_i + 1)
        t_len = 16 - s_i * 1.2
        tx = tail_prev[0] + math.cos(t_ang) * t_len
        ty = tail_prev[1] + math.sin(t_ang) * t_len
        
        t_width = max(5, int(12 - s_i * 1.4))
        draw.line([tail_prev, (tx, ty)], fill=(18, 24, 34), width=t_width)
        draw.ellipse([tx - t_width//2, ty - t_width//2, tx + t_width//2, ty + t_width//2], fill=(28, 38, 52))
        tail_prev = (tx, ty)

    # Venomous Telson Bulb & Sharp Needle Stinger
    draw.ellipse([tail_prev[0]-7, tail_prev[1]-7, tail_prev[0]+7, tail_prev[1]+7], fill=(202, 138, 4), outline=(254, 240, 138), width=2)
    sting_tip = (tail_prev[0] + math.cos(t_ang + 0.8) * 18, tail_prev[1] + math.sin(t_ang + 0.8) * 18)
    draw.line([tail_prev, sting_tip], fill=(254, 240, 138), width=3)

    # 6. Viral Call-To-Action (Comment :- "Scorpion" 📩)
    cta_y = 950
    cta_font = get_font(56, bold=True, serif=True)
    keyword = species["comment_keyword"]
    cta_txt = f'Comment :- "{keyword}"'
    draw.text((WIDTH // 2 - 50, cta_y), cta_txt, font=cta_font, fill=(255, 255, 255), anchor="mt")

    # Vector Envelope Icon
    env_x = WIDTH // 2 + 250
    env_y = cta_y + 16
    draw.rounded_rectangle([env_x, env_y, env_x + 58, env_y + 44], radius=6, fill=(225, 240, 255), outline=(100, 160, 230), width=3)
    draw.line([(env_x, env_y), (env_x + 29, env_y + 24), (env_x + 58, env_y)], fill=(100, 160, 230), width=3)
    draw.polygon([(env_x + 29, env_y - 2), (env_x + 20, env_y - 14), (env_x + 38, env_y - 14)], fill=(240, 60, 60))

    # 7. macOS VS Code Dark Window (Scorpion.js)
    card_w, card_h = 880, 560
    card_x = (WIDTH - card_w) // 2
    card_y = 1070

    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=20, fill=(12, 18, 25), outline=(28, 38, 50), width=2)

    # Titlebar
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + 52], radius=20, fill=(8, 13, 19))
    draw.ellipse([card_x + 24, card_y + 20, card_x + 38, card_y + 34], fill=(255, 95, 86))
    draw.ellipse([card_x + 48, card_y + 20, card_x + 62, card_y + 34], fill=(255, 189, 46))
    draw.ellipse([card_x + 72, card_y + 20, card_x + 86, card_y + 34], fill=(39, 201, 63))

    draw.rounded_rectangle([card_x + 120, card_y + 10, card_x + 144, card_y + 38], radius=4, fill=(247, 223, 30))
    draw.text((card_x + 125, card_y + 13), "JS", font=get_font(14, bold=True), fill=(20, 20, 20))
    draw.text((card_x + 154, card_y + 15), species["file_name"], font=get_font(18, bold=True), fill=(160, 175, 195))

    code_font = get_font(17, mono=True)
    c_y = card_y + 70
    for line in species["code_lines"]:
        if c_y > card_y + card_h - 25:
            break
        if line.strip().startswith("//"):
            draw.text((card_x + 35, c_y), line, font=code_font, fill=(100, 116, 139))
        elif "const " in line or "let " in line or "for " in line:
            draw.text((card_x + 35, c_y), line, font=code_font, fill=(224, 108, 117))
        elif "Math." in line or "solve" in line or "render" in line:
            draw.text((card_x + 35, c_y), line, font=code_font, fill=(97, 175, 239))
        else:
            draw.text((card_x + 35, c_y), line, font=code_font, fill=(226, 232, 240))
        c_y += 26

    # 8. Bottom Pill Card
    pill_w, pill_h = 880, 120
    pill_x = (WIDTH - pill_w) // 2
    pill_y = 1670

    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=18, fill=(14, 22, 30), outline=(32, 44, 58), width=2)
    pill_title_font = get_font(28, bold=True)
    pill_sub_font = get_font(22, bold=False)

    draw.text((pill_x + 30, pill_y + 24), "Interactive motion • 8-legged tripod gait follows pointer", font=pill_title_font, fill=(255, 255, 255))
    draw.text((pill_x + 30, pill_y + 68), f"Species: {species['scientific']}", font=pill_sub_font, fill=(140, 155, 175))

    # 9. Bottom Progress Bar
    bar_w = 880
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 1840
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 10], radius=5, fill=(40, 52, 68))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + 10], radius=5, fill=(230, 235, 240))

    return img.convert("RGB")
