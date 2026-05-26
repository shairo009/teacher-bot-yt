"""
Thumbnail Generator for YouTube Videos
Creates eye-catching 1280x720 thumbnails with Hindi text,
math decorations, and NCERT branding.
"""

import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)

# YouTube thumbnail standard size
WIDTH = 1280
HEIGHT = 720

# Color palettes (randomly picked per thumbnail)
PALETTES = [
    {'bg_top': '#1E3A8A', 'bg_bot': '#7C3AED', 'text': '#FFFFFF', 'accent': '#FBBF24', 'badge': '#EF4444'},
    {'bg_top': '#0F766E', 'bg_bot': '#2563EB', 'text': '#FFFFFF', 'accent': '#FCD34D', 'badge': '#DC2626'},
    {'bg_top': '#7C3AED', 'bg_bot': '#EC4899', 'text': '#FFFFFF', 'accent': '#34D399', 'badge': '#F59E0B'},
    {'bg_top': '#1D4ED8', 'bg_bot': '#06B6D4', 'text': '#FFFFFF', 'accent': '#FBBF24', 'badge': '#EF4444'},
    {'bg_top': '#9333EA', 'bg_bot': '#3B82F6', 'text': '#FFFFFF', 'accent': '#FDE68A', 'badge': '#10B981'},
]

# Math symbols for decoration
MATH_SYMBOLS = ['+', '-', '×', '÷', '=', 'π', '∑', '√', '∞', 'Δ', 'θ', 'α', 'β', '%']


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def get_font(size, bold=False):
    """Get Hindi font at given size."""
    font_path = Path(_PROJECT_ROOT) / 'assets' / 'fonts' / 'hindi_font.ttf'
    if font_path.exists():
        return ImageFont.truetype(str(font_path), size)
    # Fallback
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                                  else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()


def draw_gradient_bg(draw, palette, width, height):
    """Draw vertical gradient background."""
    c1 = hex_to_rgb(palette['bg_top'])
    c2 = hex_to_rgb(palette['bg_bot'])
    for y in range(height):
        t = y / height
        color = lerp_color(c1, c2, t)
        draw.line([(0, y), (width, y)], fill=color)


def draw_math_decorations(draw, palette, width, height):
    """Scatter math symbols as background decoration."""
    accent = hex_to_rgb(palette['accent'])
    # Semi-transparent effect via lighter color
    light_accent = tuple(min(255, c + 80) for c in accent)

    for _ in range(20):
        symbol = random.choice(MATH_SYMBOLS)
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(30, 80)
        font = get_font(size)
        # Use lighter version for bg decoration
        draw.text((x, y), symbol, fill=light_accent + (60,), font=font)


def draw_class_badge(draw, class_num, palette, x=50, y=50):
    """Draw a colored badge showing class number."""
    badge_color = hex_to_rgb(palette['badge'])
    text_color = hex_to_rgb(palette['text'])

    badge_w, badge_h = 180, 80
    # Rounded rectangle
    draw.rounded_rectangle(
        [x, y, x + badge_w, y + badge_h],
        radius=15,
        fill=badge_color
    )
    font = get_font(36, bold=True)
    text = f"Class {class_num}"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        (x + (badge_w - tw) // 2, y + (badge_h - th) // 2 - 2),
        text, fill=text_color, font=font
    )


def draw_ncert_strip(draw, palette, width, height):
    """Draw NCERT branding strip at bottom."""
    strip_h = 50
    strip_y = height - strip_h
    accent = hex_to_rgb(palette['accent'])

    draw.rectangle([0, strip_y, width, height], fill=accent + (200,))

    text_color = hex_to_rgb('#1E293B')
    font = get_font(24, bold=True)
    text = "NCERT Mathematics | Hindi Medium"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(
        ((width - tw) // 2, strip_y + 12),
        text, fill=text_color, font=font
    )


def draw_topic_text(draw, topic_name, palette, width, height):
    """Draw main topic text centered."""
    text_color = hex_to_rgb(palette['text'])

    # Try big font first, shrink if needed
    for size in [72, 64, 56, 48, 40]:
        font = get_font(size, bold=True)
        bbox = draw.textbbox((0, 0), topic_name, font=font)
        tw = bbox[2] - bbox[0]
        if tw < width - 120:
            break

    x = (width - tw) // 2
    y = height // 2 - 60

    # Shadow
    shadow_color = (0, 0, 0, 100)
    draw.text((x + 3, y + 3), topic_name, fill=shadow_color, font=font)
    # Main text
    draw.text((x, y), topic_name, fill=text_color, font=font)


def draw_chapter_subtext(draw, chapter, palette, width, height):
    """Draw chapter name below topic."""
    accent = hex_to_rgb(palette['accent'])
    font = get_font(32)
    bbox = draw.textbbox((0, 0), chapter, font=font)
    tw = bbox[2] - bbox[0]
    x = (width - tw) // 2
    y = height // 2 + 30

    draw.text((x, y), chapter, fill=accent, font=font)


def draw_math_shapes(draw, palette, width, height):
    """Draw decorative math shapes."""
    accent = hex_to_rgb(palette['accent'])
    shapes = ['circle', 'triangle', 'square', 'star']

    for _ in range(5):
        shape = random.choice(shapes)
        x = random.randint(50, width - 100)
        y = random.randint(150, height - 200)
        s = random.randint(20, 50)

        if shape == 'circle':
            draw.ellipse([x, y, x+s, y+s], outline=accent, width=3)
        elif shape == 'triangle':
            draw.polygon([(x+s//2, y), (x, y+s), (x+s, y+s)], outline=accent, width=3)
        elif shape == 'square':
            draw.rectangle([x, y, x+s, y+s], outline=accent, width=3)
        elif shape == 'star':
            draw.text((x, y), '★', fill=accent, font=get_font(s))


def generate_thumbnail(topic_name, class_num, chapter="", output_path=None):
    """
    Generate a YouTube thumbnail.

    Args:
        topic_name: Main topic text (Hindi)
        class_num: Class number (1-10)
        chapter: Chapter name (optional)
        output_path: Where to save (default: outputs/thumbnail.png)

    Returns:
        Path to saved thumbnail, or None on failure.
    """
    try:
        palette = random.choice(PALETTES)

        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img)

        # Background gradient
        draw_gradient_bg(draw, palette, WIDTH, HEIGHT)

        # Math decorations (background layer)
        draw_math_decorations(draw, palette, WIDTH, HEIGHT)

        # Math shapes
        draw_math_shapes(draw, palette, WIDTH, HEIGHT)

        # Class badge
        draw_class_badge(draw, class_num, palette)

        # Main topic text
        draw_topic_text(draw, topic_name, palette, WIDTH, HEIGHT)

        # Chapter subtext
        if chapter:
            draw_chapter_subtext(draw, chapter, palette, WIDTH, HEIGHT)

        # NCERT strip at bottom
        draw_ncert_strip(draw, palette, WIDTH, HEIGHT)

        # Save
        if output_path is None:
            output_path = str(Path(_PROJECT_ROOT) / 'outputs' / 'thumbnail.png')

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.convert('RGB').save(output_path, 'PNG', quality=95)
        print(f"  Thumbnail saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"  Thumbnail generation failed: {e}")
        return None


if __name__ == "__main__":
    # Test
    path = generate_thumbnail(
        topic_name="Skip Counting सीखो",
        class_num=2,
        chapter="Counting in Groups"
    )
    print(f"Generated: {path}")
