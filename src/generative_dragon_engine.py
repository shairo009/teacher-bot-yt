"""
Minimalist Code-Reel Engine (Upper Creature Display + Lower Sliding Code Window)
Features:
- Full HD 1080 x 1920 Vertical format
- Top Bar: Animal Name ONLY
- Upper Section: Clean Framed Canvas Box with Modular Articulated Creature
- Lower Section: macOS Dark Editor Window with Smooth Auto-Sliding/Scrolling JS Code
- No unnecessary descriptions/trivia text — strictly Animal + Real Code
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

def solve_ik_3segment(origin: tuple[float, float], target: tuple[float, float], l1: float, l2: float, l3: float, side: float):
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    base_angle = math.atan2(dy, dx)
    coxa_ang = base_angle + side * 0.35
    j1 = (origin[0] + math.cos(coxa_ang) * l1, origin[1] + math.sin(coxa_ang) * l1)
    d2 = math.hypot(target[0] - j1[0], target[1] - j1[1])
    clamped_d2 = min(d2, l2 + l3 - 0.001)
    base_ang2 = math.atan2(target[1] - j1[1], target[0] - j1[0])
    cos_a = (l2 * l2 + clamped_d2 * clamped_d2 - l3 * l3) / (2 * l2 * clamped_d2)
    angle_a = math.acos(max(-1.0, min(1.0, cos_a)))
    knee_ang = base_ang2 + angle_a * side
    j2 = (j1[0] + math.cos(knee_ang) * l2, j1[1] + math.sin(knee_ang) * l2)
    return origin, j1, j2, target

CREATURE_SPECIES = [
    {
        "id": "emperor_scorpion",
        "name": "EMPEROR SCORPION",
        "file_name": "Scorpion.js",
        "accent": (234, 179, 8),
        "code_lines": [
            "// ─── EMPEROR SCORPION INVERSE KINEMATICS ───",
            "const scorpion = new CreatureSkeleton({ segments: 38 });",
            "",
            "const animateScorpion = () => {",
            "  requestAnimationFrame(animateScorpion);",
            "  const p = getPointerPosition();",
            "",
            "  // 1. Solve 3-Joint Crusher Pincer Arms (Hands)",
            "  solvePincerIK(scorpion.leftArm,  p, 54, 62, -1);",
            "  solvePincerIK(scorpion.rightArm, p, 54, 62,  1);",
            "",
            "  // 2. 8-Legged Tripod Stepping Gait (4 Left, 4 Right)",
            "  for (let i = 0; i < 8; i++) {",
            "    const leg = scorpion.legs[i];",
            "    const side = i < 4 ? -1 : 1;",
            "    const hip = getHipSocket(scorpion.carapace, i, side);",
            "    const step = computeTripodStep(leg, frm, side);",
            "    const ik = solve3SegmentIK(hip, step.target, 24, 30, 26, side);",
            "    renderArticulatedLeg(ctx, ik);",
            "  }",
            "",
            "  // 3. 7 Mesosoma Chitin Tergites Follow-Chain",
            "  for (let t = 0; t < 7; t++) {",
            "    const prev = t === 0 ? scorpion.carapace : scorpion.tergites[t - 1];",
            "    updateTergitePhysics(scorpion.tergites[t], prev, 18);",
            "    renderChitinPlate(ctx, scorpion.tergites[t]);",
            "  }",
            "",
            "  // 4. 5 Metasoma Tail Segments & Venom Stinger",
            "  curlStingerTail(scorpion.tail, Math.sin(frm * 3.5) * 0.4);",
            "  renderTelsonBulb(ctx, scorpion.tail.end, '#EAB308');",
            "};"
        ],
        "yt_title": "Realistic Emperor Scorpion Interactive Cursor in JS 🦂🔥 #JavaScript #Shorts #Coding",
        "yt_desc": "🦂 Realistic Emperor Scorpion with 38 articulated chitin parts, 8-legged tripod gait, and 3-joint pincer arms in JavaScript!\n\n#JavaScript #CreativeCoding #WebDev #Shorts #Coding"
    },
    {
        "id": "komodo_dragon",
        "name": "KOMODO DRAGON",
        "file_name": "Dragon.js",
        "accent": (255, 120, 40),
        "code_lines": [
            "// ─── KOMODO DRAGON IK SWIMMING ENGINE ───",
            "const dragon = new DragonRig({ vertebrae: 26, legs: 4 });",
            "",
            "const run = () => {",
            "  requestAnimationFrame(run);",
            "  let head = spine[0];",
            "  const ax = (Math.cos(3 * frm) * rad * width) / height;",
            "  const ay = (Math.sin(4 * frm) * rad * height) / width;",
            "  head.x += (ax + pointer.x - head.x) / 10;",
            "  head.y += (ay + pointer.y - head.y) / 10;",
            "",
            "  // 1. Articulated 2-Joint Forelimbs & Hindlimbs",
            "  dragon.legs.forEach((leg, idx) => {",
            "    const shoulder = getSpineAnchor(spine, leg.vertebra, leg.side);",
            "    const step = computeGaitArc(leg.phase, frm);",
            "    const ik = solve2JointIK(shoulder, step.foot, leg.l1, leg.l2, leg.side);",
            "    renderLimbWithClaws(ctx, ik);",
            "  });",
            "",
            "  // 2. Inverse Kinematics Spine Follow-Chain",
            "  for (let i = 1; i < N; i++) {",
            "    let e = spine[i]; let ep = spine[i - 1];",
            "    const a = Math.atan2(e.y - ep.y, e.x - ep.x);",
            "    e.x += (ep.x - e.x + (Math.cos(a) * (100 - i)) / 5) / 4;",
            "    e.y += (ep.y - e.y + (Math.sin(a) * (100 - i)) / 5) / 4;",
            "    renderRibTendril(ctx, e, ep, a, i);",
            "  }",
            "};"
        ],
        "yt_title": "Realistic Komodo Dragon Interactive Cursor in JS 🐉✨ #JavaScript #Coding #Shorts",
        "yt_desc": "🐉 Realistic Komodo Dragon with 2-joint IK legs, swimming spine, and articulated claws in JavaScript!\n\n#JavaScript #CreativeCoding #WebDevelopment #Shorts"
    },
    {
        "id": "cyber_wolf",
        "name": "CYBER ROBOT WOLF",
        "file_name": "CyberWolf.js",
        "accent": (0, 220, 255),
        "code_lines": [
            "// ─── CYBER ROBOT WOLF QUADRUPED GAIT ───",
            "const wolf = new QuadrupedRobot({ limbs: 4, vertebrae: 20 });",
            "",
            "const runWolfGait = () => {",
            "  requestAnimationFrame(runWolfGait);",
            "  updateSpineLag(wolf.spine, pointer);",
            "",
            "  // 1. 4-Leg Dynamic Gallop Gait with 2-Joint IK",
            "  for (let l = 0; l < 4; l++) {",
            "    const leg = wolf.legs[l];",
            "    const shoulder = wolf.spine[leg.spineIndex];",
            "    const step = computeGallopArc(leg.phase, frm);",
            "    const ik = solveIK(shoulder, step.footPos, 38, 42, leg.side);",
            "    drawHydraulicLimb(ctx, ik);",
            "  }",
            "",
            "  // 2. Cyber Head Visor & Armor Plating",
            "  renderCarbonFiberCarapace(ctx, wolf.spine);",
            "  renderCyanVisorGlow(ctx, wolf.head, '#00DCFF');",
            "};"
        ],
        "yt_title": "Interactive Cyber Wolf with 2-Joint IK Paws in JS 🐺⚡ #Coding #Shorts #JavaScript",
        "yt_desc": "🐺 Mechanical Cyber Wolf Cursor with realistic 2-joint IK leg galloping physics in JavaScript Canvas!\n\n#JavaScript #WebDevelopment #Frontend #Shorts"
    }
]

def render_generative_frame(species: dict, frame_idx: int, total_frames: int) -> Image.Image:
    t = (frame_idx / total_frames) * 2 * math.pi
    progress = frame_idx / total_frames

    # 1. Deep Midnight Navy Clean Background
    img = Image.new("RGBA", (WIDTH, HEIGHT), (11, 27, 38, 255))
    draw = ImageDraw.Draw(img)

    # Soft Vignette
    grad = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grad)
    g_draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(14, 35, 49, 255))
    g_draw.ellipse([WIDTH//2 - 500, HEIGHT//2 - 600, WIDTH//2 + 500, HEIGHT//2 + 600], fill=(22, 50, 70, 200))
    img = Image.alpha_composite(img, grad.filter(ImageFilter.GaussianBlur(80)))
    draw = ImageDraw.Draw(img)

    # 2. Top Header: ANIMAL NAME ONLY
    header_h = 140
    draw.rectangle([0, 0, WIDTH, header_h], fill=(15, 18, 22, 255))
    draw.line([(0, header_h), (WIDTH, header_h)], fill=(30, 36, 44), width=2)

    name_font = get_font(58, bold=True)
    draw.text((WIDTH // 2, 40), species["name"], font=name_font, fill=(255, 255, 255), anchor="mt")

    # 3. Upper Section: Framed Creature Display Window
    box_w, box_h = 920, 680
    box_x = (WIDTH - box_w) // 2
    box_y = 175

    # Drop Shadow
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rectangle([box_x - 12, box_y - 12, box_x + box_w + 12, box_y + box_h + 12], fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(25)))
    draw = ImageDraw.Draw(img)

    # Frame Outer Border (Bevel)
    draw.rectangle([box_x - 12, box_y - 12, box_x + box_w + 12, box_y + box_h + 12], fill=(235, 230, 220), outline=(190, 185, 175), width=2)
    # Box Inner Background (Warm Parchment #EFECE4)
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=(239, 236, 228))

    # ─────────────────────────────────────────────────────────────
    # RENDER ARTICULATED CREATURE INSIDE UPPER DISPLAY
    # ─────────────────────────────────────────────────────────────
    cb_x = box_x + box_w // 2
    cb_y = box_y + box_h // 2
    rad_x = box_w * 0.33
    rad_y = box_h * 0.30

    if species["id"] == "emperor_scorpion":
        # Autonomous 8-figure wandering crawl
        scorp_x = cb_x + math.cos(3 * t) * rad_x
        scorp_y = cb_y + math.sin(4 * t) * rad_y
        dx_dt = -3 * math.sin(3 * t) * rad_x
        dy_dt =  4 * math.cos(4 * t) * rad_y
        scorp_angle = math.atan2(dy_dt, dx_dt)

        cos_a = math.cos(scorp_angle)
        sin_a = math.sin(scorp_angle)
        perp_x = -sin_a
        perp_y =  cos_a

        # 8 Symmetrical Walking Legs (4 Left, 4 Right)
        leg_spreads = [-0.85, -1.30, -1.75, -2.20, 0.85, 1.30, 1.75, 2.20]
        for idx in range(8):
            side = -1 if idx < 4 else 1
            leg_i = idx % 4
            hip_along = 14 - leg_i * 11
            hip = (scorp_x + cos_a * hip_along + perp_x * (26 * side),
                   scorp_y + sin_a * hip_along + perp_y * (26 * side))

            group = (idx % 2)
            gait_clock = t * 12.0 + (math.pi if group == 1 else 0.0)
            is_swing = math.sin(gait_clock) > 0.0
            step_lead = math.cos(gait_clock) * 22 if is_swing else -10
            step_lift = math.sin(gait_clock) * 10 if is_swing else 0

            reach_ang = scorp_angle + leg_spreads[idx]
            rest_dist = 82 + (leg_i % 2) * 10
            foot_x = hip[0] + math.cos(reach_ang) * rest_dist + cos_a * step_lead
            foot_y = hip[1] + math.sin(reach_ang) * rest_dist + sin_a * step_lead - step_lift
            foot = (foot_x, foot_y)

            h_p, j1_p, j2_p, f_p = solve_ik_3segment(hip, foot, 26, 34, 30, side)

            draw.line([h_p, j1_p], fill=(16, 22, 32), width=7)
            draw.line([j1_p, j2_p], fill=(24, 32, 46), width=6)
            draw.line([j2_p, f_p], fill=(12, 16, 22), width=4)
            draw.ellipse([j1_p[0]-3.5, j1_p[1]-3.5, j1_p[0]+3.5, j1_p[1]+3.5], fill=(234, 179, 8))
            draw.ellipse([j2_p[0]-3.5, j2_p[1]-3.5, j2_p[0]+3.5, j2_p[1]+3.5], fill=(234, 179, 8))
            draw.ellipse([f_p[0]-3, f_p[1]-3, f_p[0]+3, f_p[1]+3], fill=(10, 12, 16))

        # 7 Segmented Tergite Armor Plates
        prev_x, prev_y = scorp_x, scorp_y
        for b_idx in range(7):
            b_lag = (b_idx + 1) * 0.02
            bx = cb_x + math.cos(3 * (t - b_lag)) * rad_x
            by = cb_y + math.sin(4 * (t - b_lag)) * rad_y
            b_ang = math.atan2(prev_y - by, prev_x - bx)
            b_cos, b_sin = math.cos(b_ang), math.sin(b_ang)
            b_perp_x, b_perp_y = -b_sin, b_cos

            half_w = max(13, 34 - b_idx * 3.0)
            half_h = 8

            p1 = (bx - b_cos * half_h + b_perp_x * half_w, by - b_sin * half_h + b_perp_y * half_w)
            p2 = (bx + b_cos * half_h + b_perp_x * (half_w * 0.9), by + b_sin * half_h + b_perp_y * (half_w * 0.9))
            p3 = (bx + b_cos * half_h - b_perp_x * (half_w * 0.9), by + b_sin * half_h - b_perp_y * (half_w * 0.9))
            p4 = (bx - b_cos * half_h - b_perp_x * half_w, by - b_sin * half_h - b_perp_y * half_w)

            draw.polygon([p1, p2, p3, p4], fill=(16, 22, 32), outline=(234, 179, 8), width=1)
            prev_x, prev_y = bx, by

        # Prosoma Head Carapace
        c_front = (scorp_x + cos_a * 30, scorp_y + sin_a * 30)
        c_r1 = (scorp_x + cos_a * 14 + perp_x * 26, scorp_y + sin_a * 14 + perp_y * 26)
        c_r2 = (scorp_x - cos_a * 16 + perp_x * 30, scorp_y - sin_a * 16 + perp_y * 30)
        c_l2 = (scorp_x - cos_a * 16 - perp_x * 30, scorp_y - sin_a * 16 - perp_y * 30)
        c_l1 = (scorp_x + cos_a * 14 - perp_x * 26, scorp_y + sin_a * 14 - perp_y * 26)
        draw.polygon([c_front, c_r1, c_r2, c_l2, c_l1], fill=(12, 16, 24), outline=(234, 179, 8), width=2)
        eye_pos = (scorp_x + cos_a * 12, scorp_y + sin_a * 12)
        draw.ellipse([eye_pos[0]-3.5, eye_pos[1]-3.5, eye_pos[0]+3.5, eye_pos[1]+3.5], fill=(234, 179, 8))

        # 2 Giant Front Pincer Crusher Arms
        for side in [-1, 1]:
            shoulder = (scorp_x + cos_a * 24 + perp_x * (22 * side),
                        scorp_y + sin_a * 24 + perp_y * (22 * side))
            snap_open = math.sin(t * 6 + side) * 0.2 + 0.35
            pincer_ang = scorp_angle + side * 0.45
            p_target = (shoulder[0] + math.cos(pincer_ang) * 90,
                        shoulder[1] + math.sin(pincer_ang) * 90)

            sh_pt, elbow_pt, wrist_pt = solve_ik_2joint(shoulder, p_target, 48, 54, side * -1)

            draw.line([sh_pt, elbow_pt], fill=(16, 22, 32), width=11)
            draw.line([elbow_pt, wrist_pt], fill=(24, 32, 46), width=9)
            draw.ellipse([elbow_pt[0]-4.5, elbow_pt[1]-4.5, elbow_pt[0]+4.5, elbow_pt[1]+4.5], fill=(234, 179, 8))

            w_ang = math.atan2(wrist_pt[1] - elbow_pt[1], wrist_pt[0] - elbow_pt[0])
            w_cos, w_sin = math.cos(w_ang), math.sin(w_ang)
            w_perp_x, w_perp_y = -w_sin, w_cos

            chela_poly = [
                (wrist_pt[0] - w_cos * 7 + w_perp_x * 14, wrist_pt[1] - w_sin * 7 + w_perp_y * 14),
                (wrist_pt[0] + w_cos * 20 + w_perp_x * 9, wrist_pt[1] + w_sin * 20 + w_perp_y * 9),
                (wrist_pt[0] + w_cos * 20 - w_perp_x * 9, wrist_pt[1] + w_sin * 20 - w_perp_y * 9),
                (wrist_pt[0] - w_cos * 7 - w_perp_x * 14, wrist_pt[1] - w_sin * 7 - w_perp_y * 14)
            ]
            draw.polygon(chela_poly, fill=(10, 14, 20), outline=(234, 179, 8), width=2)

            f_tip = (wrist_pt[0] + math.cos(w_ang + side * 0.3) * 38,
                     wrist_pt[1] + math.sin(w_ang + side * 0.3) * 38)
            draw.line([(wrist_pt[0] + w_cos * 18, wrist_pt[1] + w_sin * 18), f_tip], fill=(234, 179, 8), width=4)

            m_tip = (wrist_pt[0] + math.cos(w_ang - side * snap_open) * 34,
                     wrist_pt[1] + math.sin(w_ang - side * snap_open) * 34)
            draw.line([(wrist_pt[0] + w_cos * 18, wrist_pt[1] + w_sin * 18), m_tip], fill=(202, 138, 4), width=3)

        # 5 Metasoma Tail Segments & Venom Stinger
        tail_prev = (prev_x, prev_y)
        t_angle_base = scorp_angle + math.pi
        for s_i in range(5):
            s_curl = math.sin(t * 4) * 0.2
            t_ang = t_angle_base + s_curl * (s_i + 1)
            t_len = 18 - s_i * 1.2
            tx = tail_prev[0] + math.cos(t_ang) * t_len
            ty = tail_prev[1] + math.sin(t_ang) * t_len
            
            t_width = max(5, int(13 - s_i * 1.4))
            draw.line([tail_prev, (tx, ty)], fill=(18, 24, 34), width=t_width)
            draw.ellipse([tx - t_width//2, ty - t_width//2, tx + t_width//2, ty + t_width//2], fill=(28, 38, 52))
            tail_prev = (tx, ty)

        draw.ellipse([tail_prev[0]-8, tail_prev[1]-8, tail_prev[0]+8, tail_prev[1]+8], fill=(202, 138, 4), outline=(254, 240, 138), width=2)
        sting_tip = (tail_prev[0] + math.cos(t_ang + 0.8) * 20, tail_prev[1] + math.sin(t_ang + 0.8) * 20)
        draw.line([tail_prev, sting_tip], fill=(254, 240, 138), width=3)

    # ─────────────────────────────────────────────────────────────
    # 4. LOWER SECTION: macOS DARK CODE WINDOW WITH AUTO-SLIDING
    # ─────────────────────────────────────────────────────────────
    card_w, card_h = 920, 940
    card_x = (WIDTH - card_w) // 2
    card_y = 885

    # Card Body
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=22, fill=(12, 18, 25), outline=(28, 38, 50), width=2)

    # macOS Titlebar
    title_h = 56
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + title_h], radius=22, fill=(8, 13, 19))
    draw.rectangle([card_x, card_y + 30, card_x + card_w, card_y + title_h], fill=(8, 13, 19))

    # Window Controls (Red, Yellow, Green)
    draw.ellipse([card_x + 26, card_y + 22, card_x + 40, card_y + 36], fill=(255, 95, 86))
    draw.ellipse([card_x + 50, card_y + 22, card_x + 64, card_y + 36], fill=(255, 189, 46))
    draw.ellipse([card_x + 74, card_y + 22, card_x + 88, card_y + 36], fill=(39, 201, 63))

    # JS Badge & File Name
    draw.rounded_rectangle([card_x + 125, card_y + 12, card_x + 150, card_y + 42], radius=4, fill=(247, 223, 30))
    draw.text((card_x + 130, card_y + 16), "JS", font=get_font(15, bold=True), fill=(20, 20, 20))
    draw.text((card_x + 162, card_y + 18), species["file_name"], font=get_font(20, bold=True), fill=(160, 175, 195))

    # ─────────────────────────────────────────────────────────────
    # AUTO-SLIDING / SCROLLING CODE CALCULATION
    # ─────────────────────────────────────────────────────────────
    all_lines = species["code_lines"]
    total_lines = len(all_lines)
    line_h = 34
    visible_lines = int((card_h - title_h - 40) / line_h)

    # Calculate smooth vertical scroll offset based on video progress
    max_scroll_lines = max(0, total_lines - visible_lines)
    # Ease in-out smooth scroll progression
    scroll_factor = 0.5 - math.cos(progress * math.pi) / 2
    curr_scroll = scroll_factor * max_scroll_lines

    start_line_idx = int(curr_scroll)
    line_pixel_offset = (curr_scroll - start_line_idx) * line_h

    code_font = get_font(20, mono=True)
    line_num_font = get_font(18, mono=True)

    # Clipping area for code
    code_box_top = card_y + title_h + 16
    code_box_bottom = card_y + card_h - 20

    for idx in range(visible_lines + 2):
        actual_line_idx = start_line_idx + idx
        if actual_line_idx >= total_lines:
            break
        
        line_text = all_lines[actual_line_idx]
        y_pos = code_box_top + (idx * line_h) - int(line_pixel_offset)

        if y_pos < code_box_top - 10 or y_pos > code_box_bottom:
            continue

        # Line Numbers (Gutter)
        draw.text((card_x + 35, y_pos), f"{actual_line_idx + 1:2d}", font=line_num_font, fill=(70, 85, 105))

        # Syntax-Highlighted Code Text
        indent_x = card_x + 85
        stripped = line_text.strip()
        if stripped.startswith("//"):
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(100, 116, 139))
        elif any(k in line_text for k in ["const ", "let ", "for ", "new ", "return "]):
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(224, 108, 117))
        elif any(f in line_text for f in ["Math.", "solve", "render", "update", "compute", "curl"]):
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(97, 175, 239))
        else:
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(226, 232, 240))

    # 5. Bottom Timeline Progress Bar
    bar_w = 920
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 1855
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 12], radius=6, fill=(35, 46, 62))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + 12], radius=6, fill=(234, 179, 8))

    return img.convert("RGB")
