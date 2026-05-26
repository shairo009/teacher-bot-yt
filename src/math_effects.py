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
    """Get a font, trying common paths."""
    font_paths = [
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

    # Detect topic type from keywords
    geometry_keywords = ['shape', 'circle', 'triangle', 'rectangle', 'square',
                         'polygon', 'angle', 'line', 'ray', 'point',
                         'symmetry', 'vertex', 'edge', 'face']
    fraction_keywords = ['fraction', 'half', 'quarter', 'part', 'whole',
                         'numerator', 'denominator', 'proper', 'improper']
    counting_keywords = ['count', 'number', 'digit', 'ones', 'tens',
                         'hundreds', 'place value', 'before', 'after',
                         'between', 'ascending', 'descending']
    equation_keywords = ['equation', 'solve', 'variable', 'expression',
                         'algebra', 'linear', 'quadratic', 'simplify']

    is_geometry = any(kw in topic_text for kw in geometry_keywords)
    is_fraction = any(kw in topic_text for kw in fraction_keywords)
    is_counting = any(kw in topic_text for kw in counting_keywords)
    is_equation = any(kw in topic_text for kw in equation_keywords)

    title = topic.get('topic', 'Math Lesson')

    if is_geometry:
        # Generate geometry shapes
        shapes = []
        shape_types = ['circle', 'rectangle', 'triangle', 'square']
        for i, st in enumerate(shape_types):
            cx = 200 + (i % 2) * 500
            cy = 500 + (i // 2) * 400
            shapes.append({
                'type': st,
                'cx': cx, 'cy': cy,
                'size': 120,
                'fill': SHAPE_FILLS[i % len(SHAPE_FILLS)],
                'outline': SHAPE_OUTLINES[i % len(SHAPE_OUTLINES)],
                'label': st.title(),
                'start_frame': i * 7,
                'end_frame': i * 7 + 6,
            })
        return engine.generate_geometry_frames(title, shapes, class_label, chapter)

    elif is_fraction:
        fractions = [
            {'numerator': 1, 'denominator': 2, 'color': '#2563EB', 'label': 'Half (1/2)', 'start_frame': 0},
            {'numerator': 1, 'denominator': 4, 'color': '#7C3AED', 'label': 'Quarter (1/4)', 'start_frame': 10},
            {'numerator': 3, 'denominator': 4, 'color': '#10B981', 'label': 'Three Quarters (3/4)', 'start_frame': 20},
        ]
        return engine.generate_fraction_frames(title, fractions, class_label, chapter)

    elif is_counting:
        count_to = min(max(class_num + 3, 5), 15)
        return engine.generate_counting_frames(title, count_to, 'stars', class_label, chapter)

    elif is_equation:
        steps = [
            {'equation': '2x + 5 = 15', 'explanation': 'Shuru karte hain!', 'highlight_color': '#2563EB'},
            {'equation': '2x = 15 - 5', 'explanation': '5 dono side se hatao', 'highlight_color': '#7C3AED'},
            {'equation': '2x = 10', 'explanation': 'Ab simplify karo', 'highlight_color': '#F59E0B'},
            {'equation': 'x = 10 / 2', 'explanation': 'Dono side ko 2 se divide karo', 'highlight_color': '#10B981'},
            {'equation': 'x = 5', 'explanation': 'Jawab mil gaya!', 'highlight_color': '#EF4444'},
        ]
        return engine.generate_equation_frames(title, steps, class_label, chapter)

    else:
        # Default: number line
        return engine.generate_number_line_frames(
            title, 0, 20, 1,
            list(range(1, 11)),
            class_label, chapter
        )
