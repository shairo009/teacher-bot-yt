"""Create polished, no-key animal Shorts from a rotating animal catalogue.

This generator deliberately has no LLM, image-generation, or paid API
dependency.  It gets a Creative Commons wildlife photo from Wikimedia Commons'
public media search (no token required), adds a Ken-Burns motion effect, then
renders a vertical fact card inspired by the reference poster layout.

Usage:
    python src/animal_short_generator.py
    python src/animal_short_generator.py --dry-run
    python src/animal_short_generator.py --animal-id 3

An internet connection is needed only the first time an animal image is
downloaded.  Downloaded photos are cached in ``tmp/animal_assets``.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TMP_DIR = ROOT / "tmp"
PROGRESS_FILE = DATA_DIR / "animal_progress.json"
HISTORY_FILE = DATA_DIR / "animal_history.json"

WIDTH, HEIGHT, FPS = 720, 1280, 30
DEFAULT_DURATION = 8.8
PHOTO_BOX = (70, 275, 650, 650)
CREAM = (245, 240, 222)
TEAL = (8, 40, 46)
MUTED_TEAL = (16, 67, 76)
GOLD = (235, 187, 77)


# Ordered rather than random: no animal repeats until this full list is used.
# Facts are intentionally short so they remain legible on a 9-second Short.
ANIMALS = [
    {
        "name": "Tiger", "query": "Bengal tiger wildlife", "accent": (233, 131, 45),
        "facts": ["Every tiger has its own stripe pattern.", "It is the largest living cat.", "A tiger's roar can carry for kilometres."],
    },
    {
        "name": "Red Panda", "query": "red panda wildlife", "accent": (203, 86, 60),
        "facts": ["It uses its fluffy tail as a blanket.", "It has a thumb-like wrist bone.", "Most of its diet is bamboo."],
    },
    {
        "name": "African Elephant", "query": "African elephant wildlife", "accent": (155, 151, 140),
        "facts": ["Its trunk has tens of thousands of muscles.", "Elephants communicate with low rumbles.", "They can recognise themselves in mirrors."],
    },
    {
        "name": "Snow Leopard", "query": "snow leopard wildlife", "accent": (161, 180, 188),
        "facts": ["Its long tail helps it balance on cliffs.", "Wide paws work like natural snowshoes.", "It cannot roar like a tiger or lion."],
    },
    {
        "name": "Giraffe", "query": "giraffe wildlife", "accent": (218, 167, 69),
        "facts": ["No two giraffes have the same coat pattern.", "Its long tongue helps strip thorny leaves.", "A giraffe has seven neck vertebrae, like us."],
    },
    {
        "name": "Orca", "query": "orca killer whale wildlife", "accent": (89, 154, 191),
        "facts": ["Every pod has its own calls and dialect.", "Orcas are the largest members of the dolphin family.", "They hunt using teamwork and strategy."],
    },
    {
        "name": "Cheetah", "query": "cheetah wildlife", "accent": (231, 179, 81),
        "facts": ["It is the fastest land animal.", "Its tail acts like a steering rudder.", "Black tear marks reduce glare from the sun."],
    },
    {
        "name": "Sea Turtle", "query": "green sea turtle wildlife", "accent": (77, 159, 134),
        "facts": ["It returns to nest near its birth beach.", "Its shell is part of its skeleton.", "It navigates using Earth's magnetic field."],
    },
    {
        "name": "Arctic Fox", "query": "Arctic fox wildlife", "accent": (185, 208, 222),
        "facts": ["Its coat changes colour with the seasons.", "Fur even covers the soles of its feet.", "It can hear prey moving under snow."],
    },
    {
        "name": "Humpback Whale", "query": "humpback whale wildlife", "accent": (86, 139, 173),
        "facts": ["Its songs can travel huge ocean distances.", "It uses bubble nets to catch fish.", "Its flippers can be as long as a small car."],
    },
    {
        "name": "Great Horned Owl", "query": "great horned owl wildlife", "accent": (186, 133, 74),
        "facts": ["Its ears are hidden on the sides of its head.", "It can rotate its head up to 270 degrees.", "Soft feathers help it fly almost silently."],
    },
    {
        "name": "Giant Panda", "query": "giant panda wildlife", "accent": (194, 199, 193),
        "facts": ["A panda can eat bamboo for many hours a day.", "It has a sixth toe-like bone for gripping.", "Newborn cubs are tiny compared with their mothers."],
    },
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        ROOT / "assets" / "fonts" / ("Montserrat-Bold.ttf" if bold else "Montserrat-Regular.ttf"),
        Path("C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _centered(draw: ImageDraw.ImageDraw, y: int, text: str, font, fill, width: int = WIDTH):
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text(((width - (bbox[2] - bbox[0])) / 2, y), text, font=font, fill=fill)


def _fit_font(draw: ImageDraw.ImageDraw, text: str, maximum_width: int, preferred_size: int, bold: bool = False):
    """Keep long animal names, such as GREAT HORNED OWL, inside the portrait frame."""
    for size in range(preferred_size, 19, -1):
        font = _font(size, bold=bold)
        if draw.textbbox((0, 0), text, font=font)[2] <= maximum_width:
            return font
    return _font(20, bold=bold)


def _commons_photo(animal: dict, index: int) -> Path:
    """Fetch a cached Commons thumbnail by species name; no secret/key is used."""
    cache = TMP_DIR / "animal_assets"
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / f"{index:02d}_{animal['name'].lower().replace(' ', '_')}.jpg"
    if destination.exists() and destination.stat().st_size > 20_000:
        return destination

    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"{animal['query']} filetype:bitmap",
        "gsrnamespace": "6", "gsrlimit": "8", "prop": "imageinfo",
        "iiprop": "url", "iiurlwidth": "1920",
    }
    request = urllib.request.Request(
        "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "TeacherBotYT/1.0 (educational animal Shorts)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    pages = (payload.get("query") or {}).get("pages") or {}
    choices = [
        page.get("imageinfo", [{}])[0].get("thumburl")
        for page in pages.values()
        if page.get("imageinfo")
    ]
    photo_url = next((url for url in choices if url), None)
    if not photo_url:
        raise RuntimeError(f"No Wikimedia Commons photo found for {animal['name']}")
    image_request = urllib.request.Request(photo_url, headers={"User-Agent": "TeacherBotYT/1.0"})
    with urllib.request.urlopen(image_request, timeout=45) as response:
        data = response.read()
    destination.write_bytes(data)
    return destination


def _cover(source: Image.Image, target_size: tuple[int, int], zoom: float, pan: float) -> Image.Image:
    target_w, target_h = target_size
    source = ImageOps.exif_transpose(source).convert("RGB")
    base_scale = max(target_w / source.width, target_h / source.height)
    scale = base_scale * zoom
    resized = source.resize((round(source.width * scale), round(source.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, min(resized.width - target_w, round((resized.width - target_w) * pan)))
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def _background() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), TEAL)
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        color = tuple(round(TEAL[i] * (1 - ratio) + MUTED_TEAL[i] * ratio) for i in range(3))
        draw.line((0, y, WIDTH, y), fill=color)
    # A quiet spotlight behind the photo keeps the source layout elegant.
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((20, 180, 700, 800), fill=(80, 184, 174, 45))
    return Image.alpha_composite(image.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(50))).convert("RGB")


def _render_frame(photo: Image.Image, animal: dict, frame_no: int, total_frames: int) -> Image.Image:
    progress = frame_no / max(1, total_frames - 1)
    image = _background()
    draw = ImageDraw.Draw(image)
    title_font = _font(52, bold=False)
    label_font = _font(18, bold=True)
    fact_font = _font(22, bold=False)
    footer_font = _font(18, bold=False)

    _centered(draw, 86, "ANIMAL OF THE DAY", label_font, (140, 213, 202))
    _centered(draw, 126, animal["name"].upper(), title_font, CREAM)
    draw.rounded_rectangle((PHOTO_BOX[0] - 5, PHOTO_BOX[1] - 5, PHOTO_BOX[2] + 5, PHOTO_BOX[3] + 5), radius=4, fill=CREAM)

    wobble = math.sin(progress * math.pi * 2) * 0.08
    photo_frame = _cover(photo, (PHOTO_BOX[2] - PHOTO_BOX[0], PHOTO_BOX[3] - PHOTO_BOX[1]), 1.04 + progress * 0.12, 0.5 + wobble)
    image.paste(photo_frame, (PHOTO_BOX[0], PHOTO_BOX[1]))
    shade = Image.new("RGBA", photo_frame.size, (0, 0, 0, 0))
    ImageDraw.Draw(shade).rectangle((0, photo_frame.height * .62, photo_frame.width, photo_frame.height), fill=(0, 0, 0, 95))
    image.paste(Image.alpha_composite(photo_frame.convert("RGBA"), shade).convert("RGB"), (PHOTO_BOX[0], PHOTO_BOX[1]))

    card_top, card_bottom = 720, 1068
    draw.rounded_rectangle((70, card_top, 650, card_bottom), radius=18, fill=(3, 24, 29), outline=(76, 139, 135), width=2)
    draw.rounded_rectangle((94, card_top + 24, 124, card_top + 54), radius=15, fill=animal["accent"])
    draw.text((142, card_top + 24), "REAL ANIMAL • QUICK FACTS", font=label_font, fill=(167, 224, 216))
    y = card_top + 83
    for fact in animal["facts"]:
        draw.ellipse((96, y + 10, 105, y + 19), fill=GOLD)
        lines = _wrap(draw, fact, fact_font, 490)
        for line in lines:
            draw.text((122, y), line, font=fact_font, fill=CREAM)
            y += 30
        y += 13

    call_to_action = f'COMMENT: "{animal["name"].upper()}"'
    name_font = _fit_font(draw, call_to_action, WIDTH - 70, 54, bold=True)
    _centered(draw, 1108, call_to_action, name_font, CREAM)
    _centered(draw, 1192, "Follow for a different real animal every day", footer_font, (145, 204, 196))
    return image


def _encode_video(frames: Path, output: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to create the MP4")
    result = subprocess.run([
        ffmpeg, "-y", "-framerate", str(FPS), "-i", str(frames / "frame_%04d.jpg"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ], text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError("ffmpeg failed: " + result.stderr[-1500:])


def generate(animal_id: int | None, duration: float, dry_run: bool) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    progress = _load_json(PROGRESS_FILE, {"current_id": 0})
    current_id = int(progress.get("current_id", 0)) if animal_id is None else animal_id
    index = current_id % len(ANIMALS)
    animal = ANIMALS[index]
    print(f"Creating animal Short #{current_id}: {animal['name']}")
    photo_path = _commons_photo(animal, index)
    photo = Image.open(photo_path)
    run_dir = TMP_DIR / f"animal_{current_id:04d}"
    frames = run_dir / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    total_frames = max(1, round(duration * FPS))
    for number in range(total_frames):
        _render_frame(photo, animal, number, total_frames).save(frames / f"frame_{number:04d}.jpg", quality=93, optimize=True)
    output = run_dir / f"{animal['name'].lower().replace(' ', '_')}_short.mp4"
    _encode_video(frames, output)
    print(f"Created: {output}")

    # A failed render never advances the rotation.  Dry runs also remain pure.
    if not dry_run and animal_id is None:
        progress["current_id"] = current_id + 1
        PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")
        history = _load_json(HISTORY_FILE, [])
        history.append({
            "id": current_id, "animal": animal["name"], "file": str(output.relative_to(ROOT)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        HISTORY_FILE.write_text(json.dumps(history[-500:], indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a real-photo animal Short with no API key")
    parser.add_argument("--animal-id", type=int, help="Use a particular rotation item without advancing progress")
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION, help="Video length in seconds (default: 8.8)")
    parser.add_argument("--dry-run", action="store_true", help="Create a preview but do not save rotation history")
    args = parser.parse_args()
    try:
        generate(args.animal_id, args.duration, args.dry_run)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
