"""
Cyber Creature Interactive Cursor Engine
Generates viral Interactive Cyber Creature / Cursor Code Reel videos.
Recreates the exact visual layout from reference:
- Off-white minimalist canvas
- Tech badges ([JS] Vanilla JavaScript, [CSS] CSS3)
- Mechanical / Cyber robotic animal chasing the mouse cursor with motion trail sketches
- MacOS Dark VS Code syntax-highlighted JavaScript physics code
"""
from __future__ import annotations

import math
import random
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT, FPS = 720, 1280, 30

def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        candidates = [
            "/system/fonts/DroidSansMono.ttf",
            "/data/data/com.termux/files/home/teacher-bot-repo/assets/fonts/Montserrat-Regular.ttf",
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

CYBER_CREATURES = [
    {
        "id": "cyber_wolf",
        "name": "Cyber Wolf",
        "title_lines": ["Interactive", "Cyber Wolf", "Cursor"],
        "subtitle": "FOLLOW THE POINTER",
        "file_name": "cyberWolf.js",
        "accent": (0, 220, 255),
        "eye_color": (0, 240, 255),
        "code_lines": [
            ("const", "canvas", "=", "document.querySelector('canvas');"),
            ("const", "ctx", "=", "canvas.getContext('2d');"),
            ("let", "mouse", "=", "{ x: innerWidth / 2, y: innerHeight / 2 };"),
            ("let", "wolf", "=", "{ x: mouse.x, y: mouse.y, angle: 0 };"),
            ("const", "trails", "=", "[];"),
            ("const", "TRAIL_LENGTH", "=", "18;"),
            ("", "", "", ""),
            ("// Track mouse pointer coordinates", "", "", ""),
            ("window.addEventListener('mousemove',", "(e) => {", "", ""),
            ("    mouse.x", "=", "e.clientX;"),
            ("    mouse.y", "=", "e.clientY;"),
            ("});", "", "", ""),
            ("", "", "", ""),
            ("// Physics & rotation kinematics loop", "", "", ""),
            ("function animate() {", "", "", ""),
            ("    ctx.clearRect(0, 0, canvas.width, canvas.height);", "", "", ""),
            ("    const dx = mouse.x - wolf.x;", "", "", ""),
            ("    const dy = mouse.y - wolf.y;", "", "", ""),
            ("    wolf.angle = Math.atan2(dy, dx);", "", "", ""),
            ("    wolf.x += Math.cos(wolf.angle) * 7.5;", "", "", ""),
            ("    wolf.y += Math.sin(wolf.angle) * 7.5;", "", "", ""),
            ("    requestAnimationFrame(animate);", "", "", ""),
            ("}", "", "", "")
        ],
        "yt_title": "Interactive Cyber Wolf Cursor in Vanilla JS 🐺⚡ #JavaScript #WebDev #Shorts #Coding",
        "yt_desc": "Build an Interactive Cyber Wolf Cursor using Vanilla JavaScript & HTML5 Canvas!\n\nFollow the mouse pointer with smooth kinematics rotation, pathfinding, and motion trails.\n\nCode file: cyberWolf.js\nTech stack: HTML5 Canvas • Vanilla JavaScript • CSS3\n\n#JavaScript #WebDevelopment #Frontend #CreativeCoding #Canvas #Shorts #TechReels #CodingTips"
    },
    {
        "id": "cyber_dragon",
        "name": "Cyber Dragon",
        "title_lines": ["Interactive", "Cyber Dragon", "Cursor"],
        "subtitle": "FOLLOW THE POINTER",
        "file_name": "cyberDragon.js",
        "accent": (255, 60, 100),
        "eye_color": (255, 80, 120),
        "code_lines": [
            ("const", "canvas", "=", "document.querySelector('canvas');"),
            ("const", "ctx", "=", "canvas.getContext('2d');"),
            ("let", "dragon", "=", "{ x: 200, y: 200, length: 24 };"),
            ("const", "spineSegments", "=", "[];"),
            ("", "", "", ""),
            ("// Inverse kinematics spine calculation", "", "", ""),
            ("function resolveSpine(targetX, targetY) {", "", "", ""),
            ("    let prev = { x: targetX, y: targetY };", "", "", ""),
            ("    for (let i = 0; i < spineSegments.length; i++) {", "", "", ""),
            ("        const seg = spineSegments[i];", "", "", ""),
            ("        const angle = Math.atan2(prev.y - seg.y, prev.x - seg.x);", "", "", ""),
            ("        seg.x = prev.x - Math.cos(angle) * 14;", "", "", ""),
            ("        seg.y = prev.y - Math.sin(angle) * 14;", "", "", ""),
            ("        prev = seg;", "", "", ""),
            ("    }", "", "", ""),
            ("}", "", "", ""),
            ("window.addEventListener('mousemove', (e) => {", "", "", ""),
            ("    resolveSpine(e.clientX, e.clientY);", "", "", ""),
            ("});", "", "", "")
        ],
        "yt_title": "Interactive Cyber Dragon Cursor in JavaScript 🐉⚡ #WebDev #Shorts #Coding",
        "yt_desc": "Build an Interactive Cyber Dragon cursor with Inverse Kinematics spine simulation in JavaScript Canvas!\n\nTech stack: Vanilla JavaScript • CSS3 • HTML5 Canvas\n\n#JavaScript #Frontend #CreativeCoding #Animation #Shorts #WebDev"
    },
    {
        "id": "cyber_scorpion",
        "name": "Emperor Scorpion",
        "title_lines": ["Interactive", "Emperor Scorpion", "Cursor"],
        "subtitle": "FOLLOW THE POINTER",
        "file_name": "cyberScorpion.js",
        "accent": (255, 180, 0),
        "eye_color": (255, 200, 0),
        "code_lines": [
            ("const", "canvas", "=", "document.getElementById('scorpion');"),
            ("const", "ctx", "=", "canvas.getContext('2d');"),
            ("const", "claws", "=", "{ leftAngle: 0, rightAngle: 0 };"),
            ("const", "tailStinger", "=", "{ segments: 6, curl: 0.8 };"),
            ("", "", "", ""),
            ("// Procedural sting strike physics", "", "", ""),
            ("function triggerSting(target) {", "", "", ""),
            ("    const dist = Math.hypot(target.x - scorpion.x, target.y - scorpion.y);", "", "", ""),
            ("    if (dist < 80) {", "", "", ""),
            ("        scorpion.strike = true;", "", "", ""),
            ("        tailStinger.curl = 1.4;", "", "", ""),
            ("    }", "", "", ""),
            ("}", "", "", ""),
            ("window.addEventListener('pointermove', (e) => {", "", "", ""),
            ("    triggerSting({ x: e.clientX, y: e.clientY });", "", "", ""),
            ("});", "", "", "")
        ],
        "yt_title": "Emperor Scorpion Interactive Cursor in Vanilla JS 🦂🔥 #Coding #WebDev #Shorts",
        "yt_desc": "Build an Emperor Scorpion interactive cursor with procedural stinger & claw tracking in Vanilla JavaScript!\n\n#JavaScript #CreativeCoding #Canvas #WebDev #Shorts"
    },
    {
        "id": "cyber_tiger",
        "name": "Cyber Tiger",
        "title_lines": ["Interactive", "Cyber Tiger", "Cursor"],
        "subtitle": "FOLLOW THE POINTER",
        "file_name": "cyberTiger.js",
        "accent": (255, 140, 30),
        "eye_color": (255, 160, 40),
        "code_lines": [
            ("const", "canvas", "=", "document.querySelector('canvas');"),
            ("const", "ctx", "=", "canvas.getContext('2d');"),
            ("let", "tiger", "=", "{ x: 300, y: 300, velocity: 8.5 };"),
            ("const", "pounceCurve", "=", "Math.PI / 4;"),
            ("", "", "", ""),
            ("// Ambush sprint trajectory vector", "", "", ""),
            ("function updateSprint(pointer) {", "", "", ""),
            ("    const angle = Math.atan2(pointer.y - tiger.y, pointer.x - tiger.x);", "", "", ""),
            ("    tiger.x += Math.cos(angle) * tiger.velocity;", "", "", ""),
            ("    tiger.y += Math.sin(angle) * tiger.velocity;", "", "", ""),
            ("    renderMechPlates(ctx, tiger.x, tiger.y, angle);", "", "", ""),
            ("}", "", "", ""),
            ("window.addEventListener('mousemove', (e) => {", "", "", ""),
            ("    updateSprint({ x: e.clientX, y: e.clientY });", "", "", ""),
            ("});", "", "", "")
        ],
        "yt_title": "Cyber Tiger Sprint Cursor in Vanilla JavaScript 🐅⚡ #Coding #Shorts #JavaScript",
        "yt_desc": "Create an Interactive Cyber Tiger Cursor sprinting towards your pointer in JavaScript Canvas!\n\n#JavaScript #WebDevelopment #Frontend #Shorts"
    }
]

def _draw_cursor_pointer(draw: ImageDraw.Draw, x: float, y: float):
    pts = [
        (x, y),
        (x, y + 26),
        (x + 6, y + 20),
        (x + 13, y + 33),
        (x + 18, y + 31),
        (x + 11, y + 18),
        (x + 20, y + 18),
    ]
    draw.polygon(pts, fill=(20, 22, 25), outline=(255, 255, 255), width=2)

def _draw_mech_quadruped(draw: ImageDraw.Draw, cx: float, cy: float, angle: float, t: float, creature_id: str, accent: tuple, is_ghost: bool = False):
    alpha = 40 if is_ghost else 255
    stroke_w = 1 if is_ghost else 2

    # Shaded Metallic Mech Palette
    PLATE_LIGHT = (235, 238, 242, alpha) if not is_ghost else (210, 215, 222, alpha)
    PLATE_MID   = (148, 163, 184, alpha) if not is_ghost else (180, 190, 200, alpha)
    PLATE_DARK  = (51, 65, 85, alpha)   if not is_ghost else (150, 160, 175, alpha)
    FRAME_BLACK = (15, 23, 42, alpha)   if not is_ghost else (130, 140, 155, alpha)
    OUTLINE     = (20, 24, 30, alpha)   if not is_ghost else (140, 150, 165, alpha)

    cos_a, sin_a = math.cos(angle), math.sin(angle)
    perp_x, perp_y = -sin_a, cos_a

    def to_w(rx, ry):
        return (cx + rx * cos_a + ry * perp_x, cy + rx * sin_a + ry * perp_y)

    leg_gallop = math.sin(t * 10)
    leg_gallop2 = math.cos(t * 10)

    # 1. Segmented Whip Tail
    tail_pts = [to_w(-80, 0)]
    for s in range(1, 8):
        tw = math.sin(t * 8 - s * 0.6) * (s * 7)
        tail_pts.append(to_w(-80 - s * 16, tw - s * 4))
    for s in range(len(tail_pts) - 1):
        draw.line([tail_pts[s], tail_pts[s+1]], fill=PLATE_MID, width=max(2, 10 - s))
        draw.ellipse([tail_pts[s][0]-3, tail_pts[s][1]-3, tail_pts[s][0]+3, tail_pts[s][1]+3], fill=FRAME_BLACK)

    # 2. Back Legs (Articulated Mech Hydraulics)
    for side in [-1, 1]:
        hip = to_w(-65, side * 14)
        thigh_rx = -95 + side * leg_gallop * 22
        thigh_ry = side * 30 + 15
        knee = to_w(thigh_rx, thigh_ry)
        ankle = to_w(thigh_rx + 20 - leg_gallop * 12, thigh_ry + 26)
        claw = to_w(thigh_rx + 35 - leg_gallop * 15, thigh_ry + 32)

        # Upper thigh armor polygon
        draw.polygon([hip, to_w(thigh_rx - 10, thigh_ry - 10), knee, to_w(-55, side * 22)], fill=PLATE_MID, outline=OUTLINE)
        draw.line([knee, ankle], fill=PLATE_DARK, width=6)
        draw.line([ankle, claw], fill=FRAME_BLACK, width=4)
        # Chrome circular joint
        draw.ellipse([knee[0]-6, knee[1]-6, knee[0]+6, knee[1]+6], fill=PLATE_LIGHT, outline=FRAME_BLACK, width=stroke_w)
        draw.ellipse([knee[0]-2, knee[1]-2, knee[0]+2, knee[1]+2], fill=FRAME_BLACK)

    # 3. Main Torso Spine Plates (Vertebrae Architecture)
    for v in range(5):
        vx = -55 + v * 22
        vy = math.sin(v * 0.8 + t * 4) * 3
        v_poly = [to_w(vx - 10, vy - 14), to_w(vx + 10, vy - 16), to_w(vx + 8, vy + 16), to_w(vx - 8, vy + 14)]
        draw.polygon(v_poly, fill=PLATE_LIGHT if v % 2 == 0 else PLATE_MID, outline=OUTLINE)

    # Chest & Core Engine Plate
    chest_poly = [to_w(-20, -20), to_w(38, -22), to_w(55, 4), to_w(20, 20), to_w(-20, 16)]
    draw.polygon(chest_poly, fill=PLATE_LIGHT, outline=OUTLINE)
    draw.line([to_w(-10, -5), to_w(35, -5)], fill=PLATE_DARK, width=2)
    draw.line([to_w(-5, 5), to_w(25, 5)], fill=PLATE_DARK, width=2)

    # Glowing Engine Core
    if not is_ghost:
        core = to_w(10, 0)
        draw.ellipse([core[0]-8, core[1]-8, core[0]+8, core[1]+8], fill=accent, outline=(255, 255, 255), width=2)
        draw.ellipse([core[0]-3, core[1]-3, core[0]+3, core[1]+3], fill=(255, 255, 255))

    # 4. Front Legs (Pouncing Forelimbs)
    for side in [-1, 1]:
        shoulder = to_w(36, side * 15)
        elbow_rx = 18 - side * leg_gallop2 * 22
        elbow_ry = side * 28 + 14
        elbow = to_w(elbow_rx, elbow_ry)
        wrist = to_w(elbow_rx + 35 + leg_gallop2 * 18, elbow_ry + 26)
        paw = to_w(elbow_rx + 48 + leg_gallop2 * 20, elbow_ry + 28)

        draw.polygon([shoulder, to_w(elbow_rx - 8, elbow_ry - 8), elbow, to_w(48, side * 18)], fill=PLATE_MID, outline=OUTLINE)
        draw.line([elbow, wrist], fill=PLATE_DARK, width=6)
        draw.line([wrist, paw], fill=FRAME_BLACK, width=4)
        draw.ellipse([elbow[0]-6, elbow[1]-6, elbow[0]+6, elbow[1]+6], fill=PLATE_LIGHT, outline=FRAME_BLACK, width=stroke_w)
        draw.ellipse([shoulder[0]-8, shoulder[1]-8, shoulder[0]+8, shoulder[1]+8], fill=PLATE_LIGHT, outline=FRAME_BLACK, width=stroke_w)

    # 5. Angular Mech Head & Jaws
    neck = to_w(55, -4)
    brow = to_w(95, -18)
    nose = to_w(132, -3)
    jaw_tip = to_w(122, 10)
    jaw_hinge = to_w(82, 14)
    head_poly = [neck, brow, nose, jaw_tip, jaw_hinge]
    draw.polygon(head_poly, fill=PLATE_LIGHT, outline=OUTLINE)

    # Head Armor Inset Line
    draw.line([to_w(75, -8), to_w(110, -6)], fill=PLATE_DARK, width=2)

    # Mech Ears
    ear_poly = [to_w(76, -14), to_w(62, -38), to_w(92, -18)]
    draw.polygon(ear_poly, fill=FRAME_BLACK, outline=OUTLINE)

    # Glowing Cyan Laser Eye
    eye_c = to_w(96, -9)
    if not is_ghost:
        draw.polygon([to_w(90, -11), to_w(105, -9), to_w(94, -6)], fill=accent)
        draw.ellipse([eye_c[0]-2, eye_c[1]-2, eye_c[0]+2, eye_c[1]+2], fill=(255, 255, 255))
    else:
        draw.polygon([to_w(90, -11), to_w(105, -9), to_w(94, -6)], fill=FRAME_BLACK)

def render_cyber_reel_frame(creature: dict, frame_idx: int, total_frames: int) -> Image.Image:
    t = frame_idx / total_frames * 2 * math.pi

    img = Image.new("RGBA", (WIDTH, HEIGHT), (244, 241, 235, 255))
    draw = ImageDraw.Draw(img)

    light_glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    l_draw = ImageDraw.Draw(light_glow)
    l_draw.ellipse([100, 120, 620, 640], fill=(255, 255, 255, 75))
    img = Image.alpha_composite(img, light_glow.filter(ImageFilter.GaussianBlur(50)))
    draw = ImageDraw.Draw(img)

    title_font = get_font(38, bold=True)
    sub_font = get_font(15, bold=True)
    badge_font = get_font(13, bold=True)

    y_head = 45
    for line in creature["title_lines"]:
        draw.text((45, y_head), line, font=title_font, fill=(24, 28, 34))
        y_head += 44

    y_head += 12
    draw.line([(45, y_head), (220, y_head)], fill=(205, 200, 190), width=1)

    y_head += 14
    draw.text((45, y_head), creature["subtitle"], font=sub_font, fill=(110, 115, 125))

    y_head += 35
    draw.rounded_rectangle([45, y_head, 68, y_head + 22], radius=4, fill=(247, 223, 30))
    draw.text((49, y_head + 3), "JS", font=badge_font, fill=(15, 15, 15))
    draw.text((76, y_head + 3), "Vanilla JavaScript", font=badge_font, fill=(50, 55, 65))

    y_head += 28
    draw.rounded_rectangle([45, y_head, 68, y_head + 22], radius=4, fill=(38, 77, 228))
    draw.text((47, y_head + 3), "CSS", font=badge_font, fill=(255, 255, 255))
    draw.text((76, y_head + 3), "CSS3", font=badge_font, fill=(50, 55, 65))

    cursor_x = 160 + math.cos(t * 1.8) * 60 + (frame_idx % 40) * 1.5
    cursor_y = 520 + math.sin(t * 2.2) * 45

    creature_x = 420 + math.cos(t * 1.8 - 0.5) * 80
    creature_y = 380 + math.sin(t * 2.2 - 0.5) * 60
    angle = math.atan2(cursor_y - creature_y, cursor_x - creature_x)

    trail_pts = []
    for step in range(12):
        px = creature_x + (cursor_x - creature_x) * (step / 12)
        py = creature_y + (cursor_y - creature_y) * (step / 12) + math.sin(step * 0.5 + t * 4) * 8
        trail_pts.append((px, py))
    for step in range(len(trail_pts) - 1):
        if step % 2 == 0:
            draw.line([trail_pts[step], trail_pts[step+1]], fill=(175, 170, 160), width=2)

    for g_idx in range(4, 0, -1):
        g_t = t - g_idx * 0.15
        gx = 420 + math.cos(g_t * 1.8 - 0.5) * 80 + g_idx * 28
        gy = 380 + math.sin(g_t * 2.2 - 0.5) * 60 - g_idx * 32
        g_angle = math.atan2(cursor_y - gy, cursor_x - gx)
        _draw_mech_quadruped(draw, gx, gy, g_angle, g_t, creature["id"], creature["accent"], is_ghost=True)

    _draw_mech_quadruped(draw, creature_x, creature_y, angle, t, creature["id"], creature["accent"], is_ghost=False)

    draw.arc([creature_x + 90, creature_y + 80, creature_x + 115, creature_y + 105], 40, 320, fill=(40, 45, 50), width=2)

    _draw_cursor_pointer(draw, cursor_x, cursor_y)

    card_y = 660
    card_h = 570
    draw.rounded_rectangle([40, card_y, 680, card_y + card_h], radius=16, fill=(15, 23, 42), outline=(30, 41, 59), width=2)

    draw.rounded_rectangle([40, card_y, 680, card_y + 44], radius=16, fill=(11, 18, 33))
    draw.ellipse([58, card_y + 16, 70, card_y + 28], fill=(239, 68, 68))
    draw.ellipse([78, card_y + 16, 90, card_y + 28], fill=(245, 158, 11))
    draw.ellipse([98, card_y + 16, 110, card_y + 28], fill=(16, 185, 129))

    draw.rounded_rectangle([130, card_y + 8, 150, card_y + 28], radius=3, fill=(247, 223, 30))
    draw.text((134, card_y + 10), "JS", font=get_font(11, bold=True), fill=(20, 20, 20))
    draw.text((158, card_y + 12), creature["file_name"], font=get_font(15, bold=True), fill=(148, 163, 184))
    draw.text((640, card_y + 8), "•••", font=get_font(16, bold=True), fill=(71, 85, 105))

    code_font = get_font(13, mono=True)
    num_font = get_font(13, mono=True)

    y_code = card_y + 60
    total_lines = len(creature["code_lines"])
    revealed_lines = min(total_lines, int((frame_idx / (total_frames * 0.7)) * total_lines) + 8)

    x_code = 95
    for l_idx in range(revealed_lines):
        if y_code > card_y + card_h - 25:
            break
        draw.text((58, y_code), f"{l_idx + 1:>2}", font=num_font, fill=(71, 85, 105))

        line_tuple = creature["code_lines"][l_idx]
        if isinstance(line_tuple, str):
            kw, var, eq, rest = line_tuple, "", "", ""
        else:
            kw = line_tuple[0] if len(line_tuple) > 0 else ""
            var = line_tuple[1] if len(line_tuple) > 1 else ""
            eq = line_tuple[2] if len(line_tuple) > 2 else ""
            rest = line_tuple[3] if len(line_tuple) > 3 else ""

        x_code = 95
        if kw.startswith("//"):
            draw.text((x_code, y_code), kw, font=code_font, fill=(100, 116, 139))
        else:
            if kw:
                draw.text((x_code, y_code), kw, font=code_font, fill=(198, 120, 221))
                x_code += len(kw) * 8 + 6
            if var:
                draw.text((x_code, y_code), var, font=code_font, fill=(224, 108, 117))
                x_code += len(var) * 8 + 6
            if eq:
                draw.text((x_code, y_code), eq, font=code_font, fill=(97, 175, 239))
                x_code += len(eq) * 8 + 6
            if rest:
                draw.text((x_code, y_code), rest, font=code_font, fill=(226, 232, 240))

        y_code += 22

    if frame_idx % 15 < 8:
        draw.rectangle([x_code + 2, y_code - 22, x_code + 10, y_code - 6], fill=(97, 175, 239))

    return img.convert("RGB")
