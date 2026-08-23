"""
Procedural Animal Vector Engine
Draws and animates full animals procedurally via Python math, geometry, and PIL.
No static photos, no external APIs required.
"""
from __future__ import annotations

import math
import random
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT, FPS = 720, 1280, 30

def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_candidates = [
        "/data/data/com.termux/files/home/teacher-bot-repo/assets/fonts/Montserrat-Bold.ttf" if bold else "/data/data/com.termux/files/home/teacher-bot-repo/assets/fonts/Montserrat-Regular.ttf",
        "/system/fonts/Roboto-Bold.ttf" if bold else "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/DroidSans.ttf",
        "assets/fonts/Montserrat-Bold.ttf" if bold else "assets/fonts/Montserrat-Regular.ttf",
    ]
    for p in font_candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

# ─────────────────────────────────────────────────────────────────────────────
# ANIMAL DEFINITIONS & FACT CATALOG
# ─────────────────────────────────────────────────────────────────────────────
SPECIES_CATALOG = [
    {
        "id": "tiger",
        "name": "Bengal Tiger",
        "title": "🐅 BENGAL TIGER",
        "accent": (245, 140, 35),
        "bg_top": (14, 45, 40),
        "bg_bot": (32, 68, 52),
        "facts": [
            "Every tiger's stripes are completely unique like human fingerprints.",
            "Their roar is so loud it can be heard 3 kilometers away.",
            "Tigers love water and are extraordinary long-distance swimmers."
        ],
        "tags": ["tiger", "bengaltiger", "bigcats", "wildlife", "animals"]
    },
    {
        "id": "panda",
        "name": "Giant Panda",
        "title": "🐼 GIANT PANDA",
        "accent": (70, 190, 130),
        "bg_top": (16, 38, 30),
        "bg_bot": (28, 58, 48),
        "facts": [
            "Pandas spend up to 14 hours every day just munching on bamboo.",
            "They have an evolved pseudo-thumb wrist bone for gripping stalks.",
            "A newborn panda cub is smaller than an apple and 1/900th its mom's weight!"
        ],
        "tags": ["panda", "giantpanda", "cuteanimals", "nature", "wildlife"]
    },
    {
        "id": "lion",
        "name": "African Lion",
        "title": "🦁 AFRICAN LION",
        "accent": (235, 175, 45),
        "bg_top": (45, 25, 15),
        "bg_bot": (75, 45, 20),
        "facts": [
            "A lion's magnificent dark mane signals health, age, and strength.",
            "Lions are the only cats that live in large social groups called prides.",
            "They can sleep up to 20 hours a day to conserve energy for hunts."
        ],
        "tags": ["lion", "kingofthejungle", "safari", "wildlife", "bigcats"]
    },
    {
        "id": "fox",
        "name": "Red Fox",
        "title": "🦊 RED FOX",
        "accent": (230, 95, 45),
        "bg_top": (25, 20, 40),
        "bg_bot": (48, 35, 65),
        "facts": [
            "Their bushy tail (brush) acts as a warm blanket in freezing weather.",
            "Foxes use Earth's magnetic field to accurately pounce on hidden prey.",
            "They communicate using over 28 different distinct vocalizations."
        ],
        "tags": ["fox", "redfox", "forest", "cuteanimals", "wildlife"]
    },
    {
        "id": "elephant",
        "name": "African Elephant",
        "title": "🐘 AFRICAN ELEPHANT",
        "accent": (140, 185, 210),
        "bg_top": (20, 32, 45),
        "bg_bot": (35, 55, 75),
        "facts": [
            "An elephant's trunk contains over 40,000 individual muscles!",
            "They recognize themselves in mirrors, demonstrating high self-awareness.",
            "Elephants communicate across miles using low infrasound vibrations."
        ],
        "tags": ["elephant", "africanelephant", "gentlegiant", "nature", "wildlife"]
    },
    {
        "id": "wolf",
        "name": "Timber Wolf",
        "title": "🐺 TIMBER WOLF",
        "accent": (160, 200, 230),
        "bg_top": (10, 18, 32),
        "bg_bot": (22, 38, 58),
        "facts": [
            "Wolf howls can be heard across 16 kilometers of open wilderness.",
            "Pack hierarchy is based on deep family loyalty and cooperation.",
            "They can travel over 60 kilometers in a single day without tiring."
        ],
        "tags": ["wolf", "timberwolf", "pack", "howl", "wildlife"]
    },
    {
        "id": "owl",
        "name": "Great Horned Owl",
        "title": "🦉 GREAT HORNED OWL",
        "accent": (235, 185, 80),
        "bg_top": (12, 14, 28),
        "bg_bot": (24, 28, 50),
        "facts": [
            "Specialized serrated wing feathers allow them to fly in complete silence.",
            "Owls can rotate their heads an incredible 270 degrees in either direction.",
            "Their eyes are tube-shaped, granting extraordinary telescopic night vision."
        ],
        "tags": ["owl", "nightbird", "predator", "nature", "wildlife"]
    },
    {
        "id": "giraffe",
        "name": "Giraffe",
        "title": "🦒 TALL GIRAFFE",
        "accent": (240, 180, 50),
        "bg_top": (35, 30, 18),
        "bg_bot": (65, 52, 28),
        "facts": [
            "Giraffes are the tallest mammals on Earth, standing up to 19 feet tall.",
            "Their 45 cm long prehensile tongue is dark blue to prevent sunburn.",
            "Despite their long neck, they have the exact same 7 neck vertebrae as humans."
        ],
        "tags": ["giraffe", "tall", "savannah", "animals", "wildlife"]
    },
    {
        "id": "orca",
        "name": "Orca (Killer Whale)",
        "title": "🌊 MAJESTIC ORCA",
        "accent": (90, 175, 235),
        "bg_top": (5, 20, 38),
        "bg_bot": (10, 48, 80),
        "facts": [
            "Orcas are actually the largest members of the oceanic dolphin family.",
            "Every pod has its own unique vocal dialect passed down generations.",
            "They hunt using strategic teamwork, coordinating complex water waves."
        ],
        "tags": ["orca", "killerwhale", "ocean", "marinelife", "wildlife"]
    },
    {
        "id": "bear",
        "name": "Grizzly Bear",
        "title": "🐻 GRIZZLY BEAR",
        "accent": (195, 125, 65),
        "bg_top": (30, 22, 18),
        "bg_bot": (55, 40, 30),
        "facts": [
            "Grizzly bears have a sense of smell 7 times stronger than a bloodhound.",
            "During hibernation, their heart rate drops from 40 to only 8 beats per minute.",
            "Despite weighing up to 350 kg, they can sprint at speeds of 55 km/h!"
        ],
        "tags": ["bear", "grizzly", "forest", "wildlife", "nature"]
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# SPECIES-SPECIFIC PROCEDURAL DRAWING ROUTINES
# ─────────────────────────────────────────────────────────────────────────────

def _draw_tiger(draw: ImageDraw.Draw, cx: float, cy: float, t: float, bobbing: float, breathing: float):
    # Wagging Tail
    tail_angle = math.sin(t * 3) * 0.4
    tail_pts = []
    tx, ty = cx + 110, cy + 90
    for s in range(6):
        curr_tx = tx + s * 22 + math.sin(tail_angle + s * 0.5) * (s * 10)
        curr_ty = ty - s * 14 + math.cos(tail_angle + s * 0.4) * (s * 6)
        tail_pts.append((curr_tx, curr_ty))
    for s in range(len(tail_pts) - 1):
        draw.line([tail_pts[s], tail_pts[s+1]], fill=(245, 140, 35), width=24 - s * 2)
    draw.ellipse([tail_pts[-1][0]-8, tail_pts[-1][1]-8, tail_pts[-1][0]+8, tail_pts[-1][1]+8], fill=(30, 25, 25))

    # Body
    draw.ellipse([cx - 120, cy - 20 + bobbing, cx + 120, cy + 150 + bobbing + breathing], fill=(245, 140, 35), outline=(210, 105, 20), width=3)
    draw.ellipse([cx - 70, cy + 30 + bobbing, cx + 70, cy + 145 + bobbing], fill=(255, 248, 235))

    # Paws
    for px in [cx - 75, cx + 75]:
        draw.ellipse([px - 35, cy + 120 + bobbing, px + 35, cy + 175 + bobbing], fill=(255, 248, 235), outline=(210, 105, 20), width=2)
        for dx in [-14, 0, 14]:
            draw.ellipse([px + dx - 6, cy + 152 + bobbing, px + dx + 6, cy + 167 + bobbing], fill=(245, 140, 35))

    # Ears
    ear_wiggle = math.sin(t * 3) * 3
    draw.polygon([(cx - 105, cy - 90 + bobbing), (cx - 130 + ear_wiggle, cy - 170 + bobbing), (cx - 50, cy - 120 + bobbing)], fill=(245, 140, 35), outline=(210, 105, 20))
    draw.polygon([(cx - 95, cy - 95 + bobbing), (cx - 118 + ear_wiggle, cy - 155 + bobbing), (cx - 60, cy - 118 + bobbing)], fill=(255, 180, 180))
    draw.polygon([(cx + 105, cy - 90 + bobbing), (cx + 130 - ear_wiggle, cy - 170 + bobbing), (cx + 50, cy - 120 + bobbing)], fill=(245, 140, 35), outline=(210, 105, 20))
    draw.polygon([(cx + 95, cy - 95 + bobbing), (cx + 118 - ear_wiggle, cy - 155 + bobbing), (cx + 60, cy - 118 + bobbing)], fill=(255, 180, 180))

    # Head
    draw.ellipse([cx - 125, cy - 135 + bobbing, cx + 125, cy + 55 + bobbing], fill=(245, 140, 35), outline=(210, 105, 20), width=3)
    draw.polygon([(cx - 125, cy - 20 + bobbing), (cx - 155, cy + 10 + bobbing), (cx - 100, cy + 35 + bobbing)], fill=(245, 140, 35))
    draw.polygon([(cx + 125, cy - 20 + bobbing), (cx + 155, cy + 10 + bobbing), (cx + 100, cy + 35 + bobbing)], fill=(245, 140, 35))

    # Stripes
    draw.polygon([(cx - 12, cy - 125 + bobbing), (cx + 12, cy - 125 + bobbing), (cx, cy - 95 + bobbing)], fill=(40, 30, 25))
    draw.polygon([(cx - 28, cy - 115 + bobbing), (cx - 12, cy - 112 + bobbing), (cx - 20, cy - 85 + bobbing)], fill=(40, 30, 25))
    draw.polygon([(cx + 28, cy - 115 + bobbing), (cx + 12, cy - 112 + bobbing), (cx + 20, cy - 85 + bobbing)], fill=(40, 30, 25))
    draw.polygon([(cx - 120, cy - 45 + bobbing), (cx - 85, cy - 35 + bobbing), (cx - 115, cy - 25 + bobbing)], fill=(40, 30, 25))
    draw.polygon([(cx + 120, cy - 45 + bobbing), (cx + 85, cy - 35 + bobbing), (cx + 115, cy - 25 + bobbing)], fill=(40, 30, 25))

    # Snout & Nose
    draw.ellipse([cx - 55, cy - 35 + bobbing, cx + 55, cy + 35 + bobbing], fill=(255, 250, 240))
    draw.polygon([(cx - 18, cy - 15 + bobbing), (cx + 18, cy - 15 + bobbing), (cx, cy + 5 + bobbing)], fill=(245, 120, 140))
    draw.arc([cx - 25, cy - 5 + bobbing, cx, cy + 22 + bobbing], 20, 160, fill=(60, 40, 30), width=3)
    draw.arc([cx, cy - 5 + bobbing, cx + 25, cy + 22 + bobbing], 20, 160, fill=(60, 40, 30), width=3)

    # Eyes with blinking
    eye_blink = 1.0 if (int(t * 10) % 22 > 1) else 0.15
    for ex in [cx - 50, cx + 50]:
        eye_h = int(24 * eye_blink)
        draw.ellipse([ex - 20, cy - 55 - eye_h + bobbing, ex + 20, cy - 55 + eye_h + bobbing], fill=(255, 255, 255), outline=(50, 40, 30), width=2)
        if eye_blink > 0.4:
            draw.ellipse([ex - 14, cy - 55 - eye_h + 3 + bobbing, ex + 14, cy - 55 + eye_h - 3 + bobbing], fill=(235, 175, 45))
            draw.ellipse([ex - 8, cy - 55 - eye_h + 6 + bobbing, ex + 8, cy - 55 + eye_h - 6 + bobbing], fill=(25, 20, 20))
            draw.ellipse([ex - 6, cy - 62 + bobbing, ex + 1, cy - 55 + bobbing], fill=(255, 255, 255))
    # Whiskers
    for dy in [-4, 8, 20]:
        draw.line([(cx - 45, cy + dy + bobbing), (cx - 105, cy + dy * 1.5 + bobbing)], fill=(255, 255, 255, 200), width=2)
        draw.line([(cx + 45, cy + dy + bobbing), (cx + 105, cy + dy * 1.5 + bobbing)], fill=(255, 255, 255, 200), width=2)


def _draw_panda(draw: ImageDraw.Draw, cx: float, cy: float, t: float, bobbing: float, breathing: float):
    # Body
    draw.ellipse([cx - 130, cy - 20 + bobbing, cx + 130, cy + 155 + bobbing + breathing], fill=(250, 250, 250), outline=(20, 20, 20), width=3)
    # Black Shoulders & Arms
    draw.ellipse([cx - 135, cy + 10 + bobbing, cx + 135, cy + 100 + bobbing], fill=(30, 30, 35))
    # White Tummy
    draw.ellipse([cx - 85, cy + 45 + bobbing, cx + 85, cy + 150 + bobbing], fill=(255, 255, 255))
    # Paws
    for px in [cx - 75, cx + 75]:
        draw.ellipse([px - 35, cy + 120 + bobbing, px + 35, cy + 175 + bobbing], fill=(30, 30, 35))
        draw.ellipse([px - 15, cy + 140 + bobbing, px + 15, cy + 165 + bobbing], fill=(80, 80, 85))

    # Bamboo Stalk in hand
    b_sway = math.sin(t * 2) * 8
    draw.line([(cx + 85, cy + 140 + bobbing), (cx + 115 + b_sway, cy - 80 + bobbing)], fill=(90, 200, 90), width=10)
    draw.polygon([(cx + 115 + b_sway, cy - 80 + bobbing), (cx + 145 + b_sway, cy - 100 + bobbing), (cx + 110 + b_sway, cy - 65 + bobbing)], fill=(120, 230, 100))

    # Ears
    draw.ellipse([cx - 135, cy - 165 + bobbing, cx - 65, cy - 95 + bobbing], fill=(30, 30, 35))
    draw.ellipse([cx + 65, cy - 165 + bobbing, cx + 135, cy - 95 + bobbing], fill=(30, 30, 35))

    # Head
    draw.ellipse([cx - 120, cy - 130 + bobbing, cx + 120, cy + 45 + bobbing], fill=(255, 255, 255), outline=(30, 30, 35), width=3)

    # Black Eye Patches (Tilted Ovals)
    draw.ellipse([cx - 75, cy - 65 + bobbing, cx - 25, cy - 5 + bobbing], fill=(30, 30, 35))
    draw.ellipse([cx + 25, cy - 65 + bobbing, cx + 75, cy - 5 + bobbing], fill=(30, 30, 35))

    # Eyes (Shiny White Catchlights)
    eye_blink = 1.0 if (int(t * 10) % 22 > 1) else 0.15
    for ex in [cx - 48, cx + 48]:
        eye_h = int(12 * eye_blink)
        draw.ellipse([ex - 9, cy - 35 - eye_h + bobbing, ex + 9, cy - 35 + eye_h + bobbing], fill=(255, 255, 255))
        if eye_blink > 0.4:
            draw.ellipse([ex - 5, cy - 38 + bobbing, ex - 1, cy - 34 + bobbing], fill=(255, 255, 255))

    # Snout & Nose
    draw.ellipse([cx - 45, cy - 15 + bobbing, cx + 45, cy + 30 + bobbing], fill=(250, 250, 250))
    draw.polygon([(cx - 16, cy - 8 + bobbing), (cx + 16, cy - 8 + bobbing), (cx, cy + 8 + bobbing)], fill=(30, 30, 35))
    draw.arc([cx - 20, cy + 2 + bobbing, cx, cy + 22 + bobbing], 20, 160, fill=(30, 30, 35), width=3)
    draw.arc([cx, cy + 2 + bobbing, cx + 20, cy + 22 + bobbing], 20, 160, fill=(30, 30, 35), width=3)


def _draw_lion(draw: ImageDraw.Draw, cx: float, cy: float, t: float, bobbing: float, breathing: float):
    # Magnificent Flowing Mane (Background layers)
    mane_pulse = math.sin(t * 2) * 6
    for angle_deg in range(0, 360, 24):
        rad = math.radians(angle_deg)
        mx = cx + math.cos(rad) * (150 + mane_pulse)
        my = (cy - 35 + bobbing) + math.sin(rad) * (150 + mane_pulse)
        draw.ellipse([mx - 40, my - 40, mx + 40, my + 40], fill=(160, 85, 25))
    for angle_deg in range(12, 360, 24):
        rad = math.radians(angle_deg)
        mx = cx + math.cos(rad) * (130 + mane_pulse * 0.5)
        my = (cy - 35 + bobbing) + math.sin(rad) * (130 + mane_pulse * 0.5)
        draw.ellipse([mx - 35, my - 35, mx + 35, my + 35], fill=(205, 125, 35))

    # Body
    draw.ellipse([cx - 110, cy + 10 + bobbing, cx + 110, cy + 155 + bobbing + breathing], fill=(235, 175, 45), outline=(180, 120, 25), width=3)
    draw.ellipse([cx - 60, cy + 40 + bobbing, cx + 60, cy + 145 + bobbing], fill=(255, 225, 145))
    # Paws
    for px in [cx - 65, cx + 65]:
        draw.ellipse([px - 32, cy + 125 + bobbing, px + 32, cy + 175 + bobbing], fill=(255, 225, 145), outline=(180, 120, 25), width=2)

    # Head
    draw.ellipse([cx - 100, cy - 120 + bobbing, cx + 100, cy + 40 + bobbing], fill=(235, 175, 45), outline=(180, 120, 25), width=3)
    # Ears
    draw.ellipse([cx - 95, cy - 125 + bobbing, cx - 50, cy - 80 + bobbing], fill=(235, 175, 45))
    draw.ellipse([cx - 85, cy - 115 + bobbing, cx - 60, cy - 90 + bobbing], fill=(160, 85, 25))
    draw.ellipse([cx + 50, cy - 125 + bobbing, cx + 95, cy - 80 + bobbing], fill=(235, 175, 45))
    draw.ellipse([cx + 60, cy - 115 + bobbing, cx + 85, cy - 90 + bobbing], fill=(160, 85, 25))

    # Snout
    draw.ellipse([cx - 50, cy - 30 + bobbing, cx + 50, cy + 30 + bobbing], fill=(255, 240, 205))
    draw.polygon([(cx - 20, cy - 15 + bobbing), (cx + 20, cy - 15 + bobbing), (cx, cy + 8 + bobbing)], fill=(50, 35, 30))
    draw.arc([cx - 25, cy - 2 + bobbing, cx, cy + 22 + bobbing], 20, 160, fill=(50, 35, 30), width=3)
    draw.arc([cx, cy - 2 + bobbing, cx + 25, cy + 22 + bobbing], 20, 160, fill=(50, 35, 30), width=3)

    # Royal Amber Eyes
    eye_blink = 1.0 if (int(t * 10) % 22 > 1) else 0.15
    for ex in [cx - 42, cx + 42]:
        eye_h = int(20 * eye_blink)
        draw.ellipse([ex - 16, cy - 50 - eye_h + bobbing, ex + 16, cy - 50 + eye_h + bobbing], fill=(255, 255, 255), outline=(50, 35, 30), width=2)
        if eye_blink > 0.4:
            draw.ellipse([ex - 11, cy - 50 - eye_h + 3 + bobbing, ex + 11, cy - 50 + eye_h - 3 + bobbing], fill=(215, 140, 25))
            draw.ellipse([ex - 6, cy - 50 - eye_h + 6 + bobbing, ex + 6, cy - 50 + eye_h - 6 + bobbing], fill=(25, 20, 20))
            draw.ellipse([ex - 4, cy - 55 + bobbing, ex + 1, cy - 50 + bobbing], fill=(255, 255, 255))


def _draw_fox(draw: ImageDraw.Draw, cx: float, cy: float, t: float, bobbing: float, breathing: float):
    # Huge Bushy Tail with White Tip
    tail_wobble = math.sin(t * 3) * 15
    draw.ellipse([cx + 40 + tail_wobble, cy - 30 + bobbing, cx + 180 + tail_wobble, cy + 130 + bobbing], fill=(230, 95, 45), outline=(190, 70, 30), width=3)
    draw.ellipse([cx + 120 + tail_wobble, cy - 20 + bobbing, cx + 180 + tail_wobble, cy + 60 + bobbing], fill=(255, 250, 245))

    # Body
    draw.ellipse([cx - 95, cy + 10 + bobbing, cx + 95, cy + 150 + bobbing + breathing], fill=(230, 95, 45), outline=(190, 70, 30), width=3)
    draw.ellipse([cx - 55, cy + 35 + bobbing, cx + 55, cy + 140 + bobbing], fill=(255, 250, 245))
    # Black Paws
    for px in [cx - 55, cx + 55]:
        draw.ellipse([px - 25, cy + 125 + bobbing, px + 25, cy + 170 + bobbing], fill=(40, 35, 40))

    # Tall Pointy Ears
    ear_wiggle = math.sin(t * 3) * 3
    draw.polygon([(cx - 95, cy - 70 + bobbing), (cx - 120 + ear_wiggle, cy - 175 + bobbing), (cx - 40, cy - 100 + bobbing)], fill=(230, 95, 45), outline=(190, 70, 30))
    draw.polygon([(cx - 90, cy - 75 + bobbing), (cx - 110 + ear_wiggle, cy - 155 + bobbing), (cx - 50, cy - 100 + bobbing)], fill=(255, 250, 245))
    draw.polygon([(cx + 95, cy - 70 + bobbing), (cx + 120 - ear_wiggle, cy - 175 + bobbing), (cx + 40, cy - 100 + bobbing)], fill=(230, 95, 45), outline=(190, 70, 30))
    draw.polygon([(cx + 90, cy - 75 + bobbing), (cx + 110 - ear_wiggle, cy - 155 + bobbing), (cx + 50, cy - 100 + bobbing)], fill=(255, 250, 245))

    # Triangular Fox Head & Cheeks
    draw.ellipse([cx - 110, cy - 110 + bobbing, cx + 110, cy + 40 + bobbing], fill=(230, 95, 45))
    draw.polygon([(cx - 110, cy - 10 + bobbing), (cx - 145, cy + 15 + bobbing), (cx - 75, cy + 40 + bobbing)], fill=(255, 250, 245))
    draw.polygon([(cx + 110, cy - 10 + bobbing), (cx + 145, cy + 15 + bobbing), (cx + 75, cy + 40 + bobbing)], fill=(255, 250, 245))
    draw.polygon([(cx - 50, cy + 5 + bobbing), (cx + 50, cy + 5 + bobbing), (cx, cy + 55 + bobbing)], fill=(255, 250, 245))

    # Cute Black Nose & Smile
    draw.ellipse([cx - 14, cy + 42 + bobbing, cx + 14, cy + 58 + bobbing], fill=(30, 25, 30))

    # Amber Eyes
    eye_blink = 1.0 if (int(t * 10) % 22 > 1) else 0.15
    for ex in [cx - 45, cx + 45]:
        eye_h = int(18 * eye_blink)
        draw.ellipse([ex - 15, cy - 40 - eye_h + bobbing, ex + 15, cy - 40 + eye_h + bobbing], fill=(255, 255, 255), outline=(40, 30, 30), width=2)
        if eye_blink > 0.4:
            draw.ellipse([ex - 10, cy - 40 - eye_h + 3 + bobbing, ex + 10, cy - 40 + eye_h - 3 + bobbing], fill=(215, 120, 35))
            draw.ellipse([ex - 5, cy - 40 - eye_h + 5 + bobbing, ex + 5, cy - 40 + eye_h - 5 + bobbing], fill=(25, 20, 20))
            draw.ellipse([ex - 4, cy - 45 + bobbing, ex + 1, cy - 40 + bobbing], fill=(255, 255, 255))


def _draw_generic(draw: ImageDraw.Draw, species_id: str, cx: float, cy: float, t: float, bobbing: float, breathing: float, accent: tuple):
    # Flexible fallbacks for Elephant, Wolf, Owl, Giraffe, Orca, Bear
    draw.ellipse([cx - 110, cy - 20 + bobbing, cx + 110, cy + 150 + bobbing + breathing], fill=accent, outline=(40, 40, 40), width=3)
    draw.ellipse([cx - 65, cy + 30 + bobbing, cx + 65, cy + 140 + bobbing], fill=(245, 245, 250))
    # Paws
    for px in [cx - 65, cx + 65]:
        draw.ellipse([px - 30, cy + 120 + bobbing, px + 30, cy + 170 + bobbing], fill=(245, 245, 250), outline=(40, 40, 40), width=2)
    # Head
    draw.ellipse([cx - 105, cy - 125 + bobbing, cx + 105, cy + 45 + bobbing], fill=accent, outline=(40, 40, 40), width=3)
    # Ears
    draw.ellipse([cx - 100, cy - 150 + bobbing, cx - 45, cy - 85 + bobbing], fill=accent)
    draw.ellipse([cx + 45, cy - 150 + bobbing, cx + 100, cy - 85 + bobbing], fill=accent)
    # Snout
    draw.ellipse([cx - 45, cy - 15 + bobbing, cx + 45, cy + 35 + bobbing], fill=(245, 245, 250))
    draw.ellipse([cx - 14, cy - 2 + bobbing, cx + 14, cy + 16 + bobbing], fill=(40, 30, 30))
    # Eyes
    eye_blink = 1.0 if (int(t * 10) % 22 > 1) else 0.15
    for ex in [cx - 45, cx + 45]:
        eye_h = int(18 * eye_blink)
        draw.ellipse([ex - 15, cy - 50 - eye_h + bobbing, ex + 15, cy - 50 + eye_h + bobbing], fill=(255, 255, 255), outline=(40, 30, 30), width=2)
        if eye_blink > 0.4:
            draw.ellipse([ex - 9, cy - 50 - eye_h + 3 + bobbing, ex + 9, cy - 50 + eye_h - 3 + bobbing], fill=(60, 50, 45))
            draw.ellipse([ex - 4, cy - 55 + bobbing, ex + 1, cy - 50 + bobbing], fill=(255, 255, 255))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN FRAME RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def render_animal_frame(species_dict: dict, frame_idx: int, total_frames: int) -> Image.Image:
    t = frame_idx / total_frames * 2 * math.pi
    img = Image.new("RGBA", (WIDTH, HEIGHT), (20, 25, 30, 255))
    draw = ImageDraw.Draw(img)

    # 1. Background Gradient
    bg_top = species_dict.get("bg_top", (15, 35, 35))
    bg_bot = species_dict.get("bg_bot", (35, 65, 60))
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(bg_top[0] * (1 - ratio) + bg_bot[0] * ratio)
        g = int(bg_top[1] * (1 - ratio) + bg_bot[1] * ratio)
        b = int(bg_top[2] * (1 - ratio) + bg_bot[2] * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

    # Soft glowing spotlight behind animal
    accent = species_dict.get("accent", (245, 140, 35))
    spotlight = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(spotlight)
    s_draw.ellipse([110, 180, 610, 720], fill=(accent[0], accent[1], accent[2], 40))
    img = Image.alpha_composite(img, spotlight.filter(ImageFilter.GaussianBlur(60)))
    draw = ImageDraw.Draw(img)

    # Ambient floating nature particles/fireflies
    for i in range(16):
        fx = (i * 47 + int(math.sin(t + i) * 25)) % (WIDTH - 40) + 20
        fy = (i * 73 + int(math.cos(t * 1.2 + i) * 20)) % 580 + 130
        fr = 3 + int(math.sin(t * 2 + i) * 2)
        draw.ellipse([fx - fr, fy - fr, fx + fr, fy + fr], fill=(255, 240, 160, 160))

    # 2. Header Badge
    badge_text = "🐾 ANIMAL OF THE DAY"
    draw.rounded_rectangle([190, 50, 530, 105], radius=25, fill=(12, 28, 30, 220), outline=(accent[0], accent[1], accent[2], 220), width=2)
    font_badge = get_font(20, bold=True)
    draw.text((230, 66), badge_text, font=font_badge, fill=accent)

    # 3. Procedural Vector Animal
    cx, cy = 360, 440
    bobbing = math.cos(t * 2) * 5
    breathing = math.sin(t * 2) * 6
    s_id = species_dict.get("id", "tiger")

    if s_id == "tiger":
        _draw_tiger(draw, cx, cy, t, bobbing, breathing)
    elif s_id == "panda":
        _draw_panda(draw, cx, cy, t, bobbing, breathing)
    elif s_id == "lion":
        _draw_lion(draw, cx, cy, t, bobbing, breathing)
    elif s_id == "fox":
        _draw_fox(draw, cx, cy, t, bobbing, breathing)
    else:
        _draw_generic(draw, s_id, cx, cy, t, bobbing, breathing, accent)

    # 4. Modern Glassmorphism Fact Card
    card_y = 680
    draw.rounded_rectangle([60, card_y, 660, 1070], radius=24, fill=(10, 24, 28, 235), outline=accent, width=3)

    font_title = get_font(34, bold=True)
    font_fact = get_font(22, bold=False)
    font_cta = get_font(26, bold=True)

    title_text = species_dict.get("title", "🐅 ANIMAL FACTS")
    draw.text((95, card_y + 30), title_text, font=font_title, fill=accent)
    draw.line([(95, card_y + 80), (625, card_y + 80)], fill=(accent[0], accent[1], accent[2], 100), width=2)

    facts = species_dict.get("facts", ["Amazing wildlife facts!"])
    fy = card_y + 105
    for fact in facts[:3]:
        draw.ellipse([95, fy + 6, 109, fy + 20], fill=accent)
        words = fact.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if draw.textbbox((0, 0), test_line, font=font_fact)[2] > 490:
                draw.text((125, fy), line, font=font_fact, fill=(240, 245, 245))
                fy += 32
                line = word
            else:
                line = test_line
        if line:
            draw.text((125, fy), line, font=font_fact, fill=(240, 245, 245))
            fy += 42

    # 5. Bottom Call to Action Pill
    draw.rounded_rectangle([100, 1110, 620, 1190], radius=40, fill=accent)
    draw.text((150, 1134), f'💬 COMMENT "{species_dict["name"].upper()}"!', font=font_cta, fill=(18, 18, 20))

    return img.convert("RGB")
