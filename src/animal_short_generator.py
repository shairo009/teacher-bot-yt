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
import math
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
VIEWPORT_BOX = (110, 285, 970, 885)
HASH_SCOPE = "viewport-v2"
MIN_PIXEL_DIFF = 20.0
MIN_HAMMING = 11

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
    bases = {extract_base_noun(h["species"]) for h in history if h.get("species")}
    from src.animal_researcher import _load_used
    bases.update(extract_base_noun(name.replace("_", " ")) for name in _load_used())
    return bases


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
    import re
    if any(not isinstance(h, str) or not re.fullmatch(r"[0-9a-fA-F]{16}", h)
           for h in (h1, h2)):
        return 0  # Malformed or wrong-width hashes must never count as novel.
    return (int(h1, 16) ^ int(h2, 16)).bit_count()

def verify_candidate_against_recent_buffer(species: dict) -> tuple[bool, float, int]:
    """
    Multi-level verification focusing on the CREATURE VIEWPORT ONLY:
      1. Renders test frame and crops creature display box (x=110..970, y=285..885)
      2. Mean pixel-difference must be >= 20% (strict repository policy).
      3. Viewport dHash Hamming distance must be > 10; old full-frame hashes are ignored.
    Returns (is_ok, min_pixel_diff, min_hamming_dist)
    """
    try:
        from PIL import Image
        CROP_BOX = VIEWPORT_BOX
        full_frame = render_generative_frame(species, 0, 100)
        candidate_crop = full_frame.crop(CROP_BOX)
        candidate_hash = compute_dhash(candidate_crop)

        # 1. Check against physical rolling buffer of last 5 frames
        min_pixel_diff = 100.0
        if RECENT_FRAMES_DIR.exists():
            for f_path in sorted(RECENT_FRAMES_DIR.glob("recent_*.jpg")):
                try:
                    with Image.open(f_path) as reference:
                        p_img = reference.crop(CROP_BOX)
                    p_diff = compute_visual_difference(p_img, candidate_crop)
                    if p_diff < min_pixel_diff:
                        min_pixel_diff = p_diff
                except Exception as exc:
                    raise RuntimeError(f"Unreadable reference frame: {f_path}") from exc
        if not list(RECENT_FRAMES_DIR.glob("recent_*.jpg")) and LAST_FRAME_FILE.exists():
            try:
                with Image.open(LAST_FRAME_FILE) as reference:
                    p_img = reference.crop(CROP_BOX)
                min_pixel_diff = compute_visual_difference(p_img, candidate_crop)
            except Exception as exc:
                raise RuntimeError("Unreadable last uploaded frame") from exc

        # 2. Check dHash against last 10 uploads in history
        history = _load_json(HISTORY_FILE, [])
        min_hamming = 64
        reference_paths = sorted(RECENT_FRAMES_DIR.glob("recent_*.jpg"))
        if not reference_paths and LAST_FRAME_FILE.exists():
            reference_paths = [LAST_FRAME_FILE]
        for reference_path in reference_paths:
            with Image.open(reference_path) as reference:
                min_hamming = min(min_hamming, hamming_distance(
                    candidate_hash, compute_dhash(reference.crop(CROP_BOX))))
        for past_item in history[-10:]:
            past_hash = past_item.get("dhash")
            if past_hash and past_item.get("dhash_scope") == HASH_SCOPE:
                dist = hamming_distance(candidate_hash, past_hash)
                if dist < min_hamming:
                    min_hamming = dist

        # Criteria: must be visually distinct on both pixel & perceptual levels
        is_ok = (min_pixel_diff >= MIN_PIXEL_DIFF) and (min_hamming >= MIN_HAMMING)
        return is_ok, min_pixel_diff, min_hamming
    except Exception as exc:
        print(f"  ⚠ Visual buffer verification check error: {exc}")
        return False, 0.0, 0

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
    """Missing state is a first run; unreadable/malformed state is NOT empty."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read state {path.name}; restore a valid backup before retrying") from exc
    valid = isinstance(value, type(default))
    if path == HISTORY_FILE:
        valid = valid and all(isinstance(item, dict) and
                              isinstance(item.get("species", ""), str) for item in value)
    if path == PROGRESS_FILE:
        valid = valid and type(value.get("current_id")) is int and value["current_id"] >= 0
    if not valid:
        raise RuntimeError(f"Invalid state structure in {path.name}; restore a valid backup before retrying")
    return value


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
        "-c:v", "libx264", "-threads", "2", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(output_path)
    ])
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError("ffmpeg failed: " + result.stderr[-1500:])


class UploadUnconfirmedError(RuntimeError):
    """The remote outcome is unknown; retain publishing intent and never retry."""


def _has_upload_credentials() -> bool:
    return bool((os.environ.get('TOKEN_JSON', '').strip() and
                 os.environ.get('CLIENT_SECRETS_JSON', '').strip()) or
                ((TMP_DIR / 'token.json').is_file() and (TMP_DIR / 'client_secrets.json').is_file()))


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
        title = species.get("yt_title", f"{name} | Procedural Python Animation #Shorts")[:100]
        description = species.get("yt_desc", "Offline procedural animal animation rendered in Python.")

        # Add anatomy notes to description if available
        notes = species.get("anatomy_notes", "")
        if notes:
            description = f"{description}\n\n📖 About this animal:\n{notes[:300]}"

        tags = species.get("yt_tags", [
            "python", "creative coding", "procedural animation", "shorts",
            "pillow", "programming", name.lower(), "animal",
        ])

        print(f"Uploading to YouTube: {title}")
        video_id = uploader.upload(
            video_path=str(video_path),
            title=title,
            description=description,
            tags=tags,
            category_id="28",
            made_for_kids=False,
            privacy_status="public",
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


def _find_next_unused_id(start_id: int, max_search: int = 600,
                         renderer: str = "auto", render_quality: str = "standard") -> tuple[int, dict]:
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

    examined: set[int] = set()

    def search_candidates(candidate_indices: list[int], pass_label: str) -> tuple[int, dict] | None:
        if not candidate_indices:
            return None
        pool_len = len(candidate_indices)
        stride_offset = (start_id * 17) % pool_len
        for step in range(pool_len):
            idx = candidate_indices[(stride_offset + step) % pool_len]
            if idx in examined or len(examined) >= max_search:
                continue
            examined.add(idx)
            sp = encyclopedia[idx]
            cand_sp = get_species_for_id(idx)
            from src.animal_3d_renderer import supports_species
            if renderer == "3d" and not supports_species(cand_sp):
                continue
            cand_sp["renderer"] = renderer
            cand_sp["render_quality"] = render_quality
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

    # Never bypass duplicate or visual guards to manufacture a successful run.
    raise RuntimeError("No unused animal passed the renderer and visual checks. "
                       "Inspect reference frames or preview an explicit ID with --dry-run; "
                       "do not delete upload history to bypass this guard.")


def generate(
    animal_id: int | None = None,
    duration: float = DEFAULT_DURATION,
    dry_run: bool = False,
    force_research: bool = True,
    renderer: str = 'auto',
    render_quality: str = 'standard',
    history_dir: Path | None = None,
    similarity_threshold: float | None = None,
    max_retries: int | None = None,
) -> Path:
    from src.unique_animal_generation_skill import (HistoryStore, UniqueAnimalGenerationSkill,
                                                    file_lock)
    production = DATA_DIR.resolve()
    history = Path(history_dir or (TMP_DIR / 'unique-preview-history' if dry_run else DATA_DIR)).resolve()
    if dry_run and (history.is_relative_to(production) or production.is_relative_to(history)):
        raise ValueError('Preview history must be isolated from production data')
    if not dry_run and history != production:
        raise ValueError('Production cannot override its permanent history directory')
    store = HistoryStore(history)
    skill = UniqueAnimalGenerationSkill(store, similarity_threshold, max_retries)
    # Hold the lock through selection, upload and legacy registry updates. Journal
    # transactions use a separate lock; local processes cannot publish the same base.
    with file_lock(history / 'generation.lock'):
        return _generate_with_skill(animal_id, duration, dry_run, force_research and not dry_run,
                                    renderer, render_quality, skill)


def _generate_with_skill(animal_id, duration, dry_run, force_research, renderer, render_quality, skill):
    from src.unique_animal_generation_skill import DiversityError
    errors = []
    # A failed completed-output check causes a NEW proposal, never a forced publish.
    budget = skill.max_retries
    while budget > 0:
        skill.max_retries = budget
        skill.attempts_used = 0
        try:
            return _generate_attempt(animal_id, duration, dry_run, force_research, renderer,
                                     render_quality, skill)
        except DiversityError as exc:
            errors.append(str(exc))
            if not skill.attempts_used:  # Planner consumed the remaining budget.
                break
            budget -= skill.attempts_used
    raise DiversityError('Generation retries exhausted; nothing published: ' + '; '.join(errors[-3:]))


def _generate_attempt(
    animal_id: int | None = None,
    duration: float = DEFAULT_DURATION,
    dry_run: bool = False,
    force_research: bool = True,
    renderer: str = "auto",
    render_quality: str = "standard",
    skill=None,
) -> Path:
    if not math.isfinite(duration) or not 0 < duration <= 180:
        raise ValueError("duration must be finite, greater than 0 and at most 180 seconds")
    if renderer not in {"auto", "2d", "3d"}:
        raise ValueError("renderer must be auto, 2d or 3d")
    if render_quality not in {"draft", "standard", "high"}:
        raise ValueError("render_quality must be draft, standard or high")
    if animal_id is not None:
        catalog = _load_json(ROOT / "data" / "animal_encyclopedia.json", [])
        if type(animal_id) is not int or not 0 <= animal_id < len(catalog):
            raise ValueError(f"animal-id must be between 0 and {len(catalog) - 1}")
    DATA_DIR.mkdir(exist_ok=True)
    progress = _load_json(PROGRESS_FILE, {"current_id": 0})

    from src.unique_animal_generation_skill import (fingerprint, file_fingerprint,
        DiversityError, checkpoint_git, atomic_json)
    from src.animal_3d_renderer import configure_species, supports_species
    from src.quality_auditor import audit_video

    # Retain the permanent legacy base-noun ban; the new ledger adds completed
    # generations, not just uploads. Never use simulation state for publishing.
    old_history = _load_json(HISTORY_FILE, [])
    used_bases = get_used_base_nouns()
    ledger = skill.store.records()
    if not dry_run:
        used_bases.update(extract_base_noun(r['plan']['species']) for r in ledger if r['status'] != 'failed')
    catalog = _load_json(ROOT / 'data' / 'animal_encyclopedia.json', [])
    ids = [animal_id] if animal_id is not None else list(range(len(catalog)))
    candidates = []
    for idx in ids:
        candidate = get_species_for_id(idx)
        if not dry_run and (is_already_used(candidate['name']) or extract_base_noun(candidate['name']) in used_bases):
            if animal_id is not None:
                raise RuntimeError(f"{candidate['name']} is already used; use --dry-run to preview")
            continue
        if renderer == '3d' and not supports_species(candidate):
            continue
        candidate.update(renderer=renderer, render_quality=render_quality, animal_id=idx)
        candidates.append(configure_species(candidate))
    # Prefer the next taxonomy class, then unused recent morphologies. These
    # preferences never override the permanent base-noun and visual barriers.
    cycle = ['aquatic', 'insect', 'quadruped', 'cephalopod', 'reptile',
             'arachnid', 'serpent', 'crustacean', 'bird', 'amphibian']
    recent_classes = {h.get('class_type') for h in old_history[-4:]}
    recent_morphologies = {h.get('morphology') for h in old_history[-8:]}
    last_class = old_history[-1].get('class_type') if old_history else None
    start = (cycle.index(last_class) + 1) % len(cycle) if last_class in cycle else 0
    target = next((cycle[(start + i) % len(cycle)] for i in range(len(cycle))
                   if cycle[(start + i) % len(cycle)] not in recent_classes), cycle[start])
    for candidate in candidates:
        candidate['rotation_penalty'] = (int(candidate.get('class_type') != target)
            + 2 * int(candidate.get('class_type') in recent_classes)
            + int(candidate.get('morphology') in recent_morphologies))

    prepared = {}
    def validate_candidate(candidate):
        species = dict(candidate)
        if force_research:
            research = research_animal(species['name'], species.get('scientific', species['name']))
            for key in ('accent', 'fur_dark', 'fur_mid', 'fur_gold', 'fur_light', 'fur_cream', 'fur_highlight',
                        'anatomy_notes', 'proportions'):
                if key in research:
                    species[key] = research[key]
        # Preview exemption is the pre-existing explicit dry-run behavior only;
        # permanent skill checks still apply within the isolated preview history.
        if not dry_run and not verify_candidate_against_recent_buffer(species)[0]:
            return False
        prepared[fingerprint(species['unique_plan'])] = species
        return True

    if not dry_run and not _has_upload_credentials():
        raise RuntimeError('YouTube credentials missing; use --dry-run for a local preview')
    _, plan = skill.select(candidates, validate_candidate)
    species = prepared[fingerprint(plan)]
    current_id = species['animal_id']
    animal_name = species['name']
    identifier = skill.store.reserve(plan, skill.threshold)
    if not dry_run:
        checkpoint_git(ROOT, skill.store)
    print(f"Unique plan {fingerprint(plan)[:12]}: {animal_name} / {plan['action']} / {plan['environment']}")

    try:
        # ── STEP 4: Render frames ──
        run_dir = TMP_DIR / f"reel_{current_id:04d}_{identifier}"
        frames_dir = run_dir / "frames"
        # A new directory per reservation preserves earlier artifacts and prevents
        # concurrent previews overwriting frames, reports or completed MP4s.
        frames_dir.mkdir(parents=True, exist_ok=False)

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
        generate_reel_audio(audio_file, duration=duration, typing_events=int(duration * 0.7), seed=plan['seed'])

        # ── STEP 6: Encode video ──
        output_file = run_dir / f"{species['id']}_short.mp4"
        print("📦 Encoding Full HD 1080×1920 video with FFmpeg...")
        _encode_video(frames_dir, output_file, audio_file)
        print(f"✅ Video created: {output_file}")

        # Validate the actual encoded output before declaring this generation completed.
        report = audit_video(output_file, run_dir / 'quality_report.json', minimum_duration=duration,
                             sample_count=3)
        if not report['passed']:
            skill.store.transition(identifier, 'failed', reason='quality audit: ' + str(report['errors']))
            raise DiversityError('Quality audit failed: ' + str(report['errors']))
        # These hashes come from ffmpeg-decoded MP4 frames, not unencoded source images.
        hashes = report.get('metrics', {}).get('visual_hashes', [])
        report_output_hash = file_fingerprint(output_file)
        try:
            skill.store.transition(identifier, 'completed', threshold=skill.threshold, validated=True,
                                   output_hash=report_output_hash, visual_hashes=hashes,
                                   file=str(output_file.relative_to(ROOT)))
        except DiversityError as exc:
            skill.store.transition(identifier, 'failed', reason=str(exc))
            raise
        atomic_json(run_dir / 'generation_manifest.json', {
            'generation_id': identifier, 'plan': plan, 'fingerprint': fingerprint(plan),
            'output_hash': report_output_hash, 'visual_hashes': hashes,
            'preview_only': dry_run, 'audit': report})

    except Exception as exc:
        record = next(r for r in skill.store.records() if r['id'] == identifier)
        if record['status'] == 'reserved':
            skill.store.transition(identifier, 'failed', reason='generation failed: ' + type(exc).__name__)
        if not dry_run:
            checkpoint_git(ROOT, skill.store)
        raise

    # An upload timeout may mean the remote accepted the video. Persist intent
    # BEFORE calling YouTube and never automatically retry that content.
    video_id = None
    if not dry_run:
        skill.store.transition(identifier, 'publishing')
        checkpoint_git(ROOT, skill.store)
        # Upload only the bytes that passed audit, including after a slow git
        # checkpoint. A changed/missing artifact retains its publishing barrier.
        if file_fingerprint(output_file) != report_output_hash:
            raise RuntimeError('Audited video changed before upload; publishing blocked')
        video_id = _upload_to_youtube(output_file, species, dry_run)
        if not isinstance(video_id, str) or not video_id.strip():
            raise UploadUnconfirmedError(
                'YouTube upload is unconfirmed; publishing intent retained. '
                'Check the channel manually before any recovery; do not retry this animal.')
        if video_id:
            skill.store.transition(identifier, 'published', video_id=video_id)
            checkpoint_git(ROOT, skill.store)

    # Legacy uploaded registry only advances on confirmation. The new ledger
    # retains completed/uncertain work so a timeout can never trigger duplicate upload.
    uploaded = bool(video_id) and not dry_run
    # ── STEP 8: Mark animal as USED only after confirmed upload ──
    if uploaded:
        mark_used(animal_name)

    # ── STEP 9: Update progress & history ──
    if uploaded and animal_id is None:
        progress["current_id"] = current_id + 1
        atomic_json(PROGRESS_FILE, progress)

    # ── Update rolling buffer of recent frames & compute dHash ──
    diff_score = 100.0
    frame_dhash = ""
    mid_frame_idx = min(15, total_frames - 1)
    source_frame = frames_dir / f"frame_{mid_frame_idx:04d}.jpg"
    if source_frame.exists():
        try:
            from PIL import Image
            with Image.open(source_frame) as source:
                curr_frame_img = source.crop(VIEWPORT_BOX)
            frame_dhash = compute_dhash(curr_frame_img)
            if LAST_FRAME_FILE.exists():
                with Image.open(LAST_FRAME_FILE) as previous:
                    prev_img = previous.crop(VIEWPORT_BOX)
                diff_score = compute_visual_difference(prev_img, curr_frame_img)
        except Exception:
            pass

    if uploaded and source_frame.exists():
        update_rolling_frame_buffer(source_frame)

    if uploaded:
        history = _load_json(HISTORY_FILE, [])
        history_entry = {
            "generation_id": identifier,
            "fingerprint": fingerprint(plan),
            "generation_plan": plan,
            "dhash":        frame_dhash,
            "dhash_scope":  HASH_SCOPE,
            "renderer":     species["resolved_renderer"],
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
        atomic_json(HISTORY_FILE, history)

    print(f"\n{'🚀' if video_id else '📁'} Done! Animal: {animal_name} | Used: {uploaded}")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Procedural Animal Shorts: dedicated and catalog-morphology 3D rigs plus legacy 2D",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/animal_short_generator.py --dry-run --no-research --animal-id 1 --renderer 3d --duration 3
  python src/animal_short_generator.py --dry-run         # Isolated preview; no research or upload
  python src/animal_short_generator.py                   # PRODUCTION: attempts research + upload
  python src/animal_short_generator.py --no-research     # PRODUCTION: skips research, still uploads
        """,
    )
    parser.add_argument("--animal-id",    type=int,   help="Select a catalogue index (production duplicate bans still apply)")
    parser.add_argument("--duration",     type=float, default=DEFAULT_DURATION,
                        help=f"Video length in seconds (default: {DEFAULT_DURATION})")
    parser.add_argument("--dry-run",      action="store_true",
                        help="Create video but do NOT upload or mark as used")
    parser.add_argument("--no-research",  action="store_true",
                        help="Skip internet research (use stored encyclopedia data)")
    parser.add_argument("--renderer", choices=["auto", "2d", "3d"], default="auto",
                        help="auto: dedicated/catalog morphology rigs use 3D; 2d: legacy; 3d: require supported metadata")
    parser.add_argument("--quality", choices=["draft", "standard", "high"], default="standard",
                        help="3D internal resolution; final video remains 1080x1920")
    parser.add_argument('--history-dir', type=Path, help='Isolated persistent preview history (dry-run only)')
    parser.add_argument('--similarity-threshold', type=float, default=None)
    parser.add_argument('--max-unique-retries', type=int, default=None)
    args = parser.parse_args()

    try:
        generate(
            animal_id=args.animal_id,
            duration=args.duration,
            dry_run=args.dry_run,
            force_research=not args.no_research,
            renderer=args.renderer,
            render_quality=args.quality,
            history_dir=args.history_dir,
            similarity_threshold=args.similarity_threshold,
            max_retries=args.max_unique_retries,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
