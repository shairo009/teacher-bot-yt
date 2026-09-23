"""Offline-only 2D anatomy previews. No uploader, research or publication state imports."""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw
from src.anatomy_profiles import anatomy_summary
from src.generative_dragon_engine import (
    FPS, WIDTH, HEIGHT, get_font, get_species_for_id, load_encyclopedia,
    render_generative_frame,
)

ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "outputs"
DEFAULT_IDS = [0, 1, 15, 17, 586, 547, 351, 280, 576, 450, 231, 403]


def output_directory(value: str | Path | None = None) -> Path:
    path = Path(value).resolve() if value else OUTPUT_ROOT / "anatomy_preview"
    if not path.is_relative_to(OUTPUT_ROOT.resolve()):
        raise ValueError("Preview output must be inside teacher-bot/outputs; source and publication ledgers are protected")
    path.mkdir(parents=True, exist_ok=True)
    return path


def timeline_frames(duration: float) -> int:
    if not math.isfinite(duration) or not 0.1 <= duration <= 30:
        raise ValueError("Preview duration must be finite and between 0.1 and 30 seconds")
    return max(1, round(duration * FPS))


def preview_species(animal_id: int, mode: str = "surface") -> dict:
    species = get_species_for_id(animal_id)
    if mode not in anatomy_summary(species)["diagnostic_modes"]:
        raise ValueError(f"{mode} is not implemented for {species['name']}; use surface mode")
    species["render_mode"] = mode
    return species


def create_contact_sheet(ids: list[int], output: Path) -> Path:
    if not ids or len(ids) > 48:
        raise ValueError("Contact sheets require 1 to 48 animal IDs")
    species_list = [preview_species(i) for i in ids]
    columns = min(4, len(ids))
    cell_w, cell_h = 420, 300
    sheet = Image.new("RGB", (columns*cell_w, 110+math.ceil(len(ids)/columns)*cell_h), (12, 20, 30))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 18), "2D ANATOMY / MOTION STUDIES", font=get_font(26, bold=True), fill=(228, 237, 244))
    draw.text((24, 61), "Family-level approximations. Rig ratios are not specimen measurements.", font=get_font(16), fill=(149, 171, 186))
    report = []
    for index, species in enumerate(species_list):
        x, y = (index % columns)*cell_w, 110+(index//columns)*cell_h
        frame = render_generative_frame(species, 45, 180)
        crop = frame.crop((110, 340, 970, 832)).resize((cell_w-12, 234), Image.Resampling.LANCZOS)
        sheet.paste(crop, (x+6, y+37))
        label = f"{species['animal_id']:03d} / {species['name']}"
        font = get_font(15, bold=True)
        while font.getlength(label) > cell_w-24:
            font = get_font(font.size-1, bold=True)
        draw.text((x+12, y+8), label, font=font, fill=(231, 239, 245))
        summary = anatomy_summary(species)
        draw.text((x+12, y+275), summary['body_plan'], font=get_font(13), fill=(131, 197, 191))
        report.append({"animal_id": species["animal_id"], "name": species["name"], **summary})
    path = output / "contact_sheet.jpg"
    sheet.save(path, quality=94)
    (output / "contact_sheet_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def encode_preview(species: dict, output: Path, duration: float) -> Path:
    """Stream frames with bounded memory and atomic output; no stale JPEG sequences."""
    total = timeline_frames(duration)
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("Install FFmpeg to encode videos; PNG previews do not need it")
    destination = output / f"{species['id']}_{species['render_mode']}.mp4"
    fd, temp_name = tempfile.mkstemp(prefix="preview_", suffix=".mp4", dir=output)
    os.close(fd)
    partial = Path(temp_name)
    command = [executable, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "pipe:0", "-an",
               "-c:v", "libx264", "-threads", "2", "-preset", "fast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(partial)]
    process = None
    try:
        with tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=errors)
            try:
                for frame_idx in range(total):
                    process.stdin.write(render_generative_frame(species, frame_idx, total).tobytes())
                process.stdin.close()
            except BrokenPipeError:
                process.stdin.close()
            status = process.wait(timeout=180)
            if status:
                errors.seek(0)
                raise RuntimeError("FFmpeg encoding failed: " + errors.read().decode(errors="replace")[-1500:])
        partial.replace(destination)
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        partial.unlink(missing_ok=True)
    return destination


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List matching catalogue IDs without rendering")
    parser.add_argument("--search", default="", help="Filter --list by name, class or morphology")
    parser.add_argument("--animal-id", type=int, default=0)
    parser.add_argument("--mode", choices=("surface", "overlay", "skeleton"), default="surface")
    parser.add_argument("--frame", type=int, default=45, help="Still image frame on a 6-second timeline (0..179)")
    parser.add_argument("--contact-sheet", action="store_true")
    parser.add_argument("--ids", default=",".join(map(str, DEFAULT_IDS)))
    parser.add_argument("--video", action="store_true", help="Also create a silent 1080x1920 MP4")
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--output-dir", help="Directory inside teacher-bot/outputs")
    args = parser.parse_args(argv)
    try:
        if args.list:
            query = args.search.casefold()
            for index, species in enumerate(load_encyclopedia()):
                fields = f"{species['name']} {species['class_type']} {species['morphology']}"
                if query in fields.casefold():
                    print(f"{index:03d}  {species['name']}  [{anatomy_summary(species)['body_plan']}]")
            return 0
        if not 0 <= args.frame < 180:
            raise ValueError("Still frame must be between 0 and 179")
        timeline_frames(args.duration)
        species = preview_species(args.animal_id, args.mode)
        ids = [int(value.strip()) for value in args.ids.split(",")]
        if args.contact_sheet:
            if not 1 <= len(ids) <= 48:
                raise ValueError("Contact sheets require 1 to 48 animal IDs")
            for animal_id in ids:
                get_species_for_id(animal_id)
        output = output_directory(args.output_dir)
        still = output / f"{species['id']}_{args.mode}.png"
        render_generative_frame(species, args.frame, 180).save(still)
        print(still)
        report = {"animal_id": args.animal_id, "name": species['name'], "mode": args.mode,
                  "offline": True, "uploaded": False, **anatomy_summary(species)}
        (output / f"{species['id']}_{args.mode}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        if args.contact_sheet:
            print(create_contact_sheet(ids, output))
        if args.video:
            print(encode_preview(species, output, args.duration))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, f"Preview error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
