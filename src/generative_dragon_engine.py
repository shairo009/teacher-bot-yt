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
import textwrap
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT, FPS = 1080, 1920, 30
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
FONTS_DIR = ROOT_DIR / "assets" / "fonts"
ENCYCLOPEDIA_FILE = DATA_DIR / "animal_encyclopedia.json"

@lru_cache(maxsize=64)
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

def solve_forelimb_ik(shoulder, paw, l1, l2, side):
    from src.bio_bone_renderer import solve_two_bone_ik
    return solve_two_bone_ik(shoulder, paw, l1, l2, -side)


def solve_ik_2joint(origin, target, l1, l2, bend_side):
    from src.bio_bone_renderer import solve_two_bone_ik
    return solve_two_bone_ik(origin, target, l1, l2, bend_side)


def solve_ik_3segment(origin, target, l1, l2, l3, side):
    angle = math.atan2(target[1] - origin[1], target[0] - origin[0]) + side * 0.35
    first = (origin[0] + math.cos(angle) * l1, origin[1] + math.sin(angle) * l1)
    _, second, endpoint = solve_ik_2joint(first, target, l2, l3, side)
    return origin, first, second, endpoint

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
        curr_x += draw.textlength(val, font=font)


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
            "  neckVertebrae: 7,",
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
    morphology = entry.get("morphology", "small_mammal")
    accent = tuple(entry.get("accent", [245, 158, 11]))
    file_name = entry.get("file_name", "".join(w.capitalize() for w in name.split()) + ".js")
    spec_id = name.lower().replace(" ", "_")

    code_lines = _generate_js_code_for_animal(name, class_type, scientific)

    hooks = [
        f"I Built an Interactive {name} with Vanilla JS IK Physics 🤯 #Shorts #Coding",
        f"Procedural {name} Motion Study (30 FPS Animation) ✨ #Shorts #WebDev",
        f"How to Code an Interactive {name} Cursor in JavaScript ⚡ #Shorts #Programming",
        f"Coding an Interactive {name} with Joint Kinematics ✨ #Shorts #Coding",
        f"I Simulated a Realistic {name} in a 2D Motion Study 🤯 #Shorts #Tech",
        f"Interactive {name} Cursor in Vanilla JS ✨ #Shorts #CreativeCoding"
    ]
    yt_title = hooks[animal_id % len(hooks)]

    return {
        "id": spec_id,
        "name": name,
        "scientific": scientific,
        "class_type": class_type,
        "morphology": morphology,
        "file_name": file_name,
        "accent": accent,
        "code_lines": code_lines,
        "animal_id": animal_id,
        "bone_structure": entry.get("bone_structure", {}),
        "yt_title": yt_title,
        "yt_desc": f"✨ Realistic {name} ({scientific}) 2D procedural motion study rendered in Python, with illustrative JavaScript kinematics snippets!\n\n#JavaScript #WebDev #Shorts #Coding #Tech #Programming #Canvas"
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
            {"id": "FL", "spine_i": 2, "side": -1, "is_front": True,  "l1": 42, "l2": 46, "phase": 0.0,     "cur": [cx + 34, cy - 56], "tgt": [cx + 34, cy - 56], "start": [cx + 34, cy - 56], "prog": 1.0, "socket": (cx, cy - 36)},
            {"id": "FR", "spine_i": 2, "side":  1, "is_front": True,  "l1": 42, "l2": 46, "phase": math.pi, "cur": [cx + 34, cy + 56], "tgt": [cx + 34, cy + 56], "start": [cx + 34, cy + 56], "prog": 1.0, "socket": (cx, cy + 36)},
            {"id": "HL", "spine_i": 7, "side": -1, "is_front": False, "l1": 44, "l2": 44, "l3": 28, "phase": math.pi, "cur": [cx - 110, cy - 50], "tgt": [cx - 110, cy - 50], "start": [cx - 110, cy - 50], "prog": 1.0, "socket": (cx - 90, cy - 30)},
            {"id": "HR", "spine_i": 7, "side":  1, "is_front": False, "l1": 44, "l2": 44, "l3": 28, "phase": 0.0,     "cur": [cx - 110, cy + 50], "tgt": [cx - 110, cy + 50], "start": [cx - 110, cy + 50], "prog": 1.0, "socket": (cx - 90, cy + 30)},
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
        if self.class_type in ("aquatic", "cephalopod"):
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
        base_s_dist = 17.0 if self.class_type == "quadruped" else (24.0 if self.class_type == "serpent" else 20.0)
        for i in range(1, len(self.spine)):
            prev = self.spine[i - 1]
            curr = self.spine[i]
            s_dist = base_s_dist - (i / len(self.spine)) * (3.5 if self.class_type == "quadruped" else 5.0)
            p_dx = curr["x"] - prev["x"]
            p_dy = curr["y"] - prev["y"]
            d = math.hypot(p_dx, p_dy)
            desired = math.atan2(-p_dy, -p_dx) if d > 0.0001 else prev["angle"]
            turn = (desired - prev["angle"] + math.pi) % (2 * math.pi) - math.pi
            # Flexible neck, stable thorax and progressively softer tail.
            limit = 0.30 if i < 3 else (0.12 if i < 10 else 0.20 + (i - 10) * 0.035)
            if self.class_type in ("serpent", "aquatic", "cephalopod"):
                limit = 0.38
            curr["angle"] = prev["angle"] + max(-limit, min(limit, turn))
            curr["x"] = prev["x"] - math.cos(curr["angle"]) * s_dist
            curr["y"] = prev["y"] - math.sin(curr["angle"]) * s_dist

        # 4 Quadruped Legs Gait (Classic Diagonal Trot)
        trot_clock = sim_time * 16.0
        for leg in self.legs4:
            s_pt = self.spine[leg["spine_i"]]
            s_ang = s_pt["angle"]
            s_cos = math.cos(s_ang)
            s_sin = math.sin(s_ang)
            s_perp_x = -s_sin
            s_perp_y =  s_cos

            sock_dist = 36 if leg["is_front"] else 30
            sock = (s_pt["x"] + s_perp_x * (sock_dist * leg["side"]),
                    s_pt["y"] + s_perp_y * (sock_dist * leg["side"]))
            leg["socket"] = sock

            f_reach = 36 if leg["is_front"] else -22
            l_spread = 56 if leg["is_front"] else 50
            ideal_x = sock[0] + s_cos * f_reach + s_perp_x * (l_spread * leg["side"])
            ideal_y = sock[1] + s_sin * f_reach + s_perp_y * (l_spread * leg["side"])

            d_ideal = math.hypot(ideal_x - leg["cur"][0], ideal_y - leg["cur"][1])
            phase_v = math.sin(trot_clock + leg["phase"])

            # Step triggers when foot is stretched back and gait phase is in swing phase
            if (d_ideal > 18 or (d_ideal > 10 and phase_v > 0.4)) and leg["prog"] >= 1.0 and phase_v > 0.0:
                leg["prog"] = 0.0
                leg["start"] = [leg["cur"][0], leg["cur"][1]]
                stride = max(24.0, self.speed * 12 + 20)
                leg["tgt"] = [
                    ideal_x + cos_a * stride,
                    ideal_y + sin_a * stride
                ]

            if leg["prog"] < 1.0:
                leg["prog"] += 0.16
                p = min(1.0, leg["prog"])
                ease_p = 0.5 - math.cos(p * math.pi) / 2
                lift = math.sin(p * math.pi) * 16
                leg["cur"][0] = leg["start"][0] + (leg["tgt"][0] - leg["start"][0]) * ease_p
                leg["cur"][1] = leg["start"][1] + (leg["tgt"][1] - leg["start"][1]) * ease_p - lift * 0.25

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
        "badge": "2D Procedural Motion Study",
        "badge_color": (56, 189, 248),
        "cursor_color": (0, 230, 255),
    },
    "SAVANNA": {
        "bg": (18, 12, 8),
        "grad_center": (65, 30, 14),
        "canvas_fill": (22, 14, 10),
        "canvas_border": (245, 158, 11),
        "card_fill": (18, 11, 8),
        "card_header": (14, 8, 6),
        "card_border": (55, 32, 18),
        "badge": "2D Procedural Motion Study",
        "badge_color": (251, 191, 36),
        "cursor_color": (239, 68, 68),
    },
    "JUNGLE": {
        "bg": (8, 20, 12),
        "grad_center": (14, 55, 28),
        "canvas_fill": (10, 24, 14),
        "canvas_border": (34, 197, 94),
        "card_fill": (10, 18, 12),
        "card_header": (6, 14, 8),
        "card_border": (24, 50, 30),
        "badge": "2D Procedural Motion Study",
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
        "badge": "2D Procedural Motion Study",
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
        "badge": "2D Procedural Motion Study",
        "badge_color": (232, 121, 249),
        "cursor_color": (244, 63, 94),
    },
    "ARCTIC": {
        "bg": (8, 18, 28),
        "grad_center": (18, 48, 75),
        "canvas_fill": (8, 20, 32),
        "canvas_border": (56, 189, 248),
        "card_fill": (8, 18, 30),
        "card_header": (5, 12, 22),
        "card_border": (20, 42, 68),
        "badge": "2D Procedural Motion Study",
        "badge_color": (125, 211, 252),
        "cursor_color": (14, 165, 233),
    }
}

def pick_animal_theme(species: dict) -> dict:
    class_type = species.get("class_type", "quadruped").lower()
    name = species.get("name", "").lower()
    
    if class_type in ("aquatic", "cephalopod") or any(k in name for k in ("shark", "whale", "fish", "eel", "manta", "squid", "octopus")):
        return ANIMAL_THEMES["OCEAN"]
    elif any(k in name for k in ("polar", "snow", "arctic", "glacier", "frost", "white", "alaska", "alaskan", "tundra", "taiga", "moose", "caribou", "reindeer")):
        return ANIMAL_THEMES["ARCTIC"]
    elif class_type in ("serpent", "insect") or any(k in name for k in ("mantis", "wasp", "tree", "chameleon", "frog", "viper")):
        return ANIMAL_THEMES["JUNGLE"]
    elif class_type in ("arachnid", "crustacean") or any(k in name for k in ("scorpion", "spider", "crab", "lobster", "lava")):
        return ANIMAL_THEMES["VOLCANIC"]
    elif any(k in name for k in ("cyber", "quantum", "neon", "matrix", "volt")):
        return ANIMAL_THEMES["CYBER"]
    else:
        return ANIMAL_THEMES["SAVANNA"]

_SIM_CACHE = OrderedDict()
MAX_SIMULATORS = 8


def _simulation_for_frame(species: dict, frame_idx: int) -> MasterSimulator:
    """Deterministic seeking: frame N is identical in previews and sequential video."""
    key = (species.get("id"), species.get("animal_id", 0), species.get("class_type", "quadruped"))
    cached = _SIM_CACHE.pop(key, None)
    if cached is None or frame_idx <= cached[0]:
        sim = MasterSimulator(540, 585, 245, 150, seed=(key[1] * 10007) & 0xFFFFFF, class_type=key[2])
        # Settle the initially straight chain and feet before the first visible frame.
        for step in range(-90, 0):
            sim.update(step / FPS * 0.4)
        last_frame = -1
    else:
        last_frame, sim = cached
    for step in range(last_frame + 1, frame_idx + 1):
        sim.update(step / FPS * 0.4)
    _SIM_CACHE[key] = (frame_idx, sim)
    while len(_SIM_CACHE) > MAX_SIMULATORS:
        _SIM_CACHE.popitem(last=False)
    return sim


@lru_cache(maxsize=6)
def _studio_background(theme_name: str) -> Image.Image:
    theme = ANIMAL_THEMES[theme_name]
    # Build the soft light at quarter resolution, once per theme, not every frame.
    glow = Image.new("RGB", (270, 480), theme["bg"])
    d = ImageDraw.Draw(glow)
    d.ellipse((5, 35, 265, 365), fill=theme["grad_center"])
    glow = glow.filter(ImageFilter.GaussianBlur(45))
    return glow.resize((WIDTH, HEIGHT), Image.Resampling.BICUBIC).convert("RGBA")


def _fit_font(text: str, max_width: int, size: int, **kwargs):
    while size > 12:
        font = get_font(size, **kwargs)
        if font.getlength(text) <= max_width:
            return font
        size -= 1
    return get_font(size, **kwargs)


class _SupersampledDraw:
    """Small ImageDraw adapter: existing biological rigs stay in world coordinates."""
    def __init__(self, image, origin, scale=2):
        self.draw = ImageDraw.Draw(image)
        self.origin, self.scale = origin, scale

    def _xy(self, xy):
        if isinstance(xy[0], (tuple, list)):
            return [((x - self.origin[0]) * self.scale, (y - self.origin[1]) * self.scale) for x, y in xy]
        return [(value - self.origin[i % 2]) * self.scale for i, value in enumerate(xy)]

    def _shape(self, kind, xy, **kwargs):
        if "width" in kwargs:
            kwargs["width"] = max(1, round(kwargs["width"] * self.scale))
        return getattr(self.draw, kind)(self._xy(xy), **kwargs)

    def line(self, xy, **kwargs):
        return self._shape("line", xy, **kwargs)

    def polygon(self, xy, **kwargs):
        return self._shape("polygon", xy, **kwargs)

    def ellipse(self, xy, **kwargs):
        return self._shape("ellipse", xy, **kwargs)

    def rectangle(self, xy, **kwargs):
        return self._shape("rectangle", xy, **kwargs)

    def arc(self, xy, start, end, **kwargs):
        return self._shape("arc", xy, start=start, end=end, **kwargs)


def _draw_creature_stage(img, species, sim, sim_time, theme):
    from src.bio_bone_renderer import draw_bio_creature
    accent = theme["canvas_border"]
    layer = Image.new("RGBA", (2400, 2400))
    origin = (sim.x - 600, sim.y - 600)
    painter = _SupersampledDraw(layer, origin)
    ca, sa = math.cos(sim.angle), math.sin(sim.angle)
    if not draw_bio_creature(painter, sim, species, sim_time, ca, sa, -sa, ca):
        raise ValueError(f"No biological rig registered for {species.get('name')}")
    bounds = layer.getbbox()
    if not bounds:
        raise ValueError("Biological renderer produced an empty silhouette")
    tx = sim.cx + math.cos(sim_time * sim.f1 + sim.p1) * sim.rx * 0.85 + math.sin(sim_time * sim.f2 + sim.p2) * sim.rx * 0.20
    ty = sim.cy + math.sin(sim_time * sim.f3 + sim.p1) * sim.ry * 0.80 + math.cos(sim_time * sim.f4 + sim.p2) * sim.ry * 0.18
    world = (bounds[0] / 2 + origin[0], bounds[1] / 2 + origin[1], bounds[2] / 2 + origin[0], bounds[3] / 2 + origin[1])
    # Frame the animal AND its target together. No tails, antlers or wings under HUD.
    left, top = min(world[0], tx - 35), min(world[1], ty - 35)
    right, bottom = max(world[2], tx + 35), max(world[3], ty + 35)
    zoom = min(1.45, 752 / (right - left), 462 / (bottom - top))
    def screen(x, y):
        return (540 + (x - (left + right) / 2) * zoom, 585 + (y - (top + bottom) / 2) * zoom)
    x, y = screen(world[0], world[1])
    creature = layer.crop(bounds).resize((max(1, round((world[2] - world[0]) * zoom)), max(1, round((world[3] - world[1]) * zoom))), Image.Resampling.LANCZOS)
    alpha = creature.getchannel("A")
    contact = Image.new("RGBA", creature.size, (0, 0, 0, 0))
    contact.putalpha(alpha.point(lambda value: value * 100 // 255))
    shadow = Image.new("RGBA", img.size)
    shadow.alpha_composite(contact, (round(x + 6), round(y + 12)))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(img)
    head = screen(sim.x, sim.y)
    target = screen(tx, ty)
    dist = math.dist(head, target)
    count = max(2, int(dist / 14))
    for idx in range(0, count, 2):
        a, b = idx / count, min(1, (idx + 0.8) / count)
        d.line([(head[0] + (target[0] - head[0]) * a, head[1] + (target[1] - head[1]) * a),
                (head[0] + (target[0] - head[0]) * b, head[1] + (target[1] - head[1]) * b)], fill=theme["card_border"], width=2)
    # Silhouette overlays its guide, never the other way around.
    img.alpha_composite(creature, (round(x), round(y)))
    d = ImageDraw.Draw(img)
    for idx in range(1, 8):
        past = sim_time - idx * 0.045
        px = sim.cx + math.cos(past * sim.f1 + sim.p1) * sim.rx * 0.85 + math.sin(past * sim.f2 + sim.p2) * sim.rx * 0.20
        py = sim.cy + math.sin(past * sim.f3 + sim.p1) * sim.ry * 0.80 + math.cos(past * sim.f4 + sim.p2) * sim.ry * 0.18
        px, py = screen(px, py)
        if 145 < px < 935 and 351 < py < 819:
            radius = max(1, 4 - idx // 2)
            color = tuple(round(a * (1 - idx / 9) + b * idx / 9) for a, b in zip(accent, theme["canvas_fill"]))
            d.ellipse((px-radius, py-radius, px+radius, py+radius), fill=color)
    px, py = target
    radius = 14 + 2 * math.sin(sim_time * 5)
    for angle in range(0, 360, 90):
        d.arc((px-radius, py-radius, px+radius, py+radius), angle + sim_time * 45, angle + sim_time * 45 + 55, fill=accent, width=2)
    d.ellipse((px-3, py-3, px+3, py+3), fill=(246, 250, 255))
    return tx, ty, math.hypot(tx - sim.x, ty - sim.y)


def _code_rows(lines, width=46):
    rows = []
    for number, line in enumerate(lines, 1):
        indent = len(line) - len(line.lstrip())
        wrapped = textwrap.wrap(line, width=width, subsequent_indent=" " * min(indent + 2, 8),
                                replace_whitespace=False, drop_whitespace=False, break_long_words=True, break_on_hyphens=False) or [""]
        rows.extend((number if idx == 0 else None, text) for idx, text in enumerate(wrapped))
    return rows


def _draw_code_panel(img, species, progress, frame_idx, theme):
    d = ImageDraw.Draw(img)
    x, y, w, h = 110, 905, 860, 610
    d.rounded_rectangle((x, y, x+w, y+h), radius=20, fill=theme["card_fill"], outline=theme["card_border"], width=2)
    d.rounded_rectangle((x+1, y+1, x+w-1, y+56), radius=18, fill=theme["card_header"])
    d.rectangle((x+2, y+30, x+w-2, y+56), fill=theme["card_header"])
    for idx, color in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((x+22+idx*22, y+22, x+32+idx*22, y+32), fill=color)
    filename = species.get("file_name", "MotionStudy.js")
    d.text((x+108, y+18), filename, font=_fit_font(filename, 470, 21, mono=True), fill=(205, 216, 230))
    d.text((x+w-20, y+20), "ILLUSTRATIVE JS", font=get_font(15, mono=True), fill=theme["badge_color"], anchor="rt")
    rows = _code_rows(species.get("code_lines") or _generate_js_code_for_animal(species["name"], species["class_type"], species.get("scientific", "")))
    font, num_font = get_font(26, mono=True), get_font(18, mono=True)
    line_h = 42
    # Hold a useful opening block, type the rest, then let viewers read the ending.
    lengths = [len(text) + 1 for _, text in rows]
    initial = sum(lengths[:5])
    revealed = min(sum(lengths), initial + round(max(0, min(1, (progress - 0.08) / 0.78)) * (sum(lengths) - initial)))
    active, consumed = 0, 0
    for idx, length in enumerate(lengths):
        if consumed + length > revealed:
            break
        consumed += length
        active = min(idx + 1, len(rows) - 1)
    visible = 12
    scroll = max(0, active - visible + 2)
    content = Image.new("RGB", (w-4, h-76), theme["card_fill"])
    cd = ImageDraw.Draw(content)
    for idx in range(scroll, min(len(rows), scroll+visible)):
        number, text = rows[idx]
        ypos = 8 + (idx-scroll) * line_h
        if idx > active:
            break
        if idx == active:
            cd.rounded_rectangle((8, ypos-3, w-16, ypos+34), radius=5, fill=theme["card_header"])
            text = text[:max(0, revealed-consumed)]
        if number is not None:
            cd.text((20, ypos+5), f"{number:02}", font=num_font, fill=(108, 125, 145))
        _draw_highlighted_js_line(cd, 76, ypos, text, font)
        if idx == active and (frame_idx // 12) % 2 == 0:
            cx = min(w-20, 76+round(font.getlength(text)))
            cd.line((cx, ypos+5, cx, ypos+29), fill=theme["badge_color"], width=2)
    # Dedicated crop makes long code and scrolling incapable of bleeding into UI.
    img.paste(content, (x+2, y+64))


def render_generative_frame(species: dict, frame_idx: int, total_frames: int) -> Image.Image:
    if total_frames < 1 or not 0 <= frame_idx < total_frames:
        raise ValueError("Frame index must lie within a non-empty timeline")
    progress = frame_idx / max(1, total_frames-1)
    sim_time = frame_idx / FPS * 0.4
    theme = pick_animal_theme(species)
    theme_name = next(key for key, value in ANIMAL_THEMES.items() if value is theme)
    img = _studio_background(theme_name).copy()
    d = ImageDraw.Draw(img)
    accent = theme["canvas_border"]
    d.text((110, 153), "BIO / MOTION LAB", font=get_font(19, bold=True, mono=True), fill=theme["badge_color"])
    d.text((970, 153), f"2D  /  {FPS} FPS", font=get_font(18, mono=True), fill=(161, 176, 195), anchor="rt")
    name = species["name"]
    d.text((540, 198), name, font=_fit_font(name, 850, 48, bold=True), fill=(245, 249, 255), anchor="mt")
    subtitle = species.get("scientific", name) + "  /  " + species.get("class_type", "creature").upper()
    d.text((540, 254), subtitle, font=_fit_font(subtitle, 830, 19, mono=True), fill=(165, 183, 200), anchor="mt")
    d.rounded_rectangle((108, 283, 972, 887), radius=18, fill=theme["canvas_fill"], outline=theme["card_border"], width=2)
    grid = tuple(min(255, c+7) for c in theme["canvas_fill"])
    for gx in range(140, 960, 40):
        for gy in range(345, 839, 40):
            d.ellipse((gx, gy, gx+1, gy+1), fill=grid)
    # Ambient particles stay in the side gutters, away from the hero silhouette.
    if species.get("class_type") in ("aquatic", "cephalopod"):
        for idx in range(12):
            px = 128 + (idx % 2) * 817
            py = 350 + ((idx * 79 - sim_time * 24) % 465)
            radius = 2 + idx % 3
            d.ellipse((px-radius, py-radius, px+radius, py+radius), outline=theme["card_border"], width=1)
    sim = _simulation_for_frame(species, frame_idx)
    tx, ty, distance = _draw_creature_stage(img, species, sim, sim_time, theme)
    d = ImageDraw.Draw(img)
    d.rectangle((125, 298, 955, 338), fill=theme["canvas_fill"])
    d.rectangle((125, 832, 955, 876), fill=theme["canvas_fill"])
    d.ellipse((132, 307, 140, 315), fill=accent)
    d.text((151, 302), "PROCEDURAL KINEMATICS", font=get_font(16, mono=True), fill=(207, 221, 236))
    d.text((948, 302), theme_name, font=get_font(16, mono=True), fill=theme["badge_color"], anchor="rt")
    d.line((130, 335, 950, 335), fill=theme["card_border"])
    d.line((130, 834, 950, 834), fill=theme["card_border"])
    d.text((132, 848), f"TARGET [{int(tx)}, {int(ty)}]   DIST {int(distance)}px", font=get_font(15, mono=True), fill=(156, 174, 195))
    d.text((948, 848), f"ROT {math.degrees(sim.angle)%360:03.0f} deg", font=get_font(15, mono=True), fill=theme["badge_color"], anchor="rt")
    _draw_code_panel(img, species, progress, frame_idx, theme)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((110, 1530, 970, 1536), radius=3, fill=theme["card_border"])
    if progress > 0:
        d.rounded_rectangle((110, 1530, 110+max(6, round(860*progress)), 1536), radius=3, fill=accent)
    d.text((110, 1550), "ANATOMY / MOTION / CODE", font=get_font(15, mono=True), fill=(155, 170, 192))
    d.text((970, 1550), f"{frame_idx/FPS:04.1f}s / {total_frames/FPS:04.1f}s", font=get_font(15, mono=True), fill=(155, 170, 192), anchor="rt")
    return img.convert("RGB")
