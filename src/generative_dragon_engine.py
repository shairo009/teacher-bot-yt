"""
Generative Realistic Interactive Creature Cursor Engine
Recreates the exact visual layout from realistic_komodo_dragon_cursor_demo.mp4 with full 2-Joint IK Legs & Hands Gait:
- Resolution: 1080 x 1920 Full HD Vertical
- Deep Midnight Navy Background (#0B1B26 / #0E2331)
- Top Header: [SPECIES NAME] / Realistic interactive cursor • [Scientific Name]
- Serif Title: Interactive Dragon Cursor
- Framed Canvas Window with warm parchment background
- Organic Generative Creature with 2-Joint IK Articulated Legs, Reaching Claws, and Stepping Gait
- Viral Call to Action: Comment :- "Dragon" 📩
- macOS Dark VS Code Card (Dragon.js) with real transform math
- Bottom Pill: Interactive motion • fluid trail follows the pointer / Species: ...
- Bottom Timeline Progress Bar
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
            "  // 2-Joint Inverse Kinematics Leg Solver",
            "  legs.forEach(leg => {",
            "    const hip = getSpineAnchor(leg.spineIdx, leg.side);",
            "    const ik = solve2JointIK(hip, leg.foot, leg.l1, leg.l2, leg.bend);",
            "    renderArticulatedLimb(ctx, ik);",
            "  });",
            "  for (let i = 1; i < N; i++) {",
            "    let e = elems[i]; let ep = elems[i - 1];",
            "    const a = Math.atan2(e.y - ep.y, e.x - ep.x);",
            "    e.x += (ep.x - e.x + (Math.cos(a) * (100 - i)) / 5) / 4;",
            "    e.y += (ep.y - e.y + (Math.sin(a) * (100 - i)) / 5) / 4;",
            "  }",
            "};"
        ],
        "yt_title": "Realistic Interactive Dragon Cursor with 2-Joint IK Legs in JS 🐉✨ #JavaScript #Coding #Shorts",
        "yt_desc": "🐉 Realistic Interactive Dragon Cursor with 2-joint Inverse Kinematics legs & reaching claws in Vanilla JavaScript!\n\nSpecies: Varanus komodoensis (Komodo Dragon)\nComment 'Dragon' to get full source code!\n\n#JavaScript #CreativeCoding #WebDevelopment #Frontend #Shorts #Coding"
    },
    {
        "id": "emperor_scorpion",
        "name": "EMPEROR SCORPION",
        "title": "Interactive Scorpion Cursor",
        "scientific": "Pandinus imperator",
        "comment_keyword": "Scorpion",
        "file_name": "Scorpion.js",
        "accent": (255, 180, 0),
        "code_lines": [
            "const animateScorpion = () => {",
            "  requestAnimationFrame(animateScorpion);",
            "  const p = getPointerPosition();",
            "  // Pincer arms IK & 6-legged tripod gait",
            "  solvePincerIK(leftClaw, p);",
            "  solvePincerIK(rightClaw, p);",
            "  stepTripodGait(walkingLegs);",
            "  renderClawsAndStinger(ctx, scorpion);",
            "};"
        ],
        "yt_title": "Realistic Emperor Scorpion IK Cursor in JS 🦂🔥 #JavaScript #Shorts #WebDev",
        "yt_desc": "🦂 Build an Emperor Scorpion interactive cursor with articulated pincer claws & walking leg gait in Vanilla JavaScript!\n\nSpecies: Pandinus imperator\nComment 'Scorpion' for code!\n\n#JavaScript #CreativeCoding #WebDev #Shorts"
    },
    {
        "id": "cyber_wolf",
        "name": "CYBER ROBOT WOLF",
        "title": "Interactive Cyber Wolf Cursor",
        "scientific": "Canis lupus cyberneticus",
        "comment_keyword": "Wolf",
        "file_name": "CyberWolf.js",
        "accent": (0, 220, 255),
        "code_lines": [
            "const runWolfGait = () => {",
            "  requestAnimationFrame(runWolfGait);",
            "  updateSpineLag(wolf.spine, pointer);",
            "  // 4-Leg Gallop Gait with 2-Joint IK",
            "  for (let l = 0; l < 4; l++) {",
            "    const leg = wolf.legs[l];",
            "    const step = computeGallopArc(leg.phase, time);",
            "    const ik = solveIK(leg.shoulder, step.footPos, 38, 42);",
            "    drawHydraulicLimb(ctx, ik);",
            "  }",
            "};"
        ],
        "yt_title": "Interactive Cyber Wolf with 2-Joint IK Paws in JS 🐺⚡ #Coding #Shorts #JavaScript",
        "yt_desc": "🐺 Mechanical Cyber Wolf Cursor with realistic 2-joint IK leg galloping physics in JavaScript Canvas!\n\nComment 'Wolf' for code!\n\n#JavaScript #WebDevelopment #Frontend #Shorts"
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

    # 5. Generative Creature Drawing inside Frame Box
    cb_x = box_x + box_w // 2
    cb_y = box_y + box_h // 2

    # Movement trajectory (Swimming Lissajous loop)
    rad_x = box_w * 0.32
    rad_y = box_h * 0.28

    NUM_SEGS = 26
    spine = []
    for s_idx in range(NUM_SEGS):
        tau = t - s_idx * 0.018
        sx = cb_x + math.cos(3 * tau) * rad_x
        sy = cb_y + math.sin(4 * tau) * rad_y
        spine.append((sx, sy))

    # ─────────────────────────────────────────────────────────────
    # ARTICULATED 2-JOINT IK LEGS & HANDS
    # ─────────────────────────────────────────────────────────────
    # Front Hands/Paws attached at spine[5]
    # Hind Feet/Paws attached at spine[16]
    leg_configs = [
        {"name": "Front-L", "spine_idx": 4,  "side": -1, "l1": 34, "l2": 36, "bend": -1, "phase": 0.0, "reach_f": 52},
        {"name": "Front-R", "spine_idx": 4,  "side":  1, "l1": 34, "l2": 36, "bend":  1, "phase": math.pi, "reach_f": 52},
        {"name": "Rear-L",  "spine_idx": 15, "side": -1, "l1": 36, "l2": 38, "bend": -1, "phase": math.pi, "reach_f": 48},
        {"name": "Rear-R",  "spine_idx": 15, "side":  1, "l1": 36, "l2": 38, "bend":  1, "phase": 0.0, "reach_f": 48},
    ]

    for leg in leg_configs:
        s_pos = spine[leg["spine_idx"]]
        s_prev = spine[leg["spine_idx"] - 1]
        b_angle = math.atan2(s_pos[1] - s_prev[1], s_pos[0] - s_prev[0])
        
        # Shoulder / Hip joint on side of spine
        hip_ang = b_angle + (math.pi / 2) * leg["side"]
        hip = (s_pos[0] + math.cos(hip_ang) * 16, s_pos[1] + math.sin(hip_ang) * 16)

        # Gait Stepping Cycle (Alternating Lift & Plant)
        gait_t = (t * 8.0 + leg["phase"]) % (2 * math.pi)
        step_is_swinging = math.sin(gait_t) > 0.0
        step_lead = math.cos(gait_t) * 20 if step_is_swinging else -10
        step_lift = math.sin(gait_t) * 12 if step_is_swinging else 0

        # Foot Target Position
        reach_ang = b_angle + leg["side"] * (math.pi * 0.42)
        foot_x = hip[0] + math.cos(reach_ang) * leg["reach_f"] + math.cos(b_angle) * step_lead
        foot_y = hip[1] + math.sin(reach_ang) * leg["reach_f"] + math.sin(b_angle) * step_lead - step_lift
        foot = (foot_x, foot_y)

        # Solve 2-Joint Analytical Inverse Kinematics
        hip_pt, knee_pt, foot_pt = solve_ik_2joint(hip, foot, leg["l1"], leg["l2"], leg["bend"])

        # Draw Articulated Limb: Upper Arm/Thigh + Forearm/Shin + Joints + Claws
        # Thigh / Upper Arm
        draw.line([hip_pt, knee_pt], fill=(30, 36, 46), width=7)
        # Shin / Forearm
        draw.line([knee_pt, foot_pt], fill=(16, 20, 26), width=5)
        # Knee/Elbow Joint Chrome Circle
        draw.ellipse([knee_pt[0]-4, knee_pt[1]-4, knee_pt[0]+4, knee_pt[1]+4], fill=(225, 235, 245), outline=(15, 20, 28), width=1)
        # Foot/Hand Claws
        draw.ellipse([foot_pt[0]-4, foot_pt[1]-4, foot_pt[0]+4, foot_pt[1]+4], fill=(12, 16, 22))
        for c in [-1, 0, 1]:
            claw_tip = (foot_pt[0] + math.cos(b_angle + c * 0.35) * 8, foot_pt[1] + math.sin(b_angle + c * 0.35) * 8)
            draw.line([foot_pt, claw_tip], fill=(20, 24, 30), width=2)

    # Helper for smooth quadratic bezier curve
    def draw_bezier(p0, p1, p2, color, width=1):
        pts = []
        steps = 10
        for st in range(steps + 1):
            u = st / steps
            bx = (1 - u)**2 * p0[0] + 2 * (1 - u) * u * p1[0] + u**2 * p2[0]
            by = (1 - u)**2 * p0[1] + 2 * (1 - u) * u * p1[1] + u**2 * p2[1]
            pts.append((bx, by))
        for st in range(len(pts) - 1):
            draw.line([pts[st], pts[st+1]], fill=color, width=width)

    # Draw Lateral Undulating Feathers / Rib Tendrils (Tail to Head)
    for s_idx in range(NUM_SEGS - 1, 1, -1):
        p1 = spine[s_idx]
        p0 = spine[s_idx - 1]
        norm = s_idx / NUM_SEGS
        seg_angle = math.atan2(p1[1] - p0[1], p1[0] - p0[0])

        envelope = math.sin(norm * math.pi) ** 0.55
        max_len = envelope * 140

        for side in [-1, 1]:
            for layer in range(2):
                l_factor = (layer + 1) / 2.0
                t_len = max_len * l_factor
                
                wave_offset = math.sin(t * 8 - s_idx * 0.45 + layer * 0.6) * 0.25
                arch_angle = seg_angle + side * (math.pi * 0.52 + wave_offset)

                ctrl_dist = t_len * 0.55
                ctrl_x = p1[0] + math.cos(arch_angle) * ctrl_dist
                ctrl_y = p1[1] + math.sin(arch_angle) * ctrl_dist

                sweep_angle = seg_angle + side * (math.pi * 0.1) + math.pi
                tip_x = ctrl_x + math.cos(sweep_angle) * (t_len * 0.7)
                tip_y = ctrl_y + math.sin(sweep_angle) * (t_len * 0.7)

                ink_color = (25, 30, 38) if layer == 1 else (90, 100, 115)
                line_w = 2 if (layer == 1 and s_idx < 12) else 1
                draw_bezier(p1, (ctrl_x, ctrl_y), (tip_x, tip_y), ink_color, width=line_w)

    # Draw Main Spine Vertebrae (Articulated Armor Scales)
    for s_idx in range(len(spine) - 1, 0, -1):
        p1 = spine[s_idx]
        p0 = spine[s_idx - 1]
        norm = s_idx / NUM_SEGS
        v_width = max(4, int(26 * (1.0 - norm * 0.75)))
        draw.line([p0, p1], fill=(16, 20, 26), width=v_width)
        draw.ellipse([p1[0]-v_width//2, p1[1]-v_width//2, p1[0]+v_width//2, p1[1]+v_width//2], fill=(26, 32, 40), outline=(10, 12, 16), width=1)

    # Draw Reptilian Dragon Head
    head_p = spine[0]
    head_prev = spine[1]
    h_angle = math.atan2(head_p[1] - head_prev[1], head_p[0] - head_prev[0])

    cos_h, sin_h = math.cos(h_angle), math.sin(h_angle)
    perp_h = (-sin_h, cos_h)

    snout = (head_p[0] + cos_h * 38, head_p[1] + sin_h * 38)
    left_jaw = (head_p[0] - cos_h * 14 + perp_h[0] * 22, head_p[1] - sin_h * 14 + perp_h[1] * 22)
    right_jaw = (head_p[0] - cos_h * 14 - perp_h[0] * 22, head_p[1] - sin_h * 14 - perp_h[1] * 22)
    crown = (head_p[0] - cos_h * 30, head_p[1] - sin_h * 30)

    draw.polygon([snout, left_jaw, crown, right_jaw], fill=(12, 15, 20), outline=(240, 245, 255), width=2)
    draw.line([(head_p[0] - cos_h * 12), (head_p[0] + cos_h * 28)], fill=(225, 235, 245), width=4)

    # Specular Eyes
    eye_l = (head_p[0] + cos_h * 6 + perp_h[0] * 11, head_p[1] + sin_h * 6 + perp_h[1] * 11)
    eye_r = (head_p[0] + cos_h * 6 - perp_h[0] * 11, head_p[1] + sin_h * 6 - perp_h[1] * 11)
    draw.ellipse([eye_l[0]-4, eye_l[0]-4, eye_l[0]+4, eye_l[0]+4], fill=(255, 255, 255))
    draw.ellipse([eye_r[0]-4, eye_r[0]-4, eye_r[0]+4, eye_r[0]+4], fill=(255, 255, 255))

    # Whiskers at Snout
    for side in [-1, 1]:
        w_ang = h_angle + side * 1.7
        w_tip = (snout[0] + math.cos(w_ang) * 45, snout[1] + math.sin(w_ang) * 45)
        draw.line([snout, w_tip], fill=(30, 35, 45), width=2)

    # 6. Viral Call-To-Action (Comment :- "Dragon" 📩)
    cta_y = 950
    cta_font = get_font(56, bold=True, serif=True)
    keyword = species["comment_keyword"]
    cta_txt = f'Comment :- "{keyword}"'
    draw.text((WIDTH // 2 - 50, cta_y), cta_txt, font=cta_font, fill=(255, 255, 255), anchor="mt")

    # Vector Envelope Icon with Down Arrow
    env_x = WIDTH // 2 + 250
    env_y = cta_y + 16
    draw.rounded_rectangle([env_x, env_y, env_x + 58, env_y + 44], radius=6, fill=(225, 240, 255), outline=(100, 160, 230), width=3)
    draw.line([(env_x, env_y), (env_x + 29, env_y + 24), (env_x + 58, env_y)], fill=(100, 160, 230), width=3)
    draw.polygon([(env_x + 29, env_y - 2), (env_x + 20, env_y - 14), (env_x + 38, env_y - 14)], fill=(240, 60, 60))

    # 7. macOS VS Code Dark Window (Dragon.js)
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
        elif "Math." in line or "setAttributeNS" in line:
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

    draw.text((pill_x + 30, pill_y + 24), "Interactive motion • fluid trail follows the pointer", font=pill_title_font, fill=(255, 255, 255))
    draw.text((pill_x + 30, pill_y + 68), f"Species: {species['scientific']}", font=pill_sub_font, fill=(140, 155, 175))

    # 9. Bottom Progress Bar
    bar_w = 880
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 1840
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 10], radius=5, fill=(40, 52, 68))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + 10], radius=5, fill=(230, 235, 240))

    return img.convert("RGB")
