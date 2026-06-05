"""
LLM-Powered Visual Generator for Teacher Bot
Uses OpenGateway API to generate topic-specific visual scenes.
PIL renders the scenes - no Manim/LaTeX needed.

Flow: Topic → LLM generates scene JSON → PIL renders frames → ffmpeg → video
"""

import os
import json
import random
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Canvas size (YouTube Shorts portrait)
WIDTH = 1080
HEIGHT = 1920
TARGET_FPS = 30

# Colors
COLORS = {
    'bg': '#FFFFFF',
    'bg_light': '#F8FAFC',
    'primary': '#2563EB',
    'secondary': '#7C3AED',
    'accent': '#F59E0B',
    'success': '#10B981',
    'danger': '#EF4444',
    'text': '#1E293B',
    'text_light': '#64748B',
    'grid': '#E2E8F0',
}


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_font(size, bold=False):
    font_paths = [
        'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/seguisb.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
        'assets/fonts/hindi_font.ttf',  # Devanagari/project-local fallback
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    try:
        return ImageFont.load_default(size)
    except:
        return ImageFont.load_default()


def draw_gradient_bg(draw, img, top_color='#667EEA', bot_color='#764BA2'):
    """Draw a smooth vertical gradient background."""
    w, h = img.size
    top = hex_to_rgb(top_color)
    bot = hex_to_rgb(bot_color)
    for y in range(h):
        ratio = y / h
        r = int(top[0] + (bot[0] - top[0]) * ratio)
        g = int(top[1] + (bot[1] - top[1]) * ratio)
        b = int(top[2] + (bot[2] - top[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    """Draw a rounded rectangle with optional shadow."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_shadow_card(draw, xy, radius=20, shadow_offset=8, card_color='#FFFFFF', shadow_color='#E2E8F0'):
    """Draw a card with drop shadow effect. xy = [(x0,y0),(x1,y1)] or (x0,y0,x1,y1)."""
    if isinstance(xy[0], (list, tuple)):
        x0, y0 = xy[0]
        x1, y1 = xy[1]
    else:
        x0, y0, x1, y1 = xy
    # Shadow (darker, offset)
    draw.rounded_rectangle(
        [(x0 + shadow_offset, y0 + shadow_offset), (x1 + shadow_offset, y1 + shadow_offset)],
        radius=radius, fill=hex_to_rgb(shadow_color)
    )
    # Card
    draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, fill=hex_to_rgb(card_color))


def draw_progress_bar(draw, x, y, w, h, progress, color='#2563EB', bg='#E2E8F0'):
    """Draw an animated progress bar."""
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=h // 2, fill=hex_to_rgb(bg))
    bar_w = max(h, int(w * min(progress, 1.0)))
    draw.rounded_rectangle([(x, y), (x + bar_w, y + h)], radius=h // 2, fill=hex_to_rgb(color))


def draw_step_dots(draw, x, y, total, current, active_color='#2563EB', inactive_color='#CBD5E1', done_color='#10B981'):
    """Draw step progress dots."""
    spacing = 45
    for i in range(total):
        dx = x + i * spacing
        r = 10
        if i < current:
            color = hex_to_rgb(done_color)
        elif i == current:
            color = hex_to_rgb(active_color)
            r = 14
        else:
            color = hex_to_rgb(inactive_color)
        draw.ellipse([(dx - r, y - r), (dx + r, y + r)], fill=color)


def draw_teacher_avatar(draw, cx, cy, size=80):
    """Draw a simple teacher avatar silhouette with PIL."""
    # Head
    head_r = size // 3
    draw.ellipse(
        [(cx - head_r, cy - size + head_r), (cx + head_r, cy - size + head_r + head_r * 2)],
        fill=hex_to_rgb('#1E293B')
    )
    # Body (triangle for dress)
    draw.polygon(
        [(cx - size, cy + head_r), (cx + size, cy + head_r), (cx, cy + size)],
        fill=hex_to_rgb('#1E293B')
    )
    # Pointer stick
    draw.line([(cx + size // 2, cy), (cx + size + 20, cy - size // 2)],
              fill=hex_to_rgb('#F59E0B'), width=3)


def draw_chapter_badge(draw, x, y, text, color='#1E293B'):
    """Draw a chapter/topic badge pill."""
    font = get_font(20, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad = 15
    draw.rounded_rectangle(
        [(x, y), (x + tw + pad * 2, y + th + pad)],
        radius=15, fill=hex_to_rgb(color)
    )
    draw.text((x + pad, y + pad // 2), text, fill=hex_to_rgb('#FFFFFF'), font=font)


def _extract_json(text):
    """Extract first valid JSON object from text that may contain reasoning + JSON mixed."""
    text = text.strip()
    # Try parsing as-is first
    try:
        json.loads(text)
        return text
    except (json.JSONDecodeError, ValueError):
        pass
    # Find first { and try raw_decode
    start = text.find('{')
    if start != -1:
        try:
            decoder = json.JSONDecoder()
            obj, _ = decoder.raw_decode(text[start:])
            return json.dumps(obj)
        except (json.JSONDecodeError, ValueError):
            pass
    return text


def _call_api(messages, model, temperature=0.7, max_tokens=3000):
    """Call OpenGateway API using requests (avoids openai library httpx issue)."""
    import requests

    api_key = os.environ.get('OPENAI_API_KEY', '')
    base_url = os.environ.get('OPENAI_BASE_URL', 'https://opengateway.gitlawb.com/v1')

    if not api_key:
        return None

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept-Encoding": "identity",  # avoid gzip decode bug
        },
        json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
        timeout=180
    )
    print(f"    [debug] resp_status={resp.status_code}, resp_keys={list(resp.json().keys()) if resp.headers.get('content-type','').startswith('application/json') else 'not json'}", flush=True)
    resp.raise_for_status()
    data = resp.json()
    msg = data["choices"][0]["message"]
    c = msg.get("content")
    rc = msg.get("reasoning_content") or msg.get("reasoning")
    if isinstance(rc, dict):
        rc = rc.get("content") or str(rc)
    elif isinstance(rc, list):
        rc = "".join(item.get("text", "") for item in rc if isinstance(item, dict))
    print(f"    [debug] msg_keys={list(msg.keys())}, content={repr(c[:100]) if c else 'None'}, reasoning={repr(rc[:100]) if rc else 'None'}", flush=True)
    content = c or rc or ""
    if not content:
        return None
    # reasoning_content may contain reasoning text + JSON mixed — extract clean JSON
    return _extract_json(content.strip())


def call_llm(topic, subtopics, class_num):
    """Call OpenGateway API to generate visual scene description."""
    model = os.environ.get('OPENAI_MODEL', 'mimo-v2.5-pro')

    prompt = f"""You are a math teacher creating visual frames AND English narration for a Class {class_num} NCERT math video.

Topic: {topic}
Subtopics: {', '.join(subtopics)}

Generate a JSON with BOTH visual scene AND narration. Each narration line must EXPLAIN what is shown in that step's visuals.

Return ONLY valid JSON (no markdown, no explanation) with this exact format:
{{
  "title": "short title for the lesson",
  "steps": [
    {{
      "label": "Step 1 title",
      "narration": "English text that teacher speaks while this visual is shown - explain what the student sees",
      "elements": [
        {{"type": "text", "x": 540, "y": 200, "text": "Hello", "size": 48, "color": "#2563EB", "bold": true}},
        {{"type": "circle", "cx": 300, "cy": 500, "r": 50, "fill": "#DBEAFE", "outline": "#2563EB"}},
        {{"type": "rect", "x": 100, "y": 300, "w": 200, "h": 100, "fill": "#D1FAE5", "outline": "#10B981"}},
        {{"type": "line", "x1": 100, "y1": 400, "x2": 900, "y2": 400, "color": "#1E293B", "width": 3}},
        {{"type": "arrow", "x1": 100, "y1": 400, "x2": 900, "y2": 400, "color": "#2563EB", "width": 3}},
        {{"type": "number_line", "x": 100, "y": 600, "min": 0, "max": 20, "highlight": [3, 5, 8]}},
        {{"type": "fraction_bar", "x": 100, "y": 700, "w": 800, "h": 60, "num": 3, "den": 4, "color": "#7C3AED"}},
        {{"type": "dots_group", "x": 200, "y": 500, "count": 5, "color": "#2563EB", "spacing": 70}},
        {{"type": "grid", "x": 100, "y": 300, "w": 800, "h": 600, "rows": 5, "cols": 5}},
        {{"type": "star", "cx": 540, "cy": 400, "size": 60, "fill": "#F59E0B", "outline": "#D97706"}},
        {{"type": "hexagon", "cx": 540, "cy": 400, "size": 80, "fill": "#E0E7FF", "outline": "#6366F1"}},
        {{"type": "ruler", "x": 100, "y": 800, "w": 800, "min": 0, "max": 30, "unit": "cm"}},
        {{"type": "clock_face", "cx": 540, "cy": 600, "r": 150, "hour": 3, "minute": 15}},
        {{"type": "bar_chart", "x": 100, "y": 400, "w": 800, "h": 500, "data": [{{"label": "Mon", "value": 5, "color": "#2563EB"}}, {{"label": "Tue", "value": 8, "color": "#7C3AED"}}]}}
      ]
    }}
  ]
}}

Rules:
- Canvas is 1080x1920 (portrait). VISUAL AREA is y=280 to y=1700. Keep ALL elements within this visual area.
- Center elements horizontally around x=540. For groups (dots, grids), calculate the group width and center it.
- Create 4-6 steps that TEACH the topic progressively (easy → concept → example → practice).
- Each step should build on the previous one.
- Use subtopics to guide step generation — each subtopic can become a step.
- For Class 1-5: use large fonts (size 48+), simple visuals (dots_group, counting), fewer steps (3-4).
- For Class 6-10: use detailed explanations, more steps (5-6), complex visuals (number_line, fraction_bar, grid).
- Use visual elements to EXPLAIN, not just display text.
- For addition/subtraction: show groups merging/separating with dots_group, then the equation.
- For multiplication: show repeated addition with dots_group arrays or grid.
- For division: show equal grouping with dots_group, separating into groups.
- For fractions: use fraction_bar to visualize parts.
- For geometry: use circle, rect, triangle, line to draw shapes.
- For number concepts: use number_line.
- For measurement: use ruler to show length/height comparison.
- For time/clock: use clock_face to show hours and minutes.
- For data handling: use bar_chart to visualize data.
- For patterns: use repeating shapes (star, hexagon, circle) in sequence.
- Colors: primary blue #2563EB, success green #10B981, accent amber #F59E0B, danger red #EF4444, purple #7C3AED.
- All text should be in English.
"""

    try:
        print(f"    [debug] model={model}, base_url={os.environ.get('OPENAI_BASE_URL', 'default')}", flush=True)
        content = _call_api(
            messages=[
                {"role": "system", "content": "You are a friendly English math teacher making a YouTube video for kids. Narration must be in English — warm, encouraging, simple words. Like: 'Very good kids!', 'Let us see', 'Understood?' Return only valid JSON, no markdown."},
                {"role": "user", "content": prompt}
            ],
            model=model, temperature=0.7, max_tokens=3000
        )
        print(f"    [debug] content={repr(content[:200]) if content else 'None'}", flush=True)
        if not content:
            return None

        # Clean up markdown code blocks if present
        if content.startswith('```'):
            content = content.split('\n', 1)[1] if '\n' in content else content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        if content.startswith('json'):
            content = content[4:].strip()

        scene = json.loads(content)
        if 'steps' in scene and len(scene['steps']) > 0:
            print(f"  LLM generated {len(scene['steps'])} visual steps", flush=True)
            return scene
        else:
            print("  LLM response missing 'steps', falling back", flush=True)
            return None

    except json.JSONDecodeError as e:
        print(f"  LLM returned invalid JSON: {e}", flush=True)
        print(f"  Content was: {repr(content[:300])}", flush=True)
        return _retry_llm_simple(model, topic, class_num)
    except Exception as e:
        print(f"  LLM API error: {type(e).__name__}: {e}", flush=True)
        return None


def _retry_llm_simple(model, topic, class_num):
    """Retry LLM with a simpler prompt after JSON parse failure."""
    simple_prompt = f"""Generate a JSON scene for teaching "{topic}" to Class {class_num} students.
Return ONLY valid JSON, no markdown, no explanation.
Format: {{"title":"...","steps":[{{"label":"...","narration":"English narration here","elements":[{{"type":"text","x":540,"y":200,"text":"...","size":48,"color":"#2563EB"}}]}}]}}
Use 4 steps with elements: text, circle, rect, dots_group, fraction_bar, number_line.
Canvas: 1080x1920. Bounds: x 50-1030, y 50-1870.
IMPORTANT: Each step MUST have a "narration" field in English that explains the visual to a child."""

    try:
        content = _call_api(
            messages=[
                {"role": "system", "content": "Return only valid JSON. Narration must be in English."},
                {"role": "user", "content": simple_prompt}
            ],
            model=model, temperature=0.5, max_tokens=2000
        )
        if not content:
            return None

        if content.startswith('```'):
            content = content.split('\n', 1)[1] if '\n' in content else content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        if content.startswith('json'):
            content = content[4:].strip()

        scene = json.loads(content)
        if 'steps' in scene and len(scene['steps']) > 0:
            print(f"  Retry generated {len(scene['steps'])} steps", flush=True)
            return scene
        return None
    except Exception as e2:
        print(f"  Retry also failed: {e2}", flush=True)
        return None


# ============ ELEMENT RENDERERS ============

def draw_element_text(draw, el):
    """Draw text element — always centered for YouTube Shorts (1080x1920)."""
    size = el.get('size', 32)
    bold = el.get('bold', False)
    font = get_font(size, bold)
    color = hex_to_rgb(el.get('color', COLORS['text']))
    text = el.get('text', '')
    y = el.get('y', 100)
    center_x = el.get('x', WIDTH // 2)
    max_width = el.get('max_width', 900)
    line_spacing = el.get('line_spacing', int(size * 0.35))

    words = str(text).split()
    lines = []
    current = []
    for word in words:
        candidate = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if current and bbox[2] - bbox[0] > max_width:
            lines.append(' '.join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(' '.join(current))
    if not lines:
        lines = ['']

    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = max(40, min(WIDTH - tw - 40, int(center_x - tw // 2)))
        draw.text((x, y + line_idx * (th + line_spacing)), line, fill=color, font=font)


def draw_element_circle(draw, el):
    """Draw circle element."""
    cx, cy = el.get('cx', 200), el.get('cy', 200)
    r = el.get('r', 50)
    fill = hex_to_rgb(el.get('fill', '#DBEAFE'))
    outline = hex_to_rgb(el.get('outline', COLORS['primary']))
    draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=fill, outline=outline, width=3)


def draw_element_rect(draw, el):
    """Draw rectangle element."""
    x, y = el.get('x', 100), el.get('y', 100)
    w, h = el.get('w', 200), el.get('h', 100)
    fill = hex_to_rgb(el.get('fill', '#DBEAFE'))
    outline = hex_to_rgb(el.get('outline', COLORS['primary']))
    radius = el.get('radius', 10)
    draw.rounded_rectangle([(x, y), (x+w, y+h)], radius=radius, fill=fill, outline=outline, width=3)


def draw_element_line(draw, el):
    """Draw line element."""
    x1, y1 = el.get('x1', 100), el.get('y1', 100)
    x2, y2 = el.get('x2', 500), el.get('y2', 100)
    color = hex_to_rgb(el.get('color', COLORS['text']))
    width = el.get('width', 3)
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)


def draw_element_arrow(draw, el):
    """Draw arrow element."""
    x1, y1 = el.get('x1', 100), el.get('y1', 100)
    x2, y2 = el.get('x2', 500), el.get('y2', 100)
    color = hex_to_rgb(el.get('color', COLORS['primary']))
    width = el.get('width', 3)
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    # Arrowhead
    angle = math.atan2(y2-y1, x2-x1)
    arrow_len = 15
    for da in [0.4, -0.4]:
        ax = x2 - arrow_len * math.cos(angle + da)
        ay = y2 - arrow_len * math.sin(angle + da)
        draw.line([(x2, y2), (int(ax), int(ay))], fill=color, width=width)


def draw_element_number_line(draw, el):
    """Draw number line with highlighted numbers."""
    x0 = el.get('x', 100)
    y = el.get('y', 600)
    min_val = el.get('min', 0)
    max_val = el.get('max', 20)
    highlight = set(el.get('highlight', []))
    line_color = hex_to_rgb(COLORS['text'])
    x1 = el.get('x1', x0 + 880)

    draw.line([(x0, y), (x1, y)], fill=line_color, width=3)
    draw.polygon([(x0, y), (x0+12, y-6), (x0+12, y+6)], fill=line_color)
    draw.polygon([(x1, y), (x1-12, y-6), (x1-12, y+6)], fill=line_color)

    num_steps = max_val - min_val
    for i in range(num_steps + 1):
        val = min_val + i
        x = x0 + i * (x1 - x0) // num_steps
        is_hl = val in highlight
        tick_color = hex_to_rgb(COLORS['primary']) if is_hl else line_color
        tick_len = 15 if is_hl else 8
        draw.line([(x, y - tick_len), (x, y + tick_len)], fill=tick_color, width=2 if is_hl else 1)
        font = get_font(20, bold=is_hl)
        label = str(val)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw // 2, y + 20), label, fill=tick_color, font=font)
        if is_hl:
            draw.ellipse([(x-8, y-8), (x+8, y+8)], fill=hex_to_rgb(COLORS['primary']))


def draw_element_fraction_bar(draw, el):
    """Draw fraction bar visualization."""
    x = el.get('x', 100)
    y = el.get('y', 700)
    w = el.get('w', 800)
    h = el.get('h', 60)
    num = el.get('num', 1)
    den = el.get('den', 2)
    color = hex_to_rgb(el.get('color', COLORS['primary']))
    light = hex_to_rgb(COLORS['grid'])
    outline = hex_to_rgb(COLORS['text'])

    part_w = w / den
    for i in range(den):
        px = x + i * part_w
        c = color if i < num else light
        draw.rectangle([(px, y), (px + part_w - 2, y + h)], fill=c, outline=outline, width=1)

    font = get_font(28, bold=True)
    label = f"{num}/{den}"
    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((x + w // 2 - tw // 2, y + h + 15), label, fill=color, font=font)


def draw_element_dots_group(draw, el):
    """Draw a group of dots (for counting, addition, subtraction)."""
    x = el.get('x', 200)
    y = el.get('y', 500)
    count = el.get('count', 5)
    color = hex_to_rgb(el.get('color', COLORS['primary']))
    outline = hex_to_rgb(el.get('outline', '#1D4ED8'))
    spacing = el.get('spacing', 70)
    r = el.get('r', 30)
    label_below = el.get('label', True)
    label_size = el.get('label_size', 30)
    label_gap = el.get('label_gap', 14)
    row_spacing = el.get('row_spacing', max(spacing, r * 2 + label_size + label_gap + 18))

    cols = min(5, count)
    font = get_font(label_size, bold=True)
    for i in range(count):
        row = i // cols
        col = i % cols
        cx = x + col * spacing
        cy = y + row * row_spacing
        draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=color, outline=outline, width=3)
        if label_below:
            label = str(i + 1)
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            lx = cx - tw // 2
            ly = cy + r + label_gap
            pad_x = 10
            pad_y = 5
            draw.rounded_rectangle(
                [(lx - pad_x, ly - pad_y), (lx + tw + pad_x, ly + th + pad_y)],
                radius=8,
                fill=hex_to_rgb('#FFFFFF'),
                outline=hex_to_rgb('#CBD5E1'),
                width=1,
            )
            draw.text((lx, ly), label, fill=hex_to_rgb('#0F172A'), font=font)


def draw_element_grid(draw, el):
    """Draw a grid."""
    x = el.get('x', 100)
    y = el.get('y', 300)
    w = el.get('w', 800)
    h = el.get('h', 600)
    rows = el.get('rows', 5)
    cols = el.get('cols', 5)
    color = hex_to_rgb(COLORS['grid'])
    bold_color = hex_to_rgb(COLORS['text_light'])

    for i in range(cols + 1):
        lx = x + i * w // cols
        c = bold_color if i % 5 == 0 else color
        draw.line([(lx, y), (lx, y + h)], fill=c, width=1)
    for j in range(rows + 1):
        ly = y + j * h // rows
        c = bold_color if j % 5 == 0 else color
        draw.line([(x, ly), (x + w, ly)], fill=c, width=1)


def draw_element_triangle(draw, el):
    """Draw triangle from 3 points."""
    points = el.get('points', [[200, 600], [500, 300], [800, 600]])
    fill = hex_to_rgb(el.get('fill', '#EDE9FE'))
    outline = hex_to_rgb(el.get('outline', COLORS['secondary']))
    pts = [(p[0], p[1]) for p in points]
    draw.polygon(pts, fill=fill, outline=outline)


def draw_element_arc(draw, el):
    """Draw arc (for angles, circles)."""
    cx, cy = el.get('cx', 400), el.get('cy', 400)
    r = el.get('r', 150)
    start = el.get('start', 0)
    end = el.get('end', 90)
    color = hex_to_rgb(el.get('color', COLORS['primary']))
    width = el.get('width', 3)
    draw.arc([(cx-r, cy-r), (cx+r, cy+r)], start, end, fill=color, width=width)


def draw_element_star(draw, el):
    """Draw a 5-pointed star."""
    import math as _math
    cx, cy = el.get('cx', 540), el.get('cy', 400)
    size = el.get('size', 60)
    fill = hex_to_rgb(el.get('fill', '#F59E0B'))
    outline = hex_to_rgb(el.get('outline', '#D97706'))
    points = []
    for i in range(10):
        angle = _math.radians(i * 36 - 90)
        r = size if i % 2 == 0 else size * 0.4
        points.append((int(cx + r * _math.cos(angle)), int(cy + r * _math.sin(angle))))
    draw.polygon(points, fill=fill, outline=outline)


def draw_element_hexagon(draw, el):
    """Draw a regular hexagon."""
    import math as _math
    cx, cy = el.get('cx', 540), el.get('cy', 400)
    size = el.get('size', 80)
    fill = hex_to_rgb(el.get('fill', '#E0E7FF'))
    outline = hex_to_rgb(el.get('outline', '#6366F1'))
    points = []
    for i in range(6):
        angle = _math.radians(60 * i - 30)
        points.append((int(cx + size * _math.cos(angle)), int(cy + size * _math.sin(angle))))
    draw.polygon(points, fill=fill, outline=outline)


def draw_element_ruler(draw, el):
    """Draw a horizontal ruler with markings."""
    x0 = el.get('x', 100)
    y = el.get('y', 800)
    w = el.get('w', 800)
    min_val = el.get('min', 0)
    max_val = el.get('max', 30)
    unit = el.get('unit', 'cm')
    line_color = hex_to_rgb(COLORS['text'])
    accent = hex_to_rgb(COLORS['primary'])

    # Main bar
    draw.rectangle([(x0, y), (x0 + w, y + 40)], fill=hex_to_rgb('#F8FAFC'), outline=line_color, width=2)

    # Tick marks
    num_ticks = max_val - min_val
    for i in range(num_ticks + 1):
        x = x0 + i * w // num_ticks
        is_major = i % 5 == 0
        tick_len = 25 if is_major else 12
        tick_color = accent if is_major else line_color
        draw.line([(x, y), (x, y + tick_len)], fill=tick_color, width=2 if is_major else 1)
        if is_major:
            font = get_font(18, bold=True)
            label = str(min_val + i)
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((x - tw // 2, y + 28), label, fill=accent, font=font)

    # Unit label
    font_unit = get_font(20, bold=True)
    draw.text((x0 + w + 10, y + 5), unit, fill=hex_to_rgb(COLORS['text_light']), font=font_unit)


def draw_element_clock_face(draw, el):
    """Draw an analog clock face."""
    import math as _math
    cx, cy = el.get('cx', 540), el.get('cy', 600)
    r = el.get('r', 150)
    hour = el.get('hour', 3)
    minute = el.get('minute', 15)
    face_color = hex_to_rgb('#F8FAFC')
    outline_color = hex_to_rgb(COLORS['text'])
    hand_color = hex_to_rgb(COLORS['primary'])
    minute_color = hex_to_rgb(COLORS['secondary'])

    # Clock circle
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=face_color, outline=outline_color, width=3)

    # Hour markers
    for i in range(12):
        angle = _math.radians(i * 30 - 90)
        inner = r - 20
        outer = r - 8
        x1 = int(cx + inner * _math.cos(angle))
        y1 = int(cy + inner * _math.sin(angle))
        x2 = int(cx + outer * _math.cos(angle))
        y2 = int(cy + outer * _math.sin(angle))
        draw.line([(x1, y1), (x2, y2)], fill=outline_color, width=3)

        # Hour numbers
        num_r = r - 35
        nx = int(cx + num_r * _math.cos(angle))
        ny = int(cy + num_r * _math.sin(angle))
        font = get_font(20, bold=True)
        label = str(i if i != 0 else 12)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((nx - tw // 2, ny - th // 2), label, fill=outline_color, font=font)

    # Hour hand
    hour_angle = _math.radians((hour % 12 + minute / 60) * 30 - 90)
    hour_len = r * 0.5
    hx = int(cx + hour_len * _math.cos(hour_angle))
    hy = int(cy + hour_len * _math.sin(hour_angle))
    draw.line([(cx, cy), (hx, hy)], fill=hand_color, width=6)

    # Minute hand
    min_angle = _math.radians(minute * 6 - 90)
    min_len = r * 0.75
    mx = int(cx + min_len * _math.cos(min_angle))
    my = int(cy + min_len * _math.sin(min_angle))
    draw.line([(cx, cy), (mx, my)], fill=minute_color, width=4)

    # Center dot
    draw.ellipse([(cx - 6, cy - 6), (cx + 6, cy + 6)], fill=hand_color)

    # Digital time below
    font_time = get_font(28, bold=True)
    time_str = f"{hour:02d}:{minute:02d}"
    bbox = draw.textbbox((0, 0), time_str, font=font_time)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw // 2, cy + r + 20), time_str, fill=hand_color, font=font_time)


def draw_element_bar_chart(draw, el):
    """Draw a bar chart."""
    x0 = el.get('x', 100)
    y0 = el.get('y', 400)
    w = el.get('w', 800)
    h = el.get('h', 500)
    data = el.get('data', [])
    if not data:
        return

    line_color = hex_to_rgb(COLORS['text'])
    grid_color = hex_to_rgb(COLORS['grid'])

    # Axes
    draw.line([(x0, y0), (x0, y0 + h)], fill=line_color, width=3)
    draw.line([(x0, y0 + h), (x0 + w, y0 + h)], fill=line_color, width=3)

    # Find max value
    max_val = max(d.get('value', 1) for d in data)
    if max_val == 0:
        max_val = 1

    # Grid lines
    for i in range(5):
        gy = y0 + h - (i + 1) * h // 5
        draw.line([(x0, gy), (x0 + w, gy)], fill=grid_color, width=1)
        font_label = get_font(16)
        val_label = str(int(max_val * (i + 1) / 5))
        draw.text((x0 - 35, gy - 8), val_label, fill=hex_to_rgb(COLORS['text_light']), font=font_label)

    # Bars
    bar_count = len(data)
    bar_gap = 20
    total_gap = bar_gap * (bar_count + 1)
    bar_width = max(40, (w - total_gap) // bar_count)

    for i, d in enumerate(data):
        bx = x0 + bar_gap + i * (bar_width + bar_gap)
        val = d.get('value', 0)
        bar_h = int(h * val / max_val)
        by = y0 + h - bar_h
        color = hex_to_rgb(d.get('color', COLORS['primary']))

        draw.rectangle([(bx, by), (bx + bar_width, y0 + h)], fill=color, outline=hex_to_rgb(COLORS['text']), width=1)

        # Value on top
        font_val = get_font(20, bold=True)
        val_text = str(val)
        bbox = draw.textbbox((0, 0), val_text, font=font_val)
        tw = bbox[2] - bbox[0]
        draw.text((bx + bar_width // 2 - tw // 2, by - 25), val_text, fill=color, font=font_val)

        # Label below
        font_lbl = get_font(18)
        lbl = d.get('label', '')
        bbox2 = draw.textbbox((0, 0), lbl, font=font_lbl)
        tw2 = bbox2[2] - bbox2[0]
        draw.text((bx + bar_width // 2 - tw2 // 2, y0 + h + 10), lbl, fill=hex_to_rgb(COLORS['text']), font=font_lbl)


# Element dispatcher
ELEMENT_RENDERERS = {
    'text': draw_element_text,
    'circle': draw_element_circle,
    'rect': draw_element_rect,
    'line': draw_element_line,
    'arrow': draw_element_arrow,
    'number_line': draw_element_number_line,
    'fraction_bar': draw_element_fraction_bar,
    'dots_group': draw_element_dots_group,
    'grid': draw_element_grid,
    'triangle': draw_element_triangle,
    'arc': draw_element_arc,
    'star': draw_element_star,
    'hexagon': draw_element_hexagon,
    'ruler': draw_element_ruler,
    'clock_face': draw_element_clock_face,
    'bar_chart': draw_element_bar_chart,
}


def _ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) * (1 - t)


def _shift_element(el, dx=0, dy=0):
    shifted = dict(el)
    for key in ('x', 'cx', 'x1', 'x2'):
        if key in shifted:
            shifted[key] += dx
    for key in ('y', 'cy', 'y1', 'y2'):
        if key in shifted:
            shifted[key] += dy
    if 'points' in shifted:
        shifted['points'] = [[x + dx, y + dy] for x, y in shifted['points']]
    return shifted


def _animated_element(el, progress):
    eased = _ease_out(progress)
    dy = int((1 - eased) * 38)
    animated = _shift_element(el, dy=dy)

    if animated.get('type') == 'dots_group':
        count = animated.get('count', 1)
        animated['count'] = max(1, min(count, int(math.ceil(count * eased))))

    return animated


def _draw_element_animated(base_img, el, progress):
    """Draw one element with simple fade, slide, and count reveal animation."""
    el_type = el.get('type', 'text')
    renderer = ELEMENT_RENDERERS.get(el_type)
    if not renderer:
        return

    layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    renderer(layer_draw, _animated_element(el, progress))

    alpha = int(255 * _ease_out(progress))
    if alpha < 255:
        alpha_layer = layer.getchannel('A').point(lambda value: value * alpha // 255)
        layer.putalpha(alpha_layer)

    base_img.alpha_composite(layer)


def render_scene(scene, frames_dir="temp_frames", frames_per_step=5):
    """Render a scene into YouTube Shorts frames (1080x1920) with PRO visuals.

    Layout:
    ┌─────────────────────────┐
    │  Gradient Background     │
    │  Header (title)    30-110│
    │  Chapter badge    120-160│
    │  Progress dots       190 │
    │  Step label card  220-290│
    │                         │
    │  VISUAL AREA      310-1650│
    │  (all elements here,    │
    │   inside shadow cards)  │
    │                         │
    │  Teacher avatar  1700    │
    │  Progress bar   1800-1840│
    │  Watermark       1870    │
    └─────────────────────────┘
    """
    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    steps = scene.get('steps', [])
    title = scene.get('title', 'Math Lesson')
    chapter = scene.get('chapter', '')
    class_num = scene.get('class', '')
    total_frames = len(steps) * frames_per_step
    frame_paths = []

    # Color palettes for variety
    gradient_pairs = [
        ('#667EEA', '#764BA2'),  # Purple-blue
        ('#F093FB', '#F5576C'),  # Pink-coral
        ('#4FACFE', '#00F2FE'),  # Cyan-blue
        ('#43E97B', '#38F9D7'),  # Green-teal
        ('#FA709A', '#FEE140'),  # Pink-yellow
        ('#A18CD1', '#FBC2EB'),  # Lavender-pink
    ]
    grad = random.choice(gradient_pairs)

    # Step colors for text variety
    step_colors = ['#2563EB', '#7C3AED', '#059669', '#D97706', '#DC2626', '#0891B2']

    # Pre-render gradient background once (reuse for all frames)
    gradient_bg = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb('#FFFFFF'))
    grad_draw = ImageDraw.Draw(gradient_bg)
    draw_gradient_bg(grad_draw, gradient_bg, grad[0], grad[1])
    # Add frosted glass overlay
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(25, 225), (WIDTH - 25, HEIGHT - 100)],
        radius=30, fill=(255, 255, 255, 180)
    )
    gradient_bg = Image.alpha_composite(gradient_bg.convert('RGBA'), overlay).convert('RGB')

    for frame_idx in range(total_frames):
        step_idx = min(frame_idx // frames_per_step, len(steps) - 1)
        step = steps[step_idx]
        step_progress = (frame_idx % frames_per_step) / frames_per_step

        # Copy pre-rendered gradient
        img = gradient_bg.copy().convert('RGBA')
        draw = ImageDraw.Draw(img)

        # ── Header bar with shadow ──
        draw_shadow_card(draw, [(30, 30), (WIDTH - 30, 115)], radius=22, card_color='#1E293B', shadow_color='#CBD5E1')
        header_font = get_font(30, bold=True)
        bbox = draw.textbbox((0, 0), title[:40], font=header_font)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, 55), title[:40], fill=hex_to_rgb('#FFFFFF'), font=header_font)

        # ── Class/Chapter badge below header ──
        badge_text = f"Class {class_num}" if class_num else ""
        if chapter:
            badge_text += f"  |  {chapter}"[:30]
        if badge_text:
            draw_chapter_badge(draw, (WIDTH - 300) // 2, 125, badge_text, '#1E293B')

        # ── Progress dots ──
        draw_step_dots(draw, (WIDTH - (len(steps) - 1) * 45) // 2, 200,
                       len(steps), step_idx)

        # ── Step label card with shadow ──
        step_label = step.get('label', f'Step {step_idx + 1}')
        label_text = f"Step {step_idx + 1}: {step_label}"
        label_font = get_font(28, bold=True)
        step_color = step_colors[step_idx % len(step_colors)]
        draw_shadow_card(draw, [(40, 230), (WIDTH - 40, 295)], radius=18, card_color='#FFFFFF', shadow_color='#E2E8F0')
        # Colored accent bar on left
        draw.rounded_rectangle([(40, 230), (52, 295)], radius=6, fill=hex_to_rgb(step_color))
        bbox2 = draw.textbbox((0, 0), label_text, font=label_font)
        tw2 = bbox2[2] - bbox2[0]
        draw.text(((WIDTH - tw2) // 2, 245), label_text, fill=hex_to_rgb(step_color), font=label_font)

        # ── Draw elements (visual area: y=310 to y=1650) in shadow card ──
        draw_shadow_card(draw, [(40, 310), (WIDTH - 40, 1650)], radius=24, card_color='#FFFFFF', shadow_color='#E2E8F0')

        elements = step.get('elements', [])
        total_elements = max(1, len(elements))
        immediately_visible = min(3, total_elements)
        for element_idx, el in enumerate(elements):
            start = element_idx / total_elements * 0.42
            element_progress = (step_progress - start) / 0.14
            if element_idx < immediately_visible:
                element_progress = max(0.35, element_progress)
            if element_progress <= 0:
                continue
            try:
                _draw_element_animated(img, el, element_progress)
            except Exception as e:
                print(f"  Warning: failed to render {el.get('type', 'element')}: {e}", flush=True)

        # ── Teacher avatar (small, bottom-left) ──
        draw_teacher_avatar(draw, 90, 1750, size=50)

        # ── Progress bar ──
        progress = (step_idx + 1) / len(steps)
        draw_progress_bar(draw, 150, 1780, WIDTH - 300, 16, progress, step_color)

        # ── Watermark / Channel name ──
        wm_font = get_font(18)
        draw.text((WIDTH // 2, HEIGHT - 40), "Learn with Fun!",
                  fill=hex_to_rgb('#94A3B8'), font=wm_font, anchor='mm')

        # Save frame
        frame_path = frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
        img.convert('RGB').save(frame_path)
        frame_paths.append(str(frame_path))

    return frame_paths


def _estimate_frames_per_step(narrations, fps=TARGET_FPS):
    """Choose enough animation frames for teacher narration to stay fluid."""
    if not narrations:
        return fps * 4

    estimated_durations = []
    for narration in narrations:
        word_count = len(str(narration).split())
        # Edge TTS teaching voice is usually around 2.2 words/sec. Add a small
        # pause so each visual breathes instead of racing the narration.
        estimated_durations.append(max(3.5, (word_count / 2.2) + 0.8))

    return max(fps * 3, min(fps * 6, int(math.ceil(max(estimated_durations) * fps))))


def generate_visual(topic, frames_dir="temp_frames"):
    """Main entry: generate visual frames for a topic using LLM + PIL.

    Returns (frames, narrations) tuple:
      - frames: list of frame file paths
      - narrations: list of English narration strings (one per step, synced with frames)
    Returns (None, None) on failure.
    """
    topic_text = topic.get('topic', '')
    chapter = topic.get('chapter', '')
    class_num = topic.get('class', 6)
    subtopics = topic.get('subtopics', [])

    print(f"  Generating LLM visual for: {topic_text}", flush=True)

    # Call LLM to get scene description
    scene = call_llm(topic_text, subtopics, class_num)

    if not scene:
        print("  LLM failed, using smart fallback...", flush=True)
        scene = _generate_fallback_scene(topic_text, subtopics, class_num)

    if scene:
        # Center all elements within visual area (y=280 to y=1700)
        for step in scene.get('steps', []):
            step['elements'] = _center_step_elements(step.get('elements', []))

        # Extract narration from each step
        narrations = []
        for step in scene.get('steps', []):
            narr = step.get('narration', '')
            if narr:
                narrations.append(narr)

        # Render enough frames per step so the 30fps video stays smooth while
        # the matching TTS clip plays.
        frames_per_step = _estimate_frames_per_step(narrations)
        frames = render_scene(scene, frames_dir, frames_per_step=frames_per_step)
        print(f"  Generated {len(frames)} visual frames, {len(narrations)} narration lines", flush=True)
        return frames, narrations

    return None, None


# Visual area bounds for YouTube Shorts
VISUAL_TOP = 280
VISUAL_BOTTOM = 1700
VISUAL_CENTER_Y = (VISUAL_TOP + VISUAL_BOTTOM) // 2  # 990


def _place_value_rows(y, tens_text, ones_text, number_text, color='#2563EB'):
    """Build reusable place-value table elements."""
    return [
        {'type': 'text', 'x': 540, 'y': y - 135, 'text': number_text, 'size': 58, 'color': color, 'bold': True},
        {'type': 'rect', 'x': 160, 'y': y, 'w': 360, 'h': 120, 'fill': '#DBEAFE', 'outline': '#2563EB', 'radius': 18, 'lock_position': True},
        {'type': 'rect', 'x': 520, 'y': y, 'w': 360, 'h': 120, 'fill': '#FEF3C7', 'outline': '#F59E0B', 'radius': 18, 'lock_position': True},
        {'type': 'text', 'x': 340, 'y': y + 18, 'text': 'TENS', 'size': 34, 'color': '#2563EB', 'bold': True},
        {'type': 'text', 'x': 700, 'y': y + 18, 'text': 'ONES', 'size': 34, 'color': '#D97706', 'bold': True},
        {'type': 'text', 'x': 340, 'y': y + 68, 'text': tens_text, 'size': 42, 'color': '#1E293B', 'bold': True},
        {'type': 'text', 'x': 700, 'y': y + 68, 'text': ones_text, 'size': 42, 'color': '#1E293B', 'bold': True},
    ]


def _generate_tens_ones_scene(topic_text, class_num):
    """Detailed deterministic fallback for place value: tens and ones."""
    return [
        {
            'label': 'What are tens and ones?',
            'narration': (
                'Today we will learn tens and ones in detail. A one is a single object. '
                'A ten is one bundle made from ten single objects. This idea helps us read numbers quickly.'
            ),
            'elements': [
                {'type': 'text', 'x': 540, 'y': 190, 'text': 'Tens and Ones', 'size': 58, 'color': '#2563EB', 'bold': True, 'max_width': 900},
                {'type': 'text', 'x': 540, 'y': 320, 'text': '1 one = single item', 'size': 38, 'color': '#1E293B', 'bold': True},
                {'type': 'dots_group', 'x': 260, 'y': 520, 'count': 1, 'color': '#F59E0B', 'spacing': 70, 'label_size': 32, 'lock_position': True},
                {'type': 'text', 'x': 540, 'y': 700, 'text': '10 ones grouped together = 1 ten', 'size': 38, 'color': '#1E293B', 'bold': True, 'max_width': 850},
                {'type': 'rect', 'x': 190, 'y': 805, 'w': 470, 'h': 310, 'fill': '#FFFFFF', 'outline': '#2563EB', 'radius': 22, 'lock_position': True},
                {'type': 'dots_group', 'x': 255, 'y': 875, 'count': 10, 'color': '#2563EB', 'spacing': 82, 'row_spacing': 116, 'r': 31, 'label_size': 31, 'lock_position': True},
                {'type': 'text', 'x': 825, 'y': 960, 'text': '= 1 ten', 'size': 44, 'color': '#10B981', 'bold': True},
            ],
        },
        {
            'label': 'Place-value chart',
            'narration': (
                'Every digit has a place. The right side is ones. The next place on the left is tens. '
                'For example, in the number twenty four, two is in the tens place and four is in the ones place.'
            ),
            'elements': [
                {'type': 'text', 'x': 540, 'y': 190, 'text': 'Place Value Chart', 'size': 54, 'color': '#7C3AED', 'bold': True},
                *_place_value_rows(520, '2', '4', '24 = 2 tens and 4 ones', '#7C3AED'),
                {'type': 'text', 'x': 540, 'y': 820, 'text': '2 tens = 20', 'size': 42, 'color': '#2563EB', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 920, 'text': '4 ones = 4', 'size': 42, 'color': '#F59E0B', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 1050, 'text': '20 + 4 = 24', 'size': 58, 'color': '#10B981', 'bold': True},
            ],
        },
        {
            'label': 'Build number 37',
            'narration': (
                'Let us build the number thirty seven. Thirty seven has three tens and seven ones. '
                'Three tens means thirty, and seven ones means seven. Thirty plus seven makes thirty seven.'
            ),
            'elements': [
                {'type': 'text', 'x': 540, 'y': 170, 'text': '37 = 3 tens + 7 ones', 'size': 50, 'color': '#2563EB', 'bold': True, 'max_width': 920},
                {'type': 'rect', 'x': 160, 'y': 390, 'w': 120, 'h': 350, 'fill': '#DBEAFE', 'outline': '#2563EB', 'radius': 18, 'lock_position': True},
                {'type': 'rect', 'x': 310, 'y': 390, 'w': 120, 'h': 350, 'fill': '#DBEAFE', 'outline': '#2563EB', 'radius': 18, 'lock_position': True},
                {'type': 'rect', 'x': 460, 'y': 390, 'w': 120, 'h': 350, 'fill': '#DBEAFE', 'outline': '#2563EB', 'radius': 18, 'lock_position': True},
                {'type': 'text', 'x': 340, 'y': 770, 'text': '3 tens = 30', 'size': 38, 'color': '#2563EB', 'bold': True},
                {'type': 'dots_group', 'x': 650, 'y': 455, 'count': 7, 'color': '#F59E0B', 'spacing': 82, 'row_spacing': 116, 'r': 31, 'label_size': 31, 'lock_position': True},
                {'type': 'text', 'x': 760, 'y': 770, 'text': '7 ones = 7', 'size': 38, 'color': '#D97706', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 940, 'text': '30 + 7 = 37', 'size': 62, 'color': '#10B981', 'bold': True},
            ],
        },
        {
            'label': 'Read any two-digit number',
            'narration': (
                'Use this rule for every two digit number. First read the tens digit, then read the ones digit. '
                'In fifty six, five tens make fifty, and six ones make six.'
            ),
            'elements': [
                {'type': 'text', 'x': 540, 'y': 170, 'text': 'Rule: tens first, ones second', 'size': 46, 'color': '#7C3AED', 'bold': True, 'max_width': 900},
                *_place_value_rows(500, '5', '6', '56', '#7C3AED'),
                {'type': 'arrow', 'x1': 335, 'y1': 720, 'x2': 335, 'y2': 860, 'color': '#2563EB', 'width': 6},
                {'type': 'arrow', 'x1': 700, 'y1': 720, 'x2': 700, 'y2': 860, 'color': '#F59E0B', 'width': 6},
                {'type': 'text', 'x': 335, 'y': 900, 'text': '5 tens = 50', 'size': 36, 'color': '#2563EB', 'bold': True},
                {'type': 'text', 'x': 700, 'y': 900, 'text': '6 ones = 6', 'size': 36, 'color': '#D97706', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 1060, 'text': '50 + 6 = 56', 'size': 56, 'color': '#10B981', 'bold': True},
            ],
        },
        {
            'label': 'Do not confuse the places',
            'narration': (
                'Be careful. In forty two, four is tens and two is ones. '
                'If we swap the digits, twenty four is a different number. Place value changes the value.'
            ),
            'elements': [
                {'type': 'text', 'x': 540, 'y': 160, 'text': '42 is not the same as 24', 'size': 50, 'color': '#EF4444', 'bold': True, 'max_width': 900},
                *_place_value_rows(430, '4', '2', '42 = 40 + 2', '#EF4444'),
                *_place_value_rows(830, '2', '4', '24 = 20 + 4', '#2563EB'),
                {'type': 'text', 'x': 540, 'y': 1160, 'text': 'Same digits, different places, different value!', 'size': 38, 'color': '#1E293B', 'bold': True, 'max_width': 880},
            ],
        },
        {
            'label': 'Practice question',
            'narration': (
                'Now try one yourself. What are the tens and ones in seventy three? '
                'The answer is seven tens and three ones. That means seventy plus three equals seventy three.'
            ),
            'elements': [
                {'type': 'text', 'x': 540, 'y': 170, 'text': 'Practice: 73', 'size': 58, 'color': '#7C3AED', 'bold': True},
                *_place_value_rows(500, '7', '3', '73 = ? tens and ? ones', '#7C3AED'),
                {'type': 'text', 'x': 540, 'y': 850, 'text': 'Answer:', 'size': 42, 'color': '#1E293B', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 960, 'text': '7 tens and 3 ones', 'size': 54, 'color': '#10B981', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 1110, 'text': '70 + 3 = 73', 'size': 56, 'color': '#2563EB', 'bold': True},
            ],
        },
    ]


def _center_step_elements(elements):
    """Adjust element positions so they're centered in the visual area (y=280 to y=1700).

    - Vertically: shift all elements so the group is centered between 280-1700
    - Horizontally: center groups (dots, grids) that are left-aligned
    """
    if not elements:
        return elements

    # Calculate bounding box of all elements
    min_y, max_y = 9999, 0
    for el in elements:
        etype = el.get('type', 'text')
        y = el.get('y', el.get('cy', 500))

        if etype == 'dots_group':
            count = el.get('count', 5)
            cols = min(5, count)
            rows = (count + cols - 1) // cols
            spacing = el.get('spacing', 70)
            top = y
            bottom = y + (rows - 1) * spacing + 50  # +50 for labels
        elif etype == 'fraction_bar':
            top = y
            bottom = y + el.get('h', 60) + 30  # +30 for label below
        elif etype == 'bar_chart':
            top = y
            bottom = y + el.get('h', 500) + 40
        elif etype == 'clock_face':
            r = el.get('r', 150)
            top = y - r
            bottom = y + r + 40  # +40 for digital time below
        elif etype == 'grid':
            top = y
            bottom = y + el.get('h', 600)
        elif etype == 'number_line':
            top = y - 30
            bottom = y + 50
        elif etype == 'ruler':
            top = y
            bottom = y + 60
        elif etype in ('circle', 'star', 'hexagon'):
            r = el.get('r', el.get('size', 50))
            top = y - r
            bottom = y + r
        else:  # text, rect, line, arrow, triangle, arc
            top = y
            # Estimate text height
            size = el.get('size', 32)
            bottom = y + size + 10

        if top < min_y:
            min_y = top
        if bottom > max_y:
            max_y = bottom

    # Calculate vertical shift to center in visual area
    content_height = max_y - min_y
    ideal_top = VISUAL_TOP + (VISUAL_BOTTOM - VISUAL_TOP - content_height) // 2
    y_shift = ideal_top - min_y

    # Don't shift if already well-centered (within 50px)
    if abs(y_shift) < 50:
        y_shift = 0

    # Apply adjustments
    for el in elements:
        etype = el.get('type', 'text')

        # Vertical shift
        if 'y' in el:
            el['y'] += y_shift
        if 'cy' in el:
            el['cy'] += y_shift
        if 'y1' in el:
            el['y1'] += y_shift
        if 'y2' in el:
            el['y2'] += y_shift

        # Horizontal centering for groups that are left-aligned
        if etype == 'dots_group' and not el.get('lock_position'):
            count = el.get('count', 5)
            cols = min(5, count)
            spacing = el.get('spacing', 70)
            group_w = (cols - 1) * spacing + 50  # 50 = dot diameter
            el['x'] = (WIDTH - group_w) // 2

        elif etype == 'grid':
            w = el.get('w', 800)
            el['x'] = (WIDTH - w) // 2

        elif etype == 'fraction_bar':
            w = el.get('w', 800)
            el['x'] = (WIDTH - w) // 2

        elif etype == 'bar_chart':
            w = el.get('w', 800)
            el['x'] = (WIDTH - w) // 2

        elif etype == 'number_line':
            line_w = 880  # default x1 - x
            el['x'] = (WIDTH - line_w) // 2
            el['x1'] = el['x'] + line_w

        elif etype == 'ruler':
            w = el.get('w', 800)
            el['x'] = (WIDTH - w) // 2

        elif etype == 'rect' and not el.get('lock_position'):
            w = el.get('w', 200)
            el['x'] = (WIDTH - w) // 2

    return elements


def _generate_fallback_scene(topic_text, subtopics, class_num):
    """Generate a scene without LLM by analyzing topic keywords."""
    topic_lower = topic_text.lower()
    title = topic_text[:60]
    steps = []

    # Detect topic type and generate appropriate steps
    if any(kw in topic_lower for kw in ['tens', 'ones', 'place value']):
        steps = _generate_tens_ones_scene(topic_text, class_num)

    elif any(kw in topic_lower for kw in ['add', 'addition', 'plus', 'sum', 'jod']):
        # Addition — 4 steps: intro → concept → example → practice
        a, b = 3, 2
        steps.append({
            'label': 'What is Addition?',
            'narration': f'Hello kids! Today we will learn Addition. Addition means combining two or more things together. It is very easy!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 200, 'text': 'Addition (+)', 'size': 56, 'color': '#2563EB', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 400, 'text': 'Adding things together', 'size': 36, 'color': '#64748B'},
                {'type': 'star', 'cx': 300, 'cy': 650, 'size': 50, 'fill': '#F59E0B', 'outline': '#D97706'},
                {'type': 'text', 'x': 420, 'y': 630, 'text': '+', 'size': 56, 'color': '#EF4444', 'bold': True},
                {'type': 'star', 'cx': 540, 'cy': 650, 'size': 50, 'fill': '#10B981', 'outline': '#059669'},
                {'type': 'text', 'x': 640, 'y': 630, 'text': '=', 'size': 56, 'color': '#7C3AED', 'bold': True},
                {'type': 'text', 'x': 720, 'y': 630, 'text': 'More!', 'size': 42, 'color': '#10B981', 'bold': True},
            ]
        })
        steps.append({
            'label': f'Let\'s Add: {a} + {b}',
            'narration': f'Let us add {a} and {b}. First look at {a} balls, then add {b} more balls. Count them one by one!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': f'{a} + {b}', 'size': 56, 'color': '#2563EB', 'bold': True},
                {'type': 'dots_group', 'x': 250, 'y': 400, 'count': a, 'color': '#2563EB', 'spacing': 80},
                {'type': 'text', 'x': 250 + a * 80 + 20, 'y': 420, 'text': '+', 'size': 56, 'color': '#F59E0B', 'bold': True},
                {'type': 'dots_group', 'x': 250 + a * 80 + 90, 'y': 400, 'count': b, 'color': '#7C3AED', 'spacing': 80},
                {'type': 'text', 'x': 540, 'y': 700, 'text': f'{a} + {b} = ?', 'size': 48, 'color': '#EF4444', 'bold': True},
            ]
        })
        steps.append({
            'label': f'Answer: {a} + {b} = {a+b}',
            'narration': f'Very good! Count all the balls together — {a} plus {b} equals {a+b}! Absolutely correct!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': f'{a} + {b} = {a+b}', 'size': 56, 'color': '#10B981', 'bold': True},
                {'type': 'dots_group', 'x': 150, 'y': 400, 'count': a + b, 'color': '#10B981', 'spacing': 70},
                {'type': 'text', 'x': 540, 'y': 700, 'text': f'{a} + {b} = {a+b}', 'size': 64, 'color': '#10B981', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 850, 'text': 'Very Good!', 'size': 36, 'color': '#F59E0B', 'bold': True},
            ]
        })
        steps.append({
            'label': 'Try Another: 4 + 3',
            'narration': f'Now it is your turn! Add four and three. Count the balls and tell — how many are there?',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': 'Your Turn!', 'size': 48, 'color': '#7C3AED', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 300, 'text': '4 + 3 = ?', 'size': 56, 'color': '#2563EB', 'bold': True},
                {'type': 'dots_group', 'x': 250, 'y': 500, 'count': 4, 'color': '#2563EB', 'spacing': 80},
                {'type': 'text', 'x': 600, 'y': 520, 'text': '+', 'size': 56, 'color': '#F59E0B', 'bold': True},
                {'type': 'dots_group', 'x': 680, 'y': 500, 'count': 3, 'color': '#7C3AED', 'spacing': 80},
                {'type': 'text', 'x': 540, 'y': 800, 'text': 'Count all dots!', 'size': 32, 'color': '#64748B'},
                {'type': 'star', 'cx': 540, 'cy': 1000, 'size': 60, 'fill': '#F59E0B', 'outline': '#D97706'},
            ]
        })

    elif any(kw in topic_lower for kw in ['subtract', 'subtraction', 'minus', 'difference', 'ghata']):
        # Subtraction — 4 steps: intro → concept → example → practice
        steps.append({
            'label': 'What is Subtraction?',
            'narration': 'Hello kids! Today we will learn Subtraction. Subtraction means taking away or reducing. Let us see!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 200, 'text': 'Subtraction (-)', 'size': 56, 'color': '#EF4444', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 400, 'text': 'Taking away things', 'size': 36, 'color': '#64748B'},
                {'type': 'dots_group', 'x': 300, 'y': 600, 'count': 5, 'color': '#2563EB', 'spacing': 70},
                {'type': 'text', 'x': 680, 'y': 620, 'text': '-', 'size': 56, 'color': '#EF4444', 'bold': True},
                {'type': 'text', 'x': 770, 'y': 620, 'text': '2', 'size': 48, 'color': '#EF4444', 'bold': True},
            ]
        })
        steps.append({
            'label': 'Remove 2 from 5',
            'narration': 'Look here, there are five balls. Now remove two balls. Remove them one by one!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': '5 - 2', 'size': 56, 'color': '#EF4444', 'bold': True},
                {'type': 'dots_group', 'x': 200, 'y': 400, 'count': 5, 'color': '#2563EB', 'spacing': 80},
                {'type': 'text', 'x': 540, 'y': 650, 'text': 'Remove 2', 'size': 42, 'color': '#EF4444', 'bold': True},
                {'type': 'dots_group', 'x': 200, 'y': 850, 'count': 3, 'color': '#10B981', 'spacing': 80},
                {'type': 'text', 'x': 540, 'y': 1100, 'text': '5 - 2 = ?', 'size': 48, 'color': '#F59E0B', 'bold': True},
            ]
        })
        steps.append({
            'label': 'Answer: 5 - 2 = 3',
            'narration': 'Very good! Take away two from five and three are left. Five minus two equals three!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': '5 - 2 = 3', 'size': 64, 'color': '#10B981', 'bold': True},
                {'type': 'dots_group', 'x': 250, 'y': 400, 'count': 3, 'color': '#10B981', 'spacing': 80},
                {'type': 'text', 'x': 540, 'y': 700, 'text': '3 dots left!', 'size': 36, 'color': '#10B981'},
                {'type': 'star', 'cx': 540, 'cy': 900, 'size': 60, 'fill': '#F59E0B', 'outline': '#D97706'},
            ]
        })
        steps.append({
            'label': 'Try: 7 - 3',
            'narration': 'Now you tell! Remove three from seven balls. How many are left? Count and tell!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': 'Your Turn!', 'size': 48, 'color': '#7C3AED', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 300, 'text': '7 - 3 = ?', 'size': 56, 'color': '#EF4444', 'bold': True},
                {'type': 'dots_group', 'x': 250, 'y': 500, 'count': 7, 'color': '#2563EB', 'spacing': 70},
                {'type': 'text', 'x': 540, 'y': 800, 'text': 'Remove 3 and count!', 'size': 32, 'color': '#64748B'},
            ]
        })

    elif any(kw in topic_lower for kw in ['multiply', 'multiplication', 'times', 'product', 'guna']):
        # Multiplication — 4 steps: intro → concept → example → practice
        steps.append({
            'label': 'What is Multiplication?',
            'narration': 'Hello kids! Today we will learn Multiplication. Multiplication means repeated addition. It is very easy!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 200, 'text': 'Multiplication (x)', 'size': 52, 'color': '#7C3AED', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 400, 'text': 'Repeated Addition', 'size': 36, 'color': '#64748B'},
                {'type': 'text', 'x': 540, 'y': 600, 'text': '2 x 3 = 2+2+2 = 6', 'size': 40, 'color': '#10B981', 'bold': True},
            ]
        })
        steps.append({
            'label': '2 x 3 with Grid',
            'narration': 'Look! Make two rows, put three balls in each row. Count the total — six balls! Two times three equals six.',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': '2 x 3 = 6', 'size': 56, 'color': '#7C3AED', 'bold': True},
                {'type': 'grid', 'x': 250, 'y': 350, 'w': 500, 'h': 350, 'rows': 2, 'cols': 3},
                {'type': 'text', 'x': 540, 'y': 800, 'text': '2 rows, 3 in each', 'size': 32, 'color': '#64748B'},
                {'type': 'text', 'x': 540, 'y': 950, 'text': '= 6', 'size': 56, 'color': '#10B981', 'bold': True},
            ]
        })
        steps.append({
            'label': '3 x 4 = 12',
            'narration': 'Now three rows, four in each. Three times four equals twelve! Count and see!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': '3 x 4 = 12', 'size': 56, 'color': '#7C3AED', 'bold': True},
                {'type': 'grid', 'x': 250, 'y': 350, 'w': 500, 'h': 350, 'rows': 3, 'cols': 4},
                {'type': 'text', 'x': 540, 'y': 800, 'text': '3 rows, 4 in each', 'size': 32, 'color': '#64748B'},
                {'type': 'text', 'x': 540, 'y': 950, 'text': '= 12', 'size': 56, 'color': '#10B981', 'bold': True},
            ]
        })
        steps.append({
            'label': 'Your Turn: 4 x 5',
            'narration': 'Now it is your turn! Four rows, five in each. How many total? Count and tell!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': '4 x 5 = ?', 'size': 56, 'color': '#7C3AED', 'bold': True},
                {'type': 'grid', 'x': 250, 'y': 350, 'w': 500, 'h': 400, 'rows': 4, 'cols': 5},
                {'type': 'text', 'x': 540, 'y': 850, 'text': 'Count all boxes!', 'size': 32, 'color': '#64748B'},
                {'type': 'star', 'cx': 540, 'cy': 1050, 'size': 60, 'fill': '#F59E0B', 'outline': '#D97706'},
            ]
        })

    elif any(kw in topic_lower for kw in ['divide', 'division', 'bhag', 'bato', 'split', 'share']):
        # Division — 4 steps: intro → concept → example → practice
        steps.append({
            'label': 'What is Division?',
            'narration': 'Hello kids! Today we will learn Division. Division means sharing equally. Like sharing chocolates!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 200, 'text': 'Division (÷)', 'size': 56, 'color': '#2563EB', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 400, 'text': 'Equal Sharing', 'size': 36, 'color': '#64748B'},
                {'type': 'dots_group', 'x': 300, 'y': 600, 'count': 6, 'color': '#2563EB', 'spacing': 60},
                {'type': 'text', 'x': 700, 'y': 620, 'text': '÷ 2', 'size': 48, 'color': '#EF4444', 'bold': True},
            ]
        })
        steps.append({
            'label': '6 ÷ 2 = 3',
            'narration': 'There are six balls. Divide them into two equal parts. Each part gets three balls. Six divided by two equals three!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': '6 ÷ 2 = 3', 'size': 56, 'color': '#2563EB', 'bold': True},
                {'type': 'dots_group', 'x': 150, 'y': 400, 'count': 3, 'color': '#2563EB', 'spacing': 70},
                {'type': 'text', 'x': 430, 'y': 420, 'text': '|', 'size': 48, 'color': '#EF4444', 'bold': True},
                {'type': 'dots_group', 'x': 500, 'y': 400, 'count': 3, 'color': '#10B981', 'spacing': 70},
                {'type': 'text', 'x': 540, 'y': 700, 'text': '2 groups of 3', 'size': 32, 'color': '#64748B'},
                {'type': 'text', 'x': 540, 'y': 850, 'text': '= 3', 'size': 56, 'color': '#10B981', 'bold': True},
            ]
        })
        steps.append({
            'label': '8 ÷ 4 = 2',
            'narration': 'Eight balls, divide into four equal parts. Each part gets two balls. Eight divided by four equals two!',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': '8 ÷ 4 = 2', 'size': 56, 'color': '#2563EB', 'bold': True},
                {'type': 'dots_group', 'x': 150, 'y': 400, 'count': 2, 'color': '#2563EB', 'spacing': 70},
                {'type': 'dots_group', 'x': 350, 'y': 400, 'count': 2, 'color': '#10B981', 'spacing': 70},
                {'type': 'dots_group', 'x': 550, 'y': 400, 'count': 2, 'color': '#F59E0B', 'spacing': 70},
                {'type': 'dots_group', 'x': 750, 'y': 400, 'count': 2, 'color': '#7C3AED', 'spacing': 70},
                {'type': 'text', 'x': 540, 'y': 700, 'text': '4 groups of 2', 'size': 32, 'color': '#64748B'},
                {'type': 'text', 'x': 540, 'y': 850, 'text': '= 2', 'size': 56, 'color': '#10B981', 'bold': True},
            ]
        })
        steps.append({
            'label': 'Try: 9 ÷ 3',
            'narration': 'Now you tell! Divide nine balls into three equal parts. How many in each part?',
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': 'Your Turn!', 'size': 48, 'color': '#7C3AED', 'bold': True},
                {'type': 'text', 'x': 540, 'y': 300, 'text': '9 ÷ 3 = ?', 'size': 56, 'color': '#2563EB', 'bold': True},
                {'type': 'dots_group', 'x': 250, 'y': 500, 'count': 9, 'color': '#2563EB', 'spacing': 60},
                {'type': 'text', 'x': 540, 'y': 800, 'text': 'Make 3 equal groups!', 'size': 32, 'color': '#64748B'},
                {'type': 'star', 'cx': 540, 'cy': 1000, 'size': 60, 'fill': '#F59E0B', 'outline': '#D97706'},
            ]
        })

    elif any(kw in topic_lower for kw in ['fraction', 'fractions', 'half', 'quarter', 'part', 'hissa', 'ansh']):
        # Fraction visual
        fractions = [(1, 2), (1, 4), (3, 4), (2, 3)]
        fraction_names = {(1,2): 'one half', (1,4): 'one quarter', (3,4): 'three quarters', (2,3): 'two thirds'}
        for num, den in fractions:
            steps.append({
                'label': f'Fraction {num}/{den}',
                'narration': f'{num} divided by {den}, that is {fraction_names.get((num, den), "")}. Divide the whole into {den} equal parts, take {num} of them. This is {num}/{den}.',
                'elements': [
                    {'type': 'text', 'x': 540, 'y': 150, 'text': f'Fraction: {num}/{den}', 'size': 42, 'color': '#7C3AED', 'bold': True},
                    {'type': 'fraction_bar', 'x': 140, 'y': 400, 'w': 800, 'h': 80, 'num': num, 'den': den, 'color': '#7C3AED'},
                    {'type': 'text', 'x': 540, 'y': 600, 'text': f'{num} out of {den} parts', 'size': 36, 'color': '#64748B'},
                ]
            })

    elif any(kw in topic_lower for kw in ['shape', 'circle', 'triangle', 'rectangle', 'square', 'geometry']):
        # Geometry visual
        shapes = [
            ('circle', 200, 400, 80, '#DBEAFE', '#2563EB'),
            ('rect', 500, 350, 80, '#D1FAE5', '#10B981'),
            ('triangle', 800, 400, 80, '#EDE9FE', '#7C3AED'),
        ]
        shape_names = {'circle': 'Circle', 'rect': 'Rectangle', 'triangle': 'Triangle'}
        for i, (shape, cx, cy, size, fill, outline) in enumerate(shapes):
            elements = [
                {'type': 'text', 'x': 540, 'y': 150, 'text': f'Geometry: {shape.title()}', 'size': 42, 'color': '#2563EB', 'bold': True},
            ]
            if shape == 'circle':
                elements.append({'type': 'circle', 'cx': cx, 'cy': cy, 'r': size, 'fill': fill, 'outline': outline})
            elif shape == 'rect':
                elements.append({'type': 'rect', 'x': cx - size, 'y': cy - int(size*0.7), 'w': size*2, 'h': int(size*1.4), 'fill': fill, 'outline': outline})
            else:
                elements.append({'type': 'triangle', 'points': [[cx, cy-size], [cx+size, cy+size], [cx-size, cy+size]], 'fill': fill, 'outline': outline})
            elements.append({'type': 'text', 'x': cx, 'y': cy + size + 40, 'text': shape.title(), 'size': 32, 'color': outline, 'bold': True})
            steps.append({'label': f'Shape: {shape.title()}', 'narration': f'This is a {shape_names.get(shape, shape)}. Look at it carefully, it has its own characteristics. Identify the {shape.title()}.', 'elements': elements})

    elif any(kw in topic_lower for kw in ['time', 'clock', 'hour', 'minute', 'ghanta']):
        # Time/clock visual
        times = [(3, 0), (6, 30), (9, 15), (12, 45)]
        for h, m in times:
            steps.append({
                'label': f'Time: {h:02d}:{m:02d}',
                'narration': f'Look at the clock. The big hand is on {m} and the small hand is on {h}. It is {h} hours and {m} minutes.',
                'elements': [
                    {'type': 'text', 'x': 540, 'y': 150, 'text': f'Time: {h:02d}:{m:02d}', 'size': 42, 'color': '#2563EB', 'bold': True},
                    {'type': 'clock_face', 'cx': 540, 'cy': 600, 'r': 200, 'hour': h, 'minute': m},
                    {'type': 'text', 'x': 540, 'y': 900, 'text': f'{h} hour{"s" if h != 1 else ""} and {m} minutes', 'size': 32, 'color': '#64748B'},
                ]
            })

    elif any(kw in topic_lower for kw in ['data', 'bar', 'chart', 'graph', 'pictograph']):
        # Data handling visual
        data_sets = [
            [{'label': 'Apple', 'value': 5, 'color': '#EF4444'}, {'label': 'Banana', 'value': 8, 'color': '#F59E0B'}, {'label': 'Orange', 'value': 3, 'color': '#10B981'}],
        ]
        for data in data_sets:
            names = ', '.join(d['label'] for d in data)
            steps.append({
                'label': 'Bar Chart',
                'narration': f'This is a bar chart. Look at the data for {names}. Tell which fruit is most liked by looking at the tallest bar?',
                'elements': [
                    {'type': 'text', 'x': 540, 'y': 150, 'text': 'Data Handling - Bar Chart', 'size': 38, 'color': '#2563EB', 'bold': True},
                    {'type': 'bar_chart', 'x': 140, 'y': 350, 'w': 800, 'h': 500, 'data': data},
                    {'type': 'text', 'x': 540, 'y': 950, 'text': 'Which fruit is most popular?', 'size': 32, 'color': '#64748B'},
                ]
            })

    elif any(kw in topic_lower for kw in ['measurement', 'length', 'height', 'weight', 'ruler', 'scale']):
        # Measurement visual
        measurements = [(10, 'cm'), (25, 'cm'), (15, 'cm')]
        for val, unit in measurements:
            steps.append({
                'label': f'Measurement: {val} {unit}',
                'narration': f'Measure it. This is {val} {unit} long. Look at the ruler, how many {unit} from zero to {val}?',
                'elements': [
                    {'type': 'text', 'x': 540, 'y': 150, 'text': f'Measurement: {val} {unit}', 'size': 42, 'color': '#2563EB', 'bold': True},
                    {'type': 'ruler', 'x': 140, 'y': 500, 'w': 800, 'min': 0, 'max': val + 5, 'unit': unit},
                    {'type': 'arrow', 'x1': 140, 'y1': 560, 'x2': 140 + int(800 * val / (val + 5)), 'y2': 560, 'color': '#EF4444', 'width': 3},
                    {'type': 'text', 'x': 540, 'y': 700, 'text': f'{val} {unit}', 'size': 56, 'color': '#EF4444', 'bold': True},
                ]
            })

    else:
        # Default: topic with visual elements (teacher-style) — RICH narration
        sub_explanations = {
            'skip counting': 'Count by twos, threes, fives — this is Skip Counting!',
            'counting': 'Learn to count one by one',
            'group counting': 'Divide counting into groups, like twos and threes',
            'dozen': 'A dozen means twelve — count in groups like this',
            'pair': 'A pair — count by twos',
            'array': 'An array — arrange in rows and columns to count',
            'row': 'A row — count in a line',
            'column': 'A column — count from top to bottom',
            'pattern': 'Look at the pattern — which number comes next? Recognize the pattern!',
            'place value': 'Every digit has a place — ones, tens, hundreds',
            'even': 'A number divisible by two is Even',
            'odd': 'A number not divisible by two is Odd',
            'prime': 'A number divisible only by 1 and itself is Prime',
            'composite': 'A number that has more factors is Composite',
            'factor': 'Factors are numbers that divide a number exactly',
            'multiple': 'Multiples are numbers that appear in a number\'s table',
            'symmetry': 'Symmetry — both sides look the same',
            'angle': 'Angle — the corner between two lines',
            'perimeter': 'Perimeter — the distance around a shape',
            'area': 'Area — the space inside a shape',
            'volume': 'Volume — how much can fit inside',
            'decimal': 'Decimal — the digits after the point',
            'percentage': 'Percentage — how many out of a hundred',
            'ratio': 'Ratio — comparing two things',
            'profit': 'Profit — sell for more than you bought',
            'loss': 'Loss — sell for less than you bought',
            'interest': 'Interest — money earns more money',
            'equation': 'Equation — both sides are equal',
            'polynomial': 'Polynomial — terms with powers of x',
            'linear': 'Linear — like a straight line',
            'quadratic': 'Quadratic — has x squared',
        }

        # Intro — randomize greeting so every video sounds different
        intro_variants = [
            f'Hello kids! Today we will learn "{topic_text}". This is an important topic for Class {class_num}. It is very easy, just pay attention!',
            f'Hey kids! Are you ready? Today\'s topic is "{topic_text}". It is very fun, let us get started!',
            f'Kids, today we will learn a new topic — "{topic_text}". It is very important for Class {class_num}. Pay attention!',
            f'Today\'s lesson is "{topic_text}"! It is very easy, just follow along. Let us begin!',
            f'Get ready kids! Today we will learn "{topic_text}". It is very interesting!',
        ]
        # Randomize color palettes for visual variety
        palette_sets = [
            ['#2563EB', '#7C3AED', '#10B981', '#F59E0B', '#EF4444'],  # Default
            ['#E11D48', '#7C3AED', '#0891B2', '#CA8A04', '#059669'],  # Warm
            ['#0369A1', '#4338CA', '#047857', '#D97706', '#BE123C'],  # Cool
            ['#6D28D9', '#B91C1C', '#0E7490', '#A16207', '#15803D'],  # Bold
        ]
        colors = random.choice(palette_sets)

        steps.append({
            'label': f'Introduction: {topic_text[:25]}',
            'narration': random.choice(intro_variants),
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': topic_text[:50], 'size': 42, 'color': colors[0], 'bold': True},
                {'type': 'text', 'x': 540, 'y': 300, 'text': f'Class {class_num}', 'size': 32, 'color': colors[2], 'bold': True},
                {'type': 'text', 'x': 540, 'y': 500, 'text': random.choice(["Let's Learn!", 'Get Started!', 'Ready?', 'Watch and Learn!', 'Let\'s Go!']), 'size': 48, 'color': colors[3], 'bold': True},
                {'type': 'star', 'cx': 540, 'cy': 750, 'size': 80, 'fill': colors[3], 'outline': colors[0]},
            ]
        })

        # Subtopic steps with rich visual elements — randomize visual order
        if subtopics:
            visual_types = ['dots_group', 'number_line', 'fraction_bar', 'grid', 'circle', 'rect', 'bar_chart', 'ruler']
            random.shuffle(visual_types)
            for i, sub in enumerate(subtopics[:4]):
                sub_lower = sub.lower()
                # Find matching explanation (longest keyword match wins)
                explanation = None
                best_len = 0
                for keyword, expl in sub_explanations.items():
                    if keyword in sub_lower and len(keyword) > best_len:
                        explanation = expl
                        best_len = len(keyword)

                narration = explanation if explanation else f'Now let us understand "{sub}". Watch carefully and learn!'
                vis_type = visual_types[i % len(visual_types)]

                # Randomize text color per step
                step_color = colors[i % len(colors)]
                elements = [
                    {'type': 'text', 'x': 540, 'y': 150, 'text': sub[:50], 'size': 42, 'color': step_color, 'bold': True},
                ]

                # Add matching visual with randomized colors
                fill_colors = ['#DBEAFE', '#D1FAE5', '#FEF3C7', '#EDE9FE', '#FCE7F3', '#CCFBF1']
                fill = random.choice(fill_colors)

                if vis_type == 'dots_group':
                    count = random.randint(4, 10)
                    elements.append({'type': 'dots_group', 'x': 300, 'y': 450, 'count': count, 'color': step_color, 'spacing': 80})
                    elements.append({'type': 'text', 'x': 540, 'y': 750, 'text': f'{count} items', 'size': 36, 'color': '#64748B'})
                elif vis_type == 'number_line':
                    start = random.randint(0, 5)
                    elements.append({'type': 'number_line', 'x': 100, 'y': 500, 'min': 0, 'max': 20, 'highlight': list(range(start, start + random.randint(5, 10)))})
                elif vis_type == 'fraction_bar':
                    den = random.choice([2, 3, 4, 5, 6])
                    num = random.randint(1, den - 1)
                    elements.append({'type': 'fraction_bar', 'x': 140, 'y': 500, 'w': 800, 'h': 80, 'num': num, 'den': den, 'color': step_color})
                elif vis_type == 'grid':
                    rows = random.randint(2, 5)
                    cols = random.randint(2, 5)
                    elements.append({'type': 'grid', 'x': 200, 'y': 400, 'w': 600, 'h': 400, 'rows': rows, 'cols': cols})
                elif vis_type == 'circle':
                    elements.append({'type': 'circle', 'cx': 540, 'cy': 650, 'r': random.randint(80, 150), 'fill': fill, 'outline': step_color})
                elif vis_type == 'rect':
                    w = random.randint(300, 500)
                    h = random.randint(200, 350)
                    elements.append({'type': 'rect', 'x': 540 - w//2, 'y': 450, 'w': w, 'h': h, 'fill': fill, 'outline': step_color})
                elif vis_type == 'bar_chart':
                    data = [
                        {'label': 'A', 'value': random.randint(2, 8), 'color': colors[0]},
                        {'label': 'B', 'value': random.randint(2, 8), 'color': colors[1]},
                        {'label': 'C', 'value': random.randint(2, 8), 'color': colors[2]},
                    ]
                    elements.append({'type': 'bar_chart', 'x': 140, 'y': 400, 'w': 800, 'h': 500, 'data': data})
                elif vis_type == 'ruler':
                    elements.append({'type': 'ruler', 'x': 140, 'y': 500, 'w': 800, 'min': 0, 'max': 30, 'unit': 'cm'})

                steps.append({
                    'label': sub[:30],
                    'narration': narration,
                    'elements': elements,
                })

        # Practice step — random outro
        outro_variants = [
            f'Very good kids! You must have understood "{topic_text}". Make sure to practice!',
            f'Wow kids! You learned "{topic_text}" very well. Now practice on your own!',
            f'Well done! "{topic_text}" is complete. If you practice daily, you will become a master!',
            f'Great job! "{topic_text}" is done. Do not forget your homework!',
        ]
        practice_labels = ['Practice Time!', 'Keep Going!', 'Well Done!', 'Excellent!', 'Great Job!']
        steps.append({
            'label': 'Practice',
            'narration': random.choice(outro_variants),
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': random.choice(practice_labels), 'size': 48, 'color': colors[2], 'bold': True},
                {'type': 'text', 'x': 540, 'y': 400, 'text': topic_text[:50], 'size': 36, 'color': '#64748B'},
                {'type': 'star', 'cx': 540, 'cy': 700, 'size': 80, 'fill': colors[3], 'outline': colors[0]},
            ]
        })

    if not steps:
        return None

    # Center all elements within visual area (y=280 to y=1700)
    for step in steps:
        step['elements'] = _center_step_elements(step.get('elements', []))

    return {'title': title, 'steps': steps}
