"""Offline-only 2D anatomy previews. No uploader, research or publication state imports."""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from PIL import Image, ImageDraw
from src.anatomy_profiles import anatomy_summary, mammal_profile
from src.natural_anatomy_renderer import gait_parameters, mammal_pose
from src.generative_dragon_engine import (
    FPS, WIDTH, HEIGHT, MOTION_RATE, get_font, get_species_for_id, load_encyclopedia,
    render_generative_frame,
)

ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "outputs"
DEFAULT_IDS = [0, 1, 15, 17, 586, 547, 351, 280, 576, 450, 231, 403]


def output_directory(value: str | Path | None = None) -> Path:
    allowed = ROOT.resolve() / "outputs"
    path = (Path(value) if value else OUTPUT_ROOT / "anatomy_preview").resolve()
    if not path.is_relative_to(allowed):
        raise ValueError("Preview output must be inside teacher-bot/outputs; source and publication ledgers are protected")
    path.mkdir(parents=True, exist_ok=True)
    return path


def output_file(output: Path, name: str) -> Path:
    """Reject traversal and pre-existing file symlinks before writing previews."""
    if Path(name).name != name:
        raise ValueError("Preview filenames must not contain directories")
    directory = output_directory(output)
    path = directory / name
    if path.is_symlink() or path.is_dir() or path.resolve().parent != directory:
        raise ValueError("Preview output must not overwrite a symlink target")
    return path


@contextmanager
def atomic_output(output: Path, name: str):
    """Replace complete artifacts; never truncate existing files or hardlinks."""
    destination = output_file(output, name)
    fd, temporary = tempfile.mkstemp(prefix="artifact_", suffix=destination.suffix, dir=destination.parent)
    os.close(fd)
    partial = Path(temporary)
    try:
        yield partial
        # Recheck in case the destination changed while rendering/encoding.
        output_file(output, name)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)


def save_image(image: Image.Image, output: Path, name: str, **options) -> Path:
    with atomic_output(output, name) as partial:
        image.save(partial, **options)
    return output_file(output, name)


def save_report(report, output: Path, name: str) -> Path:
    with atomic_output(output, name) as partial:
        partial.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return output_file(output, name)


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
    path = save_image(sheet, output, "contact_sheet.jpg", quality=94)
    save_report(report, output, "contact_sheet_report.json")
    return path


def create_comparison(animal_id: int, frame_idx: int, output: Path) -> Path:
    """Aligned diagnostic views at one timestamp and one fixed camera scale."""
    modes = ("surface", "overlay", "skeleton")
    subjects = [preview_species(animal_id, mode) for mode in modes]
    sheet = Image.new("RGB", (1720, 490), (12, 20, 30))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 18), subjects[0]["name"] + " / LINKED 2D RIG", font=get_font(26, bold=True), fill=(231, 239, 245))
    draw.text((24, 60), f"Same pose and camera / frame {frame_idx} / family-level approximation, not a specimen reconstruction", font=get_font(16), fill=(151, 175, 187))
    for index, subject in enumerate(subjects):
        x = 10 + index*570
        draw.text((x+14, 108), modes[index].upper(), font=get_font(19, bold=True), fill=(135, 211, 203))
        image = render_generative_frame(subject, frame_idx, 180)
        crop = image.crop((110, 340, 970, 832)).resize((560, 320), Image.Resampling.LANCZOS)
        sheet.paste(crop, (x, 148))
    return save_image(sheet, output, f"{subjects[0]['id']}_comparison.jpg", quality=94)


def gait_report(species: dict) -> dict:
    """Numerical rig checks across a complete cycle, not biological validation."""
    if anatomy_summary(species)["body_plan"] != "mammal":
        raise ValueError("Gait diagnostics are currently implemented for mammals only")
    p = mammal_profile(species)
    stride, duty = gait_parameters(p)
    bone_error = height_error = contact_drift = 0.0
    previous = {}
    stance_samples = 0
    for step in range(121):
        travel = stride*step/120
        _, _, limbs = mammal_pose(species, travel/72, travel)
        for limb in limbs:
            points = limb["points"]
            bone_error = max(bone_error, *(abs(math.dist(a,b)-length)
                                         for a,b,length in zip(points,points[1:],limb["lengths"])))
            key = (limb["side"], limb["front"])
            if limb["planted"]:
                stance_samples += 1
                height_error = max(height_error, abs(points[-1][1]-p.legs))
                prev = previous.get(key)
                if prev and prev["planted"] and limb["phase"] > prev["phase"]:
                    contact_drift = max(contact_drift, abs(limb["contact_x"]-prev["contact_x"]))
            previous[key] = limb
    return {"animal_id": species["animal_id"], "name": species["name"],
            "gait": p.gait, "stride_rig_units": stride, "stance_fraction": duty,
            "cycle_seconds_at_preview_speed": stride/(72*MOTION_RATE), "numerical_samples": 121,
            "planted_limb_samples": stance_samples, "max_bone_length_error": bone_error,
            "max_planted_height_error": height_error, "max_stance_world_drift": contact_drift,
            "units": "procedural rig units, not centimeters",
            "offline": True, "uploaded": False, **anatomy_summary(species)}


def create_gait_sheet(animal_id: int, output: Path) -> Path:
    """Eight aligned overlay poses and stance/swing indicators over one stride."""
    species = preview_species(animal_id, "overlay")
    report = gait_report(species)
    cell_w, cell_h = 430, 332
    sheet = Image.new("RGB", (1720, 804), (12,20,30))
    draw = ImageDraw.Draw(sheet)
    title = species["name"] + " / ONE GAIT CYCLE"
    draw.text((24,18), title, font=get_font(25,bold=True), fill=(231,239,245))
    draw.text((24,57), "Same camera / shared skin, head, tail and limb rig / near and far sides are layered in 2D", font=get_font(16), fill=(154,179,192))
    draw.text((24,86), "Four limbs: F=front, H=hind; N=near, F=far. Green=stance, amber=swing. Overlap is expected in a lateral view.", font=get_font(15), fill=(154,179,192))
    cycle_frames = report["cycle_seconds_at_preview_speed"]*FPS
    report["poses"] = []
    for index in range(8):
        frame_idx = round(cycle_frames*index/7)
        time = frame_idx/FPS*MOTION_RATE
        _, _, limbs = mammal_pose(species,time)
        frame = render_generative_frame(species,frame_idx,max(180,math.ceil(cycle_frames)+1))
        x,y = (index%4)*cell_w,126+(index//4)*cell_h
        draw.text((x+12,y+3), f"{index+1:02} / {frame_idx/FPS:.2f}s / phase {time*72/report['stride_rig_units']:.2f}", font=get_font(16,bold=True), fill=(231,239,245))
        crop = frame.crop((110,340,970,832)).resize((418,239), Image.Resampling.LANCZOS)
        sheet.paste(crop,(x+6,y+34))
        statuses = []
        for offset,limb in enumerate(limbs):
            label = ("F" if limb["front"] else "H")+("N" if limb["side"]==1 else "F")
            color = (123,220,177) if limb["planted"] else (236,187,111)
            draw.rounded_rectangle((x+9+offset*105,y+285,x+109+offset*105,y+310),radius=4,outline=color)
            draw.text((x+15+offset*105,y+291),label+(" stance" if limb["planted"] else " swing"),font=get_font(12),fill=color)
            statuses.append({"limb": label, "planted": limb["planted"], "points": limb["points"], "lengths": limb["lengths"]})
        report["poses"].append({"frame":frame_idx,"time_seconds":frame_idx/FPS,"limbs":statuses})
    path = save_image(sheet,output,f"{species['id']}_gait.jpg",quality=94)
    save_report(report,output,f"{species['id']}_gait.json")
    return path


def encode_preview(species: dict, output: Path, duration: float) -> Path:
    """Stream frames with bounded memory and atomic output; no stale JPEG sequences."""
    total = timeline_frames(duration)
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("Install FFmpeg to encode videos; PNG previews do not need it")
    destination = output_file(output, f"{species['id']}_{species['render_mode']}.mp4")
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
            except BrokenPipeError as exc:
                raise RuntimeError("FFmpeg closed the stream before every frame was sent") from exc
            status = process.wait(timeout=180)
            if status:
                errors.seek(0)
                raise RuntimeError("FFmpeg encoding failed: " + errors.read().decode(errors="replace")[-1500:])
        output_file(output, destination.name)
        partial.replace(destination)
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdin and not process.stdin.closed:
                try:
                    process.stdin.close()
                except BrokenPipeError:
                    pass
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
    parser.add_argument("--comparison", action="store_true", help="Aligned mammal surface, overlay and skeleton sheet")
    parser.add_argument("--gait-sheet", action="store_true", help="Eight mammal poses across a full stride, with JSON rig checks")
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
        if args.comparison or args.gait_sheet:
            preview_species(args.animal_id, "skeleton")
        ids = [int(value.strip()) for value in args.ids.split(",")] if args.contact_sheet else []
        if args.contact_sheet:
            if not 1 <= len(ids) <= 48:
                raise ValueError("Contact sheets require 1 to 48 animal IDs")
            for animal_id in ids:
                get_species_for_id(animal_id)
        output = output_directory(args.output_dir)
        still = save_image(render_generative_frame(species, args.frame, 180), output, f"{species['id']}_{args.mode}.png")
        print(still)
        report = {"animal_id": args.animal_id, "name": species['name'], "mode": args.mode,
                  "offline": True, "uploaded": False, **anatomy_summary(species)}
        save_report(report, output, f"{species['id']}_{args.mode}.json")
        if args.contact_sheet:
            print(create_contact_sheet(ids, output))
        if args.comparison:
            print(create_comparison(args.animal_id, args.frame, output))
        if args.gait_sheet:
            print(create_gait_sheet(args.animal_id, output))
        if args.video:
            print(encode_preview(species, output, args.duration))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, f"Preview error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
