"""
Realistic Generative Creature Interactive Cursor Generator
===========================================================
UPGRADED FLOW (v2.0):
  1. Research     — Internet pe animal ki real anatomy search karo
  2. No-Repeat    — Agar ye animal pehle upload ho chuka hai to skip karo
  3. Render       — Research ke real colors & proportions se video banao
  4. Upload       — YouTube pe upload karo
  5. Mark Used    — used_animals.json mein permanent mark karo

Features:
  - Resolution: 1080 x 1920 Full HD Vertical
  - Real anatomy colors from Wikipedia/DuckDuckGo
  - Every animal uploaded EXACTLY once (no-repeat guarantee)
  - Discrete IK Physics Simulation (Smooth real-life speed)
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

from src.generative_dragon_engine import get_species_for_id, render_generative_frame, WIDTH, HEIGHT, FPS
from src.sound_engine import generate_reel_audio
from src.animal_researcher import (
    research_animal,
    is_already_used,
    mark_used,
)

DATA_DIR = ROOT / "data"
TMP_DIR = ROOT / "tmp"
PROGRESS_FILE = DATA_DIR / "animal_progress.json"
HISTORY_FILE = DATA_DIR / "animal_history.json"
DEFAULT_DURATION = 58.0


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
        title = species.get("yt_title", f"Realistic Interactive {name} in JavaScript ✨ #Shorts")[:100]
        description = species.get("yt_desc", "Realistic Interactive JavaScript Canvas Animation Short!")

        # Add anatomy notes to description if available
        notes = species.get("anatomy_notes", "")
        if notes:
            description = f"{description}\n\n📖 About this animal:\n{notes[:300]}"

        tags = [
            "javascript", "web development", "creative coding", "coding", "shorts",
            "canvas", "frontend", "programming", name.lower(), "interactive cursor",
            "animal", "biology", "realistic animation",
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
        else:
            print("❌ Upload returned no video ID")
            return None
    except Exception as exc:
        print(f"❌ YouTube upload error: {exc}")
        return None


def _find_next_unused_id(start_id: int, max_search: int = 500) -> tuple[int, dict]:
    """
    start_id se shuru karke aage khojo — pehla animal jo:
      1. Encyclopedia mein hai
      2. used_animals.json mein NAHI hai
    Tuple return karta hai: (animal_id, species_dict)
    """
    from src.generative_dragon_engine import get_species_for_id

    # Load encyclopedia to know total count
    try:
        enc_path = ROOT / "data" / "animal_encyclopedia.json"
        encyclopedia = json.loads(enc_path.read_text(encoding="utf-8"))
        total = len(encyclopedia)
    except Exception:
        total = 1000  # safe fallback

    checked = 0
    current = start_id
    while checked < max_search:
        idx = current % total
        species = get_species_for_id(idx)
        animal_name = species["name"]

        if not is_already_used(animal_name):
            return current, species

        print(f"  ⏭ Skipping '{animal_name}' — already uploaded before.")
        current += 1
        checked += 1

    raise RuntimeError(
        f"Koi naya animal nahi mila {max_search} animals check karne ke baad. "
        "Nayi species encyclopedia mein add karo!"
    )


def generate(
    animal_id: int | None = None,
    duration: float = DEFAULT_DURATION,
    dry_run: bool = False,
    force_research: bool = True,
) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    progress = _load_json(PROGRESS_FILE, {"current_id": 0})
    start_id = int(progress.get("current_id", 0)) if animal_id is None else animal_id

    # ── STEP 1: Find next animal that hasn't been used yet ──
    if animal_id is None:
        print(f"\n🔎 Unused animal dhundh raha hoon (ID {start_id} se)...")
        current_id, base_species = _find_next_unused_id(start_id)
    else:
        current_id = animal_id
        base_species = get_species_for_id(current_id)
        if is_already_used(base_species["name"]) and not dry_run:
            print(f"⚠ WARNING: '{base_species['name']}' pehle upload ho chuka hai! (--dry-run mode mein chalao test ke liye)")

    animal_name = base_species["name"]
    scientific   = base_species.get("scientific", animal_name)

    print(f"\n⚡ [Research-First Engine] Animal #{current_id}: {animal_name} ({scientific})")

    # ── STEP 2: Internet se real anatomy research karo ──
    if force_research:
        research = research_animal(animal_name, scientific)
        print(f"\n📊 Research Summary:")
        print(f"   Class      : {research['class_type']}")
        print(f"   Accent RGB : {research['accent']}")
        print(f"   Fur colors : {research['body_colors']}")
        print(f"   Anatomy    : {research['anatomy_notes'][:100]}...")
    else:
        # Dry-run without internet: use encyclopedia data as-is
        research = {
            "class_type":    base_species.get("class_type", "quadruped"),
            "accent":        list(base_species.get("accent", [245, 158, 11])),
            "fur_dark":      [120, 60,  5],
            "fur_mid":       [190, 110, 20],
            "fur_gold":      [230, 160, 45],
            "fur_light":     [255, 210, 100],
            "fur_cream":     [255, 235, 170],
            "fur_highlight": [255, 248, 210],
            "anatomy_notes": "",
            "proportions":   {"body_width_scale": 1.0, "leg_length_scale": 1.0,
                               "head_size_scale": 1.0, "tail_wag": 0.65},
        }

    # ── STEP 3: Merge research into species dict ──
    # Research se mili real colors aur class_type override karti hain encyclopedia entry
    species = {**base_species}
    species["class_type"]    = research["class_type"]
    species["accent"]        = tuple(research["accent"])
    species["anatomy_notes"] = research.get("anatomy_notes", "")
    # Fur colors (used by renderer)
    species["fur_dark"]      = tuple(research.get("fur_dark",      [120, 60,  5]))
    species["fur_mid"]       = tuple(research.get("fur_mid",       [190, 110, 20]))
    species["fur_gold"]      = tuple(research.get("fur_gold",      [230, 160, 45]))
    species["fur_light"]     = tuple(research.get("fur_light",     [255, 210, 100]))
    species["fur_cream"]     = tuple(research.get("fur_cream",     [255, 235, 170]))
    species["fur_highlight"] = tuple(research.get("fur_highlight", [255, 248, 210]))
    species["proportions"]   = research.get("proportions", {})

    # ── STEP 4: Render frames ──
    run_dir = TMP_DIR / f"reel_{current_id:04d}"
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    total_frames = max(1, round(duration * FPS))
    print(f"\n🎬 Rendering {total_frames} Full HD (1080×1920) frames @ {FPS} FPS...")
    for number in range(total_frames):
        frame = render_generative_frame(species, number, total_frames)
        frame.save(frames_dir / f"frame_{number:04d}.jpg", quality=95, optimize=True)
        if number % 60 == 0:
            print(f"   Frame {number}/{total_frames} rendered...")

    # ── STEP 5: Generate audio ──
    audio_file = run_dir / "audio.wav"
    print("🔊 Synthesizing ASMR mechanical typing clicks & cursor SFX...")
    generate_reel_audio(audio_file, duration=duration, typing_events=int(duration * 0.7), seed=current_id)

    # ── STEP 6: Encode video ──
    output_file = run_dir / f"{species['id']}_short.mp4"
    print("📦 Encoding Full HD 1080×1920 video with FFmpeg...")
    _encode_video(frames_dir, output_file, audio_file)
    print(f"✅ Video created: {output_file}")

    # ── STEP 7: Upload to YouTube ──
    video_id = None
    if not dry_run:
        video_id = _upload_to_youtube(output_file, species, dry_run)

    # ── STEP 8: Mark animal as USED (no-repeat guarantee) ──
    if not dry_run:
        mark_used(animal_name)

    # ── STEP 9: Update progress & history ──
    if not dry_run and animal_id is None:
        progress["current_id"] = current_id + 1
        PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")

    history = _load_json(HISTORY_FILE, [])
    history_entry = {
        "id":           current_id,
        "species":      species["name"],
        "scientific":   species.get("scientific", species["name"]),
        "class_type":   species["class_type"],
        "accent":       list(species["accent"]),
        "anatomy_notes": species.get("anatomy_notes", "")[:200],
        "file":         str(output_file.relative_to(ROOT)),
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "uploaded":     video_id is not None,
        "dry_run":      dry_run,
    }
    if video_id:
        history_entry["video_id"] = video_id
        history_entry["youtube_url"] = f"https://youtu.be/{video_id}"

    history.append(history_entry)
    HISTORY_FILE.write_text(json.dumps(history[-500:], indent=2), encoding="utf-8")

    print(f"\n{'🚀' if video_id else '📁'} Done! Animal: {animal_name} | Used: {not dry_run}")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Research-First Realistic Animal Code-Reel Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/animal_short_generator.py                   # Next unused animal, auto research + upload
  python src/animal_short_generator.py --dry-run         # Test without upload or marking used
  python src/animal_short_generator.py --animal-id 5     # Force species index 5
  python src/animal_short_generator.py --no-research     # Skip web search (use stored data)
        """,
    )
    parser.add_argument("--animal-id",    type=int,   help="Force a specific species index from catalog")
    parser.add_argument("--duration",     type=float, default=DEFAULT_DURATION,
                        help=f"Video length in seconds (default: {DEFAULT_DURATION})")
    parser.add_argument("--dry-run",      action="store_true",
                        help="Create video but do NOT upload or mark as used")
    parser.add_argument("--no-research",  action="store_true",
                        help="Skip internet research (use stored encyclopedia data)")
    args = parser.parse_args()

    try:
        generate(
            animal_id=args.animal_id,
            duration=args.duration,
            dry_run=args.dry_run,
            force_research=not args.no_research,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
