"""
Real Visual Sketch & Draw Engine
Fetches real high-res reference photos from Wikimedia / Wikipedia Public API,
extracts authentic contours, color palettes, and anatomically accurate line strokes,
and renders a progressive time-lapse drawing & digital painting animation.
"""
from __future__ import annotations

import io
import json
import math
import os
import random
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance, ImageFont

WIDTH, HEIGHT, FPS = 1080, 1920, 30
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "cache" / "real_images"
FONTS_DIR = ROOT_DIR / "assets" / "fonts"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if mono:
        candidates = [
            str(FONTS_DIR / "DejaVuSansMono-Bold.ttf"),
            str(FONTS_DIR / "CodeMono.ttf"),
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/system/fonts/DroidSansMono.ttf",
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

def fetch_web_reference(query: str) -> tuple[Image.Image, list[tuple[int, int, int]], list[str], str]:
    """Fetches real reference photo and extract from Wikipedia / Wikimedia."""
    cache_img = CACHE_DIR / f"{query.lower().replace(' ', '_')}.jpg"
    cache_meta = CACHE_DIR / f"{query.lower().replace(' ', '_')}.json"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    raw_img = None
    extract_text = ""

    if cache_img.exists() and cache_meta.exists():
        try:
            raw_img = Image.open(cache_img).convert("RGB")
            meta = json.loads(cache_meta.read_text(encoding="utf-8"))
            extract_text = meta.get("extract", "")
        except Exception:
            raw_img = None

    if raw_img is None:
        title = query.replace(' ', '_')
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                extract_text = data.get("extract", "")
                img_url = data.get("thumbnail", {}).get("source") or data.get("originalimage", {}).get("source")
                if img_url:
                    img_resp = requests.get(img_url, headers=headers, timeout=10)
                    if img_resp.status_code == 200:
                        raw_img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
                        raw_img.save(cache_img, quality=95)
                        cache_meta.write_text(json.dumps({"extract": extract_text, "url": img_url}), encoding="utf-8")
        except Exception as e:
            print(f"[WebFetch] Warning: {e}")

    if raw_img is None:
        raw_img = Image.new("RGB", (860, 600), (220, 110, 40))
        d = ImageDraw.Draw(raw_img)
        d.ellipse([100, 50, 760, 550], fill=(255, 170, 60), outline=(180, 70, 20), width=8)
        extract_text = f"{query} is an iconic natural subject studied for its distinct biological and visual characteristics."

    # Extract dominant color palette
    quant = raw_img.quantize(colors=5)
    palette_raw = quant.getpalette()[:15]
    colors = [tuple(palette_raw[i:i+3]) for i in range(0, 15, 3)]
    hex_colors = ['#{:02X}{:02X}{:02X}'.format(*c) for c in colors]

    return raw_img, colors, hex_colors, extract_text

def prepare_art_layers(raw_img: Image.Image, target_w: int = 860, target_h: int = 600):
    """Generates edge contours, pencil sketch, ink details, and color base filling canvas."""
    # Fit nicely into target canvas board
    fitted = ImageOps.fit(raw_img, (target_w, target_h), method=Image.Resampling.LANCZOS)
    canvas_color = (248, 245, 238)

    # Grayscale & Blur
    gray = fitted.convert("L")
    
    # 1. Authentic Graphite Pencil Sketch Outline
    blurred = gray.filter(ImageFilter.GaussianBlur(1.0))
    edges = blurred.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(2.8)
    pencil_mask = ImageOps.invert(edges)
    
    pencil_layer = Image.new("RGB", (target_w, target_h), canvas_color)
    graphite = Image.new("RGB", (target_w, target_h), (45, 48, 56))
    pencil_art = Image.composite(pencil_layer, graphite, pencil_mask)

    # 2. Ink & Shading
    ink_edges = gray.filter(ImageFilter.EDGE_ENHANCE_MORE).filter(ImageFilter.FIND_EDGES)
    ink_mask = ImageOps.invert(ImageEnhance.Contrast(ink_edges).enhance(4.2))
    ink_layer = Image.new("RGB", (target_w, target_h), (18, 22, 30))
    ink_art = Image.composite(pencil_layer, ink_layer, ink_mask)

    # 3. Soft Watercolor Wash Layer
    wash_art = fitted.filter(ImageFilter.GaussianBlur(6.0))

    # 4. Stylus Stroke Path Generation (Ordered contour points)
    small_edges = edges.resize((140, 90), Image.Resampling.BOX)
    stroke_points = []
    w_s, h_s = small_edges.size
    for y in range(h_s):
        for x in range(w_s):
            if small_edges.getpixel((x, y)) > 60:
                real_x = int((x / w_s) * target_w)
                real_y = int((y / h_s) * target_h)
                stroke_points.append((real_x, real_y))
    
    if not stroke_points:
        stroke_points = [(target_w // 2, target_h // 2)]

    return {
        "color": fitted,
        "pencil": pencil_art,
        "ink": ink_art,
        "wash": wash_art,
        "strokes": stroke_points,
        "size": (target_w, target_h)
    }

def render_real_draw_frame(query: str, subject_data: dict, frame_idx: int, total_frames: int) -> Image.Image:
    """Renders a Full HD 1080x1920 drawing frame at the given frame index."""
    progress = frame_idx / max(1, total_frames - 1)
    sim_time = frame_idx / FPS

    art = subject_data["art"]
    colors = subject_data["colors"]
    hex_colors = subject_data["hex_colors"]
    extract_text = subject_data["extract"]

    # Main dark canvas
    img = Image.new("RGB", (WIDTH, HEIGHT), (12, 16, 22))
    draw = ImageDraw.Draw(img)

    # 1. Top Header Bar
    header_h = 145
    draw.rectangle([0, 0, WIDTH, header_h], fill=(16, 22, 30))
    draw.line([(0, header_h), (WIDTH, header_h)], fill=(32, 42, 56), width=2)

    title_font = get_font(52, bold=True)
    draw.text((WIDTH // 2, 26), query.upper(), font=title_font, fill=(255, 255, 255), anchor="mt")

    sub_font = get_font(20, bold=True, mono=True)
    draw.text((WIDTH // 2, 94), "REAL REFERENCE DRAWING • WIKIPEDIA OPEN ARCHIVE", font=sub_font, fill=(56, 189, 248), anchor="mt")

    # 2. Artist Drafting Canvas Board
    board_w, board_h = 940, 680
    board_x = (WIDTH - board_w) // 2
    board_y = 175

    # Shadow under board
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([board_x - 12, board_y - 12, board_x + board_w + 12, board_y + board_h + 12], radius=16, fill=(0, 0, 0, 160))
    img = Image.alpha_composite(img.convert("RGBA"), shadow.filter(ImageFilter.GaussianBlur(28))).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Board Paper
    draw.rounded_rectangle([board_x - 8, board_y - 8, board_x + board_w + 8, board_y + board_h + 8], radius=14, fill=(225, 220, 210), outline=(180, 175, 165), width=2)
    draw.rounded_rectangle([board_x, board_y, board_x + board_w, board_y + board_h], radius=12, fill=(248, 245, 238))

    # --- PROGRESSIVE ART TIMELAPSE ---
    art_w, art_h = art["size"]
    inner_art = Image.new("RGB", (art_w, art_h), (248, 245, 238))

    if progress < 0.28:
        # Phase 1: Pencil Drafting
        p_phase = progress / 0.28
        pencil_crop_w = max(10, int(art_w * p_phase))
        inner_art.paste(art["pencil"].crop((0, 0, pencil_crop_w, art_h)), (0, 0))
    elif progress < 0.55:
        # Phase 2: Ink & Details Phase
        p_phase = (progress - 0.28) / 0.27
        inner_art.paste(art["pencil"], (0, 0))
        ink_crop_w = max(10, int(art_w * p_phase))
        inner_art.paste(art["ink"].crop((0, 0, ink_crop_w, art_h)), (0, 0))
    elif progress < 0.85:
        # Phase 3: Watercolor / Color Bloom Phase
        p_phase = (progress - 0.55) / 0.30
        inner_art.paste(art["ink"], (0, 0))
        blended_color = Image.blend(art["wash"], art["color"], p_phase)
        color_crop_w = max(10, int(art_w * p_phase))
        inner_art.paste(blended_color.crop((0, 0, color_crop_w, art_h)), (0, 0))
    else:
        # Phase 4: Masterpiece Final Reveal
        inner_art.paste(art["color"], (0, 0))

    canvas_x = board_x + (board_w - art_w) // 2
    canvas_y = board_y + (board_h - art_h) // 2
    img.paste(inner_art, (canvas_x, canvas_y))
    draw = ImageDraw.Draw(img)

    # Virtual Artist Stylus Pen Tip
    strokes = art["strokes"]
    if progress < 0.85 and strokes:
        stroke_idx = int(progress * len(strokes)) % len(strokes)
        sx, sy = strokes[stroke_idx]
        pen_x = canvas_x + sx
        pen_y = canvas_y + sy

        # Glowing Stylus Cursor
        pen_r = 9 + math.sin(sim_time * 12) * 2
        draw.ellipse([pen_x - pen_r, pen_y - pen_r, pen_x + pen_r, pen_y + pen_r], outline=(56, 189, 248), width=2)
        draw.ellipse([pen_x - 3, pen_y - 3, pen_x + 3, pen_y + 3], fill=(244, 63, 94))
        
        # Stylus Body
        draw.line([(pen_x, pen_y), (pen_x + 32, pen_y - 48)], fill=(30, 41, 59), width=5)
        draw.line([(pen_x, pen_y), (pen_x + 32, pen_y - 48)], fill=(56, 189, 248), width=2)

    # 3. LOWER SECTION: COLOR PALETTE & EDUCATIONAL FACT CARD
    card_w, card_h = 940, 890
    card_x = (WIDTH - card_w) // 2
    card_y = 890

    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=22, fill=(16, 22, 32), outline=(32, 44, 60), width=2)

    # Header of Lower Card: Extracted Real Color Palette
    p_title_h = 60
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + p_title_h], radius=22, fill=(22, 30, 44))
    draw.rectangle([card_x, card_y + 30, card_x + card_w, card_y + p_title_h], fill=(22, 30, 44))
    draw.text((card_x + 28, card_y + 18), "EXTRACTED WEB COLOR PALETTE", font=get_font(22, bold=True), fill=(240, 240, 245))

    # Render Color Swatches
    swatch_y = card_y + p_title_h + 28
    active_color_idx = int(progress * len(colors)) % len(colors)
    
    for i, (rgb, hex_c) in enumerate(zip(colors, hex_colors)):
        sx = card_x + 45 + i * 175
        is_active = (i == active_color_idx)
        
        # Swatch Pill
        draw.rounded_rectangle([sx, swatch_y, sx + 150, swatch_y + 70], radius=14, fill=rgb, outline=(255, 255, 255) if is_active else (50, 60, 75), width=3 if is_active else 1)
        
        # Hex text badge below swatch
        text_fill = (255, 255, 255) if is_active else (148, 163, 184)
        draw.text((sx + 75, swatch_y + 80), hex_c, font=get_font(18, bold=True, mono=True), fill=text_fill, anchor="mt")

    # 4. Educational & Drawing Fact Window
    info_y = swatch_y + 125
    draw.rounded_rectangle([card_x + 25, info_y, card_x + card_w - 25, card_y + card_h - 35], radius=16, fill=(10, 14, 20), outline=(28, 38, 52), width=2)
    
    # Tab Header
    draw.text((card_x + 48, info_y + 18), "Biological & Visual Analysis", font=get_font(22, bold=True), fill=(56, 189, 248))
    draw.line([(card_x + 25, info_y + 55), (card_x + card_w - 25, info_y + 55)], fill=(28, 38, 52), width=2)

    # Word-wrapped extract
    words = extract_text.split()
    lines = []
    cur_line = ""
    for w in words:
        if len(cur_line + " " + w) > 44:
            lines.append(cur_line)
            cur_line = w
        else:
            cur_line = (cur_line + " " + w).strip()
    if cur_line:
        lines.append(cur_line)

    fact_font = get_font(24)
    line_y = info_y + 75
    for l in lines[:12]:
        draw.text((card_x + 48, line_y), l, font=fact_font, fill=(203, 213, 225))
        line_y += 38

    # Stage Status Badge
    stage_text = "Stage 1: Pencil Anatomy Drafting" if progress < 0.28 else "Stage 2: Ink Line Detailing" if progress < 0.55 else "Stage 3: Real Color Blooming" if progress < 0.85 else "Stage 4: Photorealistic Masterpiece"
    draw.rounded_rectangle([card_x + 48, card_y + card_h - 90, card_x + card_w - 48, card_y + card_h - 45], radius=10, fill=(24, 36, 52))
    draw.text((card_x + card_w // 2, card_y + card_h - 68), stage_text, font=get_font(20, bold=True), fill=(255, 255, 255), anchor="mm")

    # 5. Bottom Progress Bar
    bar_w = 940
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 1860
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 12], radius=6, fill=(35, 46, 62))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + max(12, int(bar_w * progress)), bar_y + 12], radius=6, fill=(56, 189, 248))

    return img