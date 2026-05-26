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
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
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


def call_llm(topic, subtopics, class_num):
    """Call OpenGateway API to generate visual scene description."""
    try:
        from openai import OpenAI
    except ImportError:
        print("  openai library not installed, skipping LLM visual generation")
        return None

    api_key = os.environ.get('OPENAI_API_KEY', '')
    base_url = os.environ.get('OPENAI_BASE_URL', 'https://opengateway.gitlawb.com/v1')
    model = os.environ.get('OPENAI_MODEL', 'mimo-v2.5-pro')

    if not api_key:
        print("  No OPENAI_API_KEY found, skipping LLM visual generation")
        return None

    client = OpenAI(api_key=api_key, base_url=base_url)

    prompt = f"""You are a math teacher creating visual frames for a Class {class_num} NCERT math video.

Topic: {topic}
Subtopics: {', '.join(subtopics)}

Generate a JSON scene description for PIL to render. The video should TEACH this topic step by step.

Return ONLY valid JSON (no markdown, no explanation) with this exact format:
{{
  "title": "short title for the lesson",
  "steps": [
    {{
      "label": "Step 1 title",
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
- Canvas is 1080x1920 (portrait). Keep all elements within bounds (x: 50-1030, y: 50-1870).
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
- All text should be in English (the audio will be in Hindi).
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a math visualization expert. Return only valid JSON, no markdown code blocks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )

        content = response.choices[0].message.content.strip()
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
            print(f"  LLM generated {len(scene['steps'])} visual steps")
            return scene
        else:
            print("  LLM response missing 'steps', falling back")
            return None

    except json.JSONDecodeError as e:
        print(f"  LLM returned invalid JSON, retrying with simpler prompt...")
        return _retry_llm_simple(client, model, topic, class_num)
    except Exception as e:
        print(f"  LLM API error: {e}")
        return None


def _retry_llm_simple(client, model, topic, class_num):
    """Retry LLM with a simpler prompt after JSON parse failure."""
    simple_prompt = f"""Generate a JSON scene for teaching "{topic}" to Class {class_num} students.
Return ONLY valid JSON, no markdown, no explanation.
Format: {{"title":"...","steps":[{{"label":"...","elements":[{{"type":"text","x":540,"y":200,"text":"...","size":48,"color":"#2563EB"}}]}}]}}
Use 4 steps with elements: text, circle, rect, dots_group, fraction_bar, number_line.
Canvas: 1080x1920. Bounds: x 50-1030, y 50-1870."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": simple_prompt}
            ],
            temperature=0.5,
            max_tokens=2000
        )
        content = response.choices[0].message.content.strip()
        if content.startswith('```'):
            content = content.split('\n', 1)[1] if '\n' in content else content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        if content.startswith('json'):
            content = content[4:].strip()

        scene = json.loads(content)
        if 'steps' in scene and len(scene['steps']) > 0:
            print(f"  Retry generated {len(scene['steps'])} steps")
            return scene
        return None
    except Exception as e2:
        print(f"  Retry also failed: {e2}")
        return None


# ============ ELEMENT RENDERERS ============

def draw_element_text(draw, el):
    """Draw text element."""
    size = el.get('size', 32)
    bold = el.get('bold', False)
    font = get_font(size, bold)
    color = hex_to_rgb(el.get('color', COLORS['text']))
    x, y = el.get('x', 100), el.get('y', 100)
    text = el.get('text', '')

    # Center text if x is near middle
    if 400 < x < 700:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = x - tw // 2

    draw.text((x, y), text, fill=color, font=font)


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
    r = el.get('r', 25)
    label_below = el.get('label', True)

    cols = min(5, count)
    for i in range(count):
        row = i // cols
        col = i % cols
        cx = x + col * spacing
        cy = y + row * spacing
        draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=color, outline=outline, width=2)
        if label_below:
            font = get_font(20, bold=True)
            label = str(i + 1)
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((cx - tw // 2, cy + r + 8), label, fill=hex_to_rgb(COLORS['text']), font=font)


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


def render_scene(scene, frames_dir="temp_frames", frames_per_step=5):
    """Render a scene (from LLM) into frame images."""
    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    steps = scene.get('steps', [])
    title = scene.get('title', 'Math Lesson')
    total_frames = len(steps) * frames_per_step
    frame_paths = []

    for frame_idx in range(total_frames):
        step_idx = min(frame_idx // frames_per_step, len(steps) - 1)
        step = steps[step_idx]

        # Create canvas
        img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
        draw = ImageDraw.Draw(img)

        # Draw gradient background
        top = hex_to_rgb('#F0F4FF')
        bot = hex_to_rgb('#FFFFFF')
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(top[0] + (bot[0] - top[0]) * ratio)
            g = int(top[1] + (bot[1] - top[1]) * ratio)
            b = int(top[2] + (bot[2] - top[2]) * ratio)
            draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

        # Draw header bar
        draw.rounded_rectangle([(30, 30), (WIDTH - 30, 130)], radius=20, fill=hex_to_rgb('#1E293B'))
        header_font = get_font(28, bold=True)
        draw.text((60, 60), title, fill=hex_to_rgb('#FFFFFF'), font=header_font)

        # Draw step label
        step_label = step.get('label', f'Step {step_idx + 1}')
        label_font = get_font(32, bold=True)
        draw.rounded_rectangle([(30, 150), (WIDTH - 30, 210)], radius=15, fill=hex_to_rgb('#EFF6FF'))
        draw.text((60, 160), f"Step {step_idx + 1}: {step_label}", fill=hex_to_rgb(COLORS['primary']), font=label_font)

        # Draw step indicator dots
        dot_y = 240
        dot_spacing = 60
        start_x = (WIDTH - (len(steps) - 1) * dot_spacing) // 2
        for i in range(len(steps)):
            dx = start_x + i * dot_spacing
            if i < step_idx:
                draw.ellipse([(dx-10, dot_y-10), (dx+10, dot_y+10)], fill=hex_to_rgb(COLORS['success']))
            elif i == step_idx:
                draw.ellipse([(dx-13, dot_y-13), (dx+13, dot_y+13)], fill=hex_to_rgb(COLORS['primary']))
            else:
                draw.ellipse([(dx-10, dot_y-10), (dx+10, dot_y+10)], fill=hex_to_rgb(COLORS['grid']))

        # Draw elements for current step
        elements = step.get('elements', [])
        for el in elements:
            el_type = el.get('type', 'text')
            renderer = ELEMENT_RENDERERS.get(el_type)
            if renderer:
                try:
                    renderer(draw, el)
                except Exception as e:
                    print(f"  Warning: failed to render {el_type}: {e}")

        # Progress bar at bottom
        progress = (step_idx + 1) / len(steps)
        bar_w = int((WIDTH - 100) * progress)
        draw.rounded_rectangle([(50, HEIGHT - 80), (50 + bar_w, HEIGHT - 50)], radius=10, fill=hex_to_rgb(COLORS['primary']))
        draw.rounded_rectangle([(50, HEIGHT - 80), (WIDTH - 50, HEIGHT - 50)], radius=10, outline=hex_to_rgb(COLORS['grid']), width=2)

        # Save frame
        frame_path = frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
        img.save(frame_path)
        frame_paths.append(str(frame_path))

    return frame_paths


def generate_visual(topic, frames_dir="temp_frames"):
    """Main entry: generate visual frames for a topic using LLM + PIL."""
    topic_text = topic.get('topic', '')
    chapter = topic.get('chapter', '')
    class_num = topic.get('class', 6)
    subtopics = topic.get('subtopics', [])

    print(f"  Generating LLM visual for: {topic_text}")

    # Call LLM to get scene description
    scene = call_llm(topic_text, subtopics, class_num)

    if not scene:
        print("  LLM failed, using smart fallback...")
        scene = _generate_fallback_scene(topic_text, subtopics, class_num)

    if scene:
        # Render scene
        frames = render_scene(scene, frames_dir, frames_per_step=5)
        print(f"  Generated {len(frames)} visual frames")
        return frames

    return None


def _generate_fallback_scene(topic_text, subtopics, class_num):
    """Generate a scene without LLM by analyzing topic keywords."""
    topic_lower = topic_text.lower()
    title = topic_text[:60]
    steps = []

    # Detect topic type and generate appropriate steps
    if any(kw in topic_lower for kw in ['add', 'plus', 'sum', 'addition', 'jod']):
        # Addition visual
        for i in range(4):
            a, b = 3 + i, 2 + i
            steps.append({
                'label': f'Addition: {a} + {b}',
                'elements': [
                    {'type': 'text', 'x': 540, 'y': 150, 'text': f'Addition: {a} + {b}', 'size': 42, 'color': '#2563EB', 'bold': True},
                    {'type': 'dots_group', 'x': 200, 'y': 400, 'count': a, 'color': '#2563EB', 'spacing': 70},
                    {'type': 'text', 'x': 200 + a * 70 + 30, 'y': 420, 'text': '+', 'size': 48, 'color': '#F59E0B', 'bold': True},
                    {'type': 'dots_group', 'x': 200 + a * 70 + 80, 'y': 400, 'count': b, 'color': '#7C3AED', 'spacing': 70},
                    {'type': 'text', 'x': 540, 'y': 700, 'text': f'{a} + {b} = {a+b}', 'size': 56, 'color': '#10B981', 'bold': True},
                ]
            })

    elif any(kw in topic_lower for kw in ['subtract', 'minus', 'difference', 'ghata']):
        # Subtraction visual
        for i in range(4):
            a, b = 8 - i, 3 + i
            steps.append({
                'label': f'Subtraction: {a} - {b}',
                'elements': [
                    {'type': 'text', 'x': 540, 'y': 150, 'text': f'Subtraction: {a} - {b}', 'size': 42, 'color': '#EF4444', 'bold': True},
                    {'type': 'dots_group', 'x': 200, 'y': 400, 'count': a, 'color': '#2563EB', 'spacing': 70},
                    {'type': 'text', 'x': 540, 'y': 650, 'text': f'Remove {b}', 'size': 36, 'color': '#EF4444'},
                    {'type': 'dots_group', 'x': 200, 'y': 800, 'count': max(0, a - b), 'color': '#10B981', 'spacing': 70},
                    {'type': 'text', 'x': 540, 'y': 1050, 'text': f'{a} - {b} = {a-b}', 'size': 56, 'color': '#10B981', 'bold': True},
                ]
            })

    elif any(kw in topic_lower for kw in ['multiply', 'times', 'product', 'guna']):
        # Multiplication visual
        for i in range(4):
            rows, cols = 2 + i, 3 + i
            steps.append({
                'label': f'Multiplication: {rows} x {cols}',
                'elements': [
                    {'type': 'text', 'x': 540, 'y': 150, 'text': f'{rows} x {cols} = {rows*cols}', 'size': 42, 'color': '#7C3AED', 'bold': True},
                    {'type': 'grid', 'x': 200, 'y': 350, 'w': 600, 'h': 400, 'rows': rows, 'cols': cols},
                    {'type': 'text', 'x': 540, 'y': 850, 'text': f'{rows} groups of {cols}', 'size': 32, 'color': '#64748B'},
                    {'type': 'text', 'x': 540, 'y': 1000, 'text': f'= {rows*cols}', 'size': 56, 'color': '#10B981', 'bold': True},
                ]
            })

    elif any(kw in topic_lower for kw in ['fraction', 'half', 'quarter', 'part']):
        # Fraction visual
        fractions = [(1, 2), (1, 4), (3, 4), (2, 3)]
        for num, den in fractions:
            steps.append({
                'label': f'Fraction {num}/{den}',
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
            steps.append({'label': f'Shape: {shape.title()}', 'elements': elements})

    elif any(kw in topic_lower for kw in ['time', 'clock', 'hour', 'minute', 'ghanta']):
        # Time/clock visual
        times = [(3, 0), (6, 30), (9, 15), (12, 45)]
        for h, m in times:
            steps.append({
                'label': f'Time: {h:02d}:{m:02d}',
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
            steps.append({
                'label': 'Bar Chart',
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
                'elements': [
                    {'type': 'text', 'x': 540, 'y': 150, 'text': f'Measurement: {val} {unit}', 'size': 42, 'color': '#2563EB', 'bold': True},
                    {'type': 'ruler', 'x': 140, 'y': 500, 'w': 800, 'min': 0, 'max': val + 5, 'unit': unit},
                    {'type': 'arrow', 'x1': 140, 'y1': 560, 'x2': 140 + int(800 * val / (val + 5)), 'y2': 560, 'color': '#EF4444', 'width': 3},
                    {'type': 'text', 'x': 540, 'y': 700, 'text': f'{val} {unit}', 'size': 56, 'color': '#EF4444', 'bold': True},
                ]
            })

    else:
        # Default: number line with topic text
        steps.append({
            'label': topic_text[:30],
            'elements': [
                {'type': 'text', 'x': 540, 'y': 150, 'text': topic_text[:50], 'size': 36, 'color': '#2563EB', 'bold': True},
                {'type': 'number_line', 'x': 100, 'y': 500, 'min': 0, 'max': 20, 'highlight': list(range(1, 11))},
            ]
        })
        if subtopics:
            for i, sub in enumerate(subtopics[:3]):
                steps.append({
                    'label': sub[:30],
                    'elements': [
                        {'type': 'text', 'x': 540, 'y': 150, 'text': sub[:50], 'size': 36, 'color': '#7C3AED', 'bold': True},
                        {'type': 'text', 'x': 540, 'y': 400, 'text': f'Part {i+1}', 'size': 32, 'color': '#64748B'},
                    ]
                })

    if not steps:
        return None

    return {'title': title, 'steps': steps}
