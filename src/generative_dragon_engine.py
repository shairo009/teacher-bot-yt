"""
Minimalist Code-Reel Engine with Infinite Procedural Animal Synthesis
Features:
- Handcrafted Mega Roster (Scorpion, Dragon, Viper, Wolf, Mantis, Spider, etc.)
- Autonomous Procedural Synthesis Engine: When index exceeds roster, procedurally generates
  brand new unique species (Cyber, Lava, Bioluminescent, Armored, Insectoid, Serpentine)
  with tailored JavaScript IK code and distinct anatomy!
- Unlimited Unique Animals (Never repeats or runs out!)
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
        "scientific": "Pandinus imperator",
        "file_name": "Scorpion.js",
        "accent": (234, 179, 8),
        "code_lines": [
            "// ─── EMPEROR SCORPION KINEMATICS ───",
            "const scorpion = new CreatureRig({ segments: 38 });",
            "",
            "const animateScorpion = () => {",
            "  requestAnimationFrame(animateScorpion);",
            "  const p = getPointerPosition();",
            "",
            "  // 1. Solve 3-Joint Pincer Arms (Hands)",
            "  solvePincerIK(scorpion.leftArm,  p, 54, 62, -1);",
            "  solvePincerIK(scorpion.rightArm, p, 54, 62,  1);",
            "",
            "  // 2. 8-Legged Tripod Stepping Gait",
            "  for (let i = 0; i < 8; i++) {",
            "    const leg = scorpion.legs[i];",
            "    const side = i < 4 ? -1 : 1;",
            "    const hip = getHipSocket(scorpion.carapace, i, side);",
            "    const step = computeTripodStep(leg, frm, side);",
            "    const ik = solve3SegmentIK(hip, step.target, 24, 30, 26, side);",
            "    renderArticulatedLeg(ctx, ik);",
            "  }",
            "",
            "  // 3. 7 Mesosoma Chitin Tergites",
            "  for (let t = 0; t < 7; t++) {",
            "    const prev = t === 0 ? scorpion.carapace : scorpion.tergites[t-1];",
            "    updateTergitePhysics(scorpion.tergites[t], prev, 18);",
            "    renderChitinPlate(ctx, scorpion.tergites[t]);",
            "  }",
            "",
            "  // 4. 5 Metasoma Tail Segments & Stinger",
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
        "scientific": "Varanus komodoensis",
        "file_name": "Dragon.js",
        "accent": (255, 120, 40),
        "code_lines": [
            "// ─── KOMODO DRAGON IK ENGINE ───",
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
        "scientific": "Dendroaspis polylepis",
        "file_name": "Viper.js",
        "accent": (34, 197, 94),
        "code_lines": [
            "// ─── BLACK MAMBA SERPENTINE ENGINE ───",
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
        "scientific": "Canis lupus cyberneticus",
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
        "scientific": "Hierodula patellifera",
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
        "scientific": "Theraphosidae",
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
# PROCEDURAL SPECIES SYNTHESIZER (Generates Infinite Unique Animals)
# ─────────────────────────────────────────────────────────────────────────────
PREFIXES = ["NEON", "CYBER", "TITAN", "MECHA", "OBSIDIAN", "PLASMA", "BIOLUMINESCENT", "EMERALD", "CRIMSON", "LAVA", "VOID", "STEALTH", "PHANTOM"]
ANIMALS = ["SCORPION", "VIPER", "DRAGON", "MANTIS", "SPIDER", "CENTIPEDE", "WOLF", "KRAKEN", "EEL", "BEETLE", "CRAB", "CHAMELEON", "STINGRAY", "COBRA"]
ACCENTS = [
    (234, 179, 8),   # Amber Gold
    (0, 220, 255),   # Cyber Cyan
    (34, 197, 94),   # Toxic Emerald
    (239, 68, 68),   # Crimson Red
    (168, 85, 247),  # Void Purple
    (249, 115, 22),  # Lava Orange
    (236, 72, 153),  # Cyber Pink
    (56, 189, 248),  # Electric Blue
    (132, 204, 22),  # Acid Lime
    (250, 204, 21),  # Solar Yellow
]

def get_species_for_id(animal_id: int) -> dict:
    if animal_id < len(CREATURE_SPECIES):
        return CREATURE_SPECIES[animal_id]

    # Deterministic procedural generation for animal_id >= len(CREATURE_SPECIES)
    rng = random.Random(animal_id * 7919)
    prefix = rng.choice(PREFIXES)
    animal = rng.choice(ANIMALS)
    name = f"{prefix} {animal}"
    spec_id = name.lower().replace(" ", "_")
    accent = rng.choice(ACCENTS)
    clean_camel = "".join(w.capitalize() for w in name.split())
    file_name = f"{clean_camel}.js"

    code_lines = [
        f"// ─── {name} PROCEDURAL IK RIG ───",
        f"const creature = new ProceduralRig({{ name: '{name}', seed: {animal_id} }});",
        "",
        "const animateCreature = () => {",
        "  requestAnimationFrame(animateCreature);",
        "  const pointer = getPointerPosition();",
        "  updateSpineLag(creature.spine, pointer, 0.12);",
        "",
        "  // 1. Solve Multi-Joint Inverse Kinematics",
        "  creature.limbs.forEach((limb, idx) => {",
        "    const socket = getSpineAnchor(creature.spine, limb.vertebra, limb.side);",
        "    const step = computeGaitArc(limb.phase, frm);",
        "    const ik = solveJointIK(socket, step.target, limb.l1, limb.l2, limb.side);",
        "    renderArticulatedLimb(ctx, ik);",
        "  });",
        "",
        "  // 2. Render Articulated Segment Carapace",
        "  for (let s = 0; s < creature.segments; s++) {",
        "    renderSegmentChitin(ctx, creature.spine[s], s);",
        "  }",
        "  renderPredatorHead(ctx, creature.head);",
        "};"
    ]

    return {
        "id": spec_id,
        "name": name,
        "scientific": f"Proceduralis {animal.lower()}",
        "file_name": file_name,
        "accent": accent,
        "code_lines": code_lines,
        "yt_title": f"Realistic Interactive {name} Cursor in JS ✨ #Shorts #JavaScript",
        "yt_desc": f"✨ Realistic {name} with procedural Inverse Kinematics (IK) physics in JavaScript!\n\n#JavaScript #CreativeCoding #WebDev #Shorts"
    }

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
        target_x = self.cx + math.cos(sim_time * 0.7) * (self.rx * 0.9) + math.sin(sim_time * 1.4) * (self.rx * 0.25)
        target_y = self.cy + math.sin(sim_time * 0.9) * (self.ry * 0.85) + math.cos(sim_time * 1.8) * (self.ry * 0.20)

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

        prev_x, prev_y, prev_ang = self.x, self.y, self.angle
        for i, t_seg in enumerate(self.tergites):
            s_dist = 18 - i * 0.8
            p_dx = prev_x - t_seg["x"]
            p_dy = prev_y - t_seg["y"]
            t_seg["angle"] = math.atan2(p_dy, p_dx)
            t_seg["x"] = prev_x - math.cos(t_seg["angle"]) * s_dist
            t_seg["y"] = prev_y - math.sin(t_seg["angle"]) * s_dist
            prev_x, prev_y = t_seg["x"], t_seg["y"]

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

            if dist_ideal > 36 and leg["prog"] >= 1.0 and group_phase > 0.1:
                leg["prog"] = 0.0
                leg["start"] = [leg["cur"][0], leg["cur"][1]]
                leg["tgt"] = [
                    ideal_x + math.cos(self.angle) * 26,
                    ideal_y + math.sin(self.angle) * 26
                ]

            if leg["prog"] < 1.0:
                leg["prog"] += 0.14
                p = min(1.0, leg["prog"])
                ease_p = 0.5 - math.cos(p * math.pi) / 2
                leg["cur"][0] = leg["start"][0] + (leg["tgt"][0] - leg["start"][0]) * ease_p
                leg["cur"][1] = leg["start"][1] + (leg["tgt"][1] - leg["start"][1]) * ease_p


_SIM_CACHE = {}

def render_generative_frame(species: dict, frame_idx: int, total_frames: int) -> Image.Image:
    progress = frame_idx / total_frames
    sim_time = (frame_idx / FPS) * 1.05

    img = Image.new("RGBA", (WIDTH, HEIGHT), (11, 27, 38, 255))
    draw = ImageDraw.Draw(img)

    grad = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grad)
    g_draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(14, 35, 49, 255))
    g_draw.ellipse([WIDTH//2 - 500, HEIGHT//2 - 600, WIDTH//2 + 500, HEIGHT//2 + 600], fill=(22, 50, 70, 200))
    img = Image.alpha_composite(img, grad.filter(ImageFilter.GaussianBlur(80)))
    draw = ImageDraw.Draw(img)

    # 1. Top Header: ANIMAL NAME ONLY
    header_h = 135
    draw.rectangle([0, 0, WIDTH, header_h], fill=(15, 18, 22, 255))
    draw.line([(0, header_h), (WIDTH, header_h)], fill=(30, 36, 44), width=2)

    name_font = get_font(58, bold=True)
    draw.text((WIDTH // 2, 38), species["name"], font=name_font, fill=(255, 255, 255), anchor="mt")

    # 2. Upper Section: Framed Creature Display Window
    box_w, box_h = 920, 640
    box_x = (WIDTH - box_w) // 2
    box_y = 165

    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rectangle([box_x - 12, box_y - 12, box_x + box_w + 12, box_y + box_h + 12], fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(25)))
    draw = ImageDraw.Draw(img)

    draw.rectangle([box_x - 12, box_y - 12, box_x + box_w + 12, box_y + box_h + 12], fill=(235, 230, 220), outline=(190, 185, 175), width=2)
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=(239, 236, 228))

    cb_x = box_x + box_w // 2
    cb_y = box_y + box_h // 2
    rad_x = box_w * 0.33
    rad_y = box_h * 0.30

    sp_id = species.get("id", "emperor_scorpion")
    accent_color = species.get("accent", (234, 179, 8))

    if "scorpion" in sp_id or "spider" in sp_id or "mantis" in sp_id or "crab" in sp_id:
        sim_key = f"{sp_id}_{total_frames}"
        if frame_idx == 0 or sim_key not in _SIM_CACHE:
            _SIM_CACHE[sim_key] = ScorpionSimulator(cb_x, cb_y, rad_x, rad_y)
        
        sim = _SIM_CACHE[sim_key]
        sim.update(sim_time)

        cos_a = math.cos(sim.angle)
        sin_a = math.sin(sim.angle)
        perp_x = -sin_a
        perp_y =  cos_a

        # Legs
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

        # Tergites
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
            draw.line([(seg["x"] - s_cos * 6, seg["y"] - s_sin * 6), (seg["x"] + s_cos * 6, seg["y"] + s_sin * 6)], fill=(202, 138, 4), width=2)

        # Carapace
        c_front = (sim.x + cos_a * 34, sim.y + sin_a * 34)
        c_r1 = (sim.x + cos_a * 18 + perp_x * 28, sim.y + sin_a * 18 + perp_y * 28)
        c_r2 = (sim.x - cos_a * 16 + perp_x * 32, sim.y - sin_a * 16 + perp_y * 32)
        c_l2 = (sim.x - cos_a * 16 - perp_x * 32, sim.y - sin_a * 16 - perp_y * 32)
        c_l1 = (sim.x + cos_a * 18 - perp_x * 28, sim.y + sin_a * 18 - perp_y * 28)
        draw.polygon([c_front, c_r1, c_r2, c_l2, c_l1], fill=(12, 16, 24), outline=accent_color, width=2)

        eye_pos = (sim.x + cos_a * 14, sim.y + sin_a * 14)
        draw.ellipse([eye_pos[0]-3.5, eye_pos[1]-3.5, eye_pos[0]+3.5, eye_pos[1]+3.5], fill=(254, 240, 138))

        # Pincers
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

        # Tail
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

    else:
        # Generic Serpentine / Dragon / Quadruped / Aquatic Kinematics
        NUM_SEGS = 30
        spine = []
        for s_idx in range(NUM_SEGS):
            tau = sim_time * 0.8 - s_idx * 0.024
            sx = cb_x + math.cos(1.8 * tau) * (rad_x * 0.9) + math.sin(2.4 * tau) * (rad_x * 0.25)
            sy = cb_y + math.sin(2.2 * tau) * (rad_y * 0.85) + math.cos(3.1 * tau) * (rad_y * 0.20)
            spine.append((sx, sy))

        # 4 Articulated Legs
        leg_anchors = [
            {"spine_i": 5, "side": -1, "l1": 38, "l2": 42, "phase": 0.0},
            {"spine_i": 5, "side":  1, "l1": 38, "l2": 42, "phase": math.pi},
            {"spine_i": 19, "side": -1, "l1": 42, "l2": 46, "phase": math.pi},
            {"spine_i": 19, "side":  1, "l1": 42, "l2": 46, "phase": 0.0},
        ]
        for leg in leg_anchors:
            s_pt = spine[leg["spine_i"]]
            s_prev = spine[leg["spine_i"] - 1]
            b_ang = math.atan2(s_pt[1] - s_prev[1], s_pt[0] - s_prev[0])
            hip_ang = b_ang + (math.pi / 2) * leg["side"]
            hip = (s_pt[0] + math.cos(hip_ang) * 18, s_pt[1] + math.sin(hip_ang) * 18)

            gait_t = (sim_time * 6.0 + leg["phase"]) % (2 * math.pi)
            is_swing = math.sin(gait_t) > 0.0
            step_lead = math.cos(gait_t) * 22 if is_swing else -10
            step_lift = math.sin(gait_t) * 12 if is_swing else 0

            foot_ang = b_ang + leg["side"] * (math.pi * 0.45)
            foot_x = hip[0] + math.cos(foot_ang) * 60 + math.cos(b_ang) * step_lead
            foot_y = hip[1] + math.sin(foot_ang) * 60 + math.sin(b_ang) * step_lead - step_lift

            hp, kp, fp = solve_ik_2joint(hip, (foot_x, foot_y), leg["l1"], leg["l2"], leg["side"])
            draw.line([hp, kp], fill=(20, 26, 36), width=8)
            draw.line([kp, fp], fill=(12, 16, 22), width=6)
            draw.ellipse([kp[0]-4, kp[1]-4, kp[0]+4, kp[1]+4], fill=accent_color)
            draw.ellipse([fp[0]-4, fp[1]-4, fp[0]+4, fp[1]+4], fill=(10, 12, 16))

        # Main Spine Scales
        for s_idx in range(len(spine) - 1, 0, -1):
            p1 = spine[s_idx]
            p0 = spine[s_idx - 1]
            norm = s_idx / NUM_SEGS
            v_width = max(4, int(26 * (1.0 - norm * 0.75)))
            draw.line([p0, p1], fill=(16, 20, 26), width=v_width)
            draw.ellipse([p1[0]-v_width//2, p1[1]-v_width//2, p1[0]+v_width//2, p1[1]+v_width//2], fill=(26, 32, 40), outline=accent_color, width=1)

        # Head
        hp = spine[0]
        hp_prev = spine[1]
        hang = math.atan2(hp[1] - hp_prev[1], hp[0] - hp_prev[0])
        snout = (hp[0] + math.cos(hang) * 42, hp[1] + math.sin(hang) * 42)
        j1 = (hp[0] - math.cos(hang) * 16 + math.cos(hang + math.pi/2) * 24, hp[1] - math.sin(hang) * 16 + math.sin(hang + math.pi/2) * 24)
        j2 = (hp[0] - math.cos(hang) * 16 - math.cos(hang + math.pi/2) * 24, hp[1] - math.sin(hang) * 16 - math.sin(hang + math.pi/2) * 24)
        crown = (hp[0] - math.cos(hang) * 32, hp[1] - math.sin(hang) * 32)
        draw.polygon([snout, j1, crown, j2], fill=(12, 15, 20), outline=accent_color, width=2)
        eye_l = (hp[0] + math.cos(hang) * 8 + math.cos(hang + math.pi/2) * 12, hp[1] + math.sin(hang) * 8 + math.sin(hang + math.pi/2) * 12)
        eye_r = (hp[0] + math.cos(hang) * 8 - math.cos(hang + math.pi/2) * 12, hp[1] + math.sin(hang) * 8 - math.sin(hang + math.pi/2) * 12)
        draw.ellipse([eye_l[0]-3, eye_l[0]-3, eye_l[0]+3, eye_l[0]+3], fill=accent_color)
        draw.ellipse([eye_r[0]-3, eye_r[0]-3, eye_r[0]+3, eye_r[0]+3], fill=accent_color)

    # ─────────────────────────────────────────────────────────────
    # LOWER SECTION: macOS DARK CODE WINDOW (LARGER TYPOGRAPHY)
    # ─────────────────────────────────────────────────────────────
    card_w, card_h = 920, 980
    card_x = (WIDTH - card_w) // 2
    card_y = 840

    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=22, fill=(12, 18, 25), outline=(28, 38, 50), width=2)

    title_h = 58
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + title_h], radius=22, fill=(8, 13, 19))
    draw.rectangle([card_x, card_y + 30, card_x + card_w, card_y + title_h], fill=(8, 13, 19))

    draw.ellipse([card_x + 28, card_y + 23, card_x + 42, card_y + 37], fill=(255, 95, 86))
    draw.ellipse([card_x + 52, card_y + 23, card_x + 66, card_y + 37], fill=(255, 189, 46))
    draw.ellipse([card_x + 76, card_y + 23, card_x + 90, card_y + 37], fill=(39, 201, 63))

    draw.rounded_rectangle([card_x + 130, card_y + 13, card_x + 158, card_y + 44], radius=4, fill=(247, 223, 30))
    draw.text((card_x + 135, card_y + 17), "JS", font=get_font(16, bold=True), fill=(20, 20, 20))
    draw.text((card_x + 170, card_y + 18), species["file_name"], font=get_font(22, bold=True), fill=(160, 175, 195))

    all_lines = species["code_lines"]
    total_lines = len(all_lines)
    
    line_h = 44
    code_font = get_font(26, mono=True)
    line_num_font = get_font(22, mono=True)
    
    visible_lines = int((card_h - title_h - 40) / line_h)
    max_scroll_lines = max(0, total_lines - visible_lines)
    scroll_factor = 0.5 - math.cos(progress * math.pi) / 2
    curr_scroll = scroll_factor * max_scroll_lines

    start_line_idx = int(curr_scroll)
    line_pixel_offset = (curr_scroll - start_line_idx) * line_h

    code_box_top = card_y + title_h + 18
    code_box_bottom = card_y + card_h - 22

    for idx in range(visible_lines + 2):
        actual_line_idx = start_line_idx + idx
        if actual_line_idx >= total_lines:
            break
        
        line_text = all_lines[actual_line_idx]
        y_pos = code_box_top + (idx * line_h) - int(line_pixel_offset)

        if y_pos < code_box_top - 12 or y_pos > code_box_bottom:
            continue

        draw.text((card_x + 36, y_pos), f"{actual_line_idx + 1:2d}", font=line_num_font, fill=(70, 85, 105))

        indent_x = card_x + 95
        stripped = line_text.strip()
        if stripped.startswith("//"):
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(100, 116, 139))
        elif any(k in line_text for k in ["const ", "let ", "for ", "new ", "return "]):
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(224, 108, 117))
        elif any(f in line_text for f in ["Math.", "solve", "render", "update", "compute", "curl"]):
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(97, 175, 239))
        else:
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(226, 232, 240))

    # Bottom Progress Bar
    bar_w = 920
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 1855
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 12], radius=6, fill=(35, 46, 62))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + 12], radius=6, fill=accent_color)

    return img.convert("RGB")
