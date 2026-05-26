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
        {{"type": "grid", "x": 100, "y": 300, "w": 800, "h": 600, "rows": 5, "cols": 5}}
      ]
    }}
  ]
}}

Rules:
- Canvas is 1080x1920 (portrait). Keep all elements within bounds (x: 50-1030, y: 50-1870).
- Create 4-6 steps that TEACH the topic progressively (easy → concept → example → practice).
- Each step should build on the previous one.
- Use visual elements to EXPLAIN, not just display text.
- For counting topics: use dots_group to show objects being counted.
- For addition/subtraction: show groups merging/separating with dots_group, then the equation.
- For fractions: use fraction_bar to visualize parts.
- For geometry: use circle, rect, line to draw shapes.
- For number concepts: use number_line.
- Keep it simple and clear for young learners (Class 1-5) or detailed for older (Class 6-10).
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
        print(f"  LLM returned invalid JSON: {e}")
        return None
    except Exception as e:
        print(f"  LLM API error: {e}")
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

    if scene:
        # Render LLM-generated scene
        frames = render_scene(scene, frames_dir, frames_per_step=5)
        print(f"  Generated {len(frames)} LLM visual frames")
        return frames
    else:
        print("  LLM generation failed, using fallback")
        return None
