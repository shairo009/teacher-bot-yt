"""
Real Visual Sketch & Draw Bot Generator
Pulls real reference photos from the web (Wikimedia / Wikipedia Open Archive),
extracts authentic contours & palettes, renders progressive 4-stage drawing timelapse,
synthesizes procedural ASMR pencil scratching & brush SFX, and uploads Full HD Shorts!
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.real_visual_draw_engine import fetch_web_reference, prepare_art_layers, render_real_draw_frame, WIDTH, HEIGHT, FPS
from src.real_sound_engine import generate_draw_audio

DATA_DIR = ROOT / "data"
TMP_DIR = ROOT / "tmp"
PROGRESS_FILE = DATA_DIR / "real_draw_progress.json"
HISTORY_FILE = DATA_DIR / "real_draw_history.json"
DEFAULT_DURATION = 20.0

SUBJECT_CATALOG = [
    "Bengal Tiger", "Indian Peafowl", "Snow Leopard", "Bald Eagle", "Great White Shark",
    "Giant Panda", "Red Fox", "Panther Chameleon", "King Cobra", "Polar Bear",
    "African Elephant", "Black Panther", "Orca", "Cheetah", "Arctic Wolf",
    "Koala", "Red Panda", "African Lion", "Giraffe", "Toucan",
    "Greater Flamingo", "Golden Eagle", "Jaguar", "Emperor Penguin", "Grizzly Bear",
    "Sea Otter", "Scarlet Macaw", "Chimpanzee", "Hippopotamus", "Fennec Fox",
    "Komodo Dragon", "Blue-Ringed Octopus", "Hummingbird", "Mandrill", "Caracal",
    "Platypus", "Barn Owl", "Siberian Husky", "Humpback Whale", "Meerkats",
    "Mantis Shrimp", "Dolphin", "Leatherback Sea Turtle", "Capybara", "Sloth",
    "Okapi", "Kangaroo", "Wolverine", "Pangolin", "Honey Badger"
]

def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def _encode_video(frames_dir: Path, output_path: Path, audio_path: Path | None = None) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to create the MP4")
    
    cmd = [
        ffmpeg, "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%04d.jpg"),
    ]
    if audio_path and audio_path.exists():
        cmd.extend([
            "-i", str(audio_path),
            "-c:a", "aac", "-b:a", "192k",
            "-shortest"
        ])
    cmd.extend([
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(output_path)
    ])
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError("ffmpeg failed: " + result.stderr[-1500:])

def _upload_to_youtube(video_path: Path, query: str, dry_run: bool) -> str | None:
    if dry_run:
        print("  [Dry run — skipping YouTube upload]")
        return None

    token_json = os.environ.get("TOKEN_JSON", "").lstrip("﻿").strip()
    client_json = os.environ.get("CLIENT_SECRETS_JSON", "").lstrip("﻿").strip()

    token_file = TMP_DIR / "token.json"
    client_file = TMP_DIR / "client_secrets.json"

    if token_json and client_json:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        token_file.write_text(token_json, encoding="utf-8")
        client_file.write_text(client_json, encoding="utf-8")
    elif not (token_file.exists() and client_file.exists()):
        print("  [No YouTube credentials found — skipping upload]")
        return None

    try:
        from src.uploader import YouTubeUploader
        uploader = YouTubeUploader(str(token_file), str(client_file))

        title = f"Drawing a Realistic {query} from Real Photo Reference 🎨✨ #Shorts #Art"[:100]
        description = f"Drawing and painting a realistic {query} step-by-step from Wikipedia Open Archive reference photo!\n\n#Art #Drawing #Painting #Shorts #Nature #Wildlife"
        tags = [
            "art", "drawing", "painting", "sketch", "time-lapse", "shorts",
            query.lower(), "artist", "creative", "satisfying", "asmr"
        ]


        print(f"Uploading to YouTube: {title}")
        video_id = uploader.upload(
            video_path=str(video_path),
            title=title,
            description=description,
            tags=tags,
            category_id="28",
            made_for_kids=False,
        )
        if video_id:
            print(f"✅ Successfully uploaded to YouTube: https://youtu.be/{video_id}")
            return video_id
        return None
    except Exception as exc:
        print(f"❌ YouTube upload error: {exc}")
        return None

def generate_real_draw(topic: str | None = None, duration: float = DEFAULT_DURATION, dry_run: bool = False) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    progress = _load_json(PROGRESS_FILE, {"current_idx": 0})
    current_idx = int(progress.get("current_idx", 0))
    
    if topic is None:
        query = SUBJECT_CATALOG[current_idx % len(SUBJECT_CATALOG)]
    else:
        query = topic

    print(f"\n🎨 [Real Draw Bot] Fetching reference & drawing #{current_idx}: {query}")
    raw_img, colors, hex_colors, extract = fetch_web_reference(query)

    art = prepare_art_layers(raw_img)

    subject_data = {
        "raw_img": raw_img,
        "art": art,
        "colors": colors,
        "hex_colors": hex_colors,
        "extract": extract
    }

    run_dir = TMP_DIR / f"real_draw_{current_idx:04d}"
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    total_frames = max(1, round(duration * FPS))
    print(f"Rendering {total_frames} Full HD (1080x1920) 4-stage drawing frames @ {FPS} FPS...")
    for number in range(total_frames):
        frame = render_real_draw_frame(query, subject_data, number, total_frames)
        frame.save(frames_dir / f"frame_{number:04d}.jpg", quality=95, optimize=True)

    audio_file = run_dir / "draw_audio.wav"
    print("Synthesizing ASMR graphite pencil scratching & brush swoosh SFX...")
    generate_draw_audio(audio_file, duration=duration, seed=current_idx)

    slug = query.lower().replace(' ', '_')
    output_file = run_dir / f"{slug}_draw_short.mp4"
    print("Encoding Full HD 1080x1920 video with FFmpeg...")
    _encode_video(frames_dir, output_file, audio_file)
    print(f"✅ Video created: {output_file}")

    video_id = None
    if not dry_run:
        video_id = _upload_to_youtube(output_file, query, dry_run)

    if not dry_run and topic is None:
        progress["current_idx"] = current_idx + 1
        PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")
        history = _load_json(HISTORY_FILE, [])
        history_entry = {
            "id": current_idx,
            "subject": query,
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
    parser = argparse.ArgumentParser(description="Generate Real Web Reference Drawing Timelapse Shorts")
    parser.add_argument("--topic", type=str, help="Specific subject to draw (e.g. 'Bald Eagle')")
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION, help="Video length in seconds (default: 20.0)")
    parser.add_argument("--dry-run", action="store_true", help="Create video without uploading or advancing rotation")
    args = parser.parse_args()

    try:
        generate_real_draw(args.topic, args.duration, args.dry_run)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()