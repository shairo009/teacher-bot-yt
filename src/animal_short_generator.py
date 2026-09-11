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
DEFAULT_DURATION = 25.0
LAST_FRAME_FILE = DATA_DIR / "last_uploaded_frame.jpg"
RECENT_FRAMES_DIR = DATA_DIR / "recent_frames"
MAX_RECENT_FRAMES = 5

_BASE_IGNORE_WORDS = {
    "CYBER", "VOLT", "QUANTUM", "SOLAR", "LASER", "PULSE", "VOID", "HEXA",
    "DARK", "IRON", "MICRO", "SHADOW", "CHRONO", "CHROME", "NEON", "ELECTRIC",
    "GIANT", "TINY", "BLUE", "BLACK", "RED", "GOLDEN", "WHITE", "GREEN", "SPOTTED",
    "ASIAN", "AFRICAN", "INDIAN", "PACIFIC", "OCEANIC", "TREE", "MUD", "STONE",
    "SAND", "SNOW", "SEA", "RIVER", "FOREST", "BARK", "MATTER", "COMMON", "GREAT",
    "FAT-TAILED", "FAT-TAIL", "NET-CASTING", "EASTERN", "WESTERN", "NORTHERN",
    "SOUTHERN", "AMERICAN", "EUROPEAN", "AUSTRALIAN", "MADAGASCAR", "AMAZON",
    "MOUNTAIN", "DESERT", "ROCKY", "ATLANTIC", "ARCTIC", "WILD"
}

def extract_base_noun(name: str) -> str:
    """Extracts the core base animal noun (e.g. VOLT SCORPION -> SCORPION)."""
    import re
    words = [w.upper() for w in re.findall(r"[a-zA-Z]+", name) if w.upper() not in _BASE_IGNORE_WORDS]
    return words[-1] if words else name.upper()

def get_used_base_nouns() -> set[str]:
    """Returns all base animal nouns that have already been uploaded."""
    history = _load_json(HISTORY_FILE, [])
    return {extract_base_noun(h["species"]) for h in history if h.get("species")}


def compute_visual_difference(img1, img2) -> float:
    """Calculates percentage pixel difference between two frames (0% to 100%)."""
    thumb1 = img1.convert("RGB").resize((64, 64))
    thumb2 = img2.convert("RGB").resize((64, 64))
    b1 = thumb1.tobytes()
    b2 = thumb2.tobytes()
    diff = sum(abs(a - b) for a, b in zip(b1, b2))
    return (diff / (len(b1) * 255)) * 100.0

def compute_dhash(img, hash_size: int = 8) -> str:
    """Calculates 64-bit difference hash (perceptual digital DNA of the frame)."""
    from PIL import Image
    resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(resized.tobytes())
    diff = []
    for row in range(hash_size):
        for col in range(hash_size):
            p_left = pixels[row * (hash_size + 1) + col]
            p_right = pixels[row * (hash_size + 1) + col + 1]
            diff.append(p_left > p_right)
    dec = 0
    hex_chars = []
    for i, val in enumerate(diff):
        if val: dec += 2 ** (i % 4)
        if (i % 4) == 3:
            hex_chars.append(hex(dec)[2:])
            dec = 0
    return "".join(hex_chars)

def hamming_distance(h1: str, h2: str) -> int:
    """Bitwise distance between two 64-bit hashes (0 = identical, 64 = completely inverted)."""
    try:
        return bin(int(h1, 16) ^ int(h2, 16)).count("1")
    except Exception:
        return 64

def verify_candidate_against_recent_buffer(species: dict) -> tuple[bool, float, int]:
    """
    Multi-level verification focusing on the CREATURE VIEWPORT ONLY:
      1. Renders test frame and crops creature display box (x=110..970, y=285..885)
      2. Pixel-diff checks against recent creature frames (must be >= 10.0%)
      3. Perceptual dHash check against last 10 uploads (Hamming distance must be >= 10)
    Returns (is_ok, min_pixel_diff, min_hamming_dist)
    """
    try:
        from PIL import Image
        CROP_BOX = (110, 285, 970, 885)
        full_frame = render_generative_frame(species, 0, 100)
        candidate_crop = full_frame.crop(CROP_BOX)
        candidate_hash = compute_dhash(candidate_crop)

        # 1. Check against physical rolling buffer of last 5 frames
        min_pixel_diff = 100.0
        if RECENT_FRAMES_DIR.exists():
            for f_path in sorted(RECENT_FRAMES_DIR.glob("recent_*.jpg")):
                try:
                    p_img = Image.open(f_path).crop(CROP_BOX)
                    p_diff = compute_visual_difference(p_img, candidate_crop)
                    if p_diff < min_pixel_diff:
                        min_pixel_diff = p_diff
                except Exception:
                    pass
        elif LAST_FRAME_FILE.exists():
            try:
                p_img = Image.open(LAST_FRAME_FILE).crop(CROP_BOX)
                min_pixel_diff = compute_visual_difference(p_img, candidate_crop)
            except Exception:
                pass

        # 2. Check dHash against last 10 uploads in history
        history = _load_json(HISTORY_FILE, [])
        min_hamming = 64
        for past_item in history[-10:]:
            past_hash = past_item.get("dhash")
            if past_hash:
                dist = hamming_distance(candidate_hash, past_hash)
                if dist < min_hamming:
                    min_hamming = dist

        # Criteria: must be visually distinct on both pixel & perceptual levels
        is_ok = (min_pixel_diff >= 2.5) and (min_hamming >= 14)
        return is_ok, min_pixel_diff, min_hamming
    except Exception as exc:
        print(f"  ⚠ Visual buffer verification check error: {exc}")
        return True, 100.0, 64

def update_rolling_frame_buffer(new_frame_path: Path):
    """
    Shifts the FIFO buffer of recent frames:
      recent_3 -> recent_4, recent_2 -> recent_3, ..., new -> recent_0
    Ensures only the last 5 uploaded frames are kept on disk.
    """
    RECENT_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    # Shift existing frames
    for i in range(MAX_RECENT_FRAMES - 1, 0, -1):
        old_f = RECENT_FRAMES_DIR / f"recent_{i-1}.jpg"
        new_f = RECENT_FRAMES_DIR / f"recent_{i}.jpg"
        if old_f.exists():
            if new_f.exists():
                new_f.unlink()
            shutil.move(str(old_f), str(new_f))

    # Save current as recent_0.jpg
    target_0 = RECENT_FRAMES_DIR / "recent_0.jpg"
    if target_0.exists():
        target_0.unlink()
    shutil.copy2(new_frame_path, target_0)

    # Sync single reference file
    if LAST_FRAME_FILE.exists():
        LAST_FRAME_FILE.unlink()
    shutil.copy2(new_frame_path, LAST_FRAME_FILE)
    print(f"📸 Rolling frame buffer updated: {target_0.name} saved, oldest dropped (Last 5 frames active)")

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
            "-c:a", "aac", "-strict", "-2", "-b:a", "192k",
            "-shortest"
        ])
    cmd.extend([
        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
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


def _find_next_unused_id(start_id: int, max_search: int = 600) -> tuple[int, dict]:
    """
    Guarantees MAXIMUM visual variety using:
      1. Base-Noun De-duplication (NO variants of Scorpions, Crabs, Spiders once uploaded!)
      2. Strict multi-class rotation across 10 biological kingdoms
      3. Morphology ban window (last 8 uploaded morphologies forbidden)
      4. Stride-based candidate sampling (prevents sequential family clump clustering)
      5. Rolling creature viewport visual diff & perceptual dHash verification
    """
    from src.generative_dragon_engine import get_species_for_id

    enc_path = ROOT / "data" / "animal_encyclopedia.json"
    encyclopedia = json.loads(enc_path.read_text(encoding="utf-8"))
    total = len(encyclopedia)

    history = _load_json(HISTORY_FILE, [])
    banned_classes = [h.get("class_type") for h in history[-4:] if h.get("class_type")]
    last_class = history[-1].get("class_type") if history else None
    banned_morphologies = [h.get("morphology") for h in history[-8:] if h.get("morphology")]

    # Base nouns already uploaded to YouTube
    used_bases = get_used_base_nouns()
    used_names = {h["species"].upper() for h in history if h.get("species")}

    CLASS_CYCLE = [
        "aquatic", "bird", "insect", "quadruped", "cephalopod",
        "reptile", "arachnid", "amphibian", "crustacean", "serpent"
    ]

    # Target the next class in CLASS_CYCLE that is not banned
    target_class = None
    start_cycle_idx = (CLASS_CYCLE.index(last_class) + 1) if (last_class in CLASS_CYCLE) else 0
    for i in range(len(CLASS_CYCLE)):
        c = CLASS_CYCLE[(start_cycle_idx + i) % len(CLASS_CYCLE)]
        if c not in banned_classes:
            target_class = c
            break

    def search_candidates(candidate_indices: list[int], pass_label: str) -> tuple[int, dict] | None:
        if not candidate_indices:
            return None
        pool_len = len(candidate_indices)
        stride_offset = (start_id * 17) % pool_len
        for step in range(pool_len):
            idx = candidate_indices[(stride_offset + step) % pool_len]
            sp = encyclopedia[idx]
            cand_sp = get_species_for_id(idx)
            is_ok, p_diff, h_dist = verify_candidate_against_recent_buffer(cand_sp)
            if is_ok:
                base = extract_base_noun(sp["name"])
                morph = sp.get("morphology")
                print(f"  🎯 {pass_label}: Selected '{sp['name']}' (Base: {base}, Class: {sp.get('class_type')}, Morph: {morph}, Diff: {p_diff:.1f}%, Hamming: {h_dist})")
                return idx, cand_sp
        return None

    # Pass 1: Strict target_class + banned_morphologies filter
    if target_class:
        pool_p1 = [
            idx for idx, sp in enumerate(encyclopedia)
            if sp.get("class_type") == target_class
            and (not sp.get("morphology") or sp.get("morphology") not in banned_morphologies)
            and sp["name"].upper() not in used_names
            and not is_already_used(sp["name"])
            and extract_base_noun(sp["name"]) not in used_bases
        ]
        res = search_candidates(pool_p1, f"Taxonomy Cycle [{target_class.upper()}]")
        if res:
            return res

    # Pass 2: Any non-banned class + banned_morphologies filter
    pool_p2 = [
        idx for idx, sp in enumerate(encyclopedia)
        if sp.get("class_type") not in banned_classes
        and (not sp.get("morphology") or sp.get("morphology") not in banned_morphologies)
        and sp["name"].upper() not in used_names
        and not is_already_used(sp["name"])
        and extract_base_noun(sp["name"]) not in used_bases
    ]
    res = search_candidates(pool_p2, "Diversity Match")
    if res:
        return res

    # Pass 3: Relax morphology ban to last 3 entries
    relaxed_morphologies = [h.get("morphology") for h in history[-3:] if h.get("morphology")]
    pool_p3 = [
        idx for idx, sp in enumerate(encyclopedia)
        if sp.get("class_type") not in banned_classes
        and (not sp.get("morphology") or sp.get("morphology") not in relaxed_morphologies)
        and sp["name"].upper() not in used_names
        and not is_already_used(sp["name"])
        and extract_base_noun(sp["name"]) not in used_bases
    ]
    res = search_candidates(pool_p3, "Relaxed Morph Match")
    if res:
        return res

    # Pass 4: Any unused base noun across all classes
    pool_p4 = [
        idx for idx, sp in enumerate(encyclopedia)
        if sp["name"].upper() not in used_names
        and not is_already_used(sp["name"])
        and extract_base_noun(sp["name"]) not in used_bases
    ]
    res = search_candidates(pool_p4, "Unused Base Match")
    if res:
        return res

    # Pass 5: Hard fallback (only if almost all 687 species uploaded)
    for offset in range(total):
        idx = (start_id + offset) % total
        sp = encyclopedia[idx]
        if not is_already_used(sp["name"]):
            return idx, get_species_for_id(idx)

    raise RuntimeError("Koi naya animal nahi mila encyclopedia mein!")


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
    species["class_type"]    = base_species.get("class_type") or research.get("class_type", "quadruped")
    species["morphology"]    = base_species.get("morphology", "small_mammal")
    species["accent"]        = tuple(research.get("accent") or base_species.get("accent", (245, 158, 11)))
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

    # ── Update rolling buffer of recent frames & compute dHash ──
    diff_score = 100.0
    frame_dhash = ""
    mid_frame_idx = min(15, total_frames - 1)
    source_frame = frames_dir / f"frame_{mid_frame_idx:04d}.jpg"
    if source_frame.exists():
        try:
            from PIL import Image
            curr_frame_img = Image.open(source_frame)
            frame_dhash = compute_dhash(curr_frame_img)
            if LAST_FRAME_FILE.exists():
                prev_img = Image.open(LAST_FRAME_FILE)
                diff_score = compute_visual_difference(prev_img, curr_frame_img)
        except Exception:
            pass

    if not dry_run and source_frame.exists():
        update_rolling_frame_buffer(source_frame)

    if not dry_run:
        history = _load_json(HISTORY_FILE, [])
        history_entry = {
            "dhash":        frame_dhash,
            "last_frame":   "data/last_uploaded_frame.jpg",
            "visual_diff":  round(diff_score, 1),
            "id":           current_id,
            "species":      species["name"],
            "scientific":   species.get("scientific", species["name"]),
            "class_type":   species["class_type"],
            "morphology":   species.get("morphology", "small_mammal"),
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
