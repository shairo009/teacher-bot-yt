"""Offline analytical 3D animal renderer, composited into a Pillow 2D poster.

Actual XYZ ellipsoids, orthographic camera rays, surface normals and a depth
buffer, not a shaded flat sprite. No GPU, Blender, network or paid API needed.
The procedural rigs are illustrative, NOT photorealistic scanned assets.
See AI_HANDOFF.md for supported species and continuation instructions.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SUPPORTED_SPECIES = {
    "TIGER": "tiger",
    "AFRICAN LION": "lion",
    "GREEN SEA TURTLE": "turtle",
    "MEXICAN REDKNEE TARANTULA": "spider",
    "LEOPARD GECKO": "gecko",
}
QUALITY_SCALE = {"draft": 0.45, "standard": 0.75, "high": 1.25}


GENERIC_3D_MORPHOLOGIES = {
    "small_mammal", "cervid_bovid", "fish", "marine_mammal", "primate",
    "shark", "bear", "kangaroo", "equine", "camelid", "rhino", "pachyderm",
    "elephant", "giraffe", "canine", "feline", "bird", "serpent", "lizard",
    "frog", "crocodile", "turtle", "spider", "scorpion", "beetle", "crab",
    "bee_wasp", "butterfly", "dragonfly", "orthoptera", "ant", "mantis",
    "lobster", "shrimp", "seahorse", "ray", "eel", "octopus", "squid",
    "cuttlefish", "jellyfish", "crustacean", "arachnid", "amphibian",
    "reptile", "aquatic", "cephalopod", "insect", "quadruped",
    "chameleon", "hippo",
}

def _morphology(species: dict) -> str:
    # A broad class must not override a more precise profile (e.g. jellyfish).
    # Unknown explicit profiles fail closed, rather than becoming a mammal.
    value = species.get("morphology") or species.get("class_type") or ""
    return str(value).strip().lower()


def supports_species(species: dict) -> bool:
    name = str(species.get("name") or "").strip().upper()
    return bool(name and (name in SUPPORTED_SPECIES or
                         _morphology(species) in GENERIC_3D_MORPHOLOGIES))


def configure_species(species: dict) -> dict:
    """Explicit 3D never silently substitutes another animal's anatomy."""
    result = dict(species)
    mode = result.get("renderer", "auto")
    if mode not in {"auto", "2d", "3d"}:
        raise ValueError(f"Unknown renderer: {mode}")
    supported = supports_species(result)
    if mode == "3d" and not supported:
        raise ValueError(f"No 3D rig for {result.get('name')}: provide a supported "
                         "catalog morphology or an exact dedicated species name")
    result["resolved_renderer"] = "3d" if supported and mode != "2d" else "2d"
    result["yt_tags"] = ["python", "creative coding", "procedural animation", "shorts",
                         "pillow", "programming", result.get("name", "animal").lower(),
                         "animal", "3d rendering" if result["resolved_renderer"] == "3d" else "2d animation"]
    if result["resolved_renderer"] == "2d":
        result['file_name'] = 'generative_dragon_engine.py'
        result['code_lines'] = ['# Python/Pillow pipeline sketch',
                                'pose = solve_joint_positions(t)',
                                'frame = draw_animal(pose)',
                                '# Illustration, not runnable code']
        result["yt_title"] = f"{result.get('name', 'Animal')} | Procedural 2D Python Animation #Shorts"[:100]
        result["yt_desc"] = ("An offline Python/Pillow procedural 2D animal animation. "
                             "Illustrative legacy rendering, not JavaScript execution, "
                             "wildlife footage or photorealistic capture.")
    if result["resolved_renderer"] == "3d":
        result["file_name"] = "animal_3d_renderer.py"
        result["yt_title"] = f"{result['name']} | Procedural 3D in a 2D scene #Shorts"[:100]
        result["yt_desc"] = ("An offline Python/NumPy procedural 3D animal rendered into a 2D "
                             "Pillow scene. Animated anatomy, depth and surface lighting. "
                             "Illustrative geometry; not wildlife footage or photorealistic capture.")
        result["code_lines"] = [
            "# Real rendering pipeline (Python)",
            "rig = build_rig(kind, seconds)",
            "# Each part has an XYZ transform",
            "camera = orthographic_view()",
            "# Intersect rays with ellipsoids",
            "depth = nearest_surface(rays, rig)",
            "normal = surface_normal(depth)",
            "color = shade(normal, material)",
            "# Composite into the 2D scene",
            "poster.alpha_composite(animal)",
            "# Pipeline sketch, not runnable",
        ]
    # Explain the actual model, not unverified wildlife facts or fake executable code.
    if result['resolved_renderer'] == '3d':
        focus = {
            'seahorse': ('A curled silhouette', 'What makes this model look like a seahorse?',
                         'A long snout and curled tail define its outline.',
                         'The silhouette carries the identity before the surface detail.'),
            'jellyfish': ('A pulsing bell', 'How can a few shapes suggest a jellyfish?',
                          'A rounded bell moves above a set of trailing tentacles.',
                          'The bell and tentacles make a different rig from a fish.'),
            'rhino': ('A distinctive head', 'Which shape makes this rhino model recognizable?',
                      'The horn projects from the head above a heavy body.',
                      'Head shape and proportions matter more than a colour swap.'),
            'butterfly': ('Wings in motion', 'How do these model wings move together?',
                          'Paired wings rotate around the narrow body.',
                          'A shared time signal keeps the wing motion coordinated.'),
            'octopus': ('Arms, not legs', 'Why does this rig need a different body plan?',
                        'Arms extend from the body instead of four walking legs.',
                        'Changing the rig changes the outline and the motion.'),
            'bird': ('A winged rig', 'What changes when a model needs wings?',
                     'Wing parts rotate around the body as time advances.',
                     'The same body can make new poses by changing joint angles.'),
            'elephant': ('A trunk silhouette', 'What separates this model from a generic mammal?',
                         'The trunk extends the outline in front of the head.',
                         'Distinctive parts help a simple model stay recognizable.'),
            'serpent': ('A curved body', 'How can linked shapes suggest a snake?',
                        'Body segments follow a curve instead of a walking-leg rig.',
                        'Changing the curve changes the entire silhouette.'),
        }.get(_morphology(result),
              ('Shapes into motion', 'How does this simple 3D model come alive?',
               'Each body part has a position, size and rotation in 3D.',
               'Depth and surface lighting turn those shapes into this 2D image.'))
    else:
        focus = ('Drawing a pose', 'How does this 2D animal change its pose?',
                 'Joint positions guide the shapes drawn on each frame.',
                 'A sequence of poses becomes a Python/Pillow animation.')
    result['story_focus'] = focus[0]
    result['story_beats'] = list(focus[1:])
    result['yt_title'] = (f"{result.get('name', 'Animal').title()}: {focus[0]} | "
                          f"Procedural {result['resolved_renderer'].upper()} #Shorts")[:100]
    result['yt_desc'] += '\n\nModel breakdown: ' + ' '.join(result['story_beats'])
    return result


@dataclass
class Part:
    center: np.ndarray
    radii: np.ndarray
    basis: np.ndarray
    color: tuple[int, int, int]
    texture: str = "skin"
    shine: float = 0.1
    role: str = "body"


def _unit(v):
    a = np.asarray(v, dtype=np.float32)
    return a / max(float(np.linalg.norm(a)), 1e-8)


def _build_specific_rig(kind: str, seconds: float) -> list[Part]:
    """Species-specific rig construction. X=length, Y=width, Z=height."""
    parts: list[Part] = []

    def ell(center, radii, color, texture="skin", shine=0.1, basis=None):
        parts.append(Part(np.array(center, dtype=np.float32),
                          np.array(radii, dtype=np.float32),
                          np.eye(3, dtype=np.float32) if basis is None else basis,
                          color, texture, shine))

    def bone(a, b, radius, color, texture="skin", thickness=None):
        a, b = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
        axis = _unit(b - a)
        other = _unit(np.cross(axis, [0, 0, 1] if abs(axis[2]) < 0.95 else [0, 1, 0]))
        basis = np.column_stack((axis, other, np.cross(axis, other)))
        ell((a+b)/2, (np.linalg.norm(b-a)/2+radius*0.6,
                      radius, thickness or radius), color, texture, basis=basis)

    def eyes(x, width, z, radius=0.06, iris=(186, 142, 45)):
        for side in (-1, 1):
            ell((x, side*width, z), (radius*1.5, radius*0.7, radius*1.1), (24, 19, 15), "solid")
            ell((x+radius*0.18, side*(width+radius*0.45), z),
                (radius, radius*0.45, radius*0.85), iris, "solid", 0.6)
            ell((x+radius*0.3, side*(width+radius*0.7), z),
                (radius*0.3, radius*0.2, radius*0.72), (7, 9, 7), "solid", 0.9)

    phase = seconds * 2.3
    if kind in {"tiger", "lion"}:
        fur = (205, 122, 39) if kind == "tiger" else (176, 135, 74)
        texture = "stripes" if kind == "tiger" else "fur"
        cream = (223, 213, 184)
        # Separate chest, lumbar mass, haunches and belly, not one generic tube.
        ell((0, 0, 1.07), (1.09, 0.37, 0.44), fur, texture)
        ell((0.67, 0, 1.11), (0.45, 0.42, 0.53), fur, texture)
        ell((-0.78, 0, 1.08), (0.44, 0.38, 0.43), fur, texture)
        ell((0.10, 0, 0.80), (0.80, 0.30, 0.21), cream, "fur")
        for front in (False, True):
            for side in (-1, 1):
                x = 0.74 if front else -0.80
                p = phase + (0 if side == 1 else math.pi) + (math.pi if front else 0)
                swing = math.sin(p)*0.15
                lift = max(0, math.cos(p))*0.075
                shoulder = (x, side*0.28, 1.10)
                knee = (x + (-0.12 if front else 0.18) + swing*0.5, side*0.32, 0.56)
                ankle = (x + swing, side*0.34, 0.20+lift)
                bone(shoulder, knee, 0.18 if front else 0.22, fur, texture)
                bone(knee, ankle, 0.105, fur, texture)
                ell((ankle[0]+0.055, ankle[1], 0.13+lift), (0.21, 0.13, 0.115), cream, "fur")
                for toe in (-0.065, 0, 0.065):
                    ell((ankle[0]+0.17, ankle[1]+toe, 0.12+lift), (0.065, 0.033, 0.056), fur, texture)
        bone((0.72, 0, 1.17), (1.16, 0, 1.49), 0.31, fur, texture)
        if kind == "lion":
            # Mane and throat ruff are specific to the male African lion rig.
            ell((1.02, 0, 1.47), (0.49, 0.48, 0.60), (83, 50, 25), "mane")
            for angle in np.linspace(0, math.tau, 20, endpoint=False):
                ell((1.02, math.cos(angle)*0.38, 1.47+math.sin(angle)*0.48),
                    (0.35, 0.13, 0.20), (112, 68, 28), "mane")
        ell((1.31, 0, 1.53), (0.36, 0.31, 0.34), fur, texture)
        for side in (-1, 1):
            ell((1.15, side*0.24, 1.80), (0.13, 0.075, 0.15), (42, 30, 22), "fur")
            ell((1.18, side*0.25, 1.82), (0.07, 0.045, 0.09), cream, "fur")
            ell((1.56, side*0.13, 1.38), (0.23, 0.145, 0.15), cream, "fur")
        ell((1.67, 0, 1.47), (0.09, 0.13, 0.07), (49, 27, 25), "solid", 0.35)
        ell((1.52, 0, 1.28), (0.20, 0.17, 0.055), cream, "fur")
        eyes(1.47, 0.269, 1.62, 0.056)
        prev = (-1.02, 0, 1.13)
        for i in range(1, 17):
            u = i/16
            point = (-1.02-u*1.05, math.sin(u*2.4+phase*0.5)*0.24, 1.13-u*0.77+u*u*0.26)
            bone(prev, point, 0.07-u*0.034, fur, texture)
            prev = point
        if kind == "lion":
            ell(prev, (0.13, 0.10, 0.10), (54, 37, 24), "mane")

    elif kind == "turtle":
        skin = (110, 125, 73)
        # Four flattened flippers, shell, short neck, beak and small tail.
        ell((0, 0, 0.79), (1.03, 0.77, 0.26), (173, 150, 91), "scales")
        ell((-0.05, 0, 0.99), (1.11, 0.80, 0.44), (91, 113, 62), "shell", 0.28)
        bone((0.76, 0, 0.91), (1.25, 0, 0.91), 0.19, skin, "scales")
        ell((1.33, 0, 0.94), (0.30, 0.21, 0.22), skin, "scales")
        ell((1.57, 0, 0.88), (0.11, 0.16, 0.10), (158, 150, 95), "scales")
        eyes(1.41, 0.18, 1.02, 0.047, (47, 43, 23))
        for side in (-1, 1):
            flap = math.sin(phase+side*0.45)*0.20
            bone((0.53, side*0.54, 0.83), (0.02, side*1.44, 0.63+flap),
                 0.22, skin, "scales", thickness=0.065)
            bone((-0.71, side*0.50, 0.79), (-1.01, side*0.93, 0.67-flap*0.4),
                 0.16, skin, "scales", thickness=0.058)
        bone((-0.99, 0, 0.77), (-1.36, 0, 0.72), 0.06, skin, "scales")

    elif kind == "spider":
        brown, orange = (39, 29, 27), (190, 80, 38)
        ell((-0.48, 0, 0.71), (0.66, 0.43, 0.44), brown, "hair", 0.15)
        ell((0.30, 0, 0.65), (0.41, 0.34, 0.25), (80, 46, 31), "hair")
        # Exactly eight legs, three segments each; two shorter pedipalps.
        for side in (-1, 1):
            for i in range(4):
                x = 0.50-i*0.23
                spread = 0.92-i*0.59
                lift = max(0, math.sin(phase*1.6+i*math.pi/2+side*math.pi))*0.11
                root = (x, side*0.20, 0.65)
                knee = (x+spread*0.57, side*0.88, 0.79)
                ankle = (x+spread*0.84, side*1.22, 0.39+lift)
                toe = (x+spread, side*1.51, 0.08+lift)
                bone(root, knee, 0.103, brown, "hair")
                ell(knee, (0.13, 0.14, 0.12), orange, "hair")
                bone(knee, ankle, 0.079, brown, "hair")
                ell(ankle, (0.095, 0.10, 0.09), orange, "hair")
                bone(ankle, toe, 0.05, brown, "hair")
            bone((0.58, side*0.17, 0.59), (0.96, side*0.32, 0.24), 0.075, brown, "hair")
            ell((0.66, side*0.10, 0.48), (0.13, 0.07, 0.17), (22, 18, 17), "solid")
        for i in range(8):
            ell((0.62+(i//4)*0.032, (i%4-1.5)*0.069, 0.76-(i//4)*0.04),
                (0.033, 0.029, 0.035), (7, 7, 6), "solid", 0.85)

    elif kind == "gecko":
        skin = (219, 171, 72)
        ell((0, 0, 0.44), (0.79, 0.28, 0.26), skin, "spots")
        ell((0.86, 0, 0.47), (0.41, 0.28, 0.23), skin, "spots")
        ell((1.11, 0, 0.42), (0.23, 0.22, 0.14), (228, 191, 114), "scales")
        for side in (-1, 1):
            ell((0.90, side*0.243, 0.57), (0.13, 0.079, 0.13), (215, 181, 102), "scales")
        eyes(0.94, 0.288, 0.57, 0.083, (154, 142, 81))
        for front in (True, False):
            for side in (-1, 1):
                x = 0.49 if front else -0.50
                move = math.sin(phase+(0 if front else math.pi)+side*math.pi/2)*0.11
                root = (x, side*0.20, 0.42)
                elbow = (x-0.22, side*0.50, 0.27)
                foot = (x+move+0.08, side*0.76, 0.09)
                bone(root, elbow, 0.10, skin, "spots")
                bone(elbow, foot, 0.069, skin, "spots")
                # Leopard geckos have five clawed toes, not adhesive toe pads.
                for toe in range(5):
                    tip = (foot[0]+(toe-2)*0.068, foot[1]+side*(0.12-abs(toe-2)*0.018), 0.06)
                    bone(foot, tip, 0.021, (211, 176, 105), "scales")
        prev = (-0.59, 0, 0.42)
        for i in range(1, 20):
            u = i/19
            point = (-0.59-u*1.54, math.sin(u*2.5+phase*0.6)*u*0.24, 0.38-u*0.23)
            radius = 0.19*math.sin(math.pi*(0.17+u*0.81))+0.018
            bone(prev, point, radius, skin, "spots")
            prev = point
    else:
        raise ValueError(f"No procedural anatomy for {kind}")
    return parts



def _generic_rig(species: dict, seconds: float) -> list[Part]:
    """Construct an anatomy-shaped rig for any encyclopedia morphology.

    This is a deliberately offline fallback: it does not claim a scanned or
    photorealistic model.  Species metadata drives proportions and distinctive
    appendages so hundreds of encyclopedia entries can render without an API.
    """
    parts: list[Part] = []
    phase = seconds * 2.1
    morph = _morphology(species)
    if morph not in GENERIC_3D_MORPHOLOGIES:
        raise ValueError(f"Unsupported generic morphology: {morph}")
    accent = tuple(int(max(20, min(240, c))) for c in species.get("accent", [125, 145, 105]))
    shade = lambda d: tuple(max(15, min(245, int(c*d))) for c in accent)
    dark, light = shade(.58), shade(1.22)

    def ell(c, r, color=accent, texture="skin", shine=.08, role="body"):
        parts.append(Part(np.array(c, dtype=np.float32), np.array(r, dtype=np.float32),
                          np.eye(3, dtype=np.float32), color, texture, shine, role))

    def bone(a, b, radius, color=accent, texture="skin", role="body"):
        a, b = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
        axis = _unit(b-a)
        other = _unit(np.cross(axis, [0,0,1] if abs(axis[2]) < .95 else [0,1,0]))
        basis = np.column_stack((axis, other, np.cross(axis, other)))
        parts.append(Part((a+b)/2, np.array([np.linalg.norm(b-a)/2+radius*.55,radius,radius],dtype=np.float32), basis, color, texture, role=role))

    def eyes(x, y, z, radius=.07):
        for side in (-1,1):
            ell((x, side*y, z), (radius, radius*.55, radius), (18,16,12), "solid", .7)
            ell((x+.02, side*(y+radius*.4), z+.01), (radius*.35,radius*.2,radius*.45), (235,220,150), "solid", .9)

    # Soft-bodied animals must dispatch BEFORE broad aquatic/class fallbacks.
    if morph in {"octopus", "squid", "cuttlefish", "cephalopod"}:
        octopus = morph in {"octopus", "cephalopod"}
        ell((-.35, 0, .90), (.62 if octopus else .98, .40, .43), accent, "skin", .25, role="mantle")
        ell((.32, 0, .76), (.30, .30, .27), light, role="head")
        eyes(.44, .26, .85, .085)
        # Eight arms for octopus; squid/cuttlefish also have two long tentacles.
        count = 8 if octopus else 10
        for arm in range(count):
            angle = math.tau * arm / count
            length = 1.20 if octopus or arm < 8 else 1.85
            prev = (.38, math.cos(angle)*.22, .74+math.sin(angle)*.16)
            role = "arm" if arm < 8 else "tentacle"
            for segment in range(1, 9):
                u = segment / 8
                pt = (.38+length*u, math.cos(angle)*(.22+u*.65),
                      .74+math.sin(angle)*.16-u*.30+math.sin(phase+u*4+angle)*u*.13)
                bone(prev, pt, .075*(1-u*.72), accent, role=role)
                prev = pt
        if not octopus:
            for side in (-1, 1):
                ell((-.70, side*.39, .93+math.sin(phase)*.07),
                    (.54, .25, .07), light, role="fin")
        return parts

    if morph == "jellyfish":
        pulse = 1 + .10*math.sin(phase)
        ell((0, 0, 1.35), (.72*pulse, .65*pulse, .38/pulse), light, "skin", .35, role="bell")
        for arm in range(12):
            angle = math.tau*arm/12
            prev = (.48*math.cos(angle), .43*math.sin(angle), 1.21)
            for segment in range(1, 9):
                u = segment/8
                pt = (.48*math.cos(angle)+.14*u*math.sin(phase+u*4+angle),
                      .43*math.sin(angle)+.09*u*math.cos(phase+u*3), 1.21-u*.98)
                bone(prev, pt, .024, accent, role="tentacle")
                prev = pt
        return parts

    # Aquatic and elongated morphologies.
    if morph in {"fish", "eel", "marine_mammal", "shark", "ray", "seahorse", "aquatic"}:
        if morph == "ray":
            ell((0,0,.72),(1.05,.95,.20),accent,"scales")
            bone((-.8,0,.72),(-1.55,0,.68),.08,dark,"scales")
            for side in (-1,1):
                ell((-.05, side*.77, .72+math.sin(phase)*.18), (.86,.63,.09), light, "scales", role="fin")
            eyes(.65,.22,.88,.055)
        elif morph == "seahorse":
            ell((0,0,.78),(.35,.28,.72),accent,"scales")
            for i in range(10):
                u=i/9; ang=u*math.tau*1.2
                ell((-.2-math.sin(ang)*.35,math.sin(phase+u*3)*u*.07,.30+u*.50),(.10,.11,.13),dark,"scales", role="tail")
            ell((.35,0,1.35),(.25,.18,.18),light,"scales"); eyes(.47,.16,1.40,.04)
        else:
            body_len = 1.35 if morph != "shark" else 1.55
            ell((0,0,.75),(body_len,.42,.34),accent,"scales",.18)
            ell((body_len*.82,0,.77),(.38,.30,.27),light,"scales")
            if morph != "eel":
                sway = math.sin(phase)*.22
                mammal = morph == "marine_mammal"
                for side in (-1, 1):
                    ell((.15, side*.52, .68+math.sin(phase)*.04),
                        (.40,.30,.06), accent, "skin", role="fin")
                bone((-1.0,0,.75), (-1.45, 0 if mammal else sway, .75+sway if mammal else .75),
                     .14, accent, role="tail")
                for side in (-1, 1):
                    ell((-1.52, side*.25 if mammal else sway,
                         .75+sway if mammal else .75+side*.22),
                        (.28,.34,.065) if mammal else (.28,.065,.30), accent, role="fluke" if mammal else "fin")
                ell((-.20,0,1.13), (.31,.06,.23), dark, role="dorsal_fin")
            if morph != "eel":
                eyes(body_len*.78,.25,.87,.05)
            else:
                prev=(-.8,0,.75)
                for i in range(1,14):
                    u=i/13; pt=(-.8-u*1.9, math.sin(u*4+phase)*.18, .75-u*.18)
                    bone(prev,pt,.11*(1-u*.55),accent,"scales"); prev=pt
        return parts

    # Arthropods: number of legs is derived from biological class.
    if morph in {"spider", "scorpion", "beetle", "crab", "bee_wasp", "butterfly", "dragonfly", "orthoptera", "ant", "mantis", "lobster", "shrimp", "insect", "arachnid", "crustacean"}:
        if morph in {"butterfly","dragonfly","bee_wasp"}:
            ell((0,0,.78),(.38,.22,.30),dark,"hair")
            for side in (-1,1):
                flap = math.sin(phase*3)*.27
                ell((-.05,side*.48,1.00+flap),(.48,.65,.07),light,"scales", role="wing")
                ell((.30,side*.42,.91+flap),(.40,.58,.05),accent,"scales", role="wing")
            for side in (-1,1):
                for i in range(3): bone((-.15+i*.18,side*.18,.68),(-.25+i*.2,side*(.55+i*.08),.25),.035,dark,"solid", role="leg")
            ell((.42, 0, .81), (.20,.20,.19), accent, role="head")
            eyes(.49,.15,.88,.035)
        else:
            ell((-.28,0,.70),(.52,.38,.36),dark,"hair",.12)
            ell((.36,0,.72),(.38,.30,.28),accent,"hair")
            nlegs = 8 if morph in {"spider", "scorpion", "arachnid"} else 6
            crustacean = morph in {"crab", "lobster", "shrimp", "crustacean"}
            # Decapods: four walking pairs plus chelipeds; shrimp has five pairs.
            if crustacean: nlegs = 10 if morph == "shrimp" else 8
            for side in (-1,1):
                for i in range(nlegs//2):
                    x=-.45+i*.28; lift=math.sin(phase+i)*.06
                    bone((x,side*.25,.66),(x-.10,side*(.60+.08*i),.48+lift),.045,dark,"hair", role="leg_upper")
                    bone((x-.10,side*(.60+.08*i),.48+lift),(x+.12,side*(.92+.10*i),.16+lift),.035,accent,"hair", role="leg_lower")
            if morph == "scorpion":
                prev = (-.60,0,.77)
                for i in range(1,9):
                    u=i/8; pt=(-.60-.65*math.sin(u*math.pi*.8),.06*math.sin(phase)*u,.77+u*.85)
                    bone(prev,pt,.08*(1-u*.55),dark,role="tail"); prev=pt
            if (crustacean and morph != "shrimp") or morph == "scorpion":
                for side in (-1,1):
                    bone((.46,side*.20,.68),(.87,side*.66,.64),.075,accent,role="cheliped")
                    ell((1.02,side*.70,.66),(.23,.14,.12),light,role="claw")
            if morph in {"lobster", "shrimp"}:
                for i in range(7):
                    ell((-.55-i*.13,math.sin(phase-i*.25)*i*.016,.69-i*.035),
                        (.17,.28-i*.025,.19-i*.016),accent,role="abdomen")
                for side in (-1,1):
                    bone((.58,side*.12,.84),(1.50,side*.50,1.04),.018,light,role="antenna")
            eyes(.55,.20,.84,.035)
        return parts

    # Birds: compact body, neck/head, wings and two legs.
    if morph == "bird":
        ell((0,0,.95),(.72,.42,.52),accent,"feathers")
        ell((.58,0,1.18),(.30,.25,.28),light,"feathers")
        for side in (-1,1):
            ell((-.05,side*.42,1.02+math.sin(phase)*.10),(.62,.10,.35),accent,"feathers", role="wing")
            stride = math.sin(phase+side*math.pi/2)*.12
            bone((.05,side*.18,.62),(-.02+stride,side*.23,.28),.055,dark,"solid", role="leg")
            ell((.10+stride,side*.24,.22),(.16,.10,.05),dark,"solid", role="foot")
        bone((.86,0,1.20),(1.28,0,1.22),.05,light,"solid")
        eyes(.73,.20,1.31,.045)
        return parts

    # Serpents.
    if morph == "serpent":
        prev=(-1.4,0,.52)
        for i in range(1,22):
            u=i/21; pt=(-1.4+u*2.8, math.sin(u*math.tau*2+phase)*.28, .52+.05*math.sin(u*math.pi))
            bone(prev,pt,.17*(.45+.55*math.sin(math.pi*(.1+.9*u))),accent,"scales"); prev=pt
        ell((1.38,0,.55),(.25,.18,.18),light,"scales"); eyes(1.48,.13,.62,.035)
        return parts

    # Reptiles/amphibians/crocodilians.
    if morph in {"lizard", "frog", "crocodile", "turtle", "chameleon", "reptile", "amphibian"}:
        ell((0,0,.68),(.90,.42,.34),accent,"scales")
        headx=.75 if morph != "crocodile" else 1.02
        ell((headx,0,.78),(.38,.34,.30),light,"scales")
        eyes(headx+.15,.25,.91,.05)
        if morph == "turtle": ell((-.05,0,.88),(1.02,.68,.28),dark,"shell",.2)
        for side in (-1,1):
            for x in (.55,-.55):
                stride = math.sin(phase+(0 if x>0 else math.pi)+side*math.pi/2)*.12
                bone((x,side*.28,.60),(x-.15+stride,side*.60,.32),.08,accent,"scales", role="leg")
                ell((x-.18+stride,side*.67,.28),(.20,.10,.07),light,"scales", role="foot")
        if morph not in {"frog", "amphibian"}:
            prev = (-.75,0,.62)
            for i in range(1,11):
                u=i/10; length=.35 if morph=="turtle" else 1.30
                pt=(-.75-length*u,math.sin(phase+u*3)*u*.16,.62-u*.32)
                bone(prev,pt,.14*(1-u*.8),accent,"scales",role="tail"); prev=pt
        if morph == "crocodile":
            ell((1.42,0,.68),(.53,.21,.12),accent,"scales",role="snout")
        return parts

    # Only known terrestrial profiles may reach this branch.
    terrestrial = {"small_mammal", "cervid_bovid", "primate", "bear", "kangaroo",
                   "equine", "camelid", "rhino", "pachyderm", "elephant", "giraffe",
                   "canine", "feline", "hippo", "quadruped"}
    if morph not in terrestrial:
        raise ValueError(f"No anatomy branch for {morph}")
    tall = morph in {"giraffe","camelid","equine","rhino","pachyderm","elephant","cervid_bovid"}
    body_len = 1.15 if tall else .95
    bulky = morph in {"bear", "hippo", "rhino", "elephant"}
    body_h = .57 if bulky else (.52 if tall else .43)
    texture = "skin" if morph in {"hippo", "rhino", "elephant", "pachyderm"} else "fur"
    ell((0,0,1.00 if tall else .82),(body_len,.56 if bulky else .43,body_h),accent,texture,.10)
    head_z = 2.12 if morph == "giraffe" else (1.65 if morph == "camelid" else 1.30)
    head_x = body_len*.98
    bone((body_len*.55,0,1.07),(head_x-.12,0,head_z),.25,light,texture,role="neck")
    ell((head_x,0,head_z),(.38,.30,.31),light,texture,role="head")
    eyes(body_len*1.10,.23,head_z+.10,.055)
    for front in (True,False):
        for side in (-1,1):
            x=.60 if front else -.62
            hip=(x,side*.28,.90 if tall else .76)
            gait = phase+(0 if front else math.pi)+side*math.pi/2
            swing, lift = math.sin(gait)*.15, max(0,math.cos(gait))*.08
            knee=(x+.05+swing*.5,side*.34,.48+lift*.5)
            paw=(x+.10+swing,side*.33,.12+lift)
            if morph == "kangaroo" and front:
                hip=(.56,side*.25,1.18); knee=(.83,side*.32,.93)
                paw=(1.02+swing*.25,side*.33,.75)
            bone(hip,knee,.17 if bulky else (.13 if tall else .11),accent,texture,role="leg_upper")
            bone(knee,paw,.12 if bulky else .09,accent,texture,role="leg_lower")
            ell((paw[0]+.08,paw[1],paw[2]-.02),(.30 if morph=="kangaroo" and not front else .18,.12,.08),dark,"solid",role="foot")
    # Tail, ears/horns and species-driven accents.
    prev=(-body_len*.9,0,1.02 if tall else .86)
    short_tail = morph in {"bear", "hippo", "primate"}
    for i in range(1,10):
        u=i/9; pt=(prev[0]-(.035 if short_tail else .12), math.sin(phase+u*3)*.12*u, prev[2]-.05*u)
        bone(prev,pt,(.13 if morph=="kangaroo" else .07)*(1-u*.65),accent,texture,role="tail"); prev=pt
    for side in (-1,1):
        ell((head_x-.12,side*.28,head_z+.23),
            (.16,.25,.28) if morph=="elephant" else (.12,.08,.16),accent,texture,role="ear")
    if morph in {"cervid_bovid","giraffe"}:
        for side in (-1,1):
            bone((head_x,side*.13,head_z+.18),(head_x,side*.18,head_z+.48),.045,dark,"solid",role="horn")
    if morph == "rhino":
        # Nasal horns are on the midline, not two giraffe-like head antlers.
        for x, height in ((head_x+.31,.46),(head_x+.05,.24)):
            bone((x,0,head_z+.08),(x+.04,0,head_z+.08+height),.08,dark,role="nasal_horn")
    if morph == "elephant":
        prev=(head_x+.25,0,head_z-.04)
        for i in range(1,13):
            u=i/12; pt=(head_x+.30+.20*u,math.sin(phase+u*2)*u*.09,head_z-.04-u*.94)
            bone(prev,pt,.12*(1-u*.55),accent,role="trunk"); prev=pt
        for side in (-1,1):
            bone((head_x+.22,side*.21,head_z-.13),(head_x+.72,side*.25,head_z-.28),.055,(227,221,190),role="tusk")
    if morph == "camelid":
        name = str(species.get('name', '')).upper()
        if 'CAMEL' in name:
            for x in ((-.40,.30) if 'BACTRIAN' in name else (0,)):
                ell((x,0,1.44),(.38,.34,.37),accent,"fur",role="hump")
    return parts


def build_rig(kind: str, seconds: float, species: dict | None = None) -> list[Part]:
    """Build a specific rig when available, otherwise a morphology rig."""
    if not math.isfinite(seconds):
        raise ValueError("A finite motion timestamp is required")
    # A morphology named 'turtle'/'spider' is not the exact sea-turtle/tarantula
    # species. Preserve the old direct build_rig(kind, t) API for dedicated rigs.
    if species is None:
        if kind in SUPPORTED_SPECIES.values():
            return _build_specific_rig(kind, seconds)
        raise ValueError(f"No species metadata for generic rig: {kind}")
    dedicated = SUPPORTED_SPECIES.get(str(species.get('name', '')).strip().upper())
    if dedicated:
        return _build_specific_rig(dedicated, seconds)
    parts = _generic_rig(species, seconds)
    # Apply bounded proportions from the actual nested catalog metadata. The
    # previous seed was read from the wrong level and its RNG was never used.
    anatomy = species.get('bone_structure') or {}
    skull, limbs = anatomy.get('skull', {}), anatomy.get('limbs', {})
    def proportion(value, reference):
        return float(np.clip(float(value) / reference, .88, 1.12))
    stretch = np.array([proportion(skull.get('length', 36), 36),
                        proportion(skull.get('width', 26), 26),
                        proportion(limbs.get('upper_bone_len', 42), 42)], dtype=np.float32)
    for part in parts:
        part.center *= stretch
        # Scale in local principal axes to retain orthonormal ray transforms.
        part.radii *= np.linalg.norm(stretch[:, None] * part.basis, axis=0)
    return parts

def _material(part: Part, local: np.ndarray) -> np.ndarray:
    """Procedural surface detail anchored to geometry, not screen pixels."""
    p = local * part.radii
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    noise = np.sin(x*163+y*117+z*97)*np.sin(x*91-y*131+z*73)
    color = np.broadcast_to(np.array(part.color, dtype=np.float32)/255,
                            local.shape).copy()
    texture = part.texture
    if texture == "stripes":
        phase = x*23 + 1.8*np.sin(z*8+y*5) + 0.5*np.sin(x*41)
        stripes = np.sin(phase) > 0.67 + 0.15*np.sin(y*17)
        color *= np.where(stripes, 0.17, 1.0)[..., None]
    elif texture == "spots":
        # Rounded, irregular dark spots over fine granular gecko skin.
        spots = np.sin(x*28+np.sin(z*19))*np.sin(y*36+z*14) > 0.68
        color *= np.where(spots, 0.19, 1.0)[..., None]
    elif texture == "shell":
        # Staggered polygonal scutes rather than a generic smooth shell.
        u = x*4.3
        v = y*5.4
        row = np.floor(v)
        fu = (u+0.5*(row % 2)) % 1
        fv = v % 1
        seam = (np.minimum(fu, 1-fu) < 0.035) | (np.minimum(fv, 1-fv) < 0.045)
        ring = np.sin((fu-0.5)**2*40+(fv-0.5)**2*30)
        color *= (0.90+0.13*ring)[..., None]
        color *= np.where(seam, 0.37, 1.0)[..., None]
    elif texture == "scales":
        scale = np.sin(x*100+y*70)*np.sin(y*110-z*80)
        color *= (0.94+scale*0.09)[..., None]
    elif texture in {"hair", "mane", "fur"}:
        hair = np.sin(x*370+np.sin(y*23)*4+z*47)
        color *= (0.93+hair*0.10)[..., None]
    if texture != "solid":
        color *= (0.97+0.035*noise)[..., None]
    return np.clip(color, 0, 1)


def render_animal_layer(species: dict, seconds: float, size=(860, 520),
                        quality: str = "standard", yaw: float | None = None) -> Image.Image:
    """RGBA 3D animal + soft contact shadow, deterministic at any timestamp.

    Quality is an INTERNAL resolution multiplier. High supersamples the
    supplied viewport. Video dimensions are controlled by the 2D compositor.
    yaw is in radians and exposed for repeatable inspection of the 3D volume.
    """
    if not supports_species(species):
        raise ValueError(f"Unsupported 3D species: {species.get('name')}")
    if quality not in QUALITY_SCALE:
        raise ValueError(f"Unknown 3D quality: {quality}")
    if not math.isfinite(seconds) or min(size) < 1:
        raise ValueError("A finite timestamp and positive image size are required")
    kind = SUPPORTED_SPECIES.get(species["name"].strip().upper(), _morphology(species))
    plan = species.get('unique_plan')
    motion_time = species.get('motion_time', seconds)
    parts = build_rig(kind, motion_time, species)
    if plan:
        tint = (1.04, .98, .91) if 'warm natural' in plan['color_pattern'] else ((.93, 1., 1.04) if 'cool natural' in plan['color_pattern'] else (1., 1., 1.))
        body_scale = .88 if plan['size'] == 'compact' else 1.
        for part in parts:
            part.color = tuple(min(255, round(c * t)) for c, t in zip(part.color, tint))
            part.center *= body_scale
            part.radii *= body_scale
    multiplier = QUALITY_SCALE[quality]
    w, h = max(1, round(size[0]*multiplier)), max(1, round(size[1]*multiplier))
    scale = min(w/5.6, h/3.8)
    angle = (-0.35+0.16*math.sin(seconds*0.55)) if yaw is None else yaw
    elevation = 0.36 if kind in {"tiger", "lion"} else 0.80
    if plan and yaw is None:
        angle = {'side': -.1, 'front oblique': .85, 'high angle': -.45, 'low angle': .25}[plan['camera_angle']]
        elevation = {'side': .36, 'front oblique': .45, 'high angle': 1.05, 'low angle': .18}[plan['camera_angle']]
        if plan['camera_movement'] == 'orbit':
            angle += .35 * math.sin(seconds * .45)
        if plan['camera_movement'] == 'tracking':
            angle += .08 * math.sin(seconds * .5)
    c, s, ce, se = math.cos(angle), math.sin(angle), math.cos(elevation), math.sin(elevation)
    view = np.array([[c, s, 0], [-s*se, c*se, ce], [s*ce, -c*ce, se]], dtype=np.float32)
    target = np.array([-0.15, 0, 0.83 if kind in {"tiger", "lion"} else (0.80 if species.get("morphology") in {"giraffe","camelid","equine","cervid_bovid"} else 0.57)], dtype=np.float32)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    depth = np.full((h, w), np.inf, dtype=np.float32)
    if plan:
        target[0] -= species.get('composition_x', 0) * 3.0
    lighting = plan['lighting'] if plan else 'daylight'
    light = _unit({'sunrise': [-.9, .3, .45], 'sunset': [.9, .4, .35],
                   'moonlight': [.2, -.6, .95]}.get(lighting, [-.45, .72, .90]))
    half_vector = _unit(light + np.array([0, 0, 1]))
    direction = np.array([0, 0, -1], dtype=np.float32)

    shadow = Image.new("RGBA", (w, h))
    shadow_draw = ImageDraw.Draw(shadow)
    for part in parts:
        if max(part.radii) < 0.12:
            continue
        foot = part.center.copy()
        foot[2] = 0
        q = view @ (foot-target)
        cx, cy = w*0.5+q[0]*scale, h*0.51-q[1]*scale
        radius = max(part.radii)*scale
        shadow_draw.ellipse((cx-radius, cy-radius*0.30, cx+radius, cy+radius*0.30),
                            fill=(0, 0, 0, 72))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(1, scale*0.045)))

    for part in parts:
        center = view @ (part.center-target)
        basis = view @ part.basis
        extent = np.sqrt(np.sum((basis*part.radii)**2, axis=1))
        x0 = max(0, int(w*0.5+(center[0]-extent[0])*scale)-1)
        x1 = min(w, int(w*0.5+(center[0]+extent[0])*scale)+2)
        y0 = max(0, int(h*0.51-(center[1]+extent[1])*scale)-1)
        y1 = min(h, int(h*0.51-(center[1]-extent[1])*scale)+2)
        if x0 >= x1 or y0 >= y1:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        origin = np.stack(((xx+0.5-w*0.5)/scale,
                           (h*0.51-yy-0.5)/scale, np.full_like(xx, 8.0)), axis=-1)
        local_origin = ((origin-center) @ basis)/part.radii
        local_dir = (direction @ basis)/part.radii
        a = float(np.dot(local_dir, local_dir))
        b = 2*np.sum(local_origin*local_dir, axis=-1)
        cc = np.sum(local_origin**2, axis=-1)-1
        discriminant = b*b-4*a*cc
        distance = (-b-np.sqrt(np.maximum(discriminant, 0)))/(2*a)
        old_depth = depth[y0:y1, x0:x1]
        visible = (discriminant >= 0) & (distance > 0) & (distance < old_depth)
        if not visible.any():
            continue
        local_hit = local_origin + distance[..., None]*local_dir
        normal = (local_hit/part.radii) @ basis.T
        normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-8)
        diffuse = np.maximum(normal @ light, 0)
        # Broad key, cool fill and restrained specular; no fake neon body glow.
        fill = np.maximum(normal @ _unit([0.8, 0.1, 0.5]), 0)*0.16
        specular = np.maximum(normal @ half_vector, 0)**(18+part.shine*60)*part.shine
        base = _material(part, local_hit)
        lit = base*(0.26+0.72*diffuse+fill)[..., None]
        lit += specular[..., None]*np.array([1.0, 0.95, 0.84])
        lit = np.clip(lit, 0, 1)**0.88
        patch = rgba[y0:y1, x0:x1]
        patch[..., :3][visible] = (lit[visible]*255).astype(np.uint8)
        patch[..., 3][visible] = 255
        old_depth[visible] = distance[visible]
    animal = Image.fromarray(rgba)
    result = Image.alpha_composite(shadow, animal)
    return result.resize(size, Image.Resampling.LANCZOS)
