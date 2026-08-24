"""
Ultra-Realistic Organic Biological Creature Engine (HTML/SVG & Code-Reel Generator)
Features:
- Pure IK Spine Kinematics with Zero Angle Inversion / Polygon Spikes
- Full support for all animal species (Quadruped, Arachnid, Serpent, Reptile, Crustacean, Aquatic)
- Large Prominent Animal Scaling
- Large 34px Bold Monospace Code Font with 56px Line Spacing (Mobile Optimized)
- Calm, Smooth, Natural Trotting/Crawling Speed (0.4x Real-Life)
- Bundled Cross-Platform TrueType Fonts
- 100% Free & Unlimited
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT, FPS = 1080, 1920, 30
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
FONTS_DIR = ROOT_DIR / "assets" / "fonts"
ENCYCLOPEDIA_FILE = DATA_DIR / "animal_encyclopedia.json"

def get_font(size: int, bold: bool = False, serif: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if mono:
        candidates = [
            str(FONTS_DIR / "DejaVuSansMono-Bold.ttf"),
            str(FONTS_DIR / "CodeMono.ttf"),
            str(FONTS_DIR / "Montserrat-Bold.ttf" if bold else FONTS_DIR / "Montserrat-Regular.ttf"),
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/system/fonts/DroidSansMono.ttf",
        ]
    elif serif:
        candidates = [
            str(FONTS_DIR / "Montserrat-Bold.ttf"),
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/system/fonts/NotoSerif-Bold.ttf",
        ]
    else:
        candidates = [
            str(FONTS_DIR / "Montserrat-Bold.ttf" if bold else FONTS_DIR / "Montserrat-Regular.ttf"),
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/system/fonts/Roboto-Bold.ttf" if bold else "/system/fonts/Roboto-Regular.ttf",
            "/system/fonts/DroidSans.ttf"
        ]

    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def solve_forelimb_ik(shoulder: tuple[float, float], paw: tuple[float, float], l1: float, l2: float, side: float):
    dx = paw[0] - shoulder[0]
    dy = paw[1] - shoulder[1]
    dist = math.hypot(dx, dy)
    clamped = min(dist, l1 + l2 - 0.001)
    base = math.atan2(dy, dx)
    cos_a = (l1 * l1 + clamped * clamped - l2 * l2) / (2 * l1 * clamped)
    ang = base - math.acos(max(-1.0, min(1.0, cos_a))) * side * 0.92
    elbow = (shoulder[0] + math.cos(ang) * l1, shoulder[1] + math.sin(ang) * l1)
    return shoulder, elbow, paw

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

def _draw_highlighted_js_line(draw: ImageDraw.ImageDraw, x: int, y: int, line: str, font: ImageFont.FreeTypeFont) -> None:
    stripped = line.strip()
    if stripped.startswith("//"):
        draw.text((x, y), line, font=font, fill=(100, 116, 139))
        return

    import re
    token_spec = [
        ('COMMENT',  r'//.*'),
        ('KEYWORD',  r'\b(const|let|var|for|new|function|return|if|else|class)\b'),
        ('TYPE',     r'\b([A-Z][a-zA-Z0-9]+)\b'),
        ('BUILTIN',  r'\b(Math\.sin|Math\.PI|Math|ctx|window|document)\b'),
        ('NUMBER',   r'\b(-?\d+(\.\d+)?)\b'),
        ('STRING',   r'[\'\"][^\'\"]*[\'\"]'),
        ('FUNC',     r'\b([a-zA-Z0-9_]+)(?=\s*\()'),
        ('IDENT',    r'\b([a-zA-Z0-9_]+)\b'),
        ('PUNCT',    r'[\(\)\{\}\[\]\:\,\;\=\>\+\-\*\/]'),
        ('WS',       r'\s+'),
        ('OTHER',    r'.'),
    ]
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_spec)

    curr_x = x
    for match in re.finditer(tok_regex, line):
        kind = match.lastgroup
        val = match.group()

        if kind == 'KEYWORD':
            color = (224, 108, 117)
        elif kind == 'TYPE':
            color = (229, 192, 123)
        elif kind == 'FUNC':
            color = (97, 175, 239)
        elif kind == 'BUILTIN':
            color = (86, 182, 194)
        elif kind == 'NUMBER':
            color = (209, 154, 102)
        elif kind == 'STRING':
            color = (152, 195, 121)
        elif kind == 'COMMENT':
            color = (100, 116, 139)
        else:
            color = (226, 232, 240)

        draw.text((curr_x, y), val, font=font, fill=color)
        bbox = draw.textbbox((curr_x, y), val, font=font)
        curr_x = bbox[2]


def _generate_js_code_for_animal(name: str, class_type: str, scientific: str) -> list[str]:
    import re
    c_name = "".join(re.sub(r'[^a-zA-Z0-9]', '', w).capitalize() for w in name.split())
    if class_type == "quadruped":
        return [
            f"// ─── {name} ───",
            f"const rig = new CanineRig({{",
            "  spineSegs: 18,",
            "  limbs: 4",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const p = getPointer();",
            "",
            "  // Forelimbs: Elbow IK",
            "  solveForelimbIK(",
            "    rig.lArm, p.fl, 52, -1",
            "  );",
            "  solveForelimbIK(",
            "    rig.rArm, p.fr, 52,  1",
            "  );",
            "",
            "  // Hindlimbs: Hock IK",
            "  solveHindlimbIK(",
            "    rig.lLeg, p.hl, 48, -1",
            "  );",
            "  solveHindlimbIK(",
            "    rig.rLeg, p.hr, 48,  1",
            "  );",
            "",
            "  // Paws, Torso & Tail",
            "  render4ToePaws(ctx, rig);",
            "  renderTorso(ctx, rig.spine);",
            "  wagTail(rig.tail, time * 6);",
            "  renderCanineHead(ctx, rig);",
            "};"
        ]
    elif class_type == "arachnid":
        return [
            f"// ─── {name} ───",
            f"const rig = new ArachnidRig({{",
            "  segments: 38,",
            "  legs: 8",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const p = getPointer();",
            "",
            "  // 3-Joint Pincer Arms",
            "  solvePincerIK(",
            "    rig.lArm, p, 54, -1",
            "  );",
            "  solvePincerIK(",
            "    rig.rArm, p, 54,  1",
            "  );",
            "",
            "  // 8-Leg Tripod Stepping",
            "  for (let i = 0; i < 8; i++) {",
            "    const s = i < 4 ? -1 : 1;",
            "    const hip = getSocket(i, s);",
            "    const step = tripodStep(i);",
            "    solve3SegIK(hip, step, s);",
            "    renderLeg(ctx, rig.legs[i]);",
            "  }",
            "",
            "  // Segmented Tail & Stinger",
            "  curlTail(rig.tail, time * 2);",
            "  renderTelson(ctx, rig.tail);",
            "};"
        ]
    elif class_type == "serpent":
        return [
            f"// ─── {name} ───",
            f"const spine = new SnakeSpine({{",
            "  vertebrae: 48,",
            "  spacing: 14",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const head = spine.head;",
            "  head.follow(pointer, 0.08);",
            "",
            "  // Undulation Wave",
            "  for (let i = 1; i < 48; i++) {",
            "    const prev = spine.get(i-1);",
            "    const curr = spine.get(i);",
            "    const wave = Math.sin(",
            "      time * 4.5 + i * 0.35",
            "    ) * 6;",
            "    curr.update(prev, 14, wave);",
            "    renderScales(ctx, curr, i);",
            "  }",
            "",
            "  // Fanged Head & Tongue",
            "  renderViperHead(ctx, head);",
            "  flickTongue(ctx, head, time);",
            "};"
        ]
    elif class_type == "reptile":
        return [
            f"// ─── {name} ───",
            f"const rig = new ReptileRig({{",
            "  vertebrae: 26,",
            "  limbs: 4",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  rig.head.follow(pointer);",
            "",
            "  // 2-Joint Claws IK",
            "  rig.limbs.forEach(l => {",
            "    const socket = getSocket(l);",
            "    const step = gaitArc(l.phase);",
            "    const ik = solve2JointIK(",
            "      socket, step.foot, l.side",
            "    );",
            "    renderClaw(ctx, ik);",
            "  });",
            "",
            "  // Heavy Armored Scales",
            "  renderScales(ctx, rig.spine);",
            "  renderReptileHead(ctx, rig);",
            "};"
        ]
    elif class_type == "crustacean":
        return [
            f"// ─── {name} ───",
            f"const rig = new CrustaceanRig({{",
            "  segments: 24,",
            "  dactylClubs: 2",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  rig.update(pointer);",
            "",
            "  // Springloaded Punch IK",
            "  solveClubIK(",
            "    rig.leftClub, pointer, -1",
            "  );",
            "  solveClubIK(",
            "    rig.rightClub, pointer, 1",
            "  );",
            "",
            "  // Pleopods & Carapace",
            "  ripplePleopods(rig, time);",
            "  renderCarapace(ctx, rig);",
            "  renderCompoundEyes(ctx, rig);",
            "};"
        ]
    elif class_type == "insect":
        return [
            f"// ─── {name} ───",
            f"const rig = new InsectRig({{",
            "  thorax: 14,",
            "  raptorialArms: 2",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  rig.head.track(pointer);",
            "",
            "  // Folded Raptorial Claws",
            "  solveRaptorialIK(",
            "    rig.lArm, pointer, -1",
            "  );",
            "  solveRaptorialIK(",
            "    rig.rArm, pointer, 1",
            "  );",
            "",
            "  // Walking Legs & Wings",
            "  stepInsectLegs(rig, time);",
            "  renderThorax(ctx, rig);",
            "  renderTriangularHead(ctx, rig);",
            "};"
        ]
    elif class_type == "cephalopod":
        return [
            f"// ─── {name} ───",
            f"const rig = new OctopusRig({{",
            "  tentacles: 8,",
            "  jointsPerArm: 16",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  rig.mantle.follow(pointer);",
            "",
            "  // Multi-Joint Tentacle IK",
            "  for (let i = 0; i < 8; i++) {",
            "    const arm = rig.arms[i];",
            "    const a = (i / 8) * Math.PI * 2;",
            "    undulateArm(arm, a, time);",
            "    renderGlowingRings(ctx, arm);",
            "  }",
            "",
            "  // Chromatophore Mantle",
            "  renderMantle(ctx, rig.mantle);",
            "  pulseBlueRings(ctx, rig, time);",
            "};"
        ]
    else:  # aquatic
        return [
            f"// ─── {name} ───",
            f"const rig = new AquaticRig({{",
            "  wingspan: 36,",
            "  ribCount: 22",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  rig.head.follow(pointer, 0.05);",
            "",
            "  // Sinusoidal Wing Flap",
            "  const flap = Math.sin(time*3)*0.4;",
            "  undulatePectoralFin(",
            "    rig.lWing, flap, -1",
            "  );",
            "  undulatePectoralFin(",
            "    rig.rWing, flap,  1",
            "  );",
            "",
            "  // Trailing Whip Tail",
            "  followSpineChain(rig.tail);",
            "  renderAquaticBody(ctx, rig);",
            "  renderCephalicLobes(ctx, rig);",
            "};"
        ]

def get_species_for_id(animal_id: int) -> dict:
    try:
        encyclopedia = json.loads(ENCYCLOPEDIA_FILE.read_text(encoding="utf-8"))
    except Exception:
        encyclopedia = []

    if not encyclopedia:
        encyclopedia = [{"name": "GOLDEN SHEPHERD DOG", "scientific": "Canis lupus familiaris", "class_type": "quadruped", "accent": [245, 158, 11], "file_name": "GoldenShepherd.js"}]

    idx = animal_id % len(encyclopedia)
    entry = encyclopedia[idx]

    name = entry["name"]
    scientific = entry.get("scientific", name)
    class_type = entry.get("class_type", "quadruped")
    accent = tuple(entry.get("accent", [245, 158, 11]))
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
        "yt_desc": f"✨ Realistic {name} ({scientific}) with biologically accurate joint kinematics in Vanilla JavaScript!\n\n#JavaScript #WebDev #Shorts #Coding #Tech"
    }

class MasterSimulator:
    def __init__(self, cx: float, cy: float, rx: float, ry: float):
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.x = cx
        self.y = cy
        self.angle = 0.0
        self.speed = 0.0
        self.spine = [{"x": cx - i * 22, "y": cy, "angle": 0.0} for i in range(20)]
        
        # 8 Arachnid Legs
        self.legs8 = [
            {"id": "L1", "side": -1, "spread": -0.85, "rest_d": 110, "l1": 34, "l2": 48, "l3": 42, "group": 0, "cur": [cx - 110, cy + 40], "tgt": [cx - 110, cy + 40], "start": [cx - 110, cy + 40], "prog": 1.0, "hip": (cx - 110, cy + 40)},
            {"id": "L2", "side": -1, "spread": -1.30, "rest_d": 130, "l1": 40, "l2": 56, "l3": 48, "group": 1, "cur": [cx - 125, cy + 40], "tgt": [cx - 125, cy + 40], "start": [cx - 125, cy + 40], "prog": 1.0, "hip": (cx - 125, cy + 40)},
            {"id": "L3", "side": -1, "spread": -1.75, "rest_d": 136, "l1": 42, "l2": 58, "l3": 50, "group": 0, "cur": [cx - 130, cy + 40], "tgt": [cx - 130, cy + 40], "start": [cx - 130, cy + 40], "prog": 1.0, "hip": (cx - 130, cy + 40)},
            {"id": "L4", "side": -1, "spread": -2.20, "rest_d": 120, "l1": 36, "l2": 50, "l3": 44, "group": 1, "cur": [cx - 115, cy + 40], "tgt": [cx - 115, cy + 40], "start": [cx - 115, cy + 40], "prog": 1.0, "hip": (cx - 115, cy + 40)},
            {"id": "R1", "side":  1, "spread":  0.85, "rest_d": 110, "l1": 34, "l2": 48, "l3": 42, "group": 1, "cur": [cx + 110, cy + 40], "tgt": [cx + 110, cy + 40], "start": [cx + 110, cy + 40], "prog": 1.0, "hip": (cx + 110, cy + 40)},
            {"id": "R2", "side":  1, "spread":  1.30, "rest_d": 130, "l1": 40, "l2": 56, "l3": 48, "group": 0, "cur": [cx + 125, cy + 40], "tgt": [cx + 125, cy + 40], "start": [cx + 125, cy + 40], "prog": 1.0, "hip": (cx + 125, cy + 40)},
            {"id": "R3", "side":  1, "spread":  1.75, "rest_d": 136, "l1": 42, "l2": 58, "l3": 50, "group": 1, "cur": [cx + 130, cy + 40], "tgt": [cx + 130, cy + 40], "start": [cx + 130, cy + 40], "prog": 1.0, "hip": (cx + 130, cy + 40)},
            {"id": "R4", "side":  1, "spread":  2.20, "rest_d": 120, "l1": 36, "l2": 50, "l3": 44, "group": 0, "cur": [cx + 115, cy + 40], "tgt": [cx + 115, cy + 40], "start": [cx + 115, cy + 40], "prog": 1.0, "hip": (cx + 115, cy + 40)},
        ]
        # 4 Quadruped Legs
        self.legs4 = [
            {"id": "FL", "spine_i": 3, "side": -1, "is_front": True,  "l1": 52, "l2": 58, "phase": 0.0,     "cur": [cx + 20, cy - 45], "tgt": [cx + 20, cy - 45], "start": [cx + 20, cy - 45], "prog": 1.0, "socket": (cx + 20, cy - 45)},
            {"id": "FR", "spine_i": 3, "side":  1, "is_front": True,  "l1": 52, "l2": 58, "phase": math.pi, "cur": [cx + 20, cy + 45], "tgt": [cx + 20, cy + 45], "start": [cx + 20, cy + 45], "prog": 1.0, "socket": (cx + 20, cy + 45)},
            {"id": "HL", "spine_i": 11, "side": -1, "is_front": False, "l1": 48, "l2": 48, "l3": 32, "phase": math.pi, "cur": [cx - 60, cy - 45], "tgt": [cx - 60, cy - 45], "start": [cx - 60, cy - 45], "prog": 1.0, "socket": (cx - 60, cy - 45)},
            {"id": "HR", "spine_i": 11, "side":  1, "is_front": False, "l1": 48, "l2": 48, "l3": 32, "phase": 0.0,     "cur": [cx - 60, cy + 45], "tgt": [cx - 60, cy + 45], "start": [cx - 60, cy + 45], "prog": 1.0, "socket": (cx - 60, cy + 45)},
        ]

    def update(self, sim_time: float):
        target_x = self.cx + math.cos(sim_time * 0.75) * (self.rx * 0.85) + math.sin(sim_time * 1.5) * (self.rx * 0.20)
        target_y = self.cy + math.sin(sim_time * 1.05) * (self.ry * 0.80) + math.cos(sim_time * 2.1) * (self.ry * 0.18)

        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        target_ang = math.atan2(dy, dx)

        diff = target_ang - self.angle
        while diff < -math.pi: diff += math.pi * 2
        while diff > math.pi: diff -= math.pi * 2
        self.angle += diff * 0.04

        if dist > 25:
            target_spd = min(2.4, dist * 0.035)
            self.speed += (target_spd - self.speed) * 0.06
        else:
            self.speed *= 0.90

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        perp_x = -sin_a
        perp_y =  cos_a

        # Pure Inverse Kinematics Spine Follow-Chain
        self.spine[0]["x"] = self.x
        self.spine[0]["y"] = self.y
        self.spine[0]["angle"] = self.angle
        for i in range(1, len(self.spine)):
            prev = self.spine[i - 1]
            curr = self.spine[i]
            s_dist = 22 - (i / len(self.spine)) * 4
            p_dx = curr["x"] - prev["x"]
            p_dy = curr["y"] - prev["y"]
            d = math.hypot(p_dx, p_dy)
            if d > 0.0001:
                curr["x"] = prev["x"] + (p_dx / d) * s_dist
                curr["y"] = prev["y"] + (p_dy / d) * s_dist
                curr["angle"] = math.atan2(prev["y"] - curr["y"], prev["x"] - curr["x"])
            else:
                curr["angle"] = prev["angle"]

        # 4 Quadruped Legs Gait
        trot_clock = sim_time * 6.5
        for leg in self.legs4:
            s_pt = self.spine[leg["spine_i"]]
            s_ang = s_pt["angle"]
            s_cos = math.cos(s_ang)
            s_sin = math.sin(s_ang)
            s_perp_x = -s_sin
            s_perp_y =  s_cos

            sock_dist = 28 if leg["is_front"] else 24
            sock = (s_pt["x"] + s_perp_x * (sock_dist * leg["side"]),
                    s_pt["y"] + s_perp_y * (sock_dist * leg["side"]))
            leg["socket"] = sock

            f_reach = 36 if leg["is_front"] else -10
            l_spread = 32 if leg["is_front"] else 28
            ideal_x = sock[0] + s_cos * f_reach + s_perp_x * (l_spread * leg["side"])
            ideal_y = sock[1] + s_sin * f_reach + s_perp_y * (l_spread * leg["side"])

            d_ideal = math.hypot(ideal_x - leg["cur"][0], ideal_y - leg["cur"][1])
            phase_v = math.sin(trot_clock + leg["phase"])

            if d_ideal > 36 and leg["prog"] >= 1.0 and phase_v > 0.1:
                leg["prog"] = 0.0
                leg["start"] = [leg["cur"][0], leg["cur"][1]]
                leg["tgt"] = [
                    ideal_x + cos_a * (self.speed * 10 + 20),
                    ideal_y + sin_a * (self.speed * 10 + 20)
                ]

            if leg["prog"] < 1.0:
                leg["prog"] += 0.10
                p = min(1.0, leg["prog"])
                ease_p = 0.5 - math.cos(p * math.pi) / 2
                lift = math.sin(p * math.pi) * 20
                leg["cur"][0] = leg["start"][0] + (leg["tgt"][0] - leg["start"][0]) * ease_p
                leg["cur"][1] = leg["start"][1] + (leg["tgt"][1] - leg["start"][1]) * ease_p - lift * 0.2

        # 8 Arachnid Legs Gait
        gait_clock = sim_time * 6.5
        for idx, leg in enumerate(self.legs8):
            leg_i = idx % 4
            hip_along = 18 - leg_i * 14
            hip_x = self.x + cos_a * hip_along + perp_x * (32 * leg["side"])
            hip_y = self.y + sin_a * hip_along + perp_y * (32 * leg["side"])
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
                    ideal_x + math.cos(self.angle) * 32,
                    ideal_y + math.sin(self.angle) * 32
                ]

            if leg["prog"] < 1.0:
                leg["prog"] += 0.10
                p = min(1.0, leg["prog"])
                ease_p = 0.5 - math.cos(p * math.pi) / 2
                leg["cur"][0] = leg["start"][0] + (leg["tgt"][0] - leg["start"][0]) * ease_p
                leg["cur"][1] = leg["start"][1] + (leg["tgt"][1] - leg["start"][1]) * ease_p


_SIM_CACHE = {}

def render_generative_frame(species: dict, frame_idx: int, total_frames: int) -> Image.Image:
    progress = frame_idx / total_frames
    sim_time = (frame_idx / FPS) * 0.4

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

    sp_id = species.get("id", "golden_shepherd_dog")
    class_type = species.get("class_type", "quadruped")
    accent_color = species.get("accent", (245, 158, 11))

    sim_key = f"{sp_id}_{total_frames}"
    if frame_idx == 0 or sim_key not in _SIM_CACHE:
        _SIM_CACHE[sim_key] = MasterSimulator(cb_x, cb_y, rad_x, rad_y)
    
    sim = _SIM_CACHE[sim_key]
    sim.update(sim_time)

    cos_a = math.cos(sim.angle)
    sin_a = math.sin(sim.angle)
    perp_x = -sin_a
    perp_y =  cos_a

    # ─────────────────────────────────────────────────────────────
    # BIOLOGICAL ANIMAL RENDERING: 8 TAXONOMIC ANIMAL CLASSES
    # ─────────────────────────────────────────────────────────────
    # Interactive Cursor Target Indicator
    draw.ellipse([sim.cx + math.cos(sim_time * 0.75) * (rad_x * 0.85) - 8,
                  sim.cy + math.sin(sim_time * 1.05) * (rad_y * 0.80) - 8,
                  sim.cx + math.cos(sim_time * 0.75) * (rad_x * 0.85) + 8,
                  sim.cy + math.sin(sim_time * 1.05) * (rad_y * 0.80) + 8],
                 outline=(239, 68, 68, 160), width=2)
    draw.ellipse([sim.cx + math.cos(sim_time * 0.75) * (rad_x * 0.85) - 3,
                  sim.cy + math.sin(sim_time * 1.05) * (rad_y * 0.80) - 3,
                  sim.cx + math.cos(sim_time * 0.75) * (rad_x * 0.85) + 3,
                  sim.cy + math.sin(sim_time * 1.05) * (rad_y * 0.80) + 3],
                 fill=(239, 68, 68, 200))

    if class_type == "quadruped" or "dog" in sp_id or "wolf" in sp_id or "tiger" in sp_id:
        # 1. 4 Articulated Legs (Elbow BACKWARD, Stifle Knee FORWARD, Hock BACKWARD)
        for leg in sim.legs4:
            paw_pos = (leg["cur"][0], leg["cur"][1])
            sock = leg["socket"]

            if leg["is_front"]:
                _, elbow, _ = solve_forelimb_ik(sock, paw_pos, leg["l1"], leg["l2"], leg["side"])
                draw.line([sock, elbow], fill=(180, 83, 9), width=22)
                draw.line([sock, elbow], fill=(245, 158, 11), width=16)
                draw.line([elbow, paw_pos], fill=(217, 119, 6), width=14)
                draw.line([elbow, paw_pos], fill=(251, 191, 36), width=10)
                draw.ellipse([elbow[0]-7, elbow[1]-7, elbow[0]+7, elbow[1]+7], fill=(245, 158, 11), outline=(180, 83, 9), width=2)
            else:
                knee = (sock[0] + cos_a * (leg["l1"] * 0.75) + perp_x * (leg["l1"] * 0.65 * leg["side"]),
                        sock[1] + sin_a * (leg["l1"] * 0.75) + perp_y * (leg["l1"] * 0.65 * leg["side"]))
                hock = (knee[0] - cos_a * (leg["l2"] * 0.65) + perp_x * (leg["l2"] * 0.2 * leg["side"]),
                        knee[1] - sin_a * (leg["l2"] * 0.65) + perp_y * (leg["l2"] * 0.2 * leg["side"]))
                draw.line([sock, knee], fill=(146, 64, 14), width=26)
                draw.line([sock, knee], fill=(217, 119, 6), width=18)
                draw.line([knee, hock], fill=(180, 83, 9), width=16)
                draw.line([knee, hock], fill=(245, 158, 11), width=12)
                draw.line([hock, paw_pos], fill=(217, 119, 6), width=13)
                draw.line([hock, paw_pos], fill=(251, 191, 36), width=9)
                draw.ellipse([knee[0]-8, knee[1]-8, knee[0]+8, knee[1]+8], fill=(245, 158, 11), outline=(146, 64, 14), width=2)
                draw.ellipse([hock[0]-6, hock[1]-6, hock[0]+6, hock[1]+6], fill=(120, 53, 15), outline=(180, 83, 9), width=2)

            # 4-Toe Digitigrade Paw Pads with Claws
            draw.ellipse([paw_pos[0]-11, paw_pos[1]-10, paw_pos[0]+11, paw_pos[1]+10], fill=(40, 30, 20), outline=(20, 15, 10), width=2)
            for t_off in [-6, -2, 2, 6]:
                bx = paw_pos[0] + cos_a * 9 + perp_x * t_off
                by = paw_pos[1] + sin_a * 9 + perp_y * t_off
                draw.ellipse([bx-3.5, by-3.5, bx+3.5, by+3.5], fill=(20, 15, 10))
                draw.line([(bx, by), (bx + cos_a * 5, by + sin_a * 5)], fill=(10, 10, 10), width=2)

        # 2. Muscular Torso & Spine Follow-Chain
        left_prof, right_prof = [], []
        spine_pts = []
        for i in range(16):
            seg = sim.spine[i]
            s_cos, s_sin = math.cos(seg["angle"]), math.sin(seg["angle"])
            s_perp_x, s_perp_y = -s_sin, s_cos
            half_w = 40 - i * 0.9 if i < 6 else 30 - (i-6)*1.4 if i < 11 else 36 - (i-11)*0.8
            half_w = max(18, half_w)
            left_prof.append((seg["x"] + s_perp_x * half_w, seg["y"] + s_perp_y * half_w))
            right_prof.append((seg["x"] - s_perp_x * half_w, seg["y"] - s_perp_y * half_w))
            spine_pts.append((seg["x"], seg["y"]))

        draw.polygon(left_prof + list(reversed(right_prof)), fill=(245, 158, 11), outline=(180, 83, 9), width=3)
        saddle_l = [((left_prof[i][0]*0.70 + spine_pts[i][0]*0.30), (left_prof[i][1]*0.70 + spine_pts[i][1]*0.30)) for i in range(2, 12)]
        saddle_r = [((right_prof[i][0]*0.70 + spine_pts[i][0]*0.30), (right_prof[i][0]*0.70 + spine_pts[i][0]*0.30)) for i in range(2, 12)]
        draw.polygon(saddle_l + list(reversed(saddle_r)), fill=(28, 17, 8))

        # 3. Harmonic Plume Tail
        tail_prev = spine_pts[-1]
        wag = math.sin(sim_time * 6.5) * 0.55
        for i in range(10):
            t_ang = sim.angle + math.pi + wag * ((i+1)/10)
            tx = tail_prev[0] + math.cos(t_ang) * (22 - i * 1.1)
            ty = tail_prev[1] + math.sin(t_ang) * (22 - i * 1.1)
            draw.line([tail_prev, (tx, ty)], fill=(180, 83, 9), width=max(8, int(26 - i * 1.9)))
            draw.line([tail_prev, (tx, ty)], fill=(245, 158, 11), width=max(5, int(20 - i * 1.5)))
            draw.line([tail_prev, (tx, ty)], fill=(254, 243, 199), width=max(2, int(10 - i * 0.9)))
            tail_prev = (tx, ty)

        # 4. Detailed Sculpted Canine Head
        hx = sim.x + cos_a * 38
        hy = sim.y + sin_a * 38
        snout = (hx + cos_a * 54, hy + sin_a * 54)

        ear_l = (hx - cos_a * 12 + perp_x * 32, hy - sin_a * 12 + perp_y * 32)
        ear_tip_l = (ear_l[0] - cos_a * 36 + perp_x * 22, ear_l[1] - sin_a * 36 + perp_y * 22)
        ear_r = (hx - cos_a * 12 - perp_x * 32, hy - sin_a * 12 - perp_y * 32)
        ear_tip_r = (ear_r[0] - cos_a * 36 - perp_x * 22, ear_r[1] - sin_a * 36 - perp_y * 22)
        draw.polygon([(hx, hy), ear_l, ear_tip_l], fill=(28, 17, 8), outline=(180, 83, 9), width=3)
        draw.polygon([(hx, hy), ear_r, ear_tip_r], fill=(28, 17, 8), outline=(180, 83, 9), width=3)
        draw.polygon([ear_l, ear_tip_l, (hx - cos_a * 8 + perp_x * 18, hy - sin_a * 8 + perp_y * 18)], fill=(253, 164, 175))
        draw.polygon([ear_r, ear_tip_r, (hx - cos_a * 8 - perp_x * 18, hy - sin_a * 8 - perp_y * 18)], fill=(253, 164, 175))

        c1 = (hx + cos_a * 26 + perp_x * 32, hy + sin_a * 26 + perp_y * 32)
        c2 = (hx - cos_a * 24 + perp_x * 36, hy - sin_a * 24 + perp_y * 36)
        c3 = (hx - cos_a * 24 - perp_x * 36, hy - sin_a * 24 - perp_y * 36)
        c4 = (hx + cos_a * 26 - perp_x * 32, hy + sin_a * 26 - perp_y * 32)
        draw.polygon([snout, c1, c2, c3, c4], fill=(245, 158, 11), outline=(180, 83, 9), width=3)

        m1 = (hx + cos_a * 22 + perp_x * 20, hy + sin_a * 22 + perp_y * 20)
        m2 = (hx + cos_a * 22 - perp_x * 20, hy + sin_a * 22 - perp_y * 20)
        draw.polygon([snout, m1, m2], fill=(28, 17, 8))

        tongue_tip = (snout[0] + cos_a * 22, snout[1] + sin_a * 22)
        draw.ellipse([tongue_tip[0]-5.5, tongue_tip[1]-5.5, tongue_tip[0]+5.5, tongue_tip[1]+5.5], fill=(251, 113, 133))
        draw.ellipse([snout[0]-8.5, snout[1]-7, snout[0]+8.5, snout[1]+7], fill=(0, 0, 0))
        draw.ellipse([snout[0]+cos_a*2-2.5, snout[1]+sin_a*2-1.5, snout[0]+cos_a*2+2.5, snout[1]+sin_a*2+1.5], fill=(148, 163, 184))

        eye_l = (hx + cos_a * 12 + perp_x * 18, hy + sin_a * 12 + perp_y * 18)
        eye_r = (hx + cos_a * 12 - perp_x * 18, hy + sin_a * 12 - perp_y * 18)
        draw.ellipse([eye_l[0]-6.5, eye_l[1]-6, eye_l[0]+6.5, eye_l[1]+6], fill=(69, 26, 3))
        draw.ellipse([eye_r[0]-6.5, eye_r[1]-6, eye_r[0]+6.5, eye_r[1]+6], fill=(69, 26, 3))
        draw.ellipse([eye_l[0]+1.8, eye_l[1]-1.8, eye_l[0]+4, eye_l[1]+0.6], fill=(255, 255, 255))
        draw.ellipse([eye_r[0]+1.8, eye_r[1]-1.8, eye_r[0]+4, eye_r[1]+0.6], fill=(255, 255, 255))

    elif class_type == "arachnid":
        # 1. 8 Articulated Walking Legs with 3-Segment IK & Tarsal Claws
        for leg in sim.legs8:
            h_p = leg["hip"]
            foot_p = (leg["cur"][0], leg["cur"][1])
            h_p, j1_p, j2_p, f_p = solve_ik_3segment(h_p, foot_p, leg["l1"], leg["l2"], leg["l3"], leg["side"])
            draw.line([h_p, j1_p], fill=(20, 24, 32), width=12)
            draw.line([h_p, j1_p], fill=(35, 42, 54), width=8)
            draw.line([j1_p, j2_p], fill=(28, 36, 48), width=10)
            draw.line([j1_p, j2_p], fill=(45, 55, 72), width=6)
            draw.line([j2_p, f_p], fill=(15, 20, 28), width=7)
            draw.ellipse([j1_p[0]-5, j1_p[1]-5, j1_p[0]+5, j1_p[1]+5], fill=accent_color)
            draw.ellipse([j2_p[0]-5, j2_p[1]-5, j2_p[0]+5, j2_p[1]+5], fill=accent_color)
            # Sharp curved needle claw at foot
            draw.ellipse([f_p[0]-4, f_p[1]-4, f_p[0]+4, f_p[1]+4], fill=(10, 12, 16))
            claw_tip = (f_p[0] + cos_a * 6 + perp_x * (4 * leg["side"]), f_p[1] + sin_a * 6 + perp_y * (4 * leg["side"]))
            draw.line([f_p, claw_tip], fill=accent_color, width=2)

        # 2. Chelae (3-Joint Pincer Arms Extending Forward)
        for side in [-1, 1]:
            arm_sock = (sim.x + cos_a * 36 + perp_x * (26 * side), sim.y + sin_a * 36 + perp_y * (26 * side))
            palm_target = (sim.x + cos_a * 95 + perp_x * (55 * side), sim.y + sin_a * 95 + perp_y * (55 * side))
            _, elbow_p, palm_p = solve_forelimb_ik(arm_sock, palm_target, 42, 48, side)
            draw.line([arm_sock, elbow_p], fill=(25, 30, 40), width=14)
            draw.line([elbow_p, palm_p], fill=(30, 38, 50), width=16)
            draw.ellipse([elbow_p[0]-6, elbow_p[1]-6, elbow_p[0]+6, elbow_p[1]+6], fill=accent_color)
            # Muscular Palm & Snapping Pincers
            draw.ellipse([palm_p[0]-12, palm_p[1]-12, palm_p[0]+12, palm_p[1]+12], fill=(18, 22, 30), outline=accent_color, width=2)
            c_angle = math.atan2(palm_p[1] - elbow_p[1], palm_p[0] - elbow_p[0])
            pinch_open = 0.28 + math.sin(sim_time * 4) * 0.12
            p1_tip = (palm_p[0] + math.cos(c_angle - pinch_open) * 28, palm_p[1] + math.sin(c_angle - pinch_open) * 28)
            p2_tip = (palm_p[0] + math.cos(c_angle + pinch_open) * 28, palm_p[1] + math.sin(c_angle + pinch_open) * 28)
            draw.line([palm_p, p1_tip], fill=accent_color, width=5)
            draw.line([palm_p, p2_tip], fill=accent_color, width=5)

        # 3. 7 Mesosoma Tergite Plates
        for i in range(1, 8):
            seg = sim.spine[i]
            s_cos, s_sin = math.cos(seg["angle"]), math.sin(seg["angle"])
            s_perp_x, s_perp_y = -s_sin, s_cos
            half_w = max(20, 52 - i * 4.4)
            half_h = 12
            p1 = (seg["x"] - s_cos * half_h + s_perp_x * half_w, seg["y"] - s_sin * half_h + s_perp_y * half_w)
            p2 = (seg["x"] + s_cos * half_h + s_perp_x * (half_w * 0.92), seg["y"] + s_sin * half_h + s_perp_y * (half_w * 0.92))
            p3 = (seg["x"] + s_cos * half_h - s_perp_x * (half_w * 0.92), seg["y"] + s_sin * half_h - s_perp_y * (half_w * 0.92))
            p4 = (seg["x"] - s_cos * half_h - s_perp_x * half_w, seg["y"] - s_sin * half_h - s_perp_y * half_w)
            draw.polygon([p1, p2, p3, p4], fill=(16, 22, 30), outline=(40, 50, 65), width=2)
            draw.line([(seg["x"] + s_perp_x * (half_w*0.8), seg["y"] + s_perp_y * (half_w*0.8)),
                       (seg["x"] - s_perp_x * (half_w*0.8), seg["y"] - s_perp_y * (half_w*0.8))], fill=accent_color, width=2)

        # 4. Sculpted Prosoma Carapace with Median Ocular Tubercle
        c_front = (sim.x + cos_a * 52, sim.y + sin_a * 52)
        c_r1 = (sim.x + cos_a * 28 + perp_x * 44, sim.y + sin_a * 28 + perp_y * 44)
        c_r2 = (sim.x - cos_a * 26 + perp_x * 48, sim.y - sin_a * 26 + perp_y * 48)
        c_l2 = (sim.x - cos_a * 26 - perp_x * 48, sim.y - sin_a * 26 - perp_y * 48)
        c_l1 = (sim.x + cos_a * 28 - perp_x * 44, sim.y + sin_a * 28 - perp_y * 44)
        draw.polygon([c_front, c_r1, c_r2, c_l2, c_l1], fill=(12, 16, 24), outline=accent_color, width=3)
        # Median eyes
        draw.ellipse([sim.x + cos_a * 15 - 4, sim.y + sin_a * 15 - 4, sim.x + cos_a * 15 + 4, sim.y + sin_a * 15 + 4], fill=accent_color)

        # 5. Curling Metasoma Tail with Venom Telson & Stinger Needle
        tail_start = sim.spine[7]
        t_prev = (tail_start["x"], tail_start["y"])
        tail_curve = math.sin(sim_time * 3.5) * 0.45
        for t_idx in range(6):
            t_ang = tail_start["angle"] + math.pi + tail_curve * (t_idx / 5)
            seg_len = 24 - t_idx * 1.5
            tx = t_prev[0] + math.cos(t_ang) * seg_len
            ty = t_prev[1] + math.sin(t_ang) * seg_len
            t_w = max(6, int(20 - t_idx * 2.2))
            draw.line([t_prev, (tx, ty)], fill=(22, 28, 38), width=t_w)
            draw.ellipse([tx - t_w//2, ty - t_w//2, tx + t_w//2, ty + t_w//2], fill=(30, 40, 55), outline=accent_color, width=1)
            t_prev = (tx, ty)
        
        # Bulbous Telson & Venom Needle
        draw.ellipse([t_prev[0]-10, t_prev[1]-10, t_prev[0]+10, t_prev[1]+10], fill=(200, 140, 10), outline=accent_color, width=2)
        needle_tip = (t_prev[0] + math.cos(sim.angle + 0.6) * 22, t_prev[1] + math.sin(sim.angle + 0.6) * 22)
        draw.line([t_prev, needle_tip], fill=(255, 230, 100), width=3)
        draw.ellipse([needle_tip[0]-2, needle_tip[1]-2, needle_tip[0]+2, needle_tip[1]+2], fill=(255, 255, 255))

    elif class_type == "serpent":
        # 1. 24-Segment Undulating Biological Snake Body
        num_v = min(24, len(sim.spine))
        for i in range(num_v - 1, 0, -1):
            p1 = (sim.spine[i]["x"], sim.spine[i]["y"])
            p0 = (sim.spine[i - 1]["x"], sim.spine[i - 1]["y"])
            norm = i / num_v
            v_width = max(6, int(38 * (1.0 - norm * 0.78)))
            # Dorsal scales (Dark emerald/black with metallic rim)
            draw.line([p0, p1], fill=(12, 24, 18), width=v_width)
            draw.line([p0, p1], fill=(24, 48, 36), width=max(2, v_width - 6))
            draw.ellipse([p1[0]-v_width//2, p1[1]-v_width//2, p1[0]+v_width//2, p1[1]+v_width//2],
                         fill=(20, 40, 30), outline=accent_color, width=1)

        # 2. Flaring Cobra Cervical Hood (Vertebrae 2 to 5)
        h_pt = sim.spine[2]
        h_cos, h_sin = math.cos(h_pt["angle"]), math.sin(h_pt["angle"])
        h_perp_x, h_perp_y = -h_sin, h_cos
        hood_l = (h_pt["x"] + h_perp_x * 46, h_pt["y"] + h_perp_y * 46)
        hood_r = (h_pt["x"] - h_perp_x * 46, h_pt["y"] - h_perp_y * 46)
        hood_f = (sim.x + cos_a * 18, sim.y + sin_a * 18)
        hood_b = (sim.spine[5]["x"], sim.spine[5]["y"])
        draw.polygon([hood_f, hood_l, hood_b, hood_r], fill=(15, 30, 22), outline=accent_color, width=3)
        # Dorsal chevron spectacle mark
        draw.line([hood_l, (h_pt["x"], h_pt["y"])], fill=accent_color, width=2)
        draw.line([hood_r, (h_pt["x"], h_pt["y"])], fill=accent_color, width=2)

        # 3. Sculpted Diamond Viper Skull
        snout = (sim.x + cos_a * 46, sim.y + sin_a * 46)
        j1 = (sim.x - cos_a * 15 + perp_x * 24, sim.y - sin_a * 15 + perp_y * 24)
        j2 = (sim.x - cos_a * 15 - perp_x * 24, sim.y - sin_a * 15 - perp_y * 24)
        crown = (sim.x - cos_a * 32, sim.y - sin_a * 32)
        draw.polygon([snout, j1, crown, j2], fill=(10, 20, 15), outline=accent_color, width=3)

        # Golden Slit Predatory Eyes with Highlight
        eye_l = (sim.x + cos_a * 12 + perp_x * 14, sim.y + sin_a * 12 + perp_y * 14)
        eye_r = (sim.x + cos_a * 12 - perp_x * 14, sim.y + sin_a * 12 - perp_y * 14)
        draw.ellipse([eye_l[0]-4.5, eye_l[1]-4.5, eye_l[0]+4.5, eye_l[1]+4.5], fill=(234, 179, 8))
        draw.ellipse([eye_r[0]-4.5, eye_r[1]-4.5, eye_r[0]+4.5, eye_r[1]+4.5], fill=(234, 179, 8))
        draw.line([(eye_l[0], eye_l[1]-3.5), (eye_l[0], eye_l[1]+3.5)], fill=(0, 0, 0), width=2)
        draw.line([(eye_r[0], eye_r[1]-3.5), (eye_r[0], eye_r[1]+3.5)], fill=(0, 0, 0), width=2)
        draw.ellipse([eye_l[0]+1, eye_l[1]-1, eye_l[0]+2.5, eye_l[1]+0.5], fill=(255, 255, 255))
        draw.ellipse([eye_r[0]+1, eye_r[1]-1, eye_r[0]+2.5, eye_r[1]+0.5], fill=(255, 255, 255))

        # 4. Animated Flicking Red Forked Tongue
        t_cycle = math.sin(sim_time * 8.0)
        if t_cycle > 0.1:
            t_len = 28 * min(1.0, t_cycle * 1.5)
            t_base = snout
            t_mid = (snout[0] + cos_a * t_len, snout[1] + sin_a * t_len)
            fork_a = 0.35
            f1 = (t_mid[0] + math.cos(sim.angle + fork_a) * 12, t_mid[1] + math.sin(sim.angle + fork_a) * 12)
            f2 = (t_mid[0] + math.cos(sim.angle - fork_a) * 12, t_mid[1] + math.sin(sim.angle - fork_a) * 12)
            draw.line([t_base, t_mid], fill=(239, 68, 68), width=3)
            draw.line([t_mid, f1], fill=(239, 68, 68), width=2)
            draw.line([t_mid, f2], fill=(239, 68, 68), width=2)

    elif class_type == "reptile":
        # 1. 4 Sprawling 2-Joint IK Limbs with 5 Spread Claws
        for leg in sim.legs4:
            s_pt = sim.spine[leg["spine_i"]]
            b_ang = s_pt["angle"]
            hip_ang = b_ang + (math.pi / 2) * leg["side"]
            hip = (s_pt["x"] + math.cos(hip_ang) * 26, s_pt["y"] + math.sin(hip_ang) * 26)
            foot_x = leg["cur"][0]
            foot_y = leg["cur"][1]
            hp, kp, fp = solve_ik_2joint(hip, (foot_x, foot_y), leg["l1"], leg["l2"], leg["side"])
            draw.line([hp, kp], fill=(24, 32, 24), width=16)
            draw.line([hp, kp], fill=(45, 65, 45), width=10)
            draw.line([kp, fp], fill=(30, 45, 30), width=12)
            draw.line([kp, fp], fill=(55, 85, 55), width=8)
            draw.ellipse([kp[0]-6, kp[1]-6, kp[0]+6, kp[1]+6], fill=accent_color)
            draw.ellipse([fp[0]-8, fp[1]-8, fp[0]+8, fp[1]+8], fill=(15, 22, 15))
            # 5 Spread Claws
            for c_i in [-0.5, -0.25, 0.0, 0.25, 0.5]:
                claw_tip = (fp[0] + math.cos(b_ang + c_i) * 14, fp[1] + math.sin(b_ang + c_i) * 14)
                draw.line([fp, claw_tip], fill=(240, 200, 120), width=2)

        # 2. Armored Osteoderm Spine & Muscular Body
        for i in range(len(sim.spine) - 1, 0, -1):
            p1 = (sim.spine[i]["x"], sim.spine[i]["y"])
            p0 = (sim.spine[i - 1]["x"], sim.spine[i - 1]["y"])
            norm = i / len(sim.spine)
            v_width = max(8, int(42 * (1.0 - norm * 0.72)))
            draw.line([p0, p1], fill=(20, 30, 20), width=v_width)
            draw.line([p0, p1], fill=(40, 60, 40), width=max(2, v_width - 8))
            draw.ellipse([p1[0]-v_width//2, p1[1]-v_width//2, p1[0]+v_width//2, p1[1]+v_width//2], fill=(30, 48, 30), outline=accent_color, width=2)

        # 3. Predatory Reptile Skull with Nostrils & Slit Eyes
        snout = (sim.x + cos_a * 50, sim.y + sin_a * 50)
        j1 = (sim.x - cos_a * 18 + perp_x * 28, sim.y - sin_a * 18 + perp_y * 28)
        j2 = (sim.x - cos_a * 18 - perp_x * 28, sim.y - sin_a * 18 - perp_y * 28)
        crown = (sim.x - cos_a * 36, sim.y - sin_a * 36)
        draw.polygon([snout, j1, crown, j2], fill=(16, 26, 18), outline=accent_color, width=3)
        draw.ellipse([snout[0]+cos_a*2-3, snout[1]+sin_a*2-3, snout[0]+cos_a*2+3, snout[1]+sin_a*2+3], fill=(0, 0, 0))
        # Eyes
        eye_l = (sim.x + cos_a * 10 + perp_x * 16, sim.y + sin_a * 10 + perp_y * 16)
        eye_r = (sim.x + cos_a * 10 - perp_x * 16, sim.y + sin_a * 10 - perp_y * 16)
        draw.ellipse([eye_l[0]-5, eye_l[1]-5, eye_l[0]+5, eye_l[1]+5], fill=(234, 179, 8))
        draw.ellipse([eye_r[0]-5, eye_r[1]-5, eye_r[0]+5, eye_r[1]+5], fill=(234, 179, 8))
        draw.ellipse([eye_l[0]+1, eye_l[1]-1, eye_l[0]+3, eye_l[1]+1], fill=(255, 255, 255))
        draw.ellipse([eye_r[0]+1, eye_r[1]-1, eye_r[0]+3, eye_r[1]+1], fill=(255, 255, 255))

    elif class_type == "crustacean":
        # Peacock Mantis Shrimp: Iridescent Turquoise Carapace & Dactyl Strike Clubs
        # 1. Pleopods / Swimming Gill Paddles along Abdomen
        for i in range(2, 10):
            seg = sim.spine[i]
            s_cos, s_sin = math.cos(seg["angle"]), math.sin(seg["angle"])
            s_perp_x, s_perp_y = -s_sin, s_cos
            paddle_phase = math.sin(sim_time * 8 + i * 0.6) * 16
            draw.line([(seg["x"] + s_perp_x * 28, seg["y"] + s_perp_y * 28),
                       (seg["x"] + s_perp_x * 46 + s_cos * paddle_phase, seg["y"] + s_perp_y * 46 + s_sin * paddle_phase)],
                      fill=(239, 68, 68), width=3)
            draw.line([(seg["x"] - s_perp_x * 28, seg["y"] - s_perp_y * 28),
                       (seg["x"] - s_perp_x * 46 + s_cos * paddle_phase, seg["y"] - s_perp_y * 46 + s_sin * paddle_phase)],
                      fill=(239, 68, 68), width=3)

        # 2. Segmented Carapace with Neon Green/Cyan Highlights
        for i in range(12, 0, -1):
            seg = sim.spine[i]
            s_cos, s_sin = math.cos(seg["angle"]), math.sin(seg["angle"])
            s_perp_x, s_perp_y = -s_sin, s_cos
            half_w = max(16, 44 - i * 2.5)
            draw.ellipse([seg["x"] - half_w, seg["y"] - 14, seg["x"] + half_w, seg["y"] + 14], fill=(6, 78, 99), outline=accent_color, width=2)

        # 3. Springloaded Raptorial Strike Clubs
        for side in [-1, 1]:
            c_sock = (sim.x + cos_a * 22 + perp_x * (20 * side), sim.y + sin_a * 22 + perp_y * (20 * side))
            club_t = (sim.x + cos_a * 68 + perp_x * (34 * side), sim.y + sin_a * 68 + perp_y * (34 * side))
            draw.line([c_sock, club_t], fill=(234, 88, 12), width=10)
            draw.ellipse([club_t[0]-10, club_t[1]-10, club_t[0]+10, club_t[1]+10], fill=(239, 68, 68), outline=(255, 230, 100), width=3)

        # 4. Mobile Trinocular Compound Eyes
        eye1 = (sim.x + cos_a * 44 + perp_x * 16, sim.y + sin_a * 44 + perp_y * 16)
        eye2 = (sim.x + cos_a * 44 - perp_x * 16, sim.y + sin_a * 44 - perp_y * 16)
        draw.ellipse([eye1[0]-8, eye1[1]-8, eye1[0]+8, eye1[1]+8], fill=(234, 179, 8), outline=(6, 182, 212), width=2)
        draw.ellipse([eye2[0]-8, eye2[1]-8, eye2[0]+8, eye2[1]+8], fill=(234, 179, 8), outline=(6, 182, 212), width=2)
        draw.ellipse([eye1[0]+1, eye1[1]-1, eye1[0]+3, eye1[1]+1], fill=(255, 255, 255))
        draw.ellipse([eye2[0]+1, eye2[1]-1, eye2[0]+3, eye2[1]+1], fill=(255, 255, 255))

    elif class_type == "insect":
        # Giant Praying Mantis: Triangular Head, Raptorial Forearms & Slender Wings
        # 1. 4 Walking Legs
        for side in [-1, 1]:
            for offset in [0, -35]:
                h_p = (sim.x + cos_a * offset + perp_x * (20 * side), sim.y + sin_a * offset + perp_y * (20 * side))
                knee_p = (h_p[0] + perp_x * (55 * side) - cos_a * 15, h_p[1] + perp_y * (55 * side) - sin_a * 15)
                foot_p = (knee_p[0] + perp_x * (35 * side) + cos_a * 25, knee_p[1] + perp_y * (35 * side) + sin_a * 25)
                draw.line([h_p, knee_p], fill=(74, 110, 40), width=5)
                draw.line([knee_p, foot_p], fill=(132, 204, 22), width=3)
                draw.ellipse([knee_p[0]-3, knee_p[1]-3, knee_p[0]+3, knee_p[1]+3], fill=(234, 179, 8))

        # 2. Slender Elongated Prothorax & Wings
        for i in range(12, 0, -1):
            seg = sim.spine[i]
            half_w = max(10, 28 - i * 1.5)
            draw.ellipse([seg["x"] - half_w, seg["y"] - 10, seg["x"] + half_w, seg["y"] + 10], fill=(24, 45, 18), outline=(132, 204, 22), width=2)

        # 3. Folded Raptorial Strike Arms
        for side in [-1, 1]:
            r_sock = (sim.x + cos_a * 35 + perp_x * (15 * side), sim.y + sin_a * 35 + perp_y * (15 * side))
            femur_tip = (sim.x + cos_a * 75 + perp_x * (28 * side), sim.y + sin_a * 75 + perp_y * (28 * side))
            tibia_tip = (sim.x + cos_a * 55 + perp_x * (10 * side), sim.y + sin_a * 55 + perp_y * (10 * side))
            draw.line([r_sock, femur_tip], fill=(101, 163, 13), width=7)
            draw.line([femur_tip, tibia_tip], fill=(132, 204, 22), width=5)
            draw.ellipse([femur_tip[0]-4, femur_tip[1]-4, femur_tip[0]+4, femur_tip[1]+4], fill=(234, 179, 8))

        # 4. Mobile Triangular Head with Bulging Compound Eyes
        h_tip = (sim.x + cos_a * 58, sim.y + sin_a * 58)
        e_l = (sim.x + cos_a * 40 + perp_x * 24, sim.y + sin_a * 40 + perp_y * 24)
        e_r = (sim.x + cos_a * 40 - perp_x * 24, sim.y + sin_a * 40 - perp_y * 24)
        draw.polygon([h_tip, e_l, e_r], fill=(30, 60, 20), outline=(132, 204, 22), width=2)
        draw.ellipse([e_l[0]-8, e_l[1]-8, e_l[0]+8, e_l[1]+8], fill=(132, 204, 22), outline=(200, 250, 50), width=2)
        draw.ellipse([e_r[0]-8, e_r[1]-8, e_r[0]+8, e_r[1]+8], fill=(132, 204, 22), outline=(200, 250, 50), width=2)

    elif class_type == "cephalopod":
        # Blue-Ringed Octopus: 8 Sinusoidal Undulating Tentacles with Glowing Cyan Rings
        # 1. 8 Independent Multi-Joint Tentacles
        for arm_i in range(8):
            base_ang = (arm_i / 8) * math.pi * 2 + sim.angle
            a_prev = (sim.x + math.cos(base_ang) * 28, sim.y + math.sin(base_ang) * 28)
            wave_f = math.sin(sim_time * 5 + arm_i * 0.75) * 0.5
            for j in range(8):
                ang_j = base_ang + wave_f * ((j + 1) / 8)
                ax = a_prev[0] + math.cos(ang_j) * 18
                ay = a_prev[1] + math.sin(ang_j) * 18
                a_w = max(4, int(18 - j * 1.8))
                draw.line([a_prev, (ax, ay)], fill=(120, 80, 40), width=a_w)
                draw.line([a_prev, (ax, ay)], fill=(180, 130, 70), width=max(2, a_w - 4))
                # Glowing Cyan Blue Rings
                if j in [2, 4, 6]:
                    draw.ellipse([ax-6, ay-6, ax+6, ay+6], fill=(0, 0, 0), outline=(0, 230, 255), width=2)
                    draw.ellipse([ax-2, ay-2, ax+2, ay+2], fill=(0, 230, 255))
                a_prev = (ax, ay)

        # 2. Domed Muscular Mantle & Golden Horizontal Eyes
        draw.ellipse([sim.x - 38, sim.y - 38, sim.x + 38, sim.y + 38], fill=(140, 90, 45), outline=(100, 60, 30), width=3)
        for ring_off in [(-16, -12), (16, -12), (0, 16)]:
            rx, ry = sim.x + ring_off[0], sim.y + ring_off[1]
            draw.ellipse([rx-8, ry-8, rx+8, ry+8], fill=(10, 10, 20), outline=(0, 230, 255), width=2)
            draw.ellipse([rx-3, ry-3, rx+3, ry+3], fill=(0, 230, 255))
        # Eyes
        draw.ellipse([sim.x - 22, sim.y - 18, sim.x - 12, sim.y - 8], fill=(234, 179, 8))
        draw.ellipse([sim.x + 12, sim.y - 18, sim.x + 22, sim.y - 8], fill=(234, 179, 8))
        draw.line([(sim.x - 20, sim.y - 13), (sim.x - 14, sim.y - 13)], fill=(0, 0, 0), width=2)
        draw.line([(sim.x + 14, sim.y - 13), (sim.x + 20, sim.y - 13)], fill=(0, 0, 0), width=2)

    else:
        # Oceanic Manta Ray: Expansive Undulating Pectoral Wing Fins & Cephalic Lobes
        flap_wave = math.sin(sim_time * 3.5) * 26
        # 1. Broad Rhomboid Diamond Wing Body
        w_nose = (sim.x + cos_a * 55, sim.y + sin_a * 55)
        w_left = (sim.x - cos_a * 15 + perp_x * 90, sim.y - sin_a * 15 + perp_y * 90 + flap_wave)
        w_right = (sim.x - cos_a * 15 - perp_x * 90, sim.y - sin_a * 15 - perp_y * 90 - flap_wave)
        w_tail = (sim.x - cos_a * 50, sim.y - sin_a * 50)
        draw.polygon([w_nose, w_left, w_tail, w_right], fill=(14, 28, 48), outline=accent_color, width=3)
        # White dorsal shoulder markings
        draw.polygon([(sim.x + cos_a * 10, sim.y + sin_a * 10),
                      (sim.x - cos_a * 10 + perp_x * 45, sim.y - sin_a * 10 + perp_y * 45 + flap_wave*0.5),
                      (sim.x - cos_a * 25, sim.y - sin_a * 25)], fill=(240, 248, 255))
        draw.polygon([(sim.x + cos_a * 10, sim.y + sin_a * 10),
                      (sim.x - cos_a * 10 - perp_x * 45, sim.y - sin_a * 10 - perp_y * 45 - flap_wave*0.5),
                      (sim.x - cos_a * 25, sim.y - sin_a * 25)], fill=(240, 248, 255))

        # 2. Cephalic Horns at Mouth
        draw.ellipse([w_nose[0] + perp_x * 16 - 6, w_nose[1] + perp_y * 16 - 6, w_nose[0] + perp_x * 16 + 6, w_nose[1] + perp_y * 16 + 6], fill=(14, 28, 48), outline=accent_color, width=2)
        draw.ellipse([w_nose[0] - perp_x * 16 - 6, w_nose[1] - perp_y * 16 - 6, w_nose[0] - perp_x * 16 + 6, w_nose[1] - perp_y * 16 + 6], fill=(14, 28, 48), outline=accent_color, width=2)

        # 3. Trailing Whip Tail
        t_prev = w_tail
        for i in range(12):
            tx = t_prev[0] - cos_a * 14 + math.sin(sim_time * 4 + i * 0.4) * 5
            ty = t_prev[1] - sin_a * 14 + math.cos(sim_time * 4 + i * 0.4) * 5
            draw.line([t_prev, (tx, ty)], fill=(14, 28, 48), width=max(2, 6 - i // 2))
            t_prev = (tx, ty)

    # ─────────────────────────────────────────────────────────────
    # LOWER SECTION: macOS DARK CODE WINDOW (MOBILE OPTIMIZED)
    # ─────────────────────────────────────────────────────────────
    card_w, card_h = 920, 980
    card_x = (WIDTH - card_w) // 2
    card_y = 840

    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=22, fill=(12, 18, 25), outline=(28, 38, 50), width=2)

    title_h = 62
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + title_h], radius=22, fill=(8, 13, 19))
    draw.rectangle([card_x, card_y + 30, card_x + card_w, card_y + title_h], fill=(8, 13, 19))

    draw.ellipse([card_x + 28, card_y + 24, card_x + 44, card_y + 40], fill=(255, 95, 86))
    draw.ellipse([card_x + 54, card_y + 24, card_x + 70, card_y + 40], fill=(255, 189, 46))
    draw.ellipse([card_x + 80, card_y + 24, card_x + 96, card_y + 40], fill=(39, 201, 63))

    draw.rounded_rectangle([card_x + 135, card_y + 14, card_x + 168, card_y + 48], radius=5, fill=(247, 223, 30))
    draw.text((card_x + 140, card_y + 18), "JS", font=get_font(18, bold=True), fill=(20, 20, 20))
    draw.text((card_x + 180, card_y + 19), species["file_name"], font=get_font(24, bold=True), fill=(160, 175, 195))

    all_lines = species["code_lines"]
    total_lines = len(all_lines)
    
    line_h = 52
    code_font = get_font(28, mono=True, bold=True)
    line_num_font = get_font(24, mono=True)
    
    visible_lines = int((card_h - title_h - 40) / line_h)
    max_scroll_lines = max(0, total_lines - visible_lines)
    scroll_factor = 0.5 - math.cos(progress * math.pi) / 2
    curr_scroll = scroll_factor * max_scroll_lines

    start_line_idx = int(curr_scroll)
    line_pixel_offset = (curr_scroll - start_line_idx) * line_h

    code_box_top = card_y + title_h + 18
    code_box_bottom = card_y + card_h - 24

    for idx in range(visible_lines + 2):
        actual_line_idx = start_line_idx + idx
        if actual_line_idx >= total_lines:
            break
        
        line_text = all_lines[actual_line_idx]
        y_pos = code_box_top + (idx * line_h) - int(line_pixel_offset)

        if y_pos < code_box_top - 16 or y_pos > code_box_bottom:
            continue

        draw.text((card_x + 36, y_pos), f"{actual_line_idx + 1:2d}", font=line_num_font, fill=(80, 100, 125))

        indent_x = card_x + 98
        _draw_highlighted_js_line(draw, indent_x, y_pos, line_text, code_font)

    # Bottom Progress Bar
    bar_w = 920
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 1855
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 12], radius=6, fill=(35, 46, 62))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + 12], radius=6, fill=accent_color)

    return img.convert("RGB")
