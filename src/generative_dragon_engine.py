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
    sp_id = name.lower()
    is_lion     = "lion" in sp_id
    is_tiger    = "tiger" in sp_id
    is_giraffe  = "giraffe" in sp_id
    is_rhino    = "rhino" in sp_id
    is_elephant = "elephant" in sp_id
    is_bear     = "bear" in sp_id or "panda" in sp_id
    is_shark    = "shark" in sp_id
    is_spider   = "spider" in sp_id or "tarantula" in sp_id
    is_cobra    = "cobra" in sp_id

    if is_lion:
        return [
            f"// ─── {name} ───",
            "const rig = new ApexFelineRig({",
            "  maneDensity: 140,",
            "  clawsRetractable: true",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const target = getPointer();",
            "",
            "  // Volumetric Feline Mane",
            "  volumetricMane(ctx, rig.mane, 180);",
            "  solveProwlGait(rig.limbs, target);",
            "  felineHeadIK(ctx, rig.skull);",
            "  wagTuftedTail(ctx, rig.tail);",
            "};"
        ]
    elif is_tiger:
        return [
            f"// ─── {name} ───",
            "const rig = new TigerRig({",
            "  stripeCount: 42,",
            "  musculature: 1.6",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const p = getPointer();",
            "",
            "  // Undulating Tiger Stripes",
            "  renderTigerStripes(ctx, rig.spine);",
            "  solveQuadrupedIK(rig.legs, p);",
            "  renderFelineMuzzle(ctx, rig.head);",
            "};"
        ]
    elif is_giraffe:
        return [
            f"// ─── {name} ───",
            "const rig = new GiraffeRig({",
            "  neckVertebrae: 14,",
            "  ossicones: 2",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const p = getPointer();",
            "",
            "  // Elongated Neck Kinematics",
            "  solveLongNeckIK(rig.neck, p);",
            "  renderTessellatedPatches(ctx, rig);",
            "  renderOssicones(ctx, rig.head);",
            "};"
        ]
    elif is_rhino:
        return [
            f"// ─── {name} ───",
            "const rig = new RhinocerosRig({",
            "  dermalArmorPlates: 3,",
            "  horns: 2",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const p = getPointer();",
            "",
            "  // Armored Plate Folds",
            "  renderNasalHorns(ctx, rig);",
            "  dermalPlateFolds(ctx, rig.torso);",
            "  heavyStompIK(rig.limbs, p);",
            "};"
        ]
    elif is_elephant:
        return [
            f"// ─── {name} ───",
            "const rig = new ElephantRig({",
            "  trunkSegments: 16,",
            "  tuskLength: 45",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const p = getPointer();",
            "",
            "  // Prehensile Trunk Wave",
            "  undulateTrunk(rig.trunk, p);",
            "  renderSweepingFanEars(ctx, rig);",
            "  pillarLegIK(rig.limbs);",
            "};"
        ]
    elif is_bear:
        return [
            f"// ─── {name} ───",
            "const rig = new UrsineRig({",
            "  muscleMass: 1.8,",
            "  clawCurve: 22",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const p = getPointer();",
            "",
            "  // Heavy Shag Coat",
            "  renderShaggyCoat(ctx, rig);",
            "  bearPawSlashIK(rig.forelimbs, p);",
            "  stubbyTailWag(rig.tail);",
            "};"
        ]
    elif is_shark:
        return [
            f"// ─── {name} ───",
            "const rig = new SharkHydroRig({",
            "  dorsalFinHeight: 42,",
            "  gillSlits: 5",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  rig.fuselage.follow(pointer, 0.06);",
            "",
            "  // Heterocercal Caudal Thrust",
            "  heterocercalThrust(rig.tail, time);",
            "  renderDorsalFin(ctx, rig.fin);",
            "  lateralLineSensor(ctx, rig);",
            "};"
        ]
    elif is_spider:
        return [
            f"// ─── {name} ───",
            "const rig = new SpiderWebRig({",
            "  abdomenBulbous: true,",
            "  eyes: 8",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const p = getPointer();",
            "",
            "  // 8-Leg Alternating Gait",
            "  tripodGaitStep(rig.legs, p, time);",
            "  renderOpisthosoma(ctx, rig);",
            "  renderCheliceraeFangs(ctx, rig);",
            "};"
        ]
    elif is_cobra:
        return [
            f"// ─── {name} ───",
            "const rig = new CobraSerpentRig({",
            "  hoodFlaring: 0.85,",
            "  vertebrae: 48",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  rig.head.follow(pointer, 0.08);",
            "",
            "  // Flared Cobra Hood",
            "  flareCobraHood(rig.neck, 0.85);",
            "  slitherTrajectory(rig.spine, time);",
            "  flickForkedTongue(ctx, rig.head);",
            "};"
        ]
    elif class_type == "quadruped":
        return [
            f"// ─── {name} ───",
            "const rig = new QuadrupedRig({",
            "  spineSegs: 18,",
            "  limbs: 4",
            "});",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  const p = getPointer();",
            "  solveForelimbIK(rig.lArm, p.fl, 52, -1);",
            "  solveForelimbIK(rig.rArm, p.fr, 52,  1);",
            "  solveHindlimbIK(rig.lLeg, p.hl, 48, -1);",
            "  solveHindlimbIK(rig.rLeg, p.hr, 48,  1);",
            "  renderTorso(ctx, rig.spine);",
            "  renderHead(ctx, rig);",
            "};"
        ]
    elif class_type == "arachnid":
        return [
            f"// ─── {name} ───",
            "const rig = new ArachnidRig({ segments: 38, legs: 8 });",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  solvePincerIK(rig.lArm, pointer, 54, -1);",
            "  solvePincerIK(rig.rArm, pointer, 54,  1);",
            "  stepLegs(rig.legs, time);",
            "  curlTail(rig.tail, time * 2);",
            "  renderTelson(ctx, rig.tail);",
            "};"
        ]
    elif class_type == "serpent":
        return [
            f"// ─── {name} ───",
            "const spine = new SnakeSpine({ vertebrae: 48, spacing: 14 });",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  spine.head.follow(pointer, 0.08);",
            "  for (let i = 1; i < 48; i++) {",
            "    const wave = Math.sin(time * 4.5 + i * 0.35) * 6;",
            "    spine.get(i).update(spine.get(i-1), 14, wave);",
            "  }",
            "  renderViperHead(ctx, spine.head);",
            "  flickTongue(ctx, spine.head, time);",
            "};"
        ]
    elif class_type == "reptile":
        return [
            f"// ─── {name} ───",
            "const rig = new ReptileRig({ vertebrae: 26, limbs: 4 });",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  rig.head.follow(pointer);",
            "  renderArmoredCarapace(ctx, rig.spine);",
            "  solveReptileClawIK(rig.limbs, pointer);",
            "  renderReptileHead(ctx, rig);",
            "};"
        ]
    elif class_type == "crustacean":
        return [
            f"// ─── {name} ───",
            "const rig = new CrustaceanRig({ segments: 24, dactylClubs: 2 });",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  solveClubIK(rig.leftClub, pointer, -1);",
            "  solveClubIK(rig.rightClub, pointer, 1);",
            "  ripplePleopods(rig, time);",
            "  renderCarapace(ctx, rig);",
            "};"
        ]
    elif class_type == "insect":
        return [
            f"// ─── {name} ───",
            "const rig = new InsectRig({ thorax: 14, raptorialArms: 2 });",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  solveRaptorialIK(rig.lArm, pointer, -1);",
            "  solveRaptorialIK(rig.rArm, pointer, 1);",
            "  stepInsectLegs(rig, time);",
            "  renderTriangularHead(ctx, rig);",
            "};"
        ]
    elif class_type == "cephalopod":
        return [
            f"// ─── {name} ───",
            "const rig = new CephalopodRig({ tentacles: 8, jointsPerArm: 16 });",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  rig.mantle.follow(pointer);",
            "  for (let i = 0; i < 8; i++) {",
            "    undulateTentacle(rig.arms[i], i, time);",
            "    renderGlowingSuctionRings(ctx, rig.arms[i]);",
            "  }",
            "  pulseChromatophores(ctx, rig.mantle);",
            "};"
        ]
    else:  # aquatic
        return [
            f"// ─── {name} ───",
            "const rig = new AquaticRig({ wingspan: 36, ribCount: 22 });",
            "",
            "function animate() {",
            "  requestAnimationFrame(animate);",
            "  rig.head.follow(pointer, 0.05);",
            "  const flap = Math.sin(time * 3) * 0.4;",
            "  undulatePectoralFin(rig.lWing, flap, -1);",
            "  undulatePectoralFin(rig.rWing, flap,  1);",
            "  renderAquaticBody(ctx, rig);",
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

    hooks = [
        f"I Built an Interactive {name} with Vanilla JS IK Physics 🤯 #Shorts #Coding",
        f"Realistic {name} in JavaScript Canvas (60 FPS Simulation) ✨ #Shorts #WebDev",
        f"How to Code an Interactive {name} Cursor in JavaScript ⚡ #Shorts #Programming",
        f"Coding an Interactive {name} with Joint Kinematics ✨ #Shorts #Coding",
        f"I Simulated a Realistic {name} in 100% Pure JavaScript 🤯 #Shorts #Tech",
        f"Interactive {name} Cursor in Vanilla JS ✨ #Shorts #CreativeCoding"
    ]
    yt_title = hooks[animal_id % len(hooks)]

    return {
        "id": spec_id,
        "name": name,
        "scientific": scientific,
        "class_type": class_type,
        "file_name": file_name,
        "accent": accent,
        "code_lines": code_lines,
        "animal_id": animal_id,
        "yt_title": yt_title,
        "yt_desc": f"✨ Realistic {name} ({scientific}) with biologically accurate joint kinematics in Vanilla JavaScript!\n\n#JavaScript #WebDev #Shorts #Coding #Tech #Programming #Canvas"
    }

class MasterSimulator:
    def __init__(self, cx: float, cy: float, rx: float, ry: float, seed: int = 0, class_type: str = "quadruped"):
        self.class_type = class_type
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.seed = seed
        self.x = cx
        self.y = cy
        self.angle = 0.0
        self.speed = 0.0
        self.spine = [{"x": cx - i * 28, "y": cy, "angle": 0.0} for i in range(20)]
        
        # Varied movement Lissajous parameters based on seed
        self.f1 = 0.65 + ((seed % 7) - 3) * 0.035
        self.f2 = 1.35 + (((seed >> 3) % 7) - 3) * 0.05
        self.f3 = 0.95 + (((seed >> 6) % 7) - 3) * 0.04
        self.f4 = 1.95 + (((seed >> 9) % 7) - 3) * 0.06
        self.p1 = ((seed >> 2) % 10) * 0.628
        self.p2 = ((seed >> 5) % 10) * 0.628

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
        t = sim_time
        target_x = self.cx + math.cos(t * self.f1 + self.p1) * (self.rx * 0.85) + math.sin(t * self.f2 + self.p2) * (self.rx * 0.20)
        target_y = self.cy + math.sin(t * self.f3 + self.p1) * (self.ry * 0.80) + math.cos(t * self.f4 + self.p2) * (self.ry * 0.18)

        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        target_ang = math.atan2(dy, dx)

        diff = target_ang - self.angle
        while diff < -math.pi: diff += math.pi * 2
        while diff > math.pi: diff -= math.pi * 2

        # Dynamic motion behavior per taxonomy class
        if self.class_type == "aquatic":
            self.angle += diff * 0.035
            target_spd = min(2.8, dist * 0.042)
            self.speed += (target_spd - self.speed) * 0.05
        elif self.class_type == "insect":
            self.angle += diff * 0.09
            is_burst = (math.sin(t * 8.0) > 0.15)
            target_spd = min(4.2, dist * 0.08) if is_burst else 0.6
            self.speed += (target_spd - self.speed) * 0.12
        elif self.class_type == "arachnid":
            self.angle += diff * 0.07
            is_scuttle = (int(t * 2.8) % 3) != 0
            target_spd = min(3.2, dist * 0.06) if is_scuttle else 0.0
            self.speed += (target_spd - self.speed) * 0.10
        elif self.class_type == "serpent":
            self.angle += diff * 0.05
            slither_osc = math.sin(t * 7.5) * 16.0
            self.speed += (min(2.6, dist * 0.038) - self.speed) * 0.06
        else: # quadruped / default
            self.angle += diff * 0.045
            target_spd = min(2.5, dist * 0.035)
            self.speed += (target_spd - self.speed) * 0.06

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
            s_dist = 28 - (i / len(self.spine)) * 5
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



ANIMAL_THEMES = {
    "OCEAN": {
        "bg": (6, 16, 32),
        "grad_center": (14, 52, 90),
        "canvas_fill": (10, 26, 48),
        "canvas_border": (0, 210, 255),
        "card_fill": (6, 14, 28),
        "card_header": (4, 10, 20),
        "card_border": (18, 45, 75),
        "badge": "⚡ [WebGL] Hydrodynamic Verlet Shaders • 60 FPS IK",
        "badge_color": (56, 189, 248),
        "cursor_color": (0, 230, 255),
    },
    "SAVANNA": {
        "bg": (28, 14, 8),
        "grad_center": (80, 36, 14),
        "canvas_fill": (245, 236, 222),
        "canvas_border": (217, 119, 6),
        "card_fill": (22, 14, 10),
        "card_header": (16, 10, 6),
        "card_border": (55, 32, 18),
        "badge": "⚡ [JS] Quadruped Inverse Kinematics • 60 FPS",
        "badge_color": (251, 191, 36),
        "cursor_color": (239, 68, 68),
    },
    "JUNGLE": {
        "bg": (8, 26, 14),
        "grad_center": (18, 70, 36),
        "canvas_fill": (232, 242, 234),
        "canvas_border": (34, 197, 94),
        "card_fill": (10, 22, 14),
        "card_header": (6, 16, 10),
        "card_border": (24, 50, 30),
        "badge": "⚡ [Canvas] Sinuous Curvature & Strike IK • 60 FPS",
        "badge_color": (74, 222, 128),
        "cursor_color": (234, 179, 8),
    },
    "VOLCANIC": {
        "bg": (20, 10, 14),
        "grad_center": (75, 20, 18),
        "canvas_fill": (28, 16, 20),
        "canvas_border": (249, 115, 22),
        "card_fill": (18, 10, 12),
        "card_header": (12, 6, 8),
        "card_border": (50, 22, 25),
        "badge": "⚡ [GLSL] Segmented Exoskeleton Shaders • 60 FPS",
        "badge_color": (251, 146, 60),
        "cursor_color": (239, 68, 68),
    },
    "CYBER": {
        "bg": (16, 8, 28),
        "grad_center": (60, 20, 95),
        "canvas_fill": (22, 12, 36),
        "canvas_border": (217, 70, 239),
        "card_fill": (14, 6, 24),
        "card_header": (10, 4, 18),
        "card_border": (45, 18, 70),
        "badge": "⚡ [Physics] Multi-Joint Biological Simulation • 60 FPS",
        "badge_color": (232, 121, 249),
        "cursor_color": (244, 63, 94),
    },
    "ARCTIC": {
        "bg": (10, 22, 36),
        "grad_center": (26, 56, 90),
        "canvas_fill": (238, 246, 255),
        "canvas_border": (56, 189, 248),
        "card_fill": (8, 18, 30),
        "card_header": (5, 12, 22),
        "card_border": (20, 42, 68),
        "badge": "⚡ [Three.js] Sub-Zero Physics & Skeletal IK • 60 FPS",
        "badge_color": (125, 211, 252),
        "cursor_color": (14, 165, 233),
    }
}

def pick_animal_theme(species: dict) -> dict:
    class_type = species.get("class_type", "quadruped").lower()
    name = species.get("name", "").lower()
    
    if class_type in ("aquatic", "cephalopod") or any(k in name for k in ("shark", "whale", "fish", "eel", "manta", "squid", "octopus")):
        return ANIMAL_THEMES["OCEAN"]
    elif class_type in ("serpent", "insect") or any(k in name for k in ("mantis", "wasp", "tree", "chameleon", "frog", "viper")):
        return ANIMAL_THEMES["JUNGLE"]
    elif class_type in ("arachnid", "crustacean") or any(k in name for k in ("scorpion", "spider", "crab", "lobster", "lava")):
        return ANIMAL_THEMES["VOLCANIC"]
    elif any(k in name for k in ("polar", "snow", "arctic", "glacier", "frost", "white")):
        return ANIMAL_THEMES["ARCTIC"]
    elif any(k in name for k in ("cyber", "quantum", "neon", "matrix", "volt")):
        return ANIMAL_THEMES["CYBER"]
    else:
        return ANIMAL_THEMES["SAVANNA"]

_SIM_CACHE = {}

def render_generative_frame(species: dict, frame_idx: int, total_frames: int) -> Image.Image:
    progress = frame_idx / total_frames
    sim_time = (frame_idx / FPS) * 0.4

    theme = pick_animal_theme(species)
    img = Image.new("RGBA", (WIDTH, HEIGHT), theme["bg"] + (255,))
    draw = ImageDraw.Draw(img)

    grad = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grad)
    g_draw.rectangle([0, 0, WIDTH, HEIGHT], fill=theme["bg"] + (255,))
    g_draw.ellipse([WIDTH//2 - 500, HEIGHT//2 - 600, WIDTH//2 + 500, HEIGHT//2 + 600], fill=theme["grad_center"] + (200,))
    img = Image.alpha_composite(img, grad.filter(ImageFilter.GaussianBlur(80)))
    draw = ImageDraw.Draw(img)

    # 1. Top Header: ANIMAL NAME & TECH BADGE
    header_h = 135
    draw.rectangle([0, 0, WIDTH, header_h], fill=theme["card_header"] + (255,))
    draw.line([(0, header_h), (WIDTH, header_h)], fill=theme["card_border"], width=2)

    name_font = get_font(52, bold=True)
    draw.text((WIDTH // 2, 24), species["name"], font=name_font, fill=(255, 255, 255), anchor="mt")

    badge_font = get_font(20, bold=True, mono=True)
    draw.text((WIDTH // 2, 88), theme["badge"], font=badge_font, fill=theme["badge_color"], anchor="mt")

    # 2. Upper Section: Framed Creature Display Window
    box_w, box_h = 920, 640
    box_x = (WIDTH - box_w) // 2
    box_y = 165

    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rectangle([box_x - 12, box_y - 12, box_x + box_w + 12, box_y + box_h + 12], fill=(0, 0, 0, 160))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(25)))
    draw = ImageDraw.Draw(img)

    draw.rectangle([box_x - 12, box_y - 12, box_x + box_w + 12, box_y + box_h + 12], fill=theme["canvas_border"], outline=theme["card_border"], width=2)
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=theme["canvas_fill"])

    cb_x = box_x + box_w // 2
    cb_y = box_y + box_h // 2
    rad_x = box_w * 0.33
    rad_y = box_h * 0.30

    sp_id = species.get("id", "golden_shepherd_dog")
    animal_id = species.get("animal_id", 0)
    class_type = species.get("class_type", "quadruped")
    accent_color = species.get("accent", (245, 158, 11))
    seed = (animal_id * 10007) & 0xFFFFFF

    sim_key = f"{sp_id}_{animal_id}_{total_frames}"
    if frame_idx == 0 or sim_key not in _SIM_CACHE:
        _SIM_CACHE[sim_key] = MasterSimulator(cb_x, cb_y, rad_x, rad_y, seed=seed, class_type=class_type)
    
    sim = _SIM_CACHE[sim_key]
    sim.update(sim_time)

    cos_a = math.cos(sim.angle)
    sin_a = math.sin(sim.angle)
    perp_x = -sin_a
    perp_y =  cos_a

    # ─────────────────────────────────────────────────────────────
    # BIOLOGICAL ANIMAL RENDERING: 8 TAXONOMIC ANIMAL CLASSES
    # ─────────────────────────────────────────────────────────────
    # Glowing Interactive Cursor Target Indicator
    t_c = sim_time
    tgt_x = sim.cx + math.cos(t_c * sim.f1 + sim.p1) * (rad_x * 0.85) + math.sin(t_c * sim.f2 + sim.p2) * (rad_x * 0.20)
    tgt_y = sim.cy + math.sin(t_c * sim.f3 + sim.p1) * (rad_y * 0.80) + math.cos(t_c * sim.f4 + sim.p2) * (rad_y * 0.18)

    pulse_r = 10 + math.sin(sim_time * 8) * 3
    draw.ellipse([tgt_x - pulse_r, tgt_y - pulse_r, tgt_x + pulse_r, tgt_y + pulse_r], outline=(239, 68, 68), width=2)
    ripple_r = 14 + (frame_idx % 35) * 0.85
    draw.ellipse([tgt_x - ripple_r, tgt_y - ripple_r, tgt_x + ripple_r, tgt_y + ripple_r], outline=(251, 113, 133), width=1)
    draw.ellipse([tgt_x - 4, tgt_y - 4, tgt_x + 4, tgt_y + 4], fill=(239, 68, 68))


    # ── Try NEW bio bone renderer first (realistic skeleton + muscle + skin) ──
    _bio_rendered = False
    try:
        from src.bio_bone_renderer import (
            draw_bio_quadruped, draw_bio_serpent, draw_bio_arachnid
        )
        if class_type in ("quadruped",) or any(k in sp_id for k in ("dog","wolf","tiger","lion","cat","leopard","cheetah","bear","fox","deer","horse","rabbit","hyena","panda")):
            draw_bio_quadruped(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
            _bio_rendered = True
        elif class_type == "serpent" or any(k in sp_id for k in ("snake","cobra","viper","boa","python","mamba")):
            draw_bio_serpent(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
            _bio_rendered = True
        elif class_type == "arachnid" or any(k in sp_id for k in ("spider","scorpion","tarantula")):
            draw_bio_arachnid(draw, sim, species, sim_time, cos_a, sin_a, perp_x, perp_y)
            _bio_rendered = True
    except ImportError:
        pass  # bio_bone_renderer not available yet — fall through to legacy renderer
    except Exception as _bio_err:
        print(f"  ⚠ Bio renderer error: {_bio_err} — falling back to legacy renderer")

    if not _bio_rendered and (class_type == "quadruped" or "dog" in sp_id or "wolf" in sp_id or "tiger" in sp_id):
        # ── Research-driven colors (from Wikipedia/web anatomy search) ──
        # Falls back to Golden Shepherd defaults if no research data available
        fur_dark   = tuple(species.get("fur_dark",      [120, 60,  5]))
        fur_mid    = tuple(species.get("fur_mid",       [190, 110, 20]))
        fur_gold   = tuple(species.get("fur_gold",      [230, 160, 45]))
        fur_light  = tuple(species.get("fur_light",     [255, 210, 100]))
        fur_cream  = tuple(species.get("fur_cream",     [255, 235, 170]))
        # Eye/nose colors derived from fur_dark and accent
        nose_black = (max(10, fur_dark[0]//3), max(8, fur_dark[1]//4), max(5, fur_dark[2]//5))
        eye_amber  = tuple(min(255, int(c * 0.65)) for c in fur_mid)
        joint_col  = tuple(int((a + b) // 2) for a, b in zip(fur_mid, fur_gold))

        def draw_limb(p1, p2, base_w, dark_col, mid_col):
            dx = p2[0] - p1[0]; dy = p2[1] - p1[1]
            ln = math.hypot(dx, dy)
            if ln < 1: return
            nx = -dy / ln; ny = dx / ln
            draw.line([p1, p2], fill=dark_col, width=base_w + 6)
            draw.line([p1, p2], fill=mid_col, width=base_w)
            hi = (min(255, mid_col[0]+45), min(255, mid_col[1]+35), min(255, mid_col[2]+20))
            draw.line([(p1[0]+nx*3, p1[1]+ny*3), (p2[0]+nx*3, p2[1]+ny*3)],
                      fill=hi, width=max(2, base_w // 3))

        # ── A. HINDLEGS (behind body) ──
        for leg in [l for l in sim.legs4 if not l["is_front"]]:
            paw_pos = (leg["cur"][0], leg["cur"][1])
            sock = leg["socket"]
            side = leg["side"]
            thigh_end = (sock[0] + cos_a * 36 + perp_x * (24 * side),
                         sock[1] + sin_a * 36 + perp_y * (24 * side))
            draw_limb(sock, thigh_end, 26, fur_dark, fur_mid)
            shin_end = (thigh_end[0] - cos_a * 34 + perp_x * (16 * side),
                        thigh_end[1] - sin_a * 34 + perp_y * (16 * side))
            draw_limb(thigh_end, shin_end, 20, fur_dark, fur_gold)
            draw.ellipse([thigh_end[0]-11, thigh_end[1]-11, thigh_end[0]+11, thigh_end[1]+11],
                         fill=joint_col, outline=fur_dark, width=2)
            hock = (shin_end[0] - cos_a * 10 + perp_x * (12 * side),
                    shin_end[1] - sin_a * 10 + perp_y * (12 * side))
            draw_limb(shin_end, hock, 16, fur_dark, fur_mid)
            draw.ellipse([hock[0]-7, hock[1]-7, hock[0]+7, hock[1]+7],
                         fill=fur_dark, outline=fur_mid, width=1)
            draw_limb(hock, paw_pos, 14, fur_dark, fur_mid)
            draw.ellipse([paw_pos[0]-15, paw_pos[1]-10, paw_pos[0]+15, paw_pos[1]+10],
                         fill=nose_black, outline=fur_dark, width=2)
            for t_off in [-6, -2, 2, 6]:
                bx = paw_pos[0] + cos_a * 12 + perp_x * t_off
                by = paw_pos[1] + sin_a * 12 + perp_y * t_off
                draw.ellipse([bx-4, by-4, bx+4, by+4], fill=(35, 25, 15))
                draw.line([(bx, by), (bx + cos_a * 6, by + sin_a * 6)], fill=(10, 8, 5), width=2)

        # ── C. FORELEGS (drawn under body as well) ──
        for leg in [l for l in sim.legs4 if l["is_front"]]:
            paw_pos = (leg["cur"][0], leg["cur"][1])
            sock = leg["socket"]
            side = leg["side"]
            _, elbow, _ = solve_forelimb_ik(sock, paw_pos, leg["l1"], leg["l2"], side)
            draw_limb(sock, elbow, 24, fur_dark, fur_mid)
            draw.ellipse([elbow[0]-11, elbow[1]-11, elbow[0]+11, elbow[1]+11],
                         fill=joint_col, outline=fur_dark, width=2)
            draw_limb(elbow, paw_pos, 18, fur_dark, fur_gold)
            draw.ellipse([paw_pos[0]-15, paw_pos[1]-10, paw_pos[0]+15, paw_pos[1]+10],
                         fill=nose_black, outline=fur_dark, width=2)
            for t_off in [-6, -2, 2, 6]:
                bx = paw_pos[0] + cos_a * 12 + perp_x * t_off
                by = paw_pos[1] + sin_a * 12 + perp_y * t_off
                draw.ellipse([bx-4, by-4, bx+4, by+4], fill=(35, 25, 15))
                draw.line([(bx, by), (bx + cos_a * 6, by + sin_a * 6)], fill=(10, 8, 5), width=2)

        # ── B. ORGANIC BODY silhouette ──
        spine_pts = [(seg["x"], seg["y"]) for seg in sim.spine[:16]]
        left_out, right_out = [], []
        for i, seg in enumerate(sim.spine[:16]):
            s_px = -math.sin(seg["angle"]); s_py = math.cos(seg["angle"])
            body_widths = [28, 36, 46, 54, 52, 50, 48, 44, 40, 44, 48, 44, 36, 28, 20, 14]
            hw = max(10, body_widths[i] if i < len(body_widths) else 12)
            left_out.append((seg["x"] + s_px * (hw + 4), seg["y"] + s_py * (hw + 4)))
            right_out.append((seg["x"] - s_px * (hw + 4), seg["y"] - s_py * (hw + 4)))

        # Drop shadow
        shadow_pts = [(x+5, y+5) for x,y in left_out] + list(reversed([(x+5, y+5) for x,y in right_out]))
        if len(shadow_pts) >= 3: draw.polygon(shadow_pts, fill=(60, 30, 5))

        # Outer fur body
        body_poly = left_out + list(reversed(right_out))
        if len(body_poly) >= 3:
            draw.polygon(body_poly, fill=fur_mid, outline=fur_dark, width=3)

        # Mid-tone inset layer
        mid_poly = [(x*0.45 + spine_pts[min(i, len(spine_pts)-1)][0]*0.55,
                     y*0.45 + spine_pts[min(i, len(spine_pts)-1)][1]*0.55)
                    for i, (x, y) in enumerate(left_out[:14])] + \
                   list(reversed([(x*0.45 + spine_pts[min(i, len(spine_pts)-1)][0]*0.55,
                                   y*0.45 + spine_pts[min(i, len(spine_pts)-1)][1]*0.55)
                                  for i, (x, y) in enumerate(right_out[:14])]))
        if len(mid_poly) >= 3: draw.polygon(mid_poly, fill=fur_gold)

        # Dorsal highlight stripe
        for i in range(len(spine_pts) - 1):
            draw.line([spine_pts[i], spine_pts[i+1]], fill=fur_light, width=4)
            draw.line([spine_pts[i], spine_pts[i+1]], fill=fur_cream, width=2)

        # Belly cream patch
        belly_pts = [(sim.spine[i]["x"] + math.cos(sim.spine[i]["angle"]) * 10,
                      sim.spine[i]["y"] + math.sin(sim.spine[i]["angle"]) * 10) for i in range(4, 11)]
        if len(belly_pts) >= 3: draw.polygon(belly_pts, fill=fur_cream)

        # ── D. WAGGING PLUME TAIL ──
        tail_prev = spine_pts[-1]
        wag = math.sin(sim_time * 7.0) * 0.65
        for i in range(12):
            frac = (i + 1) / 12
            t_ang = sim.angle + math.pi + wag * frac * frac
            seg_len = 22 - i * 1.2
            tx = tail_prev[0] + math.cos(t_ang) * seg_len
            ty = tail_prev[1] + math.sin(t_ang) * seg_len
            w = max(5, int(24 - i * 1.6))
            draw.line([tail_prev, (tx, ty)], fill=fur_dark, width=w + 4)
            draw.line([tail_prev, (tx, ty)], fill=fur_gold, width=w)
            draw.line([tail_prev, (tx, ty)], fill=fur_cream, width=max(2, w - 6))
            tail_prev = (tx, ty)
        draw.ellipse([tail_prev[0]-8, tail_prev[1]-8, tail_prev[0]+8, tail_prev[1]+8], fill=fur_cream)

        # ── E. REALISTIC CANINE HEAD ──
        hx = sim.x + cos_a * 44
        hy = sim.y + sin_a * 44

        # Skull
        draw.ellipse([hx-28, hy-28, hx+28, hy+28], fill=fur_mid, outline=fur_dark, width=3)
        draw.ellipse([hx+cos_a*4-12, hy+sin_a*4-12, hx+cos_a*4+12, hy+sin_a*4+12], fill=fur_gold)
        draw.ellipse([hx+cos_a*6-6, hy+sin_a*6-6, hx+cos_a*6+6, hy+sin_a*6+6], fill=fur_light)

        # Drop ears
        ear_l = (hx - cos_a * 16 + perp_x * 28, hy - sin_a * 16 + perp_y * 28)
        ear_tip_l = (ear_l[0] - cos_a * 32 + perp_x * 14, ear_l[1] - sin_a * 32 + perp_y * 14)
        ear_base_l = (hx + cos_a * 4 + perp_x * 24, hy + sin_a * 4 + perp_y * 24)
        ear_r = (hx - cos_a * 16 - perp_x * 28, hy - sin_a * 16 - perp_y * 28)
        ear_tip_r = (ear_r[0] - cos_a * 32 - perp_x * 14, ear_r[1] - sin_a * 32 - perp_y * 14)
        ear_base_r = (hx + cos_a * 4 - perp_x * 24, hy + sin_a * 4 - perp_y * 24)
        draw.polygon([ear_base_l, ear_l, ear_tip_l], fill=fur_dark, outline=fur_dark, width=2)
        draw.polygon([ear_base_r, ear_r, ear_tip_r], fill=fur_dark, outline=fur_dark, width=2)
        inner_l_tip = (ear_l[0] + cos_a * 8 - perp_x * 5, ear_l[1] + sin_a * 8 - perp_y * 5)
        inner_r_tip = (ear_r[0] + cos_a * 8 + perp_x * 5, ear_r[1] + sin_a * 8 + perp_y * 5)
        draw.polygon([(hx + perp_x * 12, hy + perp_y * 12), ear_l, inner_l_tip], fill=(210, 130, 140))
        draw.polygon([(hx - perp_x * 12, hy - perp_y * 12), ear_r, inner_r_tip], fill=(210, 130, 140))

        # Muzzle ellipse
        snout_cx = hx + cos_a * 36; snout_cy = hy + sin_a * 36
        draw.ellipse([snout_cx-18, snout_cy-13, snout_cx+18, snout_cy+13], fill=fur_cream, outline=fur_mid, width=2)

        # Nose (wet black)
        nose_cx = snout_cx + cos_a * 14; nose_cy = snout_cy + sin_a * 14
        draw.ellipse([nose_cx-9, nose_cy-7, nose_cx+9, nose_cy+7], fill=nose_black, outline=(40, 35, 30), width=2)
        draw.ellipse([nose_cx+cos_a*2-3, nose_cy+sin_a*2-2, nose_cx+cos_a*2+3, nose_cy+sin_a*2+2], fill=(80, 80, 80))
        draw.ellipse([nose_cx+perp_x*4-2, nose_cy+perp_y*4-2, nose_cx+perp_x*4+2, nose_cy+perp_y*4+2], fill=(10, 8, 5))
        draw.ellipse([nose_cx-perp_x*4-2, nose_cy-perp_y*4-2, nose_cx-perp_x*4+2, nose_cy-perp_y*4+2], fill=(10, 8, 5))

        # Panting tongue
        tongue_phase = math.sin(sim_time * 1.5) * 0.3 + 0.7
        if tongue_phase > 0.4:
            t_len = 16 * tongue_phase
            t_base = (snout_cx + cos_a * 2, snout_cy + sin_a * 2)
            t_tip = (t_base[0] + cos_a * t_len, t_base[1] + sin_a * t_len)
            draw.line([t_base, t_tip], fill=(230, 80, 100), width=10)
            draw.ellipse([t_tip[0]-5, t_tip[1]-5, t_tip[0]+5, t_tip[1]+5], fill=(220, 70, 90))
            draw.line([t_base, t_tip], fill=(200, 60, 80), width=2)

        # Eyes with iris + pupil + highlight
        eye_l = (hx + cos_a * 10 + perp_x * 17, hy + sin_a * 10 + perp_y * 17)
        eye_r = (hx + cos_a * 10 - perp_x * 17, hy + sin_a * 10 - perp_y * 17)
        for eye_pt in [eye_l, eye_r]:
            draw.ellipse([eye_pt[0]-8, eye_pt[1]-7, eye_pt[0]+8, eye_pt[1]+7],
                         fill=(30, 18, 5), outline=fur_dark, width=2)
            draw.ellipse([eye_pt[0]-6, eye_pt[1]-5.5, eye_pt[0]+6, eye_pt[1]+5.5], fill=eye_amber)
            draw.ellipse([eye_pt[0]-2.5, eye_pt[1]-4, eye_pt[0]+2.5, eye_pt[1]+4], fill=(5, 3, 1))
            draw.ellipse([eye_pt[0]+2.5, eye_pt[1]-3.5, eye_pt[0]+5, eye_pt[1]-1], fill=(255, 255, 240))

        # Eyebrow spots
        brow_l = (hx - cos_a * 4 + perp_x * 16, hy - sin_a * 4 + perp_y * 16)
        brow_r = (hx - cos_a * 4 - perp_x * 16, hy - sin_a * 4 - perp_y * 16)
        draw.ellipse([brow_l[0]-3, brow_l[1]-2, brow_l[0]+3, brow_l[1]+2], fill=fur_dark)
        draw.ellipse([brow_r[0]-3, brow_r[1]-2, brow_r[0]+3, brow_r[1]+2], fill=fur_dark)

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
        # Aquatic Class: Distinct Kinematics for Swimming Fish vs Expansive Wing Rays
        is_ray = ("ray" in sp_id or "manta" in sp_id or "skate" in sp_id)

        if is_ray:
            # Oceanic Manta / Eagle Ray: Undulating Pectoral Wing Fins & Cephalic Lobes
            flap_wave = math.sin(sim_time * 3.5) * 26
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

            # Cephalic Horns at Mouth
            draw.ellipse([w_nose[0] + perp_x * 16 - 6, w_nose[1] + perp_y * 16 - 6, w_nose[0] + perp_x * 16 + 6, w_nose[1] + perp_y * 16 + 6], fill=(14, 28, 48), outline=accent_color, width=2)
            draw.ellipse([w_nose[0] - perp_x * 16 - 6, w_nose[1] - perp_y * 16 - 6, w_nose[0] - perp_x * 16 + 6, w_nose[1] - perp_y * 16 + 6], fill=(14, 28, 48), outline=accent_color, width=2)

            # Trailing Whip Tail
            t_prev = w_tail
            for i in range(12):
                tx = t_prev[0] - cos_a * 14 + math.sin(sim_time * 4 + i * 0.4) * 5
                ty = t_prev[1] - sin_a * 14 + math.cos(sim_time * 4 + i * 0.4) * 5
                draw.line([t_prev, (tx, ty)], fill=(14, 28, 48), width=max(2, 6 - i // 2))
                t_prev = (tx, ty)
        else:
            # Swimming Fish / Shark / Eel / Koi: Lateral Undulation, Flowing Caudal Fin & Pectoral Flippers
            swim_wave = math.sin(sim_time * 6)
            
            # 1. Pectoral Side Swimming Fins (Left & Right)
            for side in [-1, 1]:
                f_root = (sim.x + cos_a * 10 + perp_x * (22 * side), sim.y + sin_a * 10 + perp_y * (22 * side))
                fin_flap = math.sin(sim_time * 6 + side * 0.5) * 12
                f_tip = (f_root[0] - cos_a * 28 + perp_x * ((38 + fin_flap) * side),
                         f_root[1] - sin_a * 28 + perp_y * ((38 + fin_flap) * side))
                f_mid = (f_root[0] - cos_a * 14 + perp_x * (28 * side), f_root[1] - sin_a * 14 + perp_y * (28 * side))
                draw.polygon([f_root, f_mid, f_tip], fill=(240, 240, 245), outline=accent_color, width=2)

            # 2. Streamlined Multi-Vertebrae Fuselage Body
            body_pts_l, body_pts_r = [], []
            spine_chain = []
            for i in range(14):
                seg_wave = math.sin(sim_time * 6 - i * 0.45) * (i * 2.2)
                sx = sim.x - cos_a * (i * 15) + perp_x * seg_wave
                sy = sim.y - sin_a * (i * 15) + perp_y * seg_wave
                spine_chain.append((sx, sy))
                
                # Fish Body Profile Width
                if i < 4:
                    hw = 20 + i * 4
                elif i < 9:
                    hw = 32 - (i - 4) * 3.5
                else:
                    hw = max(6, 16 - (i - 9) * 2.5)

                body_pts_l.append((sx + perp_x * hw, sy + perp_y * hw))
                body_pts_r.append((sx - perp_x * hw, sy - perp_y * hw))

            # Render Fish Torso
            h_nose = (sim.x + cos_a * 35, sim.y + sin_a * 35)
            fish_poly = [h_nose] + body_pts_l + list(reversed(body_pts_r))
            draw.polygon(fish_poly, fill=(25, 35, 50), outline=accent_color, width=3)

            # Dorsal Spine Accent Stripe
            for i in range(len(spine_chain) - 1):
                draw.line([spine_chain[i], spine_chain[i+1]], fill=accent_color, width=3)

            # 3. Flowing 2-Lobe Caudal Tail Fin (Fish Tail)
            tail_base = spine_chain[-1]
            tail_wave = math.sin(sim_time * 6 - 6.0) * 24
            t_tip_top = (tail_base[0] - cos_a * 45 + perp_x * (32 + tail_wave),
                         tail_base[1] - sin_a * 45 + perp_y * (32 + tail_wave))
            t_tip_bot = (tail_base[0] - cos_a * 45 - perp_x * (32 - tail_wave),
                         tail_base[1] - sin_a * 45 - perp_y * (32 - tail_wave))
            t_mid_notch = (tail_base[0] - cos_a * 25 + perp_x * (tail_wave * 0.5),
                           tail_base[1] - sin_a * 25 + perp_y * (tail_wave * 0.5))
            
            draw.polygon([tail_base, t_tip_top, t_mid_notch, t_tip_bot], fill=(245, 245, 250), outline=accent_color, width=2)

            # 4. Fish Head: Eyes & Gill Cover Arch
            eye_l = (sim.x + cos_a * 20 + perp_x * 16, sim.y + sin_a * 20 + perp_y * 16)
            eye_r = (sim.x + cos_a * 20 - perp_x * 16, sim.y + sin_a * 20 - perp_y * 16)
            draw.ellipse([eye_l[0]-6, eye_l[1]-6, eye_l[0]+6, eye_l[1]+6], fill=(245, 245, 250), outline=accent_color, width=2)
            draw.ellipse([eye_r[0]-6, eye_r[1]-6, eye_r[0]+6, eye_r[1]+6], fill=(245, 245, 250), outline=accent_color, width=2)
            draw.ellipse([eye_l[0]-3, eye_l[1]-3, eye_l[0]+3, eye_l[1]+3], fill=(10, 15, 25))
            draw.ellipse([eye_r[0]-3, eye_r[1]-3, eye_r[0]+3, eye_r[1]+3], fill=(10, 15, 25))
            draw.ellipse([eye_l[0]+1, eye_l[1]-1, eye_l[0]+2.5, eye_l[1]+0.5], fill=(255, 255, 255))
            draw.ellipse([eye_r[0]+1, eye_r[1]-1, eye_r[0]+2.5, eye_r[1]+0.5], fill=(255, 255, 255))

            # Gill Operculum Arch
            draw.arc([sim.x + cos_a * 8 - 18, sim.y + sin_a * 8 - 18, sim.x + cos_a * 8 + 18, sim.y + sin_a * 8 + 18],
                     start=int(math.degrees(sim.angle) + 60), end=int(math.degrees(sim.angle) + 300), fill=accent_color, width=2)


    # ─────────────────────────────────────────────────────────────
    # LOWER SECTION: macOS DARK CODE WINDOW (MOBILE OPTIMIZED)
    # ─────────────────────────────────────────────────────────────
    card_w, card_h = 920, 980
    card_x = (WIDTH - card_w) // 2
    card_y = 840

    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=22, fill=theme["card_fill"], outline=theme["card_border"], width=2)

    title_h = 62
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + title_h], radius=22, fill=theme["card_header"])
    draw.rectangle([card_x, card_y + 30, card_x + card_w, card_y + title_h], fill=theme["card_header"])

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

    active_idx = min(total_lines - 1, start_line_idx + 2)

    for idx in range(visible_lines + 2):
        actual_line_idx = start_line_idx + idx
        if actual_line_idx >= total_lines:
            break
        
        line_text = all_lines[actual_line_idx]
        y_pos = code_box_top + (idx * line_h) - int(line_pixel_offset)

        if y_pos < code_box_top - 16 or y_pos > code_box_bottom:
            continue

        # Soft active line background highlight
        if actual_line_idx == active_idx:
            draw.rounded_rectangle([card_x + 16, y_pos - 4, card_x + card_w - 16, y_pos + line_h - 8], radius=6, fill=(24, 34, 48))

        draw.text((card_x + 36, y_pos), f"{actual_line_idx + 1:2d}", font=line_num_font, fill=(140, 160, 185) if actual_line_idx == active_idx else (80, 100, 125))

        indent_x = card_x + 98
        _draw_highlighted_js_line(draw, indent_x, y_pos, line_text, code_font)

        # Blinking cursor on active line
        if actual_line_idx == active_idx and (frame_idx // 10) % 2 == 0:
            cursor_x = indent_x + int(len(line_text) * 16.5)
            if cursor_x < card_x + card_w - 30:
                draw.rectangle([cursor_x, y_pos + 4, cursor_x + 3, y_pos + 32], fill=accent_color)

    # Bottom Progress Bar with Accent Glow
    bar_w = 920
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 1855
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 12], radius=6, fill=(35, 46, 62))
    fill_w = max(12, int(bar_w * progress))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + 12], radius=6, fill=accent_color)

    return img.convert("RGB")

