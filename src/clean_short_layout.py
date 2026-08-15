"""Minimal, phone-first composition cleanup for Teacher Bot videos.
Keeps only useful educational text and improves visual readability on phones.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

W, H = 1080, 1920
HEADER = (0, 200)
VIZ_UI = (200, 285)
CTA = (1060, 1140)
CODE = (1140, 1740)
FOOTER = (1740, 1920)


def _font(size=42, bold=True):
    candidates = [
        "assets/fonts/Montserrat-Bold.ttf" if bold else "assets/fonts/Montserrat-Regular.ttf",
        "assets/fonts/hindi_font_bold.ttf" if bold else "assets/fonts/hindi_font.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap_title(title: str, max_chars: int = 31):
    words = title.split()
    lines, cur = [], ""
    for word in words:
        candidate = (cur + " " + word).strip()
        if cur and len(candidate) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = candidate
    if cur:
        lines.append(cur)
    return lines[:2]


def clean_frame(img: Image.Image, scene: dict) -> Image.Image:
    """Return a clean 9:16 frame with only useful educational text."""
    img = img.convert("RGB")
    out = img.copy()

    # Make the primary concept visibly stronger without changing the code panel.
    viz = out.crop((0, VIZ_UI[1], W, CTA[0]))
    viz = ImageEnhance.Contrast(viz).enhance(1.22)
    viz = ImageEnhance.Brightness(viz).enhance(1.10)
    out.paste(viz, (0, VIZ_UI[1]))

    d = ImageDraw.Draw(out)
    bg = (9, 11, 18)

    # Remove non-essential game/UI text bands.
    d.rectangle([0, HEADER[0], W, HEADER[1]], fill=bg)
    d.rectangle([0, VIZ_UI[0], W, VIZ_UI[1]], fill=(7, 10, 17))
    d.rectangle([0, CTA[0], W, CTA[1]], fill=bg)
    d.rectangle([0, FOOTER[0], W, FOOTER[1]], fill=bg)

    # Remove decorative editor filename tab.
    d.rectangle([0, CODE[0], W, CODE[0] + 38], fill=(18, 20, 28))

    # Keep only the useful educational topic title, wrapped instead of truncated.
    title = str(scene.get("title", scene.get("topic", ""))).strip()
    if title:
        font = _font(42, True)
        lines = _wrap_title(title, 31)
        line_h = 50
        start_y = 46 if len(lines) == 2 else 64
        for i, line in enumerate(lines):
            bbox = d.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = max(32, min((W - tw) // 2, W - tw - 32))
            d.text((x, start_y + i * line_h), line, font=font, fill=(245, 248, 255))

    return out
