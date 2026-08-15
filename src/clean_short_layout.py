"""Minimal, phone-first composition cleanup for Teacher Bot Shorts.
Removes non-essential game UI text while preserving the educational title and code.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
HEADER = (0, 200)
VIZ = (200, 1060)
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
    """Return a clean 9:16 frame with only useful educational text.

    We intentionally remove puzzle numbers, difficulty, stars, CTA strips,
    timers, complexity stats, and decorative labels. The topic title remains.
    """
    img = img.convert("RGB")
    out = img.copy()
    d = ImageDraw.Draw(out)

    # Preserve the visual and code areas; simplify the surrounding UI bands.
    d.rectangle([0, HEADER[0], W, HEADER[1]], fill=(9, 11, 18))
    d.rectangle([0, CTA[0], W, CTA[1]], fill=(9, 11, 18))
    d.rectangle([0, FOOTER[0], W, FOOTER[1]], fill=(9, 11, 18))

    # Remove the editor's decorative filename tab, leaving the code itself.
    d.rectangle([0, CODE[0], W, CODE[0] + 36], fill=(18, 20, 28))

    # Keep only the useful topic title. No puzzle number, difficulty, stars,
    # live-execution label, CTA, timer, memory/complexity stats, or step text.
    title = str(scene.get("title", "")).strip()
    if title:
        font = _font(44, True)
        # Safe horizontal clipping so long AI titles never leave the canvas.
        max_chars = 42
        if len(title) > max_chars:
            title = title[: max_chars - 1].rstrip() + "…"
        bbox = d.textbbox((0, 0), title, font=font)
        tw = bbox[2] - bbox[0]
        x = max(36, min((W - tw) // 2, W - tw - 36))
        d.text((x, 72), title, font=font, fill=(235, 240, 250))

    return out
