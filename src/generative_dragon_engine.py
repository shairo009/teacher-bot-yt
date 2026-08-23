"""
Minimalist Code-Reel Engine with Biological Modular Rigging & Large Mobile Typography
Features:
- Calm, smooth, natural real-world crawl & trot speed
- Large 34px Bold Monospace Code Font with 56px Line Spacing (Crisp on Phone Screens)
- True Canine, Arachnid, Serpent, Reptile biological kinematics
- Clean Minimalist Header (Animal Name ONLY)
- macOS Dark Editor with Auto-Sliding/Scrolling JS Code
- 100% Free & Unlimited
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT, FPS = 1080, 1920, 30
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ENCYCLOPEDIA_FILE = DATA_DIR / "animal_encyclopedia.json"

def get_font(size: int, bold: bool = False, serif: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        candidates = [
            "/system/fonts/DroidSansMono.ttf",
            "/data/data/com.termux/files/home/teacher-bot-repo/assets/fonts/Montserrat-Bold.ttf" if bold else "/data/data/com.termux/files/home/teacher-bot-repo/assets/fonts/Montserrat-Regular.ttf"
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

def solve_forelimb_ik(shoulder: tuple[float, float], paw: tuple[float, float], l1: float, l2: float, side: float):
    dx = paw[0] - shoulder[0]
    dy = paw[1] - shoulder[1]
    dist = math.hypot(dx, dy)
    clamped = min(dist, l1 + l2 - 0.001)
    base = math.atan2(dy, dx)
    cos_a = (l1 * l1 + clamped * clamped - l2 * l2) / (2 * l1 * clamped)
    ang = base - math.acos(max(-1.0, min(1.0, cos_a))) * side * 0.9
    elbow = (shoulder[0] + math.cos(ang) * l1, shoulder[1] + math.sin(ang) * l1)
    return shoulder, elbow, paw

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
    if class_type == "quadruped":
        return [
            f"// ─── {name} ({scientific.upper()}) ───",
            f"const {c_name} = new CanineRig({{ spineSegs: 18 }});",
            "",
            f"const update{c_name} = () => {{",
            f"  requestAnimationFrame(update{c_name});",
            "  const p = getPointerPosition();",
            "",
            "  // 1. Forelimbs: Elbow Bends BACKWARD",
            f"  solveForelimbIK({c_name}.leftArm,  p.fl, 34, 38, -1);",
            f"  solveForelimbIK({c_name}.rightArm, p.fr, 34, 38,  1);",
            "",
            "  // 2. Hindlimbs: Stifle Knee FORWARD, Hock BACKWARD",
            f"  solveHindlimbIK({c_name}.leftLeg,  p.hl, 32, 32, 20, -1);",
            f"  solveHindlimbIK({c_name}.rightLeg, p.hr, 32, 32, 20,  1);",
            "",
            "  // 3. 4-Toe Digitigrade Paw Pads with Claws",
            f"  render4ToePaw({c_name}.leftArm.target);",
            f"  render4ToePaw({c_name}.rightArm.target);",
            "",
            "  // 4. Organic Torso, Saddle & Harmonic Wagging Tail",
            f"  renderCanineTorso(ctx, {c_name}.spine);",
            f"  wagPlumeTail({c_name}.tail, Math.sin(time * 6.5) * 0.45);",
            f"  renderCanineHeadWithEars(ctx, {c_name}.head);",
            "};"
        ]
    elif class_type == "arachnid":
        return [
            f"// ─── {name} ({scientific.upper()}) ───",
            f"const {c_name} = new ArachnidSkeleton({{ segments: 38 }});",
            "",
            f"const animate{c_name} = () => {{",
            f"  requestAnimationFrame(animate{c_name});",
            "  const p = getPointerPosition();",
            "",
            "  // 1. Solve 3-Joint Pincer Arms (Chelae)",
            f"  solvePincerIK({c_name}.leftArm,  p, 54, 62, -1);",
            f"  solvePincerIK({c_name}.rightArm, p, 54, 62,  1);",
            "",
            "  // 2. 8-Legged Tripod Stepping Gait",
            "  for (let i = 0; i < 8; i++) {",
            f"    const leg = {c_name}.legs[i];",
            "    const side = i < 4 ? -1 : 1;",
            f"    const hip = getHipSocket({c_name}.carapace, i, side);",
            "    const step = computeTripodStep(leg, frm, side);",
            "    const ik = solve3SegmentIK(hip, step.target, 24, 30, 26, side);",
            "    renderArticulatedLeg(ctx, ik);",
            "  }",
            "",
            "  // 3. 7 Mesosoma Plates & 5-Segment Tail",
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
            f"  const head = {c_name}.spine[0];",
            "  head.x += (pointer.x - head.x) * 0.08;",
            "  head.y += (pointer.y - head.y) * 0.08;",
            "",
            "  // 1. Serpentine Lateral Undulation Wave",
            f"  for (let i = 1; i < {c_name}.length; i++) {{",
            f"    const prev = {c_name}.spine[i - 1];",
            f"    const curr = {c_name}.spine[i];",
            "    const wave = Math.sin(time * 4.5 + i * 0.35) * 6;",
            "    updateVertebra(curr, prev, 14, wave);",
            "    renderScalesAndScutes(ctx, curr, i);",
            "  }",
            "",
            "  // 2. Fanged Diamond Head & Flaring Hood",
            f"  renderCobraHood(ctx, head, {c_name}.spine[2]);",
            f"  renderForkedTongueAndEyes(ctx, head);",
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
            "  // 1. Articulated 2-Joint Claws",
            f"  {c_name}.limbs.forEach(limb => {{",
            f"    const socket = getSpineAnchor({c_name}.spine, limb.vertebra, limb.side);",
            "    const step = computeGaitArc(limb.phase, frm);",
            "    const ik = solve2JointIK(socket, step.foot, limb.l1, limb.l2, limb.side);",
            "    renderLimbWithSpreadClaws(ctx, ik);",
            "  });",
            f"  renderReptilianHeadWithNostrils(ctx, {c_name}.spine[0]);",
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
        self.spine = [{"x": cx - i * 14, "y": cy, "angle": 0.0} for i in range(24)]
        
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
        # 4 Quadruped Legs
        self.legs4 = [
            {"id": "FL", "spine_i": 3, "side": -1, "is_front": True,  "l1": 34, "l2": 38, "phase": 0.0,     "cur": [cx + 10, cy - 25], "tgt": [cx + 10, cy - 25], "start": [cx + 10, cy - 25], "prog": 1.0},
            {"id": "FR", "spine_i": 3, "side":  1, "is_front": True,  "l1": 34, "l2": 38, "phase": math.pi, "cur": [cx + 10, cy + 25], "tgt": [cx + 10, cy + 25], "start": [cx + 10, cy + 25], "prog": 1.0},
            {"id": "HL", "spine_i": 12, "side": -1, "is_front": False, "l1": 32, "l2": 32, "l3": 20, "phase": math.pi, "cur": [cx - 40, cy - 25], "tgt": [cx - 40, cy - 25], "start": [cx - 40, cy - 25], "prog": 1.0},
            {"id": "HR", "spine_i": 12, "side":  1, "is_front": False, "l1": 32, "l2": 32, "l3": 20, "phase": 0.0,     "cur": [cx - 40, cy + 25], "tgt": [cx - 40, cy + 25], "start": [cx - 40, cy + 25], "prog": 1.0},
        ]

    def update(self, sim_time: float):
        # Calm, smooth trajectory
        target_x = self.cx + math.cos(sim_time * 0.75) * (self.rx * 0.9) + math.sin(sim_time * 1.5) * (self.rx * 0.22)
        target_y = self.cy + math.sin(sim_time * 1.05) * (self.ry * 0.85) + math.cos(sim_time * 2.1) * (self.ry * 0.20)

        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        target_ang = math.atan2(dy, dx)

        diff = target_ang - self.angle
        while diff < -math.pi: diff += math.pi * 2
        while diff > math.pi: diff -= math.pi * 2
        self.angle += diff * 0.04  # Calm, graceful turning

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

        # Spine Follow-Chain
        self.spine[0]["x"] = self.x
        self.spine[0]["y"] = self.y
        self.spine[0]["angle"] = self.angle
        for i in range(1, len(self.spine)):
            prev = self.spine[i - 1]
            curr = self.spine[i]
            s_dist = 14 - (i / len(self.spine)) * 3
            wave = math.sin(sim_time * 4.5 + i * 0.35) * (2.0 if i > 2 else 0.5)
            p_dx = prev["x"] - curr["x"]
            p_dy = prev["y"] - curr["y"]
            curr["angle"] = math.atan2(p_dy, p_dx)
            curr["x"] = prev["x"] - math.cos(curr["angle"]) * s_dist + math.cos(curr["angle"] + math.pi/2) * wave
            curr["y"] = prev["y"] - math.sin(curr["angle"]) * s_dist + math.sin(curr["angle"] + math.pi/2) * wave

        # 4 Quadruped Legs Gait
        trot_clock = sim_time * 6.5
        for leg in self.legs4:
            s_pt = self.spine[leg["spine_i"]]
            s_ang = s_pt["angle"]
            s_cos = math.cos(s_ang)
            s_sin = math.sin(s_ang)
            s_perp_x = -s_sin
            s_perp_y =  s_cos

            sock_dist = 18 if leg["is_front"] else 16
            sock = (s_pt["x"] + s_perp_x * (sock_dist * leg["side"]),
                    s_pt["y"] + s_perp_y * (sock_dist * leg["side"]))
            leg["socket"] = sock

            f_reach = 22 if leg["is_front"] else -6
            l_spread = 20 if leg["is_front"] else 18
            ideal_x = sock[0] + s_cos * f_reach + s_perp_x * (l_spread * leg["side"])
            ideal_y = sock[1] + s_sin * f_reach + s_perp_y * (l_spread * leg["side"])

            d_ideal = math.hypot(ideal_x - leg["cur"][0], ideal_y - leg["cur"][1])
            phase_v = math.sin(trot_clock + leg["phase"])

            if d_ideal > 24 and leg["prog"] >= 1.0 and phase_v > 0.1:
                leg["prog"] = 0.0
                leg["start"] = [leg["cur"][0], leg["cur"][1]]
                leg["tgt"] = [
                    ideal_x + cos_a * (self.speed * 8 + 14),
                    ideal_y + sin_a * (self.speed * 8 + 14)
                ]

            if leg["prog"] < 1.0:
                leg["prog"] += 0.10  # Smooth, calm foot swing
                p = min(1.0, leg["prog"])
                ease_p = 0.5 - math.cos(p * math.pi) / 2
                lift = math.sin(p * math.pi) * 14
                leg["cur"][0] = leg["start"][0] + (leg["tgt"][0] - leg["start"][0]) * ease_p
                leg["cur"][1] = leg["start"][1] + (leg["tgt"][1] - leg["start"][1]) * ease_p - lift * 0.2


_SIM_CACHE = {}

def render_generative_frame(species: dict, frame_idx: int, total_frames: int) -> Image.Image:
    progress = frame_idx / total_frames
    sim_time = (frame_idx / FPS) * 0.4  # Calm, natural real-life speed

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
    # QUADRUPED DOG ANATOMY (True Elbow Backwards & Knee Forward)
    # ─────────────────────────────────────────────────────────────
    if class_type == "quadruped" or "dog" in sp_id or "wolf" in sp_id:
        # 1. Limbs Layer
        for leg in sim.legs4:
            paw_pos = (leg["cur"][0], leg["cur"][1])
            sock = leg["socket"]

            if leg["is_front"]:
                # Elbow bends BACKWARD
                _, elbow, _ = solve_forelimb_ik(sock, paw_pos, leg["l1"], leg["l2"], leg["side"])
                draw.line([sock, elbow], fill=(217, 119, 6), width=13)
                draw.line([elbow, paw_pos], fill=(251, 164, 68), width=9)
                draw.ellipse([elbow[0]-4, elbow[1]-4, elbow[0]+4, elbow[1]+4], fill=(245, 158, 11))
            else:
                # Stifle Knee bends FORWARD, Hock bends BACKWARD
                knee = (sock[0] + cos_a * (32 * 0.75) + perp_x * (32 * 0.65 * leg["side"]),
                        sock[1] + sin_a * (32 * 0.75) + perp_y * (32 * 0.65 * leg["side"]))
                hock = (knee[0] - cos_a * (32 * 0.65) + perp_x * (32 * 0.2 * leg["side"]),
                        knee[1] - sin_a * (32 * 0.65) + perp_y * (32 * 0.2 * leg["side"]))
                draw.line([sock, knee], fill=(217, 119, 6), width=16)
                draw.line([knee, hock], fill=(217, 119, 6), width=12)
                draw.line([hock, paw_pos], fill=(251, 164, 68), width=8)
                draw.ellipse([knee[0]-5, knee[1]-5, knee[0]+5, knee[1]+5], fill=(245, 158, 11))
                draw.ellipse([hock[0]-4, hock[1]-4, hock[0]+4, hock[1]+4], fill=(120, 53, 15))

            # 4-Toe Digitigrade Paw Pad
            draw.ellipse([paw_pos[0]-7, paw_pos[1]-6, paw_pos[0]+7, paw_pos[1]+6], fill=(30, 41, 59))

        # 2. Torso (Organic Golden Coat + Dark Saddle)
        left_prof, right_prof = [], []
        spine_pts = []
        for i in range(16):
            seg = sim.spine[i]
            s_cos, s_sin = math.cos(seg["angle"]), math.sin(seg["angle"])
            s_perp_x, s_perp_y = -s_sin, s_cos
            half_w = 26 - i * 0.7 if i < 6 else 19 - (i-6)*1.1 if i < 11 else 23 - (i-11)*0.6
            half_w = max(11, half_w)
            left_prof.append((seg["x"] + s_perp_x * half_w, seg["y"] + s_perp_y * half_w))
            right_prof.append((seg["x"] - s_perp_x * half_w, seg["y"] - s_perp_y * half_w))
            spine_pts.append((seg["x"], seg["y"]))

        draw.polygon(left_prof + list(reversed(right_prof)), fill=(245, 158, 11), outline=(180, 83, 9), width=2)
        saddle_l = [((left_prof[i][0]*0.7 + spine_pts[i][0]*0.3), (left_prof[i][1]*0.7 + spine_pts[i][1]*0.3)) for i in range(2, 13)]
        saddle_r = [((right_prof[i][0]*0.7 + spine_pts[i][0]*0.3), (right_prof[i][1]*0.7 + spine_pts[i][1]*0.3)) for i in range(2, 13)]
        draw.polygon(saddle_l + list(reversed(saddle_r)), fill=(28, 17, 8))

        # 3. Wagging Tail
        tail_prev = spine_pts[-1]
        wag = math.sin(sim_time * 6.5) * 0.52
        for i in range(9):
            t_ang = sim.angle + math.pi + wag * ((i+1)/9)
            tx = tail_prev[0] + math.cos(t_ang) * (14 - i * 0.8)
            ty = tail_prev[1] + math.sin(t_ang) * (14 - i * 0.8)
            draw.line([tail_prev, (tx, ty)], fill=(245, 158, 11), width=max(4, int(15 - i * 1.2)))
            tail_prev = (tx, ty)

        # 4. Sculpted Canine Head
        hx = sim.x + cos_a * 26
        hy = sim.y + sin_a * 26
        snout = (hx + cos_a * 36, hy + sin_a * 36)

        ear_l = (hx - cos_a * 8 + perp_x * 22, hy - sin_a * 8 + perp_y * 22)
        ear_tip_l = (ear_l[0] - cos_a * 24 + perp_x * 14, ear_l[1] - sin_a * 24 + perp_y * 14)
        ear_r = (hx - cos_a * 8 - perp_x * 22, hy - sin_a * 8 - perp_y * 22)
        ear_tip_r = (ear_r[0] - cos_a * 24 - perp_x * 14, ear_r[1] - sin_a * 24 - perp_y * 14)
        draw.polygon([(hx, hy), ear_l, ear_tip_l], fill=(28, 17, 8), outline=(180, 83, 9), width=2)
        draw.polygon([(hx, hy), ear_r, ear_tip_r], fill=(28, 17, 8), outline=(180, 83, 9), width=2)
        draw.polygon([ear_l, ear_tip_l, (hx - cos_a * 6 + perp_x * 12, hy - sin_a * 6 + perp_y * 12)], fill=(253, 164, 175))
        draw.polygon([ear_r, ear_tip_r, (hx - cos_a * 6 - perp_x * 12, hy - sin_a * 6 - perp_y * 12)], fill=(253, 164, 175))

        c1 = (hx + cos_a * 16 + perp_x * 22, hy + sin_a * 16 + perp_y * 22)
        c2 = (hx - cos_a * 16 + perp_x * 24, hy - sin_a * 16 + perp_y * 24)
        c3 = (hx - cos_a * 16 - perp_x * 24, hy - sin_a * 16 - perp_y * 24)
        c4 = (hx + cos_a * 16 - perp_x * 22, hy + sin_a * 16 - perp_y * 22)
        draw.polygon([snout, c1, c2, c3, c4], fill=(245, 158, 11), outline=(180, 83, 9), width=2)

        m1 = (hx + cos_a * 14 + perp_x * 14, hy + sin_a * 14 + perp_y * 14)
        m2 = (hx + cos_a * 14 - perp_x * 14, hy + sin_a * 14 - perp_y * 14)
        draw.polygon([snout, m1, m2], fill=(28, 17, 8))

        tongue_tip = (snout[0] + cos_a * 16, snout[1] + sin_a * 16)
        draw.ellipse([tongue_tip[0]-3, tongue_tip[1]-3, tongue_tip[0]+3, tongue_tip[1]+3], fill=(251, 113, 133))
        draw.ellipse([snout[0]-5, snout[1]-4, snout[0]+5, snout[1]+4], fill=(0, 0, 0))

        eye_l = (hx + cos_a * 8 + perp_x * 12, hy + sin_a * 8 + perp_y * 12)
        eye_r = (hx + cos_a * 8 - perp_x * 12, hy + sin_a * 8 - perp_y * 12)
        draw.ellipse([eye_l[0]-4, eye_l[1]-3.5, eye_l[0]+4, eye_l[1]+3.5], fill=(69, 26, 3))
        draw.ellipse([eye_r[0]-4, eye_r[1]-3.5, eye_r[0]+4, eye_r[1]+3.5], fill=(69, 26, 3))
        draw.ellipse([eye_l[0]+1, eye_l[1]-1, eye_l[0]+2.5, eye_l[1]+0.5], fill=(255, 255, 255))
        draw.ellipse([eye_r[0]+1, eye_r[1]-1, eye_r[0]+2.5, eye_r[1]+0.5], fill=(255, 255, 255))

    elif class_type == "arachnid":
        # Arachnid Scorpion
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

        c_front = (sim.x + cos_a * 34, sim.y + sin_a * 34)
        c_r1 = (sim.x + cos_a * 18 + perp_x * 28, sim.y + sin_a * 18 + perp_y * 28)
        c_r2 = (sim.x - cos_a * 16 + perp_x * 32, sim.y - sin_a * 16 + perp_y * 32)
        c_l2 = (sim.x - cos_a * 16 - perp_x * 32, sim.y - sin_a * 16 - perp_y * 32)
        c_l1 = (sim.x + cos_a * 18 - perp_x * 28, sim.y + sin_a * 18 - perp_y * 28)
        draw.polygon([c_front, c_r1, c_r2, c_l2, c_l1], fill=(12, 16, 24), outline=accent_color, width=2)

    else:
        # Serpent / Dragon
        for i in range(len(sim.spine) - 1, 0, -1):
            p1 = (sim.spine[i]["x"], sim.spine[i]["y"])
            p0 = (sim.spine[i - 1]["x"], sim.spine[i - 1]["y"])
            norm = i / len(sim.spine)
            v_width = max(4, int(28 * (1.0 - norm * 0.75)))
            draw.line([p0, p1], fill=(16, 26, 20), width=v_width)
            draw.ellipse([p1[0]-v_width//2, p1[1]-v_width//2, p1[0]+v_width//2, p1[1]+v_width//2], fill=(24, 40, 30), outline=accent_color, width=1)

        snout = (sim.x + cos_a * 38, sim.y + sin_a * 38)
        j1 = (sim.x - cos_a * 12 + perp_x * 20, sim.y - sin_a * 12 + perp_y * 20)
        j2 = (sim.x - cos_a * 12 - perp_x * 20, sim.y - sin_a * 12 - perp_y * 20)
        crown = (sim.x - cos_a * 26, sim.y - sin_a * 26)
        draw.polygon([snout, j1, crown, j2], fill=(10, 18, 14), outline=accent_color, width=2)

    # ─────────────────────────────────────────────────────────────
    # LOWER SECTION: macOS DARK CODE WINDOW (LARGE 34PX BOLD FONT)
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
    
    line_h = 56          # Large line height for high legibility
    code_font = get_font(34, mono=True, bold=True)      # 34px BOLD font
    line_num_font = get_font(28, mono=True)             # 28px line numbers
    
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

        # Line Number in Gutter
        draw.text((card_x + 36, y_pos), f"{actual_line_idx + 1:2d}", font=line_num_font, fill=(75, 92, 115))

        # Syntax Highlighting
        indent_x = card_x + 105
        stripped = line_text.strip()
        if stripped.startswith("//"):
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(100, 116, 139))
        elif any(k in line_text for k in ["const ", "let ", "for ", "new ", "return "]):
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(224, 108, 117))
        elif any(f in line_text for f in ["Math.", "solve", "render", "update", "compute", "wag", "curl"]):
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(97, 175, 239))
        elif any(cls in line_text for cls in ["CanineRig", "ArachnidSkeleton", "SerpentineSpine"]):
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(229, 192, 123))
        else:
            draw.text((indent_x, y_pos), line_text, font=code_font, fill=(226, 232, 240))

    # Bottom Progress Bar
    bar_w = 920
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 1855
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 12], radius=6, fill=(35, 46, 62))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + 12], radius=6, fill=accent_color)

    return img.convert("RGB")
