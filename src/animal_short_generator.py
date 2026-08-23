"""
Procedural Animated Animal Shorts Generator
100% Code-Generated Animation — No static photos, No API keys required.
Renders smooth procedural vector wildlife animation and uploads directly to YouTube.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.procedural_animal_engine import SPECIES_CATALOG, render_animal_frame, WIDTH, HEIGHT, FPS

DATA_DIR = ROOT / "data"
TMP_DIR = ROOT / "tmp"
PROGRESS_FILE = DATA_DIR / "animal_progress.json"
HISTORY_FILE = DATA_DIR / "animal_history.json"
DEFAULT_DURATION = 8.8


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _encode_video(frames_dir: Path, output_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to create the MP4")
    result = subprocess.run([
        ffmpeg, "-y", "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%04d.jpg"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(output_path),
    ], text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError("ffmpeg failed: " + result.stderr[-1500:])


def _upload_to_youtube(video_path: Path, species: dict, dry_run: bool) -> str | None:
    if dry_run:
        print("  [Dry run — skipping YouTube upload]")
        return None

    token_json = os.environ.get("TOKEN_JSON", "").lstrip("\ufeff").strip()
    client_json = os.environ.get("CLIENT_SECRETS_JSON", "").lstrip("\ufeff").strip()

    token_file = TMP_DIR / "token.json"
    client_file = TMP_DIR / "client_secrets.json"

    if token_json and client_json:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        token_file.write_text(token_json, encoding="utf-8")
        client_file.write_text(client_json, encoding="utf-8")
    elif not (token_file.exists() and client_file.exists()):
        print("  [No YouTube credentials found in env/files — skipping upload]")
        return None

    try:
        from src.uploader import YouTubeUploader
        uploader = YouTubeUploader(str(token_file), str(client_file))

        name = species["name"]
        clean_tag = name.replace(" ", "")
        title = f"{name} Facts You Didn't Know! 🐾 #Shorts #Animals"[:100]

        facts_text = "\n".join(f"• {f}" for f in species.get("facts", []))
        description = (
            f"🐾 Quick Animated Facts about the {name}!\n\n"
            f"{facts_text}\n\n"
            f"Comment \"{name.upper()}\" if you love wildlife! 🦁\n"
            f"Subscribe for daily procedural animal animations! 🔔\n\n"
            f"#Shorts #Animals #{clean_tag} #Wildlife #Nature #AnimalFacts #Animation #DidYouKnow"
        )
        tags = [
            "shorts", "animals", "wildlife", "animal facts", "nature", "animation",
            name.lower(), f"{name.lower()} facts", "did you know", "cartoon animal"
        ] + species.get("tags", [])

        print(f"Uploading to YouTube: {title}")
        video_id = uploader.upload(
            video_path=str(video_path),
            title=title,
            description=description,
            tags=tags,
            category_id="15",  # Pets & Animals
            made_for_kids=False,
        )
        if video_id:
            print(f"✅ Successfully uploaded to YouTube: https://youtu.be/{video_id}")
            return video_id
        else:
            print("❌ Upload returned no video ID")
            return None
    except Exception as exc:
        print(f"❌ YouTube upload error: {exc}")
        return None


def generate(animal_id: int | None = None, duration: float = DEFAULT_DURATION, dry_run: bool = False) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    progress = _load_json(PROGRESS_FILE, {"current_id": 0})
    current_id = int(progress.get("current_id", 0)) if animal_id is None else animal_id
    index = current_id % len(SPECIES_CATALOG)
    species = SPECIES_CATALOG[index]

    print(f"\n🎨 [Procedural Engine] Creating Animated Short #{current_id}: {species['name']}")
    run_dir = TMP_DIR / f"animal_{current_id:04d}"
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    total_frames = max(1, round(duration * FPS))
    print(f"Rendering {total_frames} procedural animation frames @ {FPS} FPS...")
    for number in range(total_frames):
        frame = render_animal_frame(species, number, total_frames)
        frame.save(frames_dir / f"frame_{number:04d}.jpg", quality=93, optimize=True)

    output_file = run_dir / f"{species['id']}_procedural_short.mp4"
    print("Encoding video with FFmpeg...")
    _encode_video(frames_dir, output_file)
    print(f"✅ Video created: {output_file}")

    video_id = None
    if not dry_run:
        video_id = _upload_to_youtube(output_file, species, dry_run)

    # Advance rotation if not dry-run
    if not dry_run and animal_id is None:
        progress["current_id"] = current_id + 1
        PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")
        history = _load_json(HISTORY_FILE, [])
        history_entry = {
            "id": current_id,
            "animal": species["name"],
            "species_id": species["id"],
            "file": str(output_file.relative_to(ROOT)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if video_id:
            history_entry["video_id"] = video_id
            history_entry["uploaded"] = True
        history.append(history_entry)
        HISTORY_FILE.write_text(json.dumps(history[-500:], indent=2), encoding="utf-8")

    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 100% code-animated procedural animal Shorts")
    parser.add_argument("--animal-id", type=int, help="Force a specific animal index from catalog")
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION, help="Video length in seconds (default: 8.8)")
    parser.add_argument("--dry-run", action="store_true", help="Create video without uploading or advancing rotation")
    args = parser.parse_args()

    try:
        generate(args.animal_id, args.duration, args.dry_run)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
