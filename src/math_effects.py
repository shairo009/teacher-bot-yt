"""
2D Math Visual Effects Engine for Teacher Bot
Generates animated frames with math visualizations:
- Step-by-step equation solving
- Geometric shapes (circles, triangles, rectangles, polygons)
- Number lines with markers
- Fraction bars
- Coordinate grid plotting
- Animated drawing effects (stroke-by-stroke)
"""

import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Canvas size (vertical/portrait for YouTube Shorts)
WIDTH = 1080
HEIGHT = 1920

# Color palette
COLORS = {
    'bg': '#FFFFFF',
    'bg_gradient_top': '#F0F4FF',
    'bg_gradient_bot': '#FFFFFF',
    'primary': '#2563EB',       # Blue
    'primary_light': '#93C5FD',
    'secondary': '#7C3AED',     # Purple
    'accent': '#F59E0B',        # Amber
    'accent2': '#10B981',       # Green
    'danger': '#EF4444',        # Red
    'text': '#1E293B',
    'text_light': '#64748B',
    'grid': '#E2E8F0',
    'grid_bold': '#CBD5E1',
    'white': '#FFFFFF',
    'shadow': '#F1F5F9',
}

# Shape colors for visual variety
SHAPE_FILLS = ['#DBEAFE', '#EDE9FE', '#FEF3C7', '#D1FAE5', '#FEE2E2', '#E0E7FF']
SHAPE_OUTLINES = ['#2563EB', '#7C3AED', '#F59E0B', '#10B981', '#EF4444', '#6366F1']


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_font(size, bold=False):
    """Get a font, trying common paths. Hindi font first for Devanagari support."""
    font_paths = [
        'assets/fonts/hindi_font.ttf',  # Hindi Devanagari font (project-local)
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
        '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/TTF/DejaVuSans.ttf',
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    # Fallback: try default
    try:
        return ImageFont.load_default(size)
    except:
        return ImageFont.load_default()


def draw_gradient_bg(draw, img, top_color='#F0F4FF', bot_color='#FFFFFF'):
    """Draw a vertical gradient background."""
    top = hex_to_rgb(top_color)
    bot = hex_to_rgb(bot_color)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(top[0] + (bot[0] - top[0]) * ratio)
        g = int(top[1] + (bot[1] - top[1]) * ratio)
        b = int(top[2] + (bot[2] - top[2]) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))


def draw_header(draw, class_label, chapter_label, topic_label=""):
    """Draw the header bar with class, chapter, and topic info."""
    # Header background
    draw.rounded_rectangle([(30, 30), (WIDTH - 30, 130)], radius=20, fill=hex_to_rgb('#1E293B'))

    # Class badge
    font = get_font(28, bold=True)
    draw.rounded_rectangle([(50, 50), (200, 110)], radius=15, fill=hex_to_rgb('#2563EB'))
    bbox = draw.textbbox((0, 0), class_label, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((125 - tw // 2, 65), class_label, fill=hex_to_rgb('#FFFFFF'), font=font)

    # Chapter label
    font_sm = get_font(24)
    draw.text((220, 70), chapter_label, fill=hex_to_rgb('#CBD5E1'), font=font_sm)

    # Topic label (right side)
    if topic_label:
        font_topic = get_font(22)
        bbox = draw.textbbox((0, 0), topic_label, font=font_topic)
        tw = bbox[2] - bbox[0]
        draw.text((WIDTH - 60 - tw, 75), topic_label, fill=hex_to_rgb('#94A3B8'), font=font_topic)


def draw_grid(draw, x0, y0, x1, y1, rows, cols, color='#E2E8F0', bold_color='#CBD5E1'):
    """Draw a grid within the given rectangle."""
    c = hex_to_rgb(color)
    bc = hex_to_rgb(bold_color)
    # Vertical lines
    for i in range(cols + 1):
        x = x0 + i * (x1 - x0) // cols
        line_color = bc if i % 5 == 0 else c
        draw.line([(x, y0), (x, y1)], fill=line_color, width=1)
    # Horizontal lines
    for j in range(rows + 1):
        y = y0 + j * (y1 - y0) // rows
        line_color = bc if j % 5 == 0 else c
        draw.line([(x0, y), (x1, y)], fill=line_color, width=1)


def draw_coordinate_axes(draw, cx, cy, length=400, label_x='x', label_y='y'):
    """Draw coordinate axes centered at (cx, cy)."""
    color = hex_to_rgb(COLORS['text'])
    arrow_color = hex_to_rgb(COLORS['primary'])
    font = get_font(24, bold=True)

    # X axis
    draw.line([(cx - length, cy), (cx + length, cy)], fill=color, width=3)
    # X arrow
    draw.polygon([(cx + length, cy), (cx + length - 15, cy - 8), (cx + length - 15, cy + 8)], fill=arrow_color)
    draw.text((cx + length + 10, cy - 15), label_x, fill=arrow_color, font=font)

    # Y axis
    draw.line([(cx, cy - length), (cx, cy + length)], fill=color, width=3)
    # Y arrow
    draw.polygon([(cx, cy - length), (cx - 8, cy - length + 15), (cx + 8, cy - length + 15)], fill=arrow_color)
    draw.text((cx + 10, cy - length - 30), label_y, fill=arrow_color, font=font)

    # Origin label
    draw.text((cx - 25, cy + 10), 'O', fill=hex_to_rgb(COLORS['text_light']), font=get_font(20))


def draw_number_line(draw, x0, x1, y, min_val, max_val, step=1, markers=None, highlight=None):
    """Draw a number line with optional markers and highlights."""
    line_color = hex_to_rgb(COLORS['text'])
    font = get_font(22)
    font_bold = get_font(24, bold=True)

    # Main line
    draw.line([(x0, y), (x1, y)], fill=line_color, width=3)

    # Arrows
    draw.polygon([(x0, y), (x0 + 12, y - 6), (x0 + 12, y + 6)], fill=line_color)
    draw.polygon([(x1, y), (x1 - 12, y - 6), (x1 - 12, y + 6)], fill=line_color)

    # Tick marks and labels
    num_steps = int((max_val - min_val) / step)
    for i in range(num_steps + 1):
        val = min_val + i * step
        x = x0 + i * (x1 - x0) // num_steps

        # Highlight this number?
        is_highlighted = highlight and val in highlight
        tick_color = hex_to_rgb(COLORS['primary']) if is_highlighted else line_color
        tick_len = 15 if is_highlighted else 10

        draw.line([(x, y - tick_len), (x, y + tick_len)], fill=tick_color, width=2 if is_highlighted else 1)

        label = str(int(val)) if val == int(val) else str(val)
        f = font_bold if is_highlighted else font
        bbox = draw.textbbox((0, 0), label, font=f)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw // 2, y + 20), label, fill=tick_color, font=f)

        # Marker dot
        if is_highlighted:
            draw.ellipse([(x - 8, y - 8), (x + 8, y + 8)], fill=hex_to_rgb(COLORS['primary']))

    # Custom markers
    if markers:
        for val, label_text, color_hex in markers:
            x = x0 + int((val - min_val) / (max_val - min_val) * (x1 - x0))
            draw.ellipse([(x - 10, y - 10), (x + 10, y + 10)], fill=hex_to_rgb(color_hex))
            draw.text((x - 5, y - 30), label_text, fill=hex_to_rgb(color_hex), font=font_bold)


def draw_fraction_bar(draw, x, y, width, height, numerator, denominator, color='#2563EB'):
    """Draw a fraction visualization as a bar divided into parts."""
    fill = hex_to_rgb(color)
    light = hex_to_rgb(COLORS['grid'])
    outline = hex_to_rgb(COLORS['text'])

    part_w = width / denominator

    for i in range(denominator):
        px = x + i * part_w
        c = fill if i < numerator else light
        draw.rectangle([(px, y), (px + part_w - 2, y + height)], fill=c, outline=outline, width=1)

    # Label
    font = get_font(28, bold=True)
    label = f"{numerator}/{denominator}"
    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((x + width // 2 - tw // 2, y + height + 15), label, fill=fill, font=font)


def draw_shape(draw, shape, cx, cy, size, fill_color='#DBEAFE', outline_color='#2563EB', progress=1.0):
    """
    Draw a geometric shape with animation progress (0.0 to 1.0).
    progress=1.0 means fully drawn, 0.0 means nothing drawn.
    """
    fill = hex_to_rgb(fill_color)
    outline = hex_to_rgb(outline_color)

    if shape == 'circle':
        # Draw arc based on progress
        bbox = [(cx - size, cy - size), (cx + size, cy + size)]
        if progress >= 1.0:
            draw.ellipse(bbox, fill=fill, outline=outline, width=3)
        else:
            # Draw partial arc
            end_angle = int(360 * progress)
            draw.arc(bbox, 0, end_angle, fill=outline, width=3)
            if progress > 0.1:
                draw.pieslice(bbox, 0, end_angle, fill=fill, outline=outline, width=3)

    elif shape == 'rectangle':
        w, h = size, int(size * 0.7)
        if progress >= 1.0:
            draw.rectangle([(cx - w, cy - h), (cx + w, cy + h)], fill=fill, outline=outline, width=3)
        else:
            # Draw sides progressively
            perimeter = 2 * (w + h)
            drawn = perimeter * progress
            points = []
            # Top side
            if drawn > 0:
                seg = min(drawn, w)
                points.append((cx - w, cy - h))
                points.append((cx - w + seg, cy - h))
            # Right side
            if drawn > w:
                seg = min(drawn - w, h)
                points.append((cx + w, cy - h + seg))
            # Bottom side
            if drawn > w + h:
                seg = min(drawn - w - h, w)
                points.append((cx + w - seg, cy + h))
            # Left side
            if drawn > 2 * w + h:
                seg = min(drawn - 2 * w - h, h)
                points.append((cx - w, cy + h - seg))
            if len(points) >= 2:
                draw.line(points, fill=outline, width=3)

    elif shape == 'triangle':
        points_full = [
            (cx, cy - size),
            (cx + size, cy + size),
            (cx - size, cy + size),
        ]
        if progress >= 1.0:
            draw.polygon(points_full, fill=fill, outline=outline)
        else:
            # Draw edges progressively
            edges = [
                (points_full[0], points_full[1]),
                (points_full[1], points_full[2]),
                (points_full[2], points_full[0]),
            ]
            total_len = sum(math.sqrt((e[1][0]-e[0][0])**2 + (e[1][1]-e[0][1])**2) for e in edges)
            drawn = total_len * progress
            accumulated = 0
            partial_points = [edges[0][0]]
            for edge in edges:
                edge_len = math.sqrt((edge[1][0]-edge[0][0])**2 + (edge[1][1]-edge[0][1])**2)
                if accumulated + edge_len <= drawn:
                    partial_points.append(edge[1])
                    accumulated += edge_len
                else:
                    remaining = drawn - accumulated
                    ratio = remaining / edge_len
                    ix = edge[0][0] + ratio * (edge[1][0] - edge[0][0])
                    iy = edge[0][1] + ratio * (edge[1][1] - edge[0][1])
                    partial_points.append((int(ix), int(iy)))
                    break
            if len(partial_points) >= 2:
                draw.line(partial_points, fill=outline, width=3)

    elif shape == 'square':
        if progress >= 1.0:
            draw.rectangle([(cx - size, cy - size), (cx + size, cy + size)], fill=fill, outline=outline, width=3)
        else:
            # Same as rectangle but square
            draw_shape(draw, 'rectangle', cx, cy, size, fill_color, outline_color, progress)


def draw_equation_step(draw, equation_parts, current_step, x, y, font_size=48):
    """
    Draw equation with step-by-step reveal.
    equation_parts: list of (text, color_hex) tuples
    current_step: how many parts are visible
    """
    font = get_font(font_size, bold=True)
    font_sm = get_font(font_size - 8)

    cx = x
    for i, (text, color) in enumerate(equation_parts):
        if i > current_step:
            break

        c = hex_to_rgb(color)
        # Highlight current step
        if i == current_step:
            # Draw highlight background
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.rounded_rectangle([(cx - 5, y - 5), (cx + tw + 10, y + th + 10)],
                                   radius=8, fill=hex_to_rgb('#FEF3C7'), outline=hex_to_rgb('#F59E0B'))
            draw.text((cx, y), text, fill=c, font=font)
        else:
            draw.text((cx, y), text, fill=c, font=font_sm)

        bbox = draw.textbbox((0, 0), text, font=font if i == current_step else font_sm)
        cx += bbox[2] - bbox[0] + 15


def draw_step_indicator(draw, total_steps, current_step, x, y):
    """Draw step progress dots."""
    dot_r = 12
    spacing = 50
    start_x = x + (WIDTH - 2 * x - (total_steps - 1) * spacing) // 2

    for i in range(total_steps):
        dx = start_x + i * spacing
        if i < current_step:
            # Completed
            draw.ellipse([(dx - dot_r, y - dot_r), (dx + dot_r, y + dot_r)],
                         fill=hex_to_rgb(COLORS['accent2']))
        elif i == current_step:
            # Current
            draw.ellipse([(dx - dot_r - 3, y - dot_r - 3), (dx + dot_r + 3, y + dot_r + 3)],
                         fill=hex_to_rgb(COLORS['primary']))
        else:
            # Future
            draw.ellipse([(dx - dot_r, y - dot_r), (dx + dot_r, y + dot_r)],
                         fill=hex_to_rgb(COLORS['grid_bold']))


def draw_pencil_cursor(draw, x, y, size=60, angle=-30):
    """Draw an animated pencil cursor at position."""
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    # Pencil body points (relative to tip)
    tip = (x, y)
    body_w = size * 0.3
    body_h = size

    # Rotate body
    def rotate(px, py):
        rx = px * cos_a - py * sin_a
        ry = px * sin_a + py * cos_a
        return (int(x + rx), int(y + ry))

    # Pencil body
    body_pts = [
        rotate(-body_w, 0),
        rotate(body_w, 0),
        rotate(body_w, -body_h),
        rotate(-body_w, -body_h),
    ]
    draw.polygon(body_pts, fill=hex_to_rgb('#FFD700'), outline=hex_to_rgb('#D97706'))

    # Eraser
    eraser_h = body_h * 0.2
    eraser_pts = [
        rotate(-body_w, -body_h),
        rotate(body_w, -body_h),
        rotate(body_w, -body_h - eraser_h),
        rotate(-body_w, -body_h - eraser_h),
    ]
    draw.polygon(eraser_pts, fill=hex_to_rgb('#F87171'), outline=hex_to_rgb('#DC2626'))

    # Tip
    tip_h = body_h * 0.3
    tip_pts = [
        rotate(-body_w, 0),
        rotate(body_w, 0),
        rotate(0, tip_h),
    ]
    draw.polygon(tip_pts, fill=hex_to_rgb('#374151'))


class MathEffects:
    """2D Math Visual Effects generator."""

    def __init__(self, frames_dir="temp_frames"):
        self.frames_dir = Path(frames_dir)
        self.frames_dir.mkdir(parents=True, exist_ok=True)

    def generate_equation_frames(self, title, steps, class_label="Class 6", chapter="", num_frames=24):
        """
        Generate frames for step-by-step equation solving.

        steps: list of dicts with:
            - 'equation': str (the equation text)
            - 'explanation': str (what's happening)
            - 'highlight_color': str (hex color for this step)
        """
        frames = []
        total_steps = len(steps)
        frames_per_step = max(3, num_frames // total_steps)

        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
            draw = ImageDraw.Draw(img)
            draw_gradient_bg(draw, img, '#F0F4FF', '#FFFFFF')

            # Header
            draw_header(draw, class_label, chapter, title)

            # Step indicator
            current_step = min(frame_idx // frames_per_step, total_steps - 1)
            draw_step_indicator(draw, total_steps, current_step, 100, 180)

            # Draw all completed steps
            y_pos = 280
            for i in range(current_step + 1):
                step = steps[i]
                is_current = (i == current_step)

                # Step number circle
                circle_color = hex_to_rgb(step.get('highlight_color', COLORS['primary']))
                draw.ellipse([(80, y_pos), (130, y_pos + 50)], fill=circle_color)
                font_num = get_font(24, bold=True)
                draw.text((95, y_pos + 10), str(i + 1), fill=hex_to_rgb('#FFFFFF'), font=font_num)

                # Equation text
                font_eq = get_font(44, bold=True)
                eq_color = hex_to_rgb(step.get('highlight_color', COLORS['text']))
                if is_current:
                    # Animated reveal: show partial text
                    progress = (frame_idx % frames_per_step) / frames_per_step
                    full_text = step['equation']
                    visible_chars = int(len(full_text) * min(progress * 1.5, 1.0))
                    visible_text = full_text[:visible_chars]
                    draw.text((150, y_pos + 5), visible_text, fill=eq_color, font=font_eq)

                    # Cursor blink
                    if progress < 0.8:
                        bbox = draw.textbbox((0, 0), visible_text, font=font_eq)
                        cursor_x = 150 + bbox[2] - bbox[0] + 5
                        draw.line([(cursor_x, y_pos + 5), (cursor_x, y_pos + 50)],
                                  fill=eq_color, width=3)
                else:
                    draw.text((150, y_pos + 5), step['equation'], fill=eq_color, font=font_eq)

                # Explanation
                if step.get('explanation'):
                    font_exp = get_font(26)
                    exp_color = hex_to_rgb(COLORS['text_light'])
                    if is_current:
                        # Fade in explanation
                        progress = (frame_idx % frames_per_step) / frames_per_step
                        if progress > 0.4:
                            alpha_progress = min((progress - 0.4) / 0.3, 1.0)
                            draw.text((150, y_pos + 65), step['explanation'],
                                      fill=exp_color, font=font_exp)
                    else:
                        draw.text((150, y_pos + 65), step['explanation'],
                                  fill=exp_color, font=font_exp)

                y_pos += 130

            # Draw decorative pencil
            draw_pencil_cursor(draw, 900, 1700, size=50, angle=-25)

            # Bottom decorative bar
            progress_pct = (current_step + 1) / total_steps
            bar_w = int((WIDTH - 100) * progress_pct)
            draw.rounded_rectangle([(50, HEIGHT - 80), (50 + bar_w, HEIGHT - 50)],
                                   radius=10, fill=hex_to_rgb(COLORS['primary']))
            draw.rounded_rectangle([(50, HEIGHT - 80), (WIDTH - 50, HEIGHT - 50)],
                                   radius=10, outline=hex_to_rgb(COLORS['grid_bold']), width=2)

            # Save
            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames

    def generate_geometry_frames(self, title, shapes, class_label="Class 6", chapter="", num_frames=30):
        """
        Generate frames for geometry lesson with shape drawing animation.

        shapes: list of dicts with:
            - 'type': 'circle' | 'rectangle' | 'triangle' | 'square'
            - 'cx', 'cy': center position
            - 'size': radius/half-size
            - 'fill': fill color hex
            - 'outline': outline color hex
            - 'label': text label
            - 'start_frame': frame when drawing begins
            - 'end_frame': frame when drawing completes
        """
        frames = []
        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
            draw = ImageDraw.Draw(img)
            draw_gradient_bg(draw, img, '#F0F8FF', '#FFFFFF')

            draw_header(draw, class_label, chapter, title)

            # Draw grid background
            draw_grid(draw, 50, 160, WIDTH - 50, HEIGHT - 150, 20, 12)

            # Draw shapes with animation
            for shape_info in shapes:
                start = shape_info.get('start_frame', 0)
                end = shape_info.get('end_frame', num_frames)

                if frame_idx < start:
                    continue

                progress = min((frame_idx - start) / max(end - start, 1), 1.0)

                draw_shape(draw,
                           shape_info['type'],
                           shape_info['cx'],
                           shape_info['cy'],
                           shape_info['size'],
                           shape_info.get('fill', '#DBEAFE'),
                           shape_info.get('outline', '#2563EB'),
                           progress)

                # Label appears after shape is drawn
                if progress >= 1.0 and shape_info.get('label'):
                    font = get_font(28, bold=True)
                    label = shape_info['label']
                    bbox = draw.textbbox((0, 0), label, font=font)
                    tw = bbox[2] - bbox[0]
                    draw.text((shape_info['cx'] - tw // 2,
                               shape_info['cy'] + shape_info['size'] + 20),
                              label, fill=hex_to_rgb(COLORS['text']), font=font)

            # Info text at bottom
            font_info = get_font(24)
            draw.text((50, HEIGHT - 130), f"Frame {frame_idx + 1}/{num_frames}",
                      fill=hex_to_rgb(COLORS['text_light']), font=font_info)

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames

    def generate_number_line_frames(self, title, min_val, max_val, step,
                                     highlight_sequence, class_label="Class 6",
                                     chapter="", num_frames=24):
        """
        Generate frames showing numbers appearing on a number line.

        highlight_sequence: list of numbers to highlight, one per animation step
        """
        frames = []
        steps_count = len(highlight_sequence)
        frames_per_step = max(2, num_frames // steps_count)

        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
            draw = ImageDraw.Draw(img)
            draw_gradient_bg(draw, img, '#FFFBEB', '#FFFFFF')

            draw_header(draw, class_label, chapter, title)

            # Number line
            y_line = 600
            current_step = min(frame_idx // frames_per_step, steps_count - 1)
            highlighted = highlight_sequence[:current_step + 1]

            draw_number_line(draw, 100, WIDTH - 100, y_line, min_val, max_val, step,
                             highlight=highlighted)

            # Show current number prominently
            if current_step < len(highlight_sequence):
                num = highlight_sequence[current_step]
                font_big = get_font(120, bold=True)
                label = str(num)
                bbox = draw.textbbox((0, 0), label, font=font_big)
                tw = bbox[2] - bbox[0]
                # Center the big number
                draw.text((WIDTH // 2 - tw // 2, 900), label,
                          fill=hex_to_rgb(COLORS['primary']), font=font_big)

                # Subtitle
                font_sub = get_font(32)
                subtitle = f"Number: {num}"
                bbox2 = draw.textbbox((0, 0), subtitle, font=font_sub)
                tw2 = bbox2[2] - bbox2[0]
                draw.text((WIDTH // 2 - tw2 // 2, 1050), subtitle,
                          fill=hex_to_rgb(COLORS['text_light']), font=font_sub)

            # Step indicator
            draw_step_indicator(draw, steps_count, current_step, 100, 1300)

            # Progress bar
            progress_pct = (current_step + 1) / steps_count
            bar_w = int((WIDTH - 100) * progress_pct)
            draw.rounded_rectangle([(50, HEIGHT - 80), (50 + bar_w, HEIGHT - 50)],
                                   radius=10, fill=hex_to_rgb(COLORS['accent']))
            draw.rounded_rectangle([(50, HEIGHT - 80), (WIDTH - 50, HEIGHT - 50)],
                                   radius=10, outline=hex_to_rgb(COLORS['grid_bold']), width=2)

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames

    def generate_fraction_frames(self, title, fractions, class_label="Class 6",
                                  chapter="", num_frames=30):
        """
        Generate frames showing fraction visualization.

        fractions: list of dicts:
            - 'numerator': int
            - 'denominator': int
            - 'color': hex color
            - 'label': str
            - 'start_frame': int
        """
        frames = []
        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
            draw = ImageDraw.Draw(img)
            draw_gradient_bg(draw, img, '#F0FFF4', '#FFFFFF')

            draw_header(draw, class_label, chapter, title)

            y_pos = 300
            for frac in fractions:
                start = frac.get('start_frame', 0)
                if frame_idx < start:
                    y_pos += 180
                    continue

                progress = min((frame_idx - start) / 8.0, 1.0)
                visible_parts = int(frac['denominator'] * progress)

                # Label
                font = get_font(32, bold=True)
                draw.text((80, y_pos), frac.get('label', ''),
                          fill=hex_to_rgb(COLORS['text']), font=font)

                # Fraction bar
                bar_y = y_pos + 50
                bar_w = WIDTH - 200
                bar_h = 80

                draw_fraction_bar(draw, 100, bar_y, bar_w, bar_h,
                                  min(visible_parts, frac['numerator']),
                                  frac['denominator'],
                                  frac.get('color', '#2563EB'))

                y_pos += 180

            # Big fraction display
            if fractions:
                current_frac = None
                for frac in fractions:
                    start = frac.get('start_frame', 0)
                    if frame_idx >= start:
                        current_frac = frac

                if current_frac:
                    font_huge = get_font(160, bold=True)
                    frac_text = f"{current_frac['numerator']}\n—\n{current_frac['denominator']}"
                    # Draw fraction line
                    cy = 1200
                    draw.text((WIDTH // 2 - 40, cy - 100), str(current_frac['numerator']),
                              fill=hex_to_rgb(COLORS['primary']), font=font_huge)
                    draw.line([(WIDTH // 2 - 80, cy + 20), (WIDTH // 2 + 80, cy + 20)],
                              fill=hex_to_rgb(COLORS['text']), width=6)
                    draw.text((WIDTH // 2 - 40, cy + 40), str(current_frac['denominator']),
                              fill=hex_to_rgb(COLORS['secondary']), font=font_huge)

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames

    def generate_counting_frames(self, title, count_to, objects='stars',
                                  class_label="Class 1", chapter="", num_frames=30):
        """
        Generate counting animation frames for young learners.
        Shows objects appearing one by one with numbers.
        """
        frames = []
        frames_per_obj = max(2, num_frames // count_to)

        # Object drawing functions
        def draw_star(draw, cx, cy, size, fill, outline):
            points = []
            for i in range(10):
                angle = math.radians(i * 36 - 90)
                r = size if i % 2 == 0 else size * 0.4
                points.append((int(cx + r * math.cos(angle)), int(cy + r * math.sin(angle))))
            draw.polygon(points, fill=fill, outline=outline)

        def draw_heart(draw, cx, cy, size, fill):
            # Simple heart using circles and triangle
            r = size // 3
            draw.ellipse([(cx - size//2, cy - size//3), (cx, cy + size//6)], fill=fill)
            draw.ellipse([(cx, cy - size//3), (cx + size//2, cy + size//6)], fill=fill)
            draw.polygon([(cx - size//2, cy), (cx + size//2, cy), (cx, cy + size)], fill=fill)

        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb('#FFF7ED'))
            draw = ImageDraw.Draw(img)

            draw_header(draw, class_label, chapter, title)

            current_count = min(frame_idx // frames_per_obj + 1, count_to)

            # Layout objects in rows
            cols = min(5, count_to)
            obj_size = 50
            spacing_x = 160
            spacing_y = 160
            start_x = (WIDTH - cols * spacing_x) // 2 + spacing_x // 2
            start_y = 350

            for i in range(current_count):
                row = i // cols
                col = i % cols
                ox = start_x + col * spacing_x
                oy = start_y + row * spacing_y

                # Animate current object (scale in)
                if i == current_count - 1:
                    progress = (frame_idx % frames_per_obj) / frames_per_obj
                    scale = min(progress * 1.3, 1.0)
                    s = int(obj_size * scale)
                else:
                    s = obj_size

                if objects == 'stars':
                    draw_star(draw, ox, oy, s,
                              hex_to_rgb(COLORS['accent']),
                              hex_to_rgb('#D97706'))
                elif objects == 'hearts':
                    draw_heart(draw, ox, oy, s, hex_to_rgb(COLORS['danger']))
                elif objects == 'circles':
                    draw.ellipse([(ox - s, oy - s), (ox + s, oy + s)],
                                 fill=hex_to_rgb(COLORS['primary']),
                                 outline=hex_to_rgb('#1D4ED8'), width=2)

                # Number label below object
                font_num = get_font(28, bold=True)
                label = str(i + 1)
                bbox = draw.textbbox((0, 0), label, font=font_num)
                tw = bbox[2] - bbox[0]
                draw.text((ox - tw // 2, oy + s + 10), label,
                          fill=hex_to_rgb(COLORS['text']), font=font_num)

            # Big number display
            font_big = get_font(200, bold=True)
            big_num = str(current_count)
            bbox = draw.textbbox((0, 0), big_num, font=font_big)
            tw = bbox[2] - bbox[0]
            draw.text((WIDTH // 2 - tw // 2, HEIGHT - 500), big_num,
                      fill=hex_to_rgb(COLORS['primary']), font=font_big)

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames


    def generate_addition_frames(self, title, a=7, b=5,
                                  class_label="Class 3", chapter="", num_frames=30):
        """
        Generate frames showing addition visually — two groups of dots merging.
        """
        frames = []
        result = a + b
        steps = [
            (f"Step 1: Start with {a}", a, None, COLORS['primary']),
            (f"Step 2: Add {b} more", a, b, COLORS['secondary']),
            (f"Step 3: Count all together", result, None, COLORS['accent2']),
            (f"Answer: {a} + {b} = {result}", result, None, COLORS['accent']),
        ]

        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
            draw = ImageDraw.Draw(img)
            draw_gradient_bg(draw, img, '#F0F4FF', '#FFFFFF')
            draw_header(draw, class_label, chapter, title)

            step_idx = min(frame_idx * len(steps) // num_frames, len(steps) - 1)
            draw_step_indicator(draw, len(steps), step_idx, 100, 180)

            step_idx = min(frame_idx * len(steps) // num_frames, len(steps) - 1)
            step_text, count_a, count_b, color = steps[step_idx]

            # Draw first group (blue dots)
            dot_r = 18
            start_x = 140
            start_y = 650
            cols = 10
            for i in range(count_a):
                cx = start_x + (i % cols) * 80
                cy = start_y + (i // cols) * 80
                opacity = min(1.0, (frame_idx * len(steps) / num_frames - step_idx) * 3) if step_idx > 0 else 1.0
                draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
                             fill=hex_to_rgb(COLORS['primary']), outline=hex_to_rgb('#1D4ED8'))

            # Draw second group (purple dots) — appears in step 2+
            if step_idx >= 1 and count_b:
                offset_y = start_y + ((count_a - 1) // cols + 1) * 80 + 40
                # Plus sign between groups
                plus_cx = 540
                plus_cy = start_y + ((count_a - 1) // cols) * 40
                draw.text((plus_cx - 20, plus_cy), "+", fill=hex_to_rgb(COLORS['text']),
                          font=get_font(48, bold=True))

                for i in range(count_b):
                    cx = start_x + (i % cols) * 80
                    cy = offset_y + (i // cols) * 80
                    draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
                                 fill=hex_to_rgb(COLORS['secondary']), outline=hex_to_rgb('#6D28D9'))

            # Draw equals and result in step 3+
            if step_idx >= 2:
                eq_cx = 540
                eq_cy = 1200
                draw.text((eq_cx - 30, eq_cy), "=", fill=hex_to_rgb(COLORS['text']),
                          font=get_font(48, bold=True))
                # Result number big
                result_cx = 540
                result_cy = 1350
                draw.ellipse([result_cx - 60, result_cy - 60, result_cx + 60, result_cy + 60],
                             fill=hex_to_rgb(COLORS['accent2']))
                draw.text((result_cx - 20, result_cy - 25), str(result),
                          fill=hex_to_rgb('#FFFFFF'), font=get_font(48, bold=True))

            # Step text
            text_y = 1550
            draw.text((540, text_y), step_text, fill=hex_to_rgb(COLORS['text']),
                      font=get_font(32, bold=True), anchor='mm')

            # Progress bar
            progress = (frame_idx + 1) / num_frames
            bar_y = 1700
            draw.rounded_rectangle([100, bar_y, 100 + int(880 * progress), bar_y + 16],
                                    radius=8, fill=hex_to_rgb(COLORS['accent2']))

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames

    def generate_multiplication_frames(self, title, rows=3, cols=4,
                                        class_label="Class 4", chapter="", num_frames=30):
        """
        Generate frames showing multiplication as rows × columns of dots.
        """
        frames = []
        total = rows * cols

        steps = [
            (f"Step 1: Make {rows} rows", 0),
            (f"Step 2: Put {cols} dots in each row", rows),
            (f"Step 3: Count all dots", total),
            (f"Answer: {rows} × {cols} = {total}", total),
        ]

        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
            draw = ImageDraw.Draw(img)
            draw_gradient_bg(draw, img, '#F0F4FF', '#FFFFFF')
            draw_header(draw, class_label, chapter, title)

            step_idx = min(frame_idx * len(steps) // num_frames, len(steps) - 1)
            draw_step_indicator(draw, len(steps), step_idx, 100, 180)
            step_text, visible_dots = steps[step_idx]

            dot_r = 22
            start_x = 180
            start_y = 600
            row_gap = 120
            col_gap = 100

            # Draw grid lines (light)
            for r in range(rows):
                for c in range(cols):
                    cx = start_x + c * col_gap
                    cy = start_y + r * row_gap
                    draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8],
                                 fill=hex_to_rgb(COLORS['grid']))

            # Draw actual dots based on progress
            dots_shown = 0
            for r in range(rows):
                for c in range(cols):
                    if dots_shown >= visible_dots and step_idx < 3:
                        break
                    cx = start_x + c * col_gap
                    cy = start_y + r * row_gap
                    color = [COLORS['primary'], COLORS['secondary'], COLORS['accent2'],
                             COLORS['accent']][r % 4]
                    draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
                                 fill=hex_to_rgb(color), outline=hex_to_rgb('#1E293B'))
                    dots_shown += 1
                if dots_shown >= visible_dots and step_idx < 3:
                    break

            # Row labels
            for r in range(rows):
                if step_idx >= 1:
                    cy = start_y + r * row_gap
                    draw.text((80, cy - 12), f"Row {r + 1}", fill=hex_to_rgb(COLORS['text_light']),
                              font=get_font(22))

            # Multiplication equation at bottom
            eq_y = 1200
            eq_text = f"{rows} × {cols} = {total}" if step_idx >= 3 else f"{rows} × {cols} = ?"
            draw.text((540, eq_y), eq_text, fill=hex_to_rgb(COLORS['text']),
                      font=get_font(52, bold=True), anchor='mm')

            # Step text
            draw.text((540, 1450), step_text, fill=hex_to_rgb(COLORS['text']),
                      font=get_font(32, bold=True), anchor='mm')

            # Progress bar
            progress = (frame_idx + 1) / num_frames
            bar_y = 1700
            draw.rounded_rectangle([100, bar_y, 100 + int(880 * progress), bar_y + 16],
                                    radius=8, fill=hex_to_rgb(COLORS['accent']))

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames

    def generate_measurement_frames(self, title, measurements=None,
                                      class_label="Class 3", chapter="", num_frames=30):
        """
        Generate frames showing a ruler/scale measuring objects.

        measurements: list of dicts:
            - 'object': str (e.g., 'Pencil')
            - 'length_cm': int (e.g., 15)
            - 'color': hex color for the object
            - 'start_frame': int
        """
        if measurements is None:
            measurements = [
                {'object': 'Pencil', 'length_cm': 15, 'color': '#2563EB', 'start_frame': 0},
                {'object': 'Book', 'length_cm': 25, 'color': '#7C3AED', 'start_frame': 10},
                {'object': 'Eraser', 'length_cm': 5, 'color': '#10B981', 'start_frame': 20},
            ]

        frames = []
        ruler_x0 = 80
        ruler_x1 = WIDTH - 80
        ruler_y = 500
        ruler_h = 80

        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
            draw = ImageDraw.Draw(img)
            draw_gradient_bg(draw, img, '#FFF7ED', '#FFFFFF')
            draw_header(draw, class_label, chapter, title)

            # Ruler background
            draw.rounded_rectangle(
                [(ruler_x0 - 10, ruler_y - 10), (ruler_x1 + 10, ruler_y + ruler_h + 10)],
                radius=8, fill=hex_to_rgb('#FEF3C7'), outline=hex_to_rgb('#D97706'), width=2)

            # Ruler fill
            draw.rectangle(
                [(ruler_x0, ruler_y), (ruler_x1, ruler_y + ruler_h)],
                fill=hex_to_rgb('#FFFBEB'))

            # Tick marks and labels for 0-30 cm
            total_cm = 30
            px_per_cm = (ruler_x1 - ruler_x0) / total_cm
            font_tick = get_font(20, bold=True)
            font_tick_sm = get_font(16)

            for cm in range(total_cm + 1):
                x = ruler_x0 + int(cm * px_per_cm)
                if cm % 5 == 0:
                    # Major tick
                    draw.line([(x, ruler_y), (x, ruler_y + ruler_h)],
                              fill=hex_to_rgb(COLORS['text']), width=2)
                    draw.text((x - 5, ruler_y + ruler_h + 8), str(cm),
                              fill=hex_to_rgb(COLORS['text']), font=font_tick)
                else:
                    # Minor tick
                    draw.line([(x, ruler_y), (x, ruler_y + ruler_h // 2)],
                              fill=hex_to_rgb(COLORS['text_light']), width=1)

            # "cm" label
            font_cm = get_font(24, bold=True)
            draw.text((ruler_x1 + 15, ruler_y + ruler_h // 2 - 10), 'cm',
                      fill=hex_to_rgb('#D97706'), font=font_cm)

            # Draw objects being measured
            current_measurement = None
            for m in measurements:
                start = m.get('start_frame', 0)
                if frame_idx >= start:
                    current_measurement = m

            if current_measurement:
                obj_len_cm = current_measurement['length_cm']
                obj_x1 = ruler_x0
                obj_x2 = ruler_x0 + int(obj_len_cm * px_per_cm)
                obj_color = hex_to_rgb(current_measurement.get('color', COLORS['primary']))
                obj_name = current_measurement['object']

                # Animated progress
                start = current_measurement.get('start_frame', 0)
                progress = min((frame_idx - start) / 6.0, 1.0)
                current_x2 = int(obj_x1 + (obj_x2 - obj_x1) * progress)

                # Object bar below ruler
                obj_y = ruler_y + ruler_h + 60
                obj_h = 40
                draw.rounded_rectangle(
                    [(obj_x1, obj_y), (current_x2, obj_y + obj_h)],
                    radius=8, fill=obj_color)

                # Measurement arrow
                arrow_y = ruler_y - 40
                draw.line([(obj_x1, arrow_y), (current_x2, arrow_y)],
                          fill=obj_color, width=3)
                # Left arrowhead
                draw.polygon([(obj_x1, arrow_y), (obj_x1 + 10, arrow_y - 6),
                              (obj_x1 + 10, arrow_y + 6)], fill=obj_color)
                # Right arrowhead
                draw.polygon([(current_x2, arrow_y), (current_x2 - 10, arrow_y - 6),
                              (current_x2 - 10, arrow_y + 6)], fill=obj_color)

                # Object name label
                font_obj = get_font(28, bold=True)
                bbox = draw.textbbox((0, 0), obj_name, font=font_obj)
                tw = bbox[2] - bbox[0]
                draw.text((obj_x1 + (current_x2 - obj_x1) // 2 - tw // 2,
                           obj_y + obj_h + 15), obj_name,
                          fill=hex_to_rgb(COLORS['text']), font=font_obj)

                # Big number display
                if progress >= 1.0:
                    font_big = get_font(140, bold=True)
                    num_text = f"{obj_len_cm} cm"
                    bbox = draw.textbbox((0, 0), num_text, font=font_big)
                    tw = bbox[2] - bbox[0]
                    draw.text((WIDTH // 2 - tw // 2, 1000), num_text,
                              fill=obj_color, font=font_big)

            # Step indicator
            draw_step_indicator(draw, len(measurements),
                                len([m for m in measurements if frame_idx >= m.get('start_frame', 0)]) - 1,
                                100, 180)

            # Progress bar
            current_step = len([m for m in measurements if frame_idx >= m.get('start_frame', 0)])
            progress_pct = current_step / len(measurements)
            bar_w = int((WIDTH - 100) * progress_pct)
            draw.rounded_rectangle([(50, HEIGHT - 80), (50 + bar_w, HEIGHT - 50)],
                                   radius=10, fill=hex_to_rgb('#D97706'))
            draw.rounded_rectangle([(50, HEIGHT - 80), (WIDTH - 50, HEIGHT - 50)],
                                   radius=10, outline=hex_to_rgb(COLORS['grid_bold']), width=2)

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames

    def generate_time_frames(self, title, times=None,
                              class_label="Class 4", chapter="", num_frames=30):
        """
        Generate frames showing an analog clock with different times.

        times: list of dicts:
            - 'hour': int (1-12)
            - 'minute': int (0-59)
            - 'label': str (e.g., "3 o'clock")
            - 'start_frame': int
        """
        if times is None:
            times = [
                {'hour': 3, 'minute': 0, 'label': "3 o'clock", 'start_frame': 0},
                {'hour': 6, 'minute': 15, 'label': "6:15", 'start_frame': 8},
                {'hour': 9, 'minute': 30, 'label': "9:30", 'start_frame': 16},
                {'hour': 12, 'minute': 0, 'label': "12 o'clock", 'start_frame': 24},
            ]

        frames = []
        clock_cx = WIDTH // 2
        clock_cy = 700
        clock_r = 280

        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
            draw = ImageDraw.Draw(img)
            draw_gradient_bg(draw, img, '#EFF6FF', '#FFFFFF')
            draw_header(draw, class_label, chapter, title)

            # Find current time
            current_time = times[0]
            for t in times:
                if frame_idx >= t.get('start_frame', 0):
                    current_time = t

            start = current_time.get('start_frame', 0)
            progress = min((frame_idx - start) / 5.0, 1.0)

            # Clock face
            draw.ellipse(
                [(clock_cx - clock_r - 5, clock_cy - clock_r - 5),
                 (clock_cx + clock_r + 5, clock_cy + clock_r + 5)],
                fill=hex_to_rgb('#1E293B'), outline=hex_to_rgb('#1E293B'))
            draw.ellipse(
                [(clock_cx - clock_r, clock_cy - clock_r),
                 (clock_cx + clock_r, clock_cy + clock_r)],
                fill=hex_to_rgb('#FFFFFF'), outline=hex_to_rgb('#1E293B'), width=4)

            # Hour markers and numbers
            font_hr = get_font(32, bold=True)
            for hr in range(1, 13):
                angle = math.radians(hr * 30 - 90)
                # Marker dot
                mx = clock_cx + int((clock_r - 25) * math.cos(angle))
                my = clock_cy + int((clock_r - 25) * math.sin(angle))
                marker_r = 4 if hr % 3 != 0 else 6
                marker_color = COLORS['primary'] if hr % 3 == 0 else COLORS['text']
                draw.ellipse([(mx - marker_r, my - marker_r), (mx + marker_r, my + marker_r)],
                             fill=hex_to_rgb(marker_color))

                # Number
                nx = clock_cx + int((clock_r - 55) * math.cos(angle))
                ny = clock_cy + int((clock_r - 55) * math.sin(angle))
                label = str(hr)
                bbox = draw.textbbox((0, 0), label, font=font_hr)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                draw.text((nx - tw // 2, ny - th // 2), label,
                          fill=hex_to_rgb(COLORS['text']), font=font_hr)

            # Minute tick marks
            for m in range(60):
                if m % 5 != 0:
                    angle = math.radians(m * 6 - 90)
                    x1 = clock_cx + int((clock_r - 10) * math.cos(angle))
                    y1 = clock_cy + int((clock_r - 10) * math.sin(angle))
                    x2 = clock_cx + int(clock_r * math.cos(angle))
                    y2 = clock_cy + int(clock_r * math.sin(angle))
                    draw.line([(x1, y1), (x2, y2)],
                              fill=hex_to_rgb(COLORS['grid_bold']), width=1)

            # Hands with animation
            target_hour = current_time['hour'] % 12
            target_minute = current_time['minute']

            # Hour hand angle (each hour = 30 degrees, plus fractional from minutes)
            hour_angle = math.radians((target_hour + target_minute / 60.0) * 30 - 90)
            # Minute hand angle
            minute_angle = math.radians(target_minute * 6 - 90)

            # Animate: sweep from 12 o'clock position
            sweep = min(progress * 1.2, 1.0)

            # Minute hand (longer, thinner)
            if sweep >= 0.5:
                m_sweep = min((sweep - 0.5) * 2, 1.0)
                m_hand_len = int(clock_r * 0.75)
                mx = clock_cx + int(m_hand_len * math.cos(minute_angle) * m_sweep)
                my = clock_cy + int(m_hand_len * math.sin(minute_angle) * m_sweep)
                draw.line([(clock_cx, clock_cy), (mx, my)],
                          fill=hex_to_rgb(COLORS['primary']), width=4)

            # Hour hand (shorter, thicker)
            h_hand_len = int(clock_r * 0.5)
            hx = clock_cx + int(h_hand_len * math.cos(hour_angle) * sweep)
            hy = clock_cy + int(h_hand_len * math.sin(hour_angle) * sweep)
            draw.line([(clock_cx, clock_cy), (hx, hy)],
                      fill=hex_to_rgb(COLORS['text']), width=6)

            # Center dot
            draw.ellipse([(clock_cx - 8, clock_cy - 8), (clock_cx + 8, clock_cy + 8)],
                         fill=hex_to_rgb(COLORS['accent']))

            # Digital time display below clock
            if progress >= 0.8:
                hr_val = current_time['hour']
                min_val = current_time['minute']
                digital = f"{hr_val:02d}:{min_val:02d}"
                font_digital = get_font(72, bold=True)
                bbox = draw.textbbox((0, 0), digital, font=font_digital)
                tw = bbox[2] - bbox[0]
                draw.rounded_rectangle(
                    [(WIDTH // 2 - tw // 2 - 20, clock_cy + clock_r + 50),
                     (WIDTH // 2 + tw // 2 + 20, clock_cy + clock_r + 140)],
                    radius=15, fill=hex_to_rgb('#1E293B'))
                draw.text((WIDTH // 2 - tw // 2, clock_cy + clock_r + 60), digital,
                          fill=hex_to_rgb(COLORS['accent']), font=font_digital)

                # Label
                font_label = get_font(36)
                label = current_time.get('label', '')
                bbox2 = draw.textbbox((0, 0), label, font=font_label)
                tw2 = bbox2[2] - bbox2[0]
                draw.text((WIDTH // 2 - tw2 // 2, clock_cy + clock_r + 160), label,
                          fill=hex_to_rgb(COLORS['text_light']), font=font_label)

            # Step indicator
            current_step = len([t for t in times if frame_idx >= t.get('start_frame', 0)]) - 1
            draw_step_indicator(draw, len(times), current_step, 100, 180)

            # Progress bar
            progress_pct = (current_step + 1) / len(times)
            bar_w = int((WIDTH - 100) * progress_pct)
            draw.rounded_rectangle([(50, HEIGHT - 80), (50 + bar_w, HEIGHT - 50)],
                                   radius=10, fill=hex_to_rgb(COLORS['primary']))
            draw.rounded_rectangle([(50, HEIGHT - 80), (WIDTH - 50, HEIGHT - 50)],
                                   radius=10, outline=hex_to_rgb(COLORS['grid_bold']), width=2)

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames

    def generate_bar_chart_frames(self, title, categories=None, values=None,
                                    class_label="Class 5", chapter="", num_frames=30):
        """
        Generate frames showing a bar chart with bars growing one by one.

        categories: list of str (e.g., ['Apple', 'Banana', 'Orange', 'Mango'])
        values: list of int (e.g., [5, 8, 3, 7])
        """
        if categories is None:
            categories = ['Apple', 'Banana', 'Orange', 'Mango']
        if values is None:
            values = [5, 8, 3, 7]

        bar_colors = ['#2563EB', '#7C3AED', '#F59E0B', '#10B981', '#EF4444', '#6366F1']
        n = len(categories)
        frames_per_bar = max(3, (num_frames - 5) // n)

        frames = []
        chart_x0 = 150
        chart_x1 = WIDTH - 80
        chart_y0 = 350
        chart_y1 = 1400
        chart_w = chart_x1 - chart_x0
        chart_h = chart_y1 - chart_y0

        max_val = max(values) if values else 10
        y_step = max(1, max_val // 5)

        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
            draw = ImageDraw.Draw(img)
            draw_gradient_bg(draw, img, '#F0FFF4', '#FFFFFF')
            draw_header(draw, class_label, chapter, title)

            # Chart title
            font_ct = get_font(32, bold=True)
            draw.text((chart_x0, chart_y0 - 60), title,
                      fill=hex_to_rgb(COLORS['text']), font=font_ct)

            # Y-axis
            draw.line([(chart_x0, chart_y0), (chart_x0, chart_y1)],
                      fill=hex_to_rgb(COLORS['text']), width=3)
            # X-axis
            draw.line([(chart_x0, chart_y1), (chart_x1, chart_y1)],
                      fill=hex_to_rgb(COLORS['text']), width=3)

            # Y-axis grid lines and labels
            font_y = get_font(22)
            for i in range(0, max_val + 1, y_step):
                y = chart_y1 - int(i / max_val * chart_h)
                draw.line([(chart_x0, y), (chart_x1, y)],
                          fill=hex_to_rgb(COLORS['grid']), width=1)
                draw.text((chart_x0 - 40, y - 10), str(i),
                          fill=hex_to_rgb(COLORS['text_light']), font=font_y)

            # Y-axis label (rotated text simulated with stacked chars)
            font_ylabel = get_font(24, bold=True)
            draw.text((50, chart_y0 + chart_h // 2 - 30), "Count",
                      fill=hex_to_rgb(COLORS['text']), font=font_ylabel)

            # Draw bars
            bar_area_w = chart_w // n
            bar_w = int(bar_area_w * 0.6)
            bar_gap = int(bar_area_w * 0.2)

            for i in range(n):
                bar_start_frame = i * frames_per_bar + 3
                if frame_idx < bar_start_frame:
                    continue

                bar_progress = min((frame_idx - bar_start_frame) / (frames_per_bar * 0.8), 1.0)
                bar_val = values[i]
                bar_h = int(bar_val / max_val * chart_h * bar_progress)

                bx = chart_x0 + i * bar_area_w + bar_gap
                by = chart_y1 - bar_h

                color = hex_to_rgb(bar_colors[i % len(bar_colors)])
                draw.rounded_rectangle(
                    [(bx, by), (bx + bar_w, chart_y1)],
                    radius=6, fill=color)

                # Value on top
                if bar_progress >= 1.0:
                    font_val = get_font(28, bold=True)
                    val_text = str(bar_val)
                    bbox = draw.textbbox((0, 0), val_text, font=font_val)
                    tw = bbox[2] - bbox[0]
                    draw.text((bx + bar_w // 2 - tw // 2, by - 35), val_text,
                              fill=color, font=font_val)

                # Category label below x-axis
                font_cat = get_font(24, bold=True)
                bbox = draw.textbbox((0, 0), categories[i], font=font_cat)
                tw = bbox[2] - bbox[0]
                draw.text((bx + bar_w // 2 - tw // 2, chart_y1 + 15), categories[i],
                          fill=hex_to_rgb(COLORS['text']), font=font_cat)

            # Step indicator
            bars_shown = len([i for i in range(n)
                              if frame_idx >= i * frames_per_bar + 3])
            draw_step_indicator(draw, n, max(0, bars_shown - 1), 100, 180)

            # Progress bar
            progress_pct = min(bars_shown / n, 1.0)
            bar_w_pb = int((WIDTH - 100) * progress_pct)
            draw.rounded_rectangle([(50, HEIGHT - 80), (50 + bar_w_pb, HEIGHT - 50)],
                                   radius=10, fill=hex_to_rgb(COLORS['accent2']))
            draw.rounded_rectangle([(50, HEIGHT - 80), (WIDTH - 50, HEIGHT - 50)],
                                   radius=10, outline=hex_to_rgb(COLORS['grid_bold']), width=2)

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames

    def generate_pattern_frames(self, title, patterns=None,
                                 class_label="Class 2", chapter="", num_frames=30):
        """
        Generate frames showing pattern sequences with missing shapes.

        patterns: list of dicts:
            - 'sequence': list of shape names (e.g., ['circle', 'square', 'circle', 'square', '?'])
            - 'answer': str (the missing shape)
            - 'start_frame': int
        """
        if patterns is None:
            patterns = [
                {'sequence': ['circle', 'square', 'circle', 'square', '?'],
                 'answer': 'circle', 'start_frame': 0},
                {'sequence': ['triangle', 'triangle', 'circle', 'triangle', 'triangle', '?'],
                 'answer': 'circle', 'start_frame': 15},
            ]

        shape_colors = {
            'circle': ('#2563EB', '#1D4ED8'),
            'square': ('#7C3AED', '#5B21B6'),
            'triangle': ('#10B981', '#059669'),
            'star': ('#F59E0B', '#D97706'),
            'heart': ('#EF4444', '#DC2626'),
        }

        frames = []

        for frame_idx in range(num_frames):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=hex_to_rgb(COLORS['bg']))
            draw = ImageDraw.Draw(img)
            draw_gradient_bg(draw, img, '#FDF4FF', '#FFFFFF')
            draw_header(draw, class_label, chapter, title)

            y_pos = 350

            for pat_idx, pat in enumerate(patterns):
                start = pat.get('start_frame', 0)
                if frame_idx < start:
                    y_pos += 300
                    continue

                sequence = pat['sequence']
                answer = pat.get('answer', 'circle')
                seq_progress = min((frame_idx - start) / len(sequence), 1.0)
                visible_count = max(1, int(seq_progress * len(sequence)) + 1)

                # Pattern label
                font_label = get_font(28, bold=True)
                draw.text((80, y_pos - 50), f"Pattern {pat_idx + 1}",
                          fill=hex_to_rgb(COLORS['text']), font=font_label)

                # Draw shapes in sequence
                shape_size = 45
                spacing = 120
                start_x = (WIDTH - len(sequence) * spacing) // 2 + spacing // 2

                for i, shape_name in enumerate(sequence):
                    if i >= visible_count:
                        break

                    sx = start_x + i * spacing
                    sy = y_pos + 50

                    if shape_name == '?':
                        # Draw question mark in a dashed circle
                        reveal_frame = start + len(sequence)
                        is_revealed = frame_idx >= reveal_frame

                        if is_revealed:
                            fill_c, outline_c = shape_colors.get(answer, ('#2563EB', '#1D4ED8'))
                            draw_shape(draw, answer, sx, sy, shape_size,
                                       fill_c, outline_c, 1.0)
                            # Checkmark
                            font_check = get_font(24, bold=True)
                            draw.text((sx - 10, sy + shape_size + 10), "✓",
                                      fill=hex_to_rgb(COLORS['accent2']), font=font_check)
                        else:
                            # Dashed circle placeholder
                            draw.ellipse(
                                [(sx - shape_size, sy - shape_size),
                                 (sx + shape_size, sy + shape_size)],
                                outline=hex_to_rgb(COLORS['grid_bold']), width=3)
                            font_q = get_font(60, bold=True)
                            bbox = draw.textbbox((0, 0), '?', font=font_q)
                            tw = bbox[2] - bbox[0]
                            th = bbox[3] - bbox[1]
                            draw.text((sx - tw // 2, sy - th // 2), '?',
                                      fill=hex_to_rgb(COLORS['accent']), font=font_q)
                    else:
                        fill_c, outline_c = shape_colors.get(shape_name, ('#DBEAFE', '#2563EB'))
                        # Animate shape appearing
                        shape_progress = min((frame_idx - start - i) / 2.0, 1.0)
                        if shape_progress > 0:
                            draw_shape(draw, shape_name, sx, sy, shape_size,
                                       fill_c, outline_c, shape_progress)

                y_pos += 300

            # Step indicator
            current_pat = len([p for p in patterns if frame_idx >= p.get('start_frame', 0)])
            draw_step_indicator(draw, len(patterns), max(0, current_pat - 1), 100, 180)

            # Progress bar
            progress_pct = current_pat / len(patterns)
            bar_w = int((WIDTH - 100) * progress_pct)
            draw.rounded_rectangle([(50, HEIGHT - 80), (50 + bar_w, HEIGHT - 50)],
                                   radius=10, fill=hex_to_rgb(COLORS['secondary']))
            draw.rounded_rectangle([(50, HEIGHT - 80), (WIDTH - 50, HEIGHT - 50)],
                                   radius=10, outline=hex_to_rgb(COLORS['grid_bold']), width=2)

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            img.save(frame_path)
            frames.append(str(frame_path))

        return frames


def _build_equation_steps(equation_str):
    """Build step-by-step equation solving steps from an equation string like '2x + 5 = 15'."""
    colors = ['#2563EB', '#7C3AED', '#F59E0B', '#10B981', '#EF4444']
    steps = [{'equation': equation_str, 'explanation': "Let's start!", 'highlight_color': colors[0]}]

    # Parse simple linear equations: ax + b = c
    import re
    m = re.match(r'(\d*)([a-z])?\s*([+\-])\s*(\d+)\s*=\s*(\d+)', equation_str.replace(' ', ''))
    if m:
        a_str, var, op, b_str, c_str = m.groups()
        a = int(a_str) if a_str else 1
        b = int(b_str)
        c = int(c_str)
        var = var or 'x'

        if op == '+':
            new_rhs = c - b
            steps.append({'equation': f'{a}{var} = {c} - {b}', 'explanation': f'Remove {b} from both sides', 'highlight_color': colors[1]})
            steps.append({'equation': f'{a}{var} = {new_rhs}', 'explanation': 'Now simplify', 'highlight_color': colors[2]})
            if a != 1:
                result = new_rhs // a
                steps.append({'equation': f'{var} = {new_rhs} / {a}', 'explanation': f'Divide both sides by {a}', 'highlight_color': colors[3]})
                steps.append({'equation': f'{var} = {result}', 'explanation': 'Got the answer!', 'highlight_color': colors[4]})
            else:
                steps.append({'equation': f'{var} = {new_rhs}', 'explanation': 'Got the answer!', 'highlight_color': colors[4]})
        elif op == '-':
            new_rhs = c + b
            steps.append({'equation': f'{a}{var} = {c} + {b}', 'explanation': f'Add {b} to both sides', 'highlight_color': colors[1]})
            steps.append({'equation': f'{a}{var} = {new_rhs}', 'explanation': 'Now simplify', 'highlight_color': colors[2]})
            if a != 1:
                result = new_rhs // a
                steps.append({'equation': f'{var} = {new_rhs} / {a}', 'explanation': f'Divide both sides by {a}', 'highlight_color': colors[3]})
                steps.append({'equation': f'{var} = {result}', 'explanation': 'Got the answer!', 'highlight_color': colors[4]})
            else:
                steps.append({'equation': f'{var} = {new_rhs}', 'explanation': 'Got the answer!', 'highlight_color': colors[4]})

    return steps


# Convenience: detect topic type and generate appropriate frames
def auto_detect_and_generate(topic, frames_dir="temp_frames"):
    """
    Analyze topic content and generate the most appropriate visual frames.
    Returns list of frame paths.
    """
    engine = MathEffects(frames_dir)
    topic_text = topic.get('topic', '').lower()
    chapter = topic.get('chapter', '')
    class_num = topic.get('class', 6)
    class_label = f"Class {class_num}"
    subtopics = topic.get('subtopics', [])
    title = topic.get('topic', 'Math Lesson')

    # ── Keyword categories ──────────────────────────────────────────
    geometry_kw = ['shape', 'circle', 'triangle', 'rectangle', 'square',
                   'polygon', 'angle', 'line', 'ray', 'point', 'symmetry',
                   'vertex', 'edge', 'face', 'quadrilateral', 'pentagon',
                   'hexagon', 'octagon', 'parallelogram', 'rhombus', 'trapezium']

    fraction_kw = ['fraction', 'half', 'quarter', 'part', 'whole',
                   'numerator', 'denominator', 'proper', 'improper', 'mixed']

    counting_kw = ['count', 'number', 'digit', 'ones', 'tens', 'hundreds',
                   'place value', 'before', 'after', 'between', 'ascending',
                   'descending', 'successor', 'predecessor']

    equation_kw = ['equation', 'solve', 'variable', 'expression', 'algebra',
                   'linear', 'quadratic', 'simplify', 'identity', 'polynomial']

    addition_kw = ['add', 'subtract', 'sum', 'difference', 'plus', 'minus',
                   'addition', 'subtraction', 'total', 'combine', 'increase',
                   'decrease', 'more than', 'less than', 'how many altogether']

    multiplication_kw = ['multiply', 'divide', 'product', 'quotient', 'times',
                         'multiplication', 'division', 'groups of', 'shared equally',
                         'factor', 'multiple', 'remainder']

    measurement_kw = ['measure', 'length', 'weight', 'capacity', 'meter',
                      'kilogram', 'litre', 'centimeter', 'ruler', 'scale',
                      'temperature', 'volume', 'area', 'perimeter', 'mass',
                      'gram', 'millilitre', 'kilometer', 'inch', 'foot']

    time_kw = ['time', 'clock', 'hour', 'minute', 'second', 'watch',
               'calendar', 'day', 'week', 'month', 'year', 'elapsed',
               'duration', 'am', 'pm', 'o\'clock', 'half past', 'quarter']

    data_kw = ['data', 'bar graph', 'pie chart', 'pictograph', 'tally',
               'frequency', 'survey', 'statistics', 'mean', 'median',
               'mode', 'average', 'bar chart', 'histogram']

    pattern_kw = ['pattern', 'sequence', 'series', 'next', 'rule', 'term',
                  'fibonacci', 'arithmetic', 'geometric', 'repeating',
                  'growing', 'number pattern']

    decimal_kw = ['decimal', 'percent', 'percentage', 'hundredth', 'tenth',
                  'point', 'ratio', 'proportion', 'discount', 'profit',
                  'loss', 'interest']

    # ── Detect topic type ───────────────────────────────────────────
    def match(keywords):
        return any(kw in topic_text for kw in keywords)

    if match(geometry_kw):
        shapes = []
        shape_types = ['circle', 'rectangle', 'triangle', 'square']
        for i, st in enumerate(shape_types):
            shapes.append({
                'type': st,
                'cx': 200 + (i % 2) * 500, 'cy': 500 + (i // 2) * 400,
                'size': 120,
                'fill': SHAPE_FILLS[i % len(SHAPE_FILLS)],
                'outline': SHAPE_OUTLINES[i % len(SHAPE_OUTLINES)],
                'label': st.title(),
                'start_frame': i * 7, 'end_frame': i * 7 + 6,
            })
        return engine.generate_geometry_frames(title, shapes, class_label, chapter)

    elif match(fraction_kw):
        fractions = [
            {'numerator': 1, 'denominator': 2, 'color': '#2563EB', 'label': 'Half (1/2)', 'start_frame': 0},
            {'numerator': 1, 'denominator': 4, 'color': '#7C3AED', 'label': 'Quarter (1/4)', 'start_frame': 10},
            {'numerator': 3, 'denominator': 4, 'color': '#10B981', 'label': 'Three Quarters (3/4)', 'start_frame': 20},
        ]
        return engine.generate_fraction_frames(title, fractions, class_label, chapter)

    elif match(counting_kw):
        count_to = min(max(class_num + 3, 5), 15)
        return engine.generate_counting_frames(title, count_to, 'stars', class_label, chapter)

    elif match(addition_kw):
        # Try to extract numbers from topic text
        import re
        nums = re.findall(r'\d+', topic_text)
        a, b = (int(nums[0]), int(nums[1])) if len(nums) >= 2 else (7, 5)
        is_subtract = any(kw in topic_text for kw in ['subtract', 'subtraction', 'minus', 'decrease', 'less than', 'difference'])
        if is_subtract:
            # Show subtraction: start with a, remove b
            return engine.generate_addition_frames(title, a=a, b=-b, class_label=class_label, chapter=chapter)
        return engine.generate_addition_frames(title, a=a, b=b, class_label=class_label, chapter=chapter)

    elif match(multiplication_kw):
        import re
        nums = re.findall(r'\d+', topic_text)
        rows, cols = (int(nums[0]), int(nums[1])) if len(nums) >= 2 else (3, 4)
        return engine.generate_multiplication_frames(title, rows=rows, cols=cols, class_label=class_label, chapter=chapter)

    elif match(measurement_kw):
        measurements = [
            {'object': 'Pencil', 'length_cm': 15, 'color': '#2563EB', 'start_frame': 0},
            {'object': 'Book', 'length_cm': 25, 'color': '#7C3AED', 'start_frame': 10},
            {'object': 'Eraser', 'length_cm': 5, 'color': '#10B981', 'start_frame': 20},
        ]
        return engine.generate_measurement_frames(title, measurements, class_label, chapter)

    elif match(time_kw):
        times = [
            {'hour': 3, 'minute': 0, 'label': '3:00'},
            {'hour': 6, 'minute': 15, 'label': '6:15'},
            {'hour': 9, 'minute': 30, 'label': '9:30'},
            {'hour': 12, 'minute': 0, 'label': '12:00'},
        ]
        return engine.generate_time_frames(title, times, class_label, chapter)

    elif match(data_kw):
        categories = ['Apple', 'Banana', 'Orange', 'Mango']
        values = [5, 8, 3, 7]
        return engine.generate_bar_chart_frames(title, categories, values, class_label, chapter)

    elif match(pattern_kw):
        patterns = [
            {'sequence': ['circle', 'square', 'circle', 'square', '?'], 'answer': 'circle', 'start_frame': 0},
            {'sequence': ['triangle', 'triangle', 'circle', 'triangle', 'triangle', '?'], 'answer': 'circle', 'start_frame': 15},
        ]
        return engine.generate_pattern_frames(title, patterns, class_label, chapter)

    elif match(decimal_kw):
        fractions = [
            {'numerator': 25, 'denominator': 100, 'color': '#2563EB', 'label': '0.25 = 25%', 'start_frame': 0},
            {'numerator': 50, 'denominator': 100, 'color': '#7C3AED', 'label': '0.50 = 50%', 'start_frame': 10},
            {'numerator': 75, 'denominator': 100, 'color': '#10B981', 'label': '0.75 = 75%', 'start_frame': 20},
        ]
        return engine.generate_fraction_frames(title, fractions, class_label, chapter)

    elif match(equation_kw):
        # Try to find an actual equation in topic text or subtopics
        import re
        combined = topic_text + ' ' + ' '.join(subtopics) if subtopics else topic_text
        eq_match = re.search(r'(\d+[a-z]?\s*[+\-*/]\s*\d+\s*=\s*\d+)', combined)
        if eq_match:
            eq = eq_match.group(1)
            steps = _build_equation_steps(eq)
        else:
            steps = [
                {'equation': '2x + 5 = 15', 'explanation': "Let's start!", 'highlight_color': '#2563EB'},
                {'equation': '2x = 15 - 5', 'explanation': '5 dono side se hatao', 'highlight_color': '#7C3AED'},
                {'equation': '2x = 10', 'explanation': 'Now simplify', 'highlight_color': '#F59E0B'},
                {'equation': 'x = 10 / 2', 'explanation': 'Dono side ko 2 se divide karo', 'highlight_color': '#10B981'},
                {'equation': 'x = 5', 'explanation': 'Got the answer!', 'highlight_color': '#EF4444'},
            ]
        return engine.generate_equation_frames(title, steps, class_label, chapter)

    else:
        # Default: number line
        return engine.generate_number_line_frames(
            title, 0, 20, 1, list(range(1, 11)),
            class_label, chapter
        )
