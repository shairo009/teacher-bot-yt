"""
Realistic Articulated Creature Code-Reel Engine
Exact 1-to-1 Discrete Physics Simulation Ported from HTML:
- Smooth, natural walking speed (not hyper fast)
- True 8-Legged Tripod Stepping Gait with foot planting & lift arcs
- 3-Joint Ball & Socket Pincer Arms reaching and snapping
- 7 Articulated Mesosoma Armor Plates with Dorsal Keels
- 5-Segment 3D Curved Stinger Tail with Glowing Venom Bulb
- Lower macOS Dark Editor with smooth sliding JS code
- Minimalist layout: Top header = Animal Name ONLY
- NO Audio (Clean video for YouTube Shorts)
"""
from __future__ import annotations

import math
import os
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
            "  curlStingerTail(scorpion.tail, Math.sin(frm * 2.5) * 0.35);",
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
        "id": "black_mamba",
        "name": "BLACK MAMBA VIPER",
        "file_name": "Viper.js",
        "accent": (34, 197, 94),
        "code_lines": [
            "// ─── BLACK MAMBA SERPENTINE WAVE ENGINE ───",
            "const viper = new SerpentineSpine({ vertebrae: 48 });",
            "",
            "const updateViperPhysics = () => {",
            "  requestAnimationFrame(updateViperPhysics);",
            "  const head = viper.spine[0];",
            "  head.x += (mouse.x - head.x) * 0.15;",
            "  head.y += (mouse.y - head.y) * 0.15;",
            "",
            "  // 1. Serpentine Lateral Undulation Wave",
            "  for (let i = 1; i < viper.length; i++) {",
            "    const prev = viper.spine[i - 1];",
            "    const curr = viper.spine[i];",
            "    const dx = prev.x - curr.x;",
            "    const dy = prev.y - curr.y;",
            "    const dist = Math.hypot(dx, dy);",
            "    const wave = Math.sin(time * 6 + i * 0.35) * 6;",
            "    curr.x = prev.x - (dx / dist) * 14 + Math.cos(curr.angle) * wave;",
            "    curr.y = prev.y - (dy / dist) * 14 + Math.sin(curr.angle) * wave;",
            "  }",
            "  renderScalesAndFangs(ctx, viper);",
            "};"
        ],
        "yt_title": "Realistic Black Mamba Viper Cursor in JavaScript 🐍⚡ #JavaScript #Coding #Shorts",
        "yt_desc": "🐍 Realistic serpentine wave physics & interactive snake cursor in Vanilla JavaScript!\n\n#JavaScript #CreativeCoding #Frontend #Shorts"
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
    },
    {
        "id": "praying_mantis",
        "name": "GIANT PRAYING MANTIS",
        "file_name": "Mantis.js",
        "accent": (132, 204, 22),
        "code_lines": [
            "// ─── PRAYING MANTIS RAPTORIAL FOREARM IK ───",
            "const mantis = new InsectoidRig({ walkingLegs: 4, scythes: 2 });",
            "",
            "const loopMantis = () => {",
            "  requestAnimationFrame(loopMantis);",
            "  const target = getHuntingTarget();",
            "",
            "  // 1. Dual Spiked Raptorial Forearms (Scythes)",
            "  solveRaptorialIK(mantis.leftScythe,  target, 48, 56, -1);",
            "  solveRaptorialIK(mantis.rightScythe, target, 48, 56,  1);",
            "",
            "  // 2. 4 Slender Walking Legs Stepping Gait",
            "  for (let w = 0; w < 4; w++) {",
            "    const leg = mantis.walkingLegs[w];",
            "    const gait = computeInsectStep(leg.phase, frm);",
            "    const ik = solve3SegmentIK(leg.coxa, gait.pos, 32, 40, 36, leg.side);",
            "    renderSlenderLimb(ctx, ik);",
            "  }",
            "  renderTriangularHead(ctx, mantis.head);",
            "};"
        ],
        "yt_title": "Realistic Praying Mantis Raptor IK in JavaScript 🦗✨ #Coding #JavaScript #Shorts",
        "yt_desc": "🦗 Giant Praying Mantis interactive cursor with raptorial scythe arms and insectoid walking gait in JS!\n\n#JavaScript #CreativeCoding #Shorts"
    },
    {
        "id": "tarantula_spider",
        "name": "TARANTULA SPIDER",
        "file_name": "Tarantula.js",
        "accent": (249, 115, 22),
        "code_lines": [
            "// ─── TARANTULA 8-LEGGED RADIAL IK RIG ───",
            "const spider = new ArachnidRig({ legs: 8, chelicerae: 2 });",
            "",
            "const animateSpider = () => {",
            "  requestAnimationFrame(animateSpider);",
            "  const p = getPointerPosition();",
            "",
            "  // 1. Alternating Metachronal Stepping Waves",
            "  for (let l = 0; l < 8; l++) {",
            "    const leg = spider.legs[l];",
            "    const side = l < 4 ? -1 : 1;",
            "    const step = computeArachnidWave(l, frm);",
            "    const ik = solve3SegmentIK(leg.coxa, step.target, 28, 38, 34, side);",
            "    renderHairyChitinLimb(ctx, ik);",
            "  }",
            "",
            "  // 2. Fanged Chelicerae & Cephalothorax",
            "  renderCheliceraeFangs(ctx, spider.head, p);",
            "  renderVelvetAbdomen(ctx, spider.abdomen);",
            "};"
        ],
        "yt_title": "Realistic 8-Legged Tarantula Spider in JavaScript 🕷️🔥 #JavaScript #Shorts #WebDev",
        "yt_desc": "🕷️ Realistic 8-legged Tarantula Spider interactive cursor with metachronal wave gait in JS!\n\n#JavaScript #CreativeCoding #Frontend #Shorts"
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# DISCRETE SKELETAL SIMULATOR (Identical to JavaScript HTML Engine)
# ─────────────────────────────────────────────────────────────────────────────
class ScorpionSimulator:
    def __init__(self, cx: float, cy: float, rx: float, ry: float):
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.x = cx
        self.y = cy
        self.angle = 0.0
        self.speed = 0.0
        self.tergites = [{"x": cx, "y": cy, "angle": 0.0} for _ in range(7)]
        self.tail = [{"x": cx, "y": cy, "angle": 0.0} for _ in range(5)]
        
        # 8 Walking Legs (4 Left, 4 Right)
        self.legs = [
            {"id": "L1", "side": -1, "spread": -0.85, "rest_d": 88, "l1": 26, "l2": 36, "l3": 32, "group": 0, "cur": [cx - 85, cy + 40], "tgt": [cx - 85, cy + 40], "start": [cx - 85, cy + 40], "prog": 1.0},
            {"id": "L2", "side": -1, "spread": -1.30, "rest_d": 102, "l1": 30, "l2": 42, "l3": 36, "group": 1, "cur": [cx - 95, cy + 40], "tgt": [cx - 95, cy + 40], "start": [cx - 95, cy + 40], "prog": 1.0},
            {"id": "L3", "side": -1, "spread": -1.75, "rest_d": 106, "l1": 32, "l2": 44, "l3": 38, "group": 0, "cur": [cx - 100, cy + 40], "tgt": [cx - 100, cy + 40], "start": [cx - 100, cy + 40], "prog": 1.0},
            {"id": "L4", "side": -1, "spread": -2.20, "rest_d": 94, "l1": 28, "l2": 38, "l3": 34, "group": 1, "cur": [cx - 90, cy + 40], "tgt": [cx - 90, cy + 40], "start": [cx - 90, cy + 40], "prog": 1.0},
            
            {"id": "R1", "side":  1, "spread":  0.85, "rest_d": 88, "l1": 26, "l2": 36, "l3": 32, "group": 1, "cur": [cx + 85, cy + 40], "tgt": [cx + 85, cy + 40], "start": [cx + 85, cy + 40], "prog": 1.0},
            {"id": "R2", "side":  1, "spread":  1.30, "rest_d": 102, "l1": 30, "l2": 42, "l3": 36, "group": 0, "cur": [cx + 95, cy + 40], "tgt": [cx + 95, cy + 40], "start": [cx + 95, cy + 40], "prog": 1.0},
            {"id": "R3", "side":  1, "spread":  1.75, "rest_d": 106, "l1": 32, "l2": 44, "l3": 38, "group": 1, "cur": [cx + 100, cy + 40], "tgt": [cx + 100, cy + 40], "start": [cx + 100, cy + 40], "prog": 1.0},
            {"id": "R4", "side":  1, "spread":  2.20, "rest_d": 94, "l1": 28, "l2": 38, "l3": 34, "group": 0, "cur": [cx + 90, cy + 40], "tgt": [cx + 90, cy + 40], "start": [cx + 90, cy + 40], "prog": 1.0},
        ]
        self.pincers = [
            {"id": "Chela-L", "side": -1, "reach": -0.42, "l1": 54, "l2": 62},
            {"id": "Chela-R", "side":  1, "reach":  0.42, "l1": 54, "l2": 62}
        ]

    def update(self, sim_time: float):
        # 1. Smooth Wandering Patrol Target (Gentle speed, exactly matching HTML)
        target_x = self.cx + math.cos(sim_time * 0.7) * (self.rx * 0.9) + math.sin(sim_time * 1.4) * (self.rx * 0.25)
        target_y = self.cy + math.sin(sim_time * 0.9) * (self.ry * 0.85) + math.cos(sim_time * 1.8) * (self.ry * 0.20)

        # 2. Smooth Steering & Realistic Forward Crawl
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        target_ang = math.atan2(dy, dx)

        diff = target_ang - self.angle
        while diff < -math.pi: diff += math.pi * 2
        while diff > math.pi: diff -= math.pi * 2
        self.angle += diff * 0.07

        if dist > 30:
            target_spd = min(3.8, dist * 0.04)
            self.speed += (target_spd - self.speed) * 0.08
        else:
            self.speed *= 0.88

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        perp_x = -sin_a
        perp_y =  cos_a

        # 3. 7 Tergite Plates Follow-Chain
        prev_x, prev_y, prev_ang = self.x, self.y, self.angle
        for i, t_seg in enumerate(self.tergites):
            s_dist = 18 - i * 0.8
            p_dx = prev_x - t_seg["x"]
            p_dy = prev_y - t_seg["y"]
            t_seg["angle"] = math.atan2(p_dy, p_dx)
            t_seg["x"] = prev_x - math.cos(t_seg["angle"]) * s_dist
            t_seg["y"] = prev_y - math.sin(t_seg["angle"]) * s_dist
            prev_x, prev_y = t_seg["x"], t_seg["y"]

        # 4. 5 Tail Segments Curving Arc
        prev_tail_x, prev_tail_y = self.tergites[-1]["x"], self.tergites[-1]["y"]
        prev_tail_ang = self.tergites[-1]["angle"]
        tail_curl = math.sin(sim_time * 2.5) * 0.15
        for i, t_seg in enumerate(self.tail):
            s_dist = 20 - i * 1.5
            t_ang = prev_tail_ang + tail_curl * (i + 1)
            t_seg["angle"] = t_ang
            t_seg["x"] = prev_tail_x - math.cos(t_ang) * s_dist
            t_seg["y"] = prev_tail_y - math.sin(t_ang) * s_dist
            prev_tail_x, prev_tail_y, prev_tail_ang = t_seg["x"], t_seg["y"], t_ang

        # 5. 8 Walking Legs with True Alternating Tripod Stepping Gait
        gait_clock = sim_time * 7.5
        for idx, leg in enumerate(self.legs):
            leg_i = idx % 4
            hip_along = 12 - leg_i * 11
            hip_x = self.x + cos_a * hip_along + perp_x * (24 * leg["side"])
            hip_y = self.y + sin_a * hip_along + perp_y * (24 * leg["side"])
            leg["hip"] = (hip_x, hip_y)

            leg_spread = self.angle + leg["spread"]
            ideal_x = hip_x + math.cos(leg_spread) * leg["rest_d"]
            ideal_y = hip_y + math.sin(leg_spread) * leg["rest_d"]

            dist_ideal = math.hypot(ideal_x - leg["cur"][0], ideal_y - leg["cur"][1])
            group_phase = math.sin(gait_clock) if leg["group"] == 0 else -math.sin(gait_clock)

            # Step Trigger
            if dist_ideal > 36 and leg["prog"] >= 1.0 and group_phase > 0.1:
                leg["prog"] = 0.0
                leg["start"] = [leg["cur"][0], leg["cur"][1]]
                leg["tgt"] = [
                    ideal_x + math.cos(self.angle) * 26,
                    ideal_y + math.sin(self.angle) * 26
                ]

            # Step Swing Progression
            if leg["prog"] < 1.0:
                leg["prog"] += 0.14
                p = min(1.0, leg["prog"])
                ease_p = 0.5 - math.cos(p * math.pi) / 2
                leg["cur"][0] = leg["start"][0] + (leg["tgt"][0] - leg["start"][0]) * ease_p
                leg["cur"][1] = leg["start"][1] + (leg["tgt"][1] - leg["start"][1]) * ease_p


# Global simulation cache for smooth continuous video generation
_SIM_CACHE = {}

def render_generative_frame(species: dict, frame_idx: int, total_frames: int) -> Image.Image:
    progress = frame_idx / total_frames
    sim_time = (frame_idx / FPS) * 1.05  # Smooth 1-to-1 real time speed!

    # 1. Deep Midnight Navy Background
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

    # Frame Outer Border & Parchment
    draw.rectangle([box_x - 12, box_y - 12, box_x + box_w + 12, box_y + box_h + 12], fill=(235, 230, 220), outline=(190, 185, 175), width=2)
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=(239, 236, 228))

    cb_x = box_x + box_w // 2
    cb_y = box_y + box_h // 2
    rad_x = box_w * 0.33
    rad_y = box_h * 0.30

    sp_id = species.get("id", "emperor_scorpion")
    accent_color = species.get("accent", (234, 179, 8))

    # Initialize / Advance Stateful Simulation for this render session
    sim_key = f"{sp_id}_{total_frames}"
    if frame_idx == 0 or sim_key not in _SIM_CACHE:
        _SIM_CACHE[sim_key] = ScorpionSimulator(cb_x, cb_y, rad_x, rad_y)
    
    sim = _SIM_CACHE[sim_key]
    sim.update(sim_time)

    # ─────────────────────────────────────────────────────────────
    # DRAW MODULAR ARTICULATED SCORPION (Symmetric 8 Legs + Claws)
    # ─────────────────────────────────────────────────────────────
    cos_a = math.cos(sim.angle)
    sin_a = math.sin(sim.angle)
    perp_x = -sin_a
    perp_y =  cos_a

    # 1. 8 Walking Legs (Coxa + Femur + Tibia + Tarsus + Amber Nodes)
    for leg in sim.legs:
        h_p = leg["hip"]
        foot_p = (leg["cur"][0], leg["cur"][1])
        h_p, j1_p, j2_p, f_p = solve_ik_3segment(h_p, foot_p, leg["l1"], leg["l2"], leg["l3"], leg["side"])

        draw.line([h_p, j1_p], fill=(16, 22, 32), width=7)
        draw.line([j1_p, j2_p], fill=(24, 32, 46), width=6)
        draw.line([j2_p, f_p], fill=(12, 16, 22), width=4)
        draw.ellipse([j1_p[0]-3, j1_p[1]-3, j1_p[0]+3, j1_p[1]+3], fill=accent_color)
        draw.ellipse([j2_p[0]-3, j2_p[1]-3, j2_p[0]+3, j2_p[1]+3], fill=accent_color)
        draw.ellipse([f_p[0]-3, f_p[1]-3, f_p[0]+3, f_p[1]+3], fill=(10, 12, 16))

    # 2. 7 Mesosoma Armor Tergite Plates with Dorsal Keels
    for i, seg in enumerate(sim.tergites):
        s_cos = math.cos(seg["angle"])
        s_sin = math.sin(seg["angle"])
        s_perp_x = -s_sin
        s_perp_y =  s_cos
        half_w = max(13, 34 - i * 3.0)
        half_h = 8

        p1 = (seg["x"] - s_cos * half_h + s_perp_x * half_w, seg["y"] - s_sin * half_h + s_perp_y * half_w)
        p2 = (seg["x"] + s_cos * half_h + s_perp_x * (half_w * 0.9), seg["y"] + s_sin * half_h + s_perp_y * (half_w * 0.9))
        p3 = (seg["x"] + s_cos * half_h - s_perp_x * (half_w * 0.9), seg["y"] + s_sin * half_h - s_perp_y * (half_w * 0.9))
        p4 = (seg["x"] - s_cos * half_h - s_perp_x * half_w, seg["y"] - s_sin * half_h - s_perp_y * half_w)

        draw.polygon([p1, p2, p3, p4], fill=(16, 22, 32), outline=accent_color, width=1)
        # Center Keel
        draw.line([(seg["x"] - s_cos * 6, seg["y"] - s_sin * 6), (seg["x"] + s_cos * 6, seg["y"] + s_sin * 6)], fill=(202, 138, 4), width=2)

    # 3. Prosoma Head Carapace
    c_front = (sim.x + cos_a * 34, sim.y + sin_a * 34)
    c_r1 = (sim.x + cos_a * 18 + perp_x * 28, sim.y + sin_a * 18 + perp_y * 28)
    c_r2 = (sim.x - cos_a * 16 + perp_x * 32, sim.y - sin_a * 16 + perp_y * 32)
    c_l2 = (sim.x - cos_a * 16 - perp_x * 32, sim.y - sin_a * 16 - perp_y * 32)
    c_l1 = (sim.x + cos_a * 18 - perp_x * 28, sim.y + sin_a * 18 - perp_y * 28)
    draw.polygon([c_front, c_r1, c_r2, c_l2, c_l1], fill=(12, 16, 24), outline=accent_color, width=2)

    eye_pos = (sim.x + cos_a * 14, sim.y + sin_a * 14)
    draw.ellipse([eye_pos[0]-3.5, eye_pos[1]-3.5, eye_pos[0]+3.5, eye_pos[1]+3.5], fill=(254, 240, 138))

    # 4. 2 Giant Front Pincer Crusher Arms (Hands / Chelae)
    for p in sim.pincers:
        shoulder = (sim.x + cos_a * 26 + perp_x * (22 * p["side"]),
                    sim.y + sin_a * 26 + perp_y * (22 * p["side"]))
        snap_open = math.sin(sim_time * 3.5 + p["side"]) * 0.2 + 0.35
        pincer_ang = sim.angle + p["reach"]
        p_target = (shoulder[0] + math.cos(pincer_ang) * 102,
                    shoulder[1] + math.sin(pincer_ang) * 102)

        sh_pt, elbow_pt, wrist_pt = solve_ik_2joint(shoulder, p_target, p["l1"], p["l2"], p["side"] * -1)

        draw.line([sh_pt, elbow_pt], fill=(16, 22, 32), width=12)
        draw.line([elbow_pt, wrist_pt], fill=(24, 32, 46), width=10)
        draw.ellipse([elbow_pt[0]-5, elbow_pt[1]-5, elbow_pt[0]+5, elbow_pt[1]+5], fill=accent_color)

        w_ang = math.atan2(wrist_pt[1] - elbow_pt[1], wrist_pt[0] - elbow_pt[0])
        w_cos, w_sin = math.cos(w_ang), math.sin(w_ang)
        w_perp_x, w_perp_y = -w_sin, w_cos

        chela_poly = [
            (wrist_pt[0] - w_cos * 8 + w_perp_x * 15, wrist_pt[1] - w_sin * 8 + w_perp_y * 15),
            (wrist_pt[0] + w_cos * 22 + w_perp_x * 10, wrist_pt[1] + w_sin * 22 + w_perp_y * 10),
            (wrist_pt[0] + w_cos * 22 - w_perp_x * 10, wrist_pt[1] + w_sin * 22 - w_perp_y * 10),
            (wrist_pt[0] - w_cos * 8 - w_perp_x * 15, wrist_pt[1] - w_sin * 8 - w_perp_y * 15)
        ]
        draw.polygon(chela_poly, fill=(10, 14, 20), outline=accent_color, width=2)

        f_tip = (wrist_pt[0] + math.cos(w_ang + p["side"] * 0.3) * 40,
                 wrist_pt[1] + math.sin(w_ang + p["side"] * 0.3) * 40)
        draw.line([(wrist_pt[0] + w_cos * 18, wrist_pt[1] + w_sin * 18), f_tip], fill=accent_color, width=4)

        m_tip = (wrist_pt[0] + math.cos(w_ang - p["side"] * snap_open) * 36,
                 wrist_pt[1] + math.sin(w_ang - p["side"] * snap_open) * 36)
        draw.line([(wrist_pt[0] + w_cos * 18, wrist_pt[1] + w_sin * 18), m_tip], fill=(202, 138, 4), width=3)

    # 5. 5 Metasoma Tail Segments & Telson Venom Stinger
    tail_prev = (sim.tergites[-1]["x"], sim.tergites[-1]["y"])
    for i, t_seg in enumerate(sim.tail):
        tx, ty = t_seg["x"], t_seg["y"]
        t_width = max(5, int(14 - i * 1.4))
        draw.line([tail_prev, (tx, ty)], fill=(18, 24, 34), width=t_width)
        draw.ellipse([tx - t_width//2, ty - t_width//2, tx + t_width//2, ty + t_width//2], fill=(28, 38, 52))
        tail_prev = (tx, ty)

    last_tail = sim.tail[-1]
    telson_bulb = (last_tail["x"], last_tail["y"])
    draw.ellipse([telson_bulb[0]-9, telson_bulb[1]-9, telson_bulb[0]+9, telson_bulb[1]+9], fill=(202, 138, 4), outline=(254, 240, 138), width=2)
    sting_tip = (telson_bulb[0] + math.cos(last_tail["angle"] + 0.8) * 22, telson_bulb[1] + math.sin(last_tail["angle"] + 0.8) * 22)
    draw.line([telson_bulb, sting_tip], fill=(254, 240, 138), width=3)

    # ─────────────────────────────────────────────────────────────
    # LOWER SECTION: macOS DARK CODE WINDOW WITH SLIDING CODE
    # ─────────────────────────────────────────────────────────────
    card_w, card_h = 920, 940
    card_x = (WIDTH - card_w) // 2
    card_y = 885

    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=22, fill=(12, 18, 25), outline=(28, 38, 50), width=2)

    title_h = 56
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + title_h], radius=22, fill=(8, 13, 19))
    draw.rectangle([card_x, card_y + 30, card_x + card_w, card_y + title_h], fill=(8, 13, 19))

    draw.ellipse([card_x + 26, card_y + 22, card_x + 40, card_y + 36], fill=(255, 95, 86))
    draw.ellipse([card_x + 50, card_y + 22, card_x + 64, card_y + 36], fill=(255, 189, 46))
    draw.ellipse([card_x + 74, card_y + 22, card_x + 88, card_y + 36], fill=(39, 201, 63))

    draw.rounded_rectangle([card_x + 125, card_y + 12, card_x + 150, card_y + 42], radius=4, fill=(247, 223, 30))
    draw.text((card_x + 130, card_y + 16), "JS", font=get_font(15, bold=True), fill=(20, 20, 20))
    draw.text((card_x + 162, card_y + 18), species["file_name"], font=get_font(20, bold=True), fill=(160, 175, 195))

    # Auto-Sliding / Smooth Code Scrolling
    all_lines = species["code_lines"]
    total_lines = len(all_lines)
    line_h = 34
    visible_lines = int((card_h - title_h - 40) / line_h)

    max_scroll_lines = max(0, total_lines - visible_lines)
    scroll_factor = 0.5 - math.cos(progress * math.pi) / 2
    curr_scroll = scroll_factor * max_scroll_lines

    start_line_idx = int(curr_scroll)
    line_pixel_offset = (curr_scroll - start_line_idx) * line_h

    code_font = get_font(20, mono=True)
    line_num_font = get_font(18, mono=True)

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

        draw.text((card_x + 35, y_pos), f"{actual_line_idx + 1:2d}", font=line_num_font, fill=(70, 85, 105))

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

    # Bottom Timeline Progress Bar
    bar_w = 920
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 1855
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 12], radius=6, fill=(35, 46, 62))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + 12], radius=6, fill=accent_color)

    return img.convert("RGB")
