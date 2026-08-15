"""Minimal, phone-first composition cleanup for Teacher Bot Shorts.
Removes non-essential game UI text while preserving the educational title and code.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

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


def clean_frame(img: Image.Image, scene: dict) -> Image.Image:
    """Return a clean 9:16 frame with only useful educational text."""
    img = img.convert("RGB")
    out = img.copy()
    d = ImageDraw.Draw(out)
    bg = (9, 11, 18)

    # Remove all non-essential game/UI text bands.
    d.rectangle([0, HEADER[0], W, HEADER[1]], fill=bg)
    d.rectangle([0, VIZ_UI[0], W, VIZ_UI[1]], fill=(7, 10, 17))
    d.rectangle([0, CTA[0], W, CTA[1]], fill=bg)
    d.rectangle([0, FOOTER[0], W, FOOTER[1]], fill=bg)

    # Remove only the decorative editor filename tab.
    d.rectangle([0, CODE[0], W, CODE[0] + 38], fill=(18, 20, 28))

    # Keep only the useful educational topic title.
    title = str(scene.get("title", scene.get("topic", ""))).strip()
    if title:
        font = _font(44, True)
        max_chars = 42
        if len(title) > max_chars:
            title = title[: max_chars - 1].rstrip() + "…"
        bbox = d.textbbox((0, 0), title, font=font)
        tw = bbox[2] - bbox[0]
        x = max(36, min((W - tw) // 2, W - tw - 36))
        d.text((x, 72), title, font=font, fill=(235, 240, 250))

    return out
