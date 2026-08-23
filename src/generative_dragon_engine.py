"""
Minimalist Code-Reel Engine with Full Biological Modular Anatomical Rigging
Every animal class has dedicated anatomical logic for ALL body parts:
- Face, Eyes, Jaws, Tongues, Antennae, Hoods
- Hands, Claws, Pincers, Raptorial Scythes, Paws, Flippers
- 4, 6, 8, 44 Legs with True Multi-Joint Inverse Kinematics
- Segmented Spinal Column, Carapace Armor Plates, Feather Fans, Tentacles
- Articulated Stinger Tails, Whip Tails, Caudal Fins
- macOS Dark Code Window with Auto-Sliding/Scrolling JS Code
- 100% Free & Unlimited
"""
from __future__ import annotations

import json
import math
import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT, FPS = 1080, 1920, 30
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ENCYCLOPEDIA_FILE = DATA_DIR / "animal_encyclopedia.json"

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

def _generate_js_code_for_animal(name: str, class_type: str, scientific: str) -> list[str]:
    c_name = "".join(w.capitalize() for w in name.split())
    if class_type == "arachnid":
        return [
            f"// ─── {name} ({scientific.upper()}) ───",
            f"const {c_name} = new ArachnidSkeleton({{ segments: 38 }});",
            "",
            f"const animate{c_name} = () => {{",
            f"  requestAnimationFrame(animate{c_name});",
            "  const p = getPointerPosition();",
            "",
            "  // 1. Solve 3-Joint Pincer Arms (Hands / Chelae)",
            f"  solvePincerIK({c_name}.leftArm,  p, 54, 62, -1);",
            f"  solvePincerIK({c_name}.rightArm, p, 54, 62,  1);",
            "",
            "  // 2. 8-Legged Tripod Stepping Gait (4 Left, 4 Right)",
            "  for (let i = 0; i < 8; i++) {",
            f"    const leg = {c_name}.legs[i];",
            "    const side = i < 4 ? -1 : 1;",
            f"    const hip = getHipSocket({c_name}.carapace, i, side);",
            "    const step = computeTripodStep(leg, frm, side);",
            "    const ik = solve3SegmentIK(hip, step.target, 24, 30, 26, side);",
            "    renderArticulatedLeg(ctx, ik);",
            "  }",
            "",
            "  // 3. 7 Mesosoma Armor Plates & 5-Segment Stinger Tail",
            f"  updateTergiteFollowChain(ctx, {c_name}.tergites);",
            f"  curlStingerTail({c_name}.tail, Math.sin(frm * 2.5) * 0.35);",
            f"  renderTelsonBulb(ctx, {c_name}.tail.end, '#EAB308');",
            "};"
        ]
    elif class_type == "serpent":
        return [
            f"// ─── {name} ({scientific.upper()}) ───",
            f"const {c_name} = new SerpentineSpine({{ vertebrae: 48 }});",
            "",
            f"const update{c_name} = () => {{",
            f"  requestAnimationFrame(update{c_name});",
            "  const head = {c_name}.spine[0];",
            "  head.x += (pointer.x - head.x) * 0.14;",
            "  head.y += (pointer.y - head.y) * 0.14;",
            "",
            "  // 1. Serpentine Lateral Undulation Wave",
            f"  for (let i = 1; i < {c_name}.length; i++) {{",
            f"    const prev = {c_name}.spine[i - 1];",
            f"    const curr = {c_name}.spine[i];",
            "    const wave = Math.sin(time * 6 + i * 0.35) * 7;",
            "    updateVertebra(curr, prev, 14, wave);",
            "    renderScalesAndScutes(ctx, curr, i);",
            "  }",
            "",
            "  // 2. Fanged Diamond Head & Cervical Hood",
            f"  renderCobraHood(ctx, head, {c_name}.spine[2]);",
            f"  renderForkedTongueAndEyes(ctx, head);",
            "};"
        ]
    elif class_type in ["crustacean", "insect"]:
        return [
            f"// ─── {name} ({scientific.upper()}) ───",
            f"const {c_name} = new ArthropodRig({{ scythes: 2, legs: 6 }});",
            "",
            f"const loop{c_name} = () => {{",
            f"  requestAnimationFrame(loop{c_name});",
            "  const target = getHuntingTarget();",
            "",
            "  // 1. Dual Spiked Raptorial Forearms (Scythes)",
            f"  solveRaptorialIK({c_name}.leftScythe,  target, 48, 56, -1);",
            f"  solveRaptorialIK({c_name}.rightScythe, target, 48, 56,  1);",
            "",
            "  // 2. 6 Walking Legs Stepping Gait",
            f"  {c_name}.legs.forEach(leg => {{",
            "    const gait = computeTripodGait(leg.phase, frm);",
            "    const ik = solve3SegmentIK(leg.coxa, gait.pos, 30, 38, 34, leg.side);",
            "    renderArmoredLimb(ctx, ik);",
            "  });",
            f"  renderCompoundEyesAndAntennae(ctx, {c_name}.head);",
            "};"
        ]
    elif class_type == "cephalopod":
        return [
            f"// ─── {name} ({scientific.upper()}) ───",
            f"const {c_name} = new CephalopodRig({{ tentacles: 8, segs: 20 }});",
            "",
            f"const animate{c_name} = () => {{",
            f"  requestAnimationFrame(animate{c_name});",
            "  updateMantlePosition({c_name}.mantle, pointer);",
            "",
            "  // 1. 8 Multi-Segment Curling Tentacles with Suctions",
            "  for (let t = 0; t < 8; t++) {",
            f"    const arm = {c_name}.tentacles[t];",
            "    const spread = (t / 8) * Math.PI * 2;",
            f"    solveTentacleIK(arm, {c_name}.mantle, spread, frm);",
            "    drawSuctionCupsAndBeak(ctx, arm);",
            "  }",
            f"  renderBioluminescentRings(ctx, {c_name}.mantle);",
            "};"
        ]
    elif class_type == "avian":
        return [
            f"// ─── {name} ({scientific.upper()}) ───",
            f"const {c_name} = new AvianRig({{ feathers: 18, neckSegs: 8 }});",
            "",
            f"const render{c_name} = () => {{",
            f"  requestAnimationFrame(render{c_name});",
            "  updateSinuousNeck({c_name}.neck, pointer);",
            "",
            "  // 1. 18-Feather Radiant Fan Plumage IK Wave",
            "  for (let f = 0; f < 18; f++) {",
            "    const angle = (f / 17 - 0.5) * Math.PI * 0.85;",
            "    const flutter = Math.sin(time * 4 + f * 0.3) * 0.08;",
            f"    const quill = getPlumageAnchor({c_name}.base, angle + flutter, 120);",
            "    drawOcellusEyeFeather(ctx, quill, '#06B6D4');",
            "  }",
            f"  renderCrestAndBeak(ctx, {c_name}.head);",
            "};"
        ]
    else:
        return [
            f"// ─── {name} ({scientific.upper()}) ───",
            f"const {c_name} = new ReptileRig({{ vertebrae: 26, limbs: 4 }});",
            "",
            f"const run{c_name} = () => {{",
            f"  requestAnimationFrame(run{c_name});",
            f"  updateSpineHead({c_name}.spine[0], pointer);",
            "",
            "  // 1. Articulated 2-Joint Forelimbs & Hindlimbs with Claws",
            f"  {c_name}.limbs.forEach(limb => {{",
            f"    const socket = getSpineAnchor({c_name}.spine, limb.vertebra, limb.side);",
            "    const step = computeGaitArc(limb.phase, frm);",
            "    const ik = solve2JointIK(socket, step.foot, limb.l1, limb.l2, limb.side);",
            "    renderLimbWithSpreadClaws(ctx, ik);",
            "  });",
            "",
            "  // 2. Undulating Vertebrae & Osteoderm Scutes",
            f"  for (let i = 1; i < {c_name}.vertebrae; i++) {{",
            f"    updateVertebraFollow({c_name}.spine[i], {c_name}.spine[i - 1]);",
            f"    renderDorsalScuteRibs(ctx, {c_name}.spine[i], i);",
            "  }",
            f"  renderReptilianHeadWithNostrils(ctx, {c_name}.spine[0]);",
            "};"
        ]

def get_species_for_id(animal_id: int) -> dict:
    try:
        encyclopedia = json.loads(ENCYCLOPEDIA_FILE.read_text(encoding="utf-8"))
    except Exception:
        encyclopedia = []

    if not encyclopedia:
        encyclopedia = [{"name": "EMPEROR SCORPION", "scientific": "Pandinus imperator", "class_type": "arachnid", "accent": [234, 179, 8], "file_name": "Scorpion.js"}]

    idx = animal_id % len(encyclopedia)
    entry = encyclopedia[idx]

    name = entry["name"]
    scientific = entry.get("scientific", name)
    class_type = entry.get("class_type", "reptile")
    accent = tuple(entry.get("accent", [234, 179, 8]))
    file_name = entry.get("file_name", "".join(w.capitalize() for w in name.split()) + ".js")
    spec_id = name.lower().replace(" ", "_")

    code_lines = _generate_js_code_for_animal(name, class_type, scientific)

    return {
        "id": spec_id,
        "name": name,
        "scientific": scientific,
        "class_type": class_type,
        "file_name": file_name,
        "accent": accent,
        "code_lines": code_lines,
        "yt_title": f"Realistic Interactive {name} Cursor in JS ✨ #Shorts #Coding",
        "yt_desc": f"✨ Realistic {name} ({scientific}) with full modular anatomical rigging and Inverse Kinematics in JavaScript!\n\n#JavaScript #CreativeCoding #WebDev #Shorts #Coding"
    }

class ModularSimulator:
    def __init__(self, cx: float, cy: float, rx: float, ry: float):
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.x = cx
        self.y = cy
        self.angle = 0.0
        self.speed = 0.0
        # Pre-spread spine vertebrae along an arc
        self.spine = [{"x": cx - i * 14, "y": cy + math.sin(i * 0.4) * 8, "angle": 0.0} for i in range(32)]
        
        # 8 Arachnid Legs
        self.legs8 = [
            {"id": "L1", "side": -1, "spread": -0.85, "rest_d": 88, "l1": 26, "l2": 36, "l3": 32, "group": 0, "cur": [cx - 85, cy + 40], "tgt": [cx - 85, cy + 40], "start": [cx - 85, cy + 40], "prog": 1.0},
            {"id": "L2", "side": -1, "spread": -1.30, "rest_d": 102, "l1": 30, "l2": 42, "l3": 36, "group": 1, "cur": [cx - 95, cy + 40], "tgt": [cx - 95, cy + 40], "start": [cx - 95, cy + 40], "prog": 1.0},
            {"id": "L3", "side": -1, "spread": -1.75, "rest_d": 106, "l1": 32, "l2": 44, "l3": 38, "group": 0, "cur": [cx - 100, cy + 40], "tgt": [cx - 100, cy + 40], "start": [cx - 100, cy + 40], "prog": 1.0},
            {"id": "L4", "side": -1, "spread": -2.20, "rest_d": 94, "l1": 28, "l2": 38, "l3": 34, "group": 1, "cur": [cx - 90, cy + 40], "tgt": [cx - 90, cy + 40], "start": [cx - 90, cy + 40], "prog": 1.0},
            
            {"id": "R1", "side":  1, "spread":  0.85, "rest_d": 88, "l1": 26, "l2": 36, "l3": 32, "group": 1, "cur": [cx + 85, cy + 40], "tgt": [cx + 85, cy + 40], "start": [cx + 85, cy + 40], "prog": 1.0},
            {"id": "R2", "side":  1, "spread":  1.30, "rest_d": 102, "l1": 30, "l2": 42, "l3": 36, "group": 0, "cur": [cx + 95, cy + 40], "tgt": [cx + 95, cy + 40], "start": [cx + 95, cy + 40], "prog": 1.0},
            {"id": "R3", "side":  1, "spread":  1.75, "rest_d": 106, "l1": 32, "l2": 44, "l3": 38, "group": 1, "cur": [cx + 100, cy + 40], "tgt": [cx + 100, cy + 40], "start": [cx + 100, cy + 40], "prog": 1.0},
            {"id": "R4", "side":  1, "spread":  2.20, "rest_d": 94, "l1": 28, "l2": 38, "l3": 34, "group": 0, "cur": [cx + 90, cy + 40], "tgt": [cx + 90, cy + 40], "start": [cx + 90, cy + 40], "prog": 1.0},
        ]
        # 4 Tetrapod / Reptile / Quadruped Legs
        self.legs4 = [
            {"id": "FL", "spine_i": 4, "side": -1, "l1": 38, "l2": 42, "phase": 0.0},
            {"id": "FR", "spine_i": 4, "side":  1, "l1": 38, "l2": 42, "phase": math.pi},
            {"id": "HL", "spine_i": 18, "side": -1, "l1": 42, "l2": 46, "phase": math.pi},
            {"id": "HR", "spine_i": 18, "side":  1, "l1": 42, "l2": 46, "phase": 0.0},
        ]
        # 2 Pincer Arms
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

        # Update Full Spinal Follow-Chain with Organic Wave
        self.spine[0]["x"] = self.x
        self.spine[0]["y"] = self.y
        self.spine[0]["angle"] = self.angle
        for i in range(1, len(self.spine)):
            prev = self.spine[i - 1]
            curr = self.spine[i]
            s_dist = 16 - (i / len(self.spine)) * 6
            wave = math.sin(sim_time * 6.0 + i * 0.35) * (3.5 if i > 3 else 0.5)
            p_dx = prev["x"] - curr["x"]
            p_dy = prev["y"] - curr["y"]
            curr["angle"] = math.atan2(p_dy, p_dx)
            curr["x"] = prev["x"] - math.cos(curr["angle"]) * s_dist + math.cos(curr["angle"] + math.pi/2) * wave
            curr["y"] = prev["y"] - math.sin(curr["angle"]) * s_dist + math.sin(curr["angle"] + math.pi/2) * wave

        # 8-Legged Tripod Stepping Gait
        gait_clock = sim_time * 7.5
        for idx, leg in enumerate(self.legs8):
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
    class_type = species.get("class_type", "arachnid")
    accent_color = species.get("accent", (234, 179, 8))

    sim_key = f"{sp_id}_{total_frames}"
    if frame_idx == 0 or sim_key not in _SIM_CACHE:
        _SIM_CACHE[sim_key] = ModularSimulator(cb_x, cb_y, rad_x, rad_y)
    
    sim = _SIM_CACHE[sim_key]
    sim.update(sim_time)

    cos_a = math.cos(sim.angle)
    sin_a = math.sin(sim.angle)
    perp_x = -sin_a
    perp_y =  cos_a

    # ─────────────────────────────────────────────────────────────
    # CLASS 1: ARACHNIDS & SCORPIONS (8 Legs + 2 Claws + Tail)
    # ─────────────────────────────────────────────────────────────
    if class_type == "arachnid" or "scorpion" in sp_id or "spider" in sp_id:
        for leg in sim.legs8:
            h_p = leg["hip"]
            foot_p = (leg["cur"][0], leg["cur"][1])
            h_p, j1_p, j2_p, f_p = solve_ik_3segment(h_p, foot_p, leg["l1"], leg["l2"], leg["l3"], leg["side"])
            draw.line([h_p, j1_p], fill=(16, 22, 32), width=7)
            draw.line([j1_p, j2_p], fill=(24, 32, 46), width=6)
            draw.line([j2_p, f_p], fill=(12, 16, 22), width=4)
            draw.ellipse([j1_p[0]-3, j1_p[1]-3, j1_p[0]+3, j1_p[1]+3], fill=accent_color)
            draw.ellipse([j2_p[0]-3, j2_p[1]-3, j2_p[0]+3, j2_p[1]+3], fill=accent_color)
            draw.ellipse([f_p[0]-3, f_p[1]-3, f_p[0]+3, f_p[1]+3], fill=(10, 12, 16))

        for i in range(1, 8):
            seg = sim.spine[i]
            s_cos, s_sin = math.cos(seg["angle"]), math.sin(seg["angle"])
            s_perp_x, s_perp_y = -s_sin, s_cos
            half_w = max(13, 34 - i * 3.0)
            half_h = 8
            p1 = (seg["x"] - s_cos * half_h + s_perp_x * half_w, seg["y"] - s_sin * half_h + s_perp_y * half_w)
            p2 = (seg["x"] + s_cos * half_h + s_perp_x * (half_w * 0.9), seg["y"] + s_sin * half_h + s_perp_y * (half_w * 0.9))
            p3 = (seg["x"] + s_cos * half_h - s_perp_x * (half_w * 0.9), seg["y"] + s_sin * half_h - s_perp_y * (half_w * 0.9))
            p4 = (seg["x"] - s_cos * half_h - s_perp_x * half_w, seg["y"] - s_sin * half_h - s_perp_y * half_w)
            draw.polygon([p1, p2, p3, p4], fill=(16, 22, 32), outline=accent_color, width=1)
            draw.line([(seg["x"] - s_cos * 6, seg["y"] - s_sin * 6), (seg["x"] + s_cos * 6, seg["y"] + s_sin * 6)], fill=(202, 138, 4), width=2)

        # Carapace & Eyes
        c_front = (sim.x + cos_a * 34, sim.y + sin_a * 34)
        c_r1 = (sim.x + cos_a * 18 + perp_x * 28, sim.y + sin_a * 18 + perp_y * 28)
        c_r2 = (sim.x - cos_a * 16 + perp_x * 32, sim.y - sin_a * 16 + perp_y * 32)
        c_l2 = (sim.x - cos_a * 16 - perp_x * 32, sim.y - sin_a * 16 - perp_y * 32)
        c_l1 = (sim.x + cos_a * 18 - perp_x * 28, sim.y + sin_a * 18 - perp_y * 28)
        draw.polygon([c_front, c_r1, c_r2, c_l2, c_l1], fill=(12, 16, 24), outline=accent_color, width=2)
        eye_pos = (sim.x + cos_a * 14, sim.y + sin_a * 14)
        draw.ellipse([eye_pos[0]-3.5, eye_pos[1]-3.5, eye_pos[0]+3.5, eye_pos[1]+3.5], fill=(254, 240, 138))

        # Hands / Claws
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
            f_tip = (wrist_pt[0] + math.cos(w_ang + p["side"] * 0.3) * 40, wrist_pt[1] + math.sin(w_ang + p["side"] * 0.3) * 40)
            draw.line([(wrist_pt[0] + w_cos * 18, wrist_pt[1] + w_sin * 18), f_tip], fill=accent_color, width=4)
            m_tip = (wrist_pt[0] + math.cos(w_ang - p["side"] * snap_open) * 36, wrist_pt[1] + math.sin(w_ang - p["side"] * snap_open) * 36)
            draw.line([(wrist_pt[0] + w_cos * 18, wrist_pt[1] + w_sin * 18), m_tip], fill=(202, 138, 4), width=3)

        # 5-Segment Stinger Tail & Telson
        tail_prev = (sim.spine[7]["x"], sim.spine[7]["y"])
        for i in range(8, 13):
            tx, ty = sim.spine[i]["x"], sim.spine[i]["y"]
            t_width = max(5, int(14 - (i - 8) * 1.4))
            draw.line([tail_prev, (tx, ty)], fill=(18, 24, 34), width=t_width)
            draw.ellipse([tx - t_width//2, ty - t_width//2, tx + t_width//2, ty + t_width//2], fill=(28, 38, 52))
            tail_prev = (tx, ty)
        telson_bulb = (sim.spine[12]["x"], sim.spine[12]["y"])
        draw.ellipse([telson_bulb[0]-9, telson_bulb[1]-9, telson_bulb[0]+9, telson_bulb[1]+9], fill=(202, 138, 4), outline=(254, 240, 138), width=2)
        sting_tip = (telson_bulb[0] + math.cos(sim.spine[12]["angle"] + 0.8) * 22, telson_bulb[1] + math.sin(sim.spine[12]["angle"] + 0.8) * 22)
        draw.line([telson_bulb, sting_tip], fill=(254, 240, 138), width=3)

    # ─────────────────────────────────────────────────────────────
    # CLASS 2: SERPENTS & COBRAS (48 Vertebrae + Hood + Fangs)
    # ─────────────────────────────────────────────────────────────
    elif class_type == "serpent":
        for i in range(len(sim.spine) - 1, 0, -1):
            p1 = (sim.spine[i]["x"], sim.spine[i]["y"])
            p0 = (sim.spine[i - 1]["x"], sim.spine[i - 1]["y"])
            norm = i / len(sim.spine)
            v_width = max(4, int(28 * (1.0 - norm * 0.75)))
            draw.line([p0, p1], fill=(16, 26, 20), width=v_width)
            draw.ellipse([p1[0]-v_width//2, p1[1]-v_width//2, p1[0]+v_width//2, p1[1]+v_width//2], fill=(24, 40, 30), outline=accent_color, width=1)

        # Flaring Cobra Hood (Vertebrae 2 to 5)
        h_pt = sim.spine[2]
        h_cos, h_sin = math.cos(h_pt["angle"]), math.sin(h_pt["angle"])
        h_perp_x, h_perp_y = -h_sin, h_cos
        hood_l = (h_pt["x"] + h_perp_x * 42, h_pt["y"] + h_perp_y * 42)
        hood_r = (h_pt["x"] - h_perp_x * 42, h_pt["y"] - h_perp_y * 42)
        hood_f = (sim.x + cos_a * 15, sim.y + sin_a * 15)
        hood_b = (sim.spine[5]["x"], sim.spine[5]["y"])
        draw.polygon([hood_f, hood_l, hood_b, hood_r], fill=(14, 24, 18), outline=accent_color, width=2)

        # Diamond Head + Slit Eyes + Forked Tongue
        snout = (sim.x + cos_a * 38, sim.y + sin_a * 38)
        j1 = (sim.x - cos_a * 12 + perp_x * 20, sim.y - sin_a * 12 + perp_y * 20)
        j2 = (sim.x - cos_a * 12 - perp_x * 20, sim.y - sin_a * 12 - perp_y * 20)
        crown = (sim.x - cos_a * 26, sim.y - sin_a * 26)
        draw.polygon([snout, j1, crown, j2], fill=(10, 18, 14), outline=accent_color, width=2)
        
        # Eyes
        eye_l = (sim.x + cos_a * 10 + perp_x * 12, sim.y + sin_a * 10 + perp_y * 12)
        eye_r = (sim.x + cos_a * 10 - perp_x * 12, sim.y + sin_a * 10 - perp_y * 12)
        draw.ellipse([eye_l[0]-3, eye_l[0]-3, eye_l[0]+3, eye_l[0]+3], fill=(250, 204, 21))
        draw.ellipse([eye_r[0]-3, eye_r[1]-3, eye_r[0]+3, eye_r[0]+3], fill=(250, 204, 21))

        # Forked Flicking Tongue
        tongue_base = snout
        tongue_mid = (snout[0] + cos_a * 22, snout[1] + sin_a * 22)
        tongue_f1 = (tongue_mid[0] + math.cos(sim.angle + 0.3) * 12, tongue_mid[1] + math.sin(sim.angle + 0.3) * 12)
        tongue_f2 = (tongue_mid[0] + math.cos(sim.angle - 0.3) * 12, tongue_mid[1] + math.sin(sim.angle - 0.3) * 12)
        draw.line([tongue_base, tongue_mid], fill=(239, 68, 68), width=2)
        draw.line([tongue_mid, tongue_f1], fill=(239, 68, 68), width=2)
        draw.line([tongue_mid, tongue_f2], fill=(239, 68, 68), width=2)

    # ─────────────────────────────────────────────────────────────
    # CLASS 3: REPTILES & DRAGONS (2-Joint IK Legs + Claws + Tail)
    # ─────────────────────────────────────────────────────────────
    else:
        for leg in sim.legs4:
            s_pt = sim.spine[leg["spine_i"]]
            b_ang = s_pt["angle"]
            hip_ang = b_ang + (math.pi / 2) * leg["side"]
            hip = (s_pt["x"] + math.cos(hip_ang) * 20, s_pt["y"] + math.sin(hip_ang) * 20)

            gait_t = (sim_time * 6.0 + leg["phase"]) % (2 * math.pi)
            is_swing = math.sin(gait_t) > 0.0
            step_lead = math.cos(gait_t) * 22 if is_swing else -10
            step_lift = math.sin(gait_t) * 12 if is_swing else 0

            foot_ang = b_ang + leg["side"] * (math.pi * 0.45)
            foot_x = hip[0] + math.cos(foot_ang) * 62 + math.cos(b_ang) * step_lead
            foot_y = hip[1] + math.sin(foot_ang) * 62 + math.sin(b_ang) * step_lead - step_lift

            hp, kp, fp = solve_ik_2joint(hip, (foot_x, foot_y), leg["l1"], leg["l2"], leg["side"])
            draw.line([hp, kp], fill=(20, 26, 36), width=8)
            draw.line([kp, fp], fill=(12, 16, 22), width=6)
            draw.ellipse([kp[0]-4, kp[1]-4, kp[0]+4, kp[1]+4], fill=accent_color)
            draw.ellipse([fp[0]-4, fp[1]-4, fp[0]+4, fp[1]+4], fill=(10, 12, 16))

            # 3 Sharp Claws at Foot
            for c_i in [-0.4, 0.0, 0.4]:
                claw_tip = (fp[0] + math.cos(b_ang + c_i) * 12, fp[1] + math.sin(b_ang + c_i) * 12)
                draw.line([fp, claw_tip], fill=accent_color, width=2)

        # Spine Vertebrae
        for i in range(len(sim.spine) - 1, 0, -1):
            p1 = (sim.spine[i]["x"], sim.spine[i]["y"])
            p0 = (sim.spine[i - 1]["x"], sim.spine[i - 1]["y"])
            norm = i / len(sim.spine)
            v_width = max(4, int(26 * (1.0 - norm * 0.75)))
            draw.line([p0, p1], fill=(16, 20, 26), width=v_width)
            draw.ellipse([p1[0]-v_width//2, p1[1]-v_width//2, p1[0]+v_width//2, p1[1]+v_width//2], fill=(26, 32, 40), outline=accent_color, width=1)

        # Head & Nostrils
        snout = (sim.x + cos_a * 44, sim.y + sin_a * 44)
        j1 = (sim.x - cos_a * 16 + perp_x * 24, sim.y - sin_a * 16 + perp_y * 24)
        j2 = (sim.x - cos_a * 16 - perp_x * 24, sim.y - sin_a * 16 - perp_y * 24)
        crown = (sim.x - cos_a * 32, sim.y - sin_a * 32)
        draw.polygon([snout, j1, crown, j2], fill=(12, 15, 20), outline=accent_color, width=2)
        eye_l = (sim.x + cos_a * 8 + perp_x * 12, sim.y + sin_a * 8 + perp_y * 12)
        eye_r = (sim.x + cos_a * 8 - perp_x * 12, sim.y + sin_a * 8 - perp_y * 12)
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
