"""Post-render quality gate for vertical Shorts.
Checks container shape, streams, duration, frame health, and safe visual occupancy.
It intentionally fails closed: an uncertain video is not upload-worthy.
"""
from __future__ import annotations
import json, math, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageStat

W, H = 1080, 1920
# Product quality profile, not a claim that YouTube requires this resolution/audio.
MIN_DURATION = 1.0
MAX_DURATION = 180.0


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _probe(path: Path) -> dict:
    code, out, err = _run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path)
    ])
    if code:
        raise RuntimeError("ffprobe failed: " + err[-500:])
    return json.loads(out)


def audit_video(path: str | Path, report_path: str | Path | None = None, *,
                minimum_duration: float = MIN_DURATION, sample_count: int = 9) -> dict:
    if not math.isfinite(minimum_duration) or not 0 < minimum_duration <= MAX_DURATION:
        raise ValueError('minimum_duration must be positive, finite and at most 180 seconds')
    if type(sample_count) is not int or not 1 <= sample_count <= 30:
        raise ValueError('sample_count must be an integer from 1 to 30')
    path = Path(path)
    report = {"passed": False, "errors": [], "warnings": [], "metrics": {}}
    if not path.is_file() or path.stat().st_size < 1024:
        report["errors"].append("missing_or_tiny_file")
        return _finish(report, report_path)

    try:
        meta = _probe(path)
        streams = meta.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if not video:
            report["errors"].append("no_video_stream")
            return _finish(report, report_path)
        if not audio:
            report["errors"].append("no_audio_stream")
        w, h = int(video.get("width", 0)), int(video.get("height", 0))
        dur = float(video.get('duration') or meta.get("format", {}).get("duration", 0) or 0)
        if not math.isfinite(dur) or dur <= 0:
            raise ValueError('invalid video duration')
        fps_text = video.get("r_frame_rate", "0/1")
        n, d = (fps_text.split("/") + ["1"])[:2]
        fps = float(n) / float(d)
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError('invalid video frame rate')
        report["metrics"].update({"width": w, "height": h, "duration": round(dur, 3), "fps": round(fps, 3), "bytes": path.stat().st_size})
        if (w, h) != (W, H): report["errors"].append(f"wrong_canvas:{w}x{h}")
        if dur > MAX_DURATION: report['errors'].append(f'too_long:{dur:.3f}s')
        if video.get('sample_aspect_ratio') not in (None, 'N/A', '1:1'):
            report['errors'].append('non_square_pixels')
        if any(float(side.get('rotation', 0)) % 360 for side in video.get('side_data_list', [])):
            report['errors'].append('rotated_video')
        if audio and audio.get('duration'):
            audio_duration = float(audio['duration'])
            report['metrics']['audio_duration'] = audio_duration
            if not math.isfinite(audio_duration) or abs(audio_duration - dur) > .25:
                report['errors'].append('audio_video_duration_mismatch')
        if abs(fps - 30) > 0.5: report["warnings"].append(f"fps_not_30:{fps:.2f}")
        if dur < minimum_duration - min(.5, minimum_duration * .1): report["errors"].append(f"too_short:{dur:.2f}s")

        # Decode the entire file, not just samples; a damaged middle segment must fail.
        code, _, err = _run(['ffmpeg', '-v', 'error', '-xerror', '-threads', '2',
                             '-i', str(path), '-f', 'null', '-'])
        report['metrics']['full_decode_passed'] = code == 0
        if code:
            report['errors'].append('full_decode_failed')

        # Samples test near-black/blank frames and produce viewport hashes.
        with tempfile.TemporaryDirectory() as td:
            pattern = str(Path(td) / "f_%02d.jpg")
            sampling_fps = sample_count / max(dur, .01)
            code, _, err = _run(["ffmpeg", "-y", "-threads", "2", "-i", str(path),
                                 '-filter_threads', '1', "-vf", f"fps={sampling_fps},scale=270:480",
                                 "-frames:v", str(sample_count), '-threads', '2', pattern])
            if code:
                report["errors"].append("frame_sampling_failed")
            else:
                frames = sorted(Path(td).glob("f_*.jpg"))
                report["metrics"]["sampled_frames"] = len(frames)
                if len(frames) < min(5, sample_count): report["errors"].append("too_few_sampled_frames")
                dark = blank = 0
                visual_hashes = []
                from src.unique_animal_generation_skill import perceptual_hash
                for fp in frames:
                    with Image.open(fp) as source:
                        im = source.convert("RGB")
                    # Hash the decoded creature viewport, never the static poster text.
                    visual_hashes.append(perceptual_hash(im.crop((27, 71, 243, 222))))
                    stats = ImageStat.Stat(im)
                    mean = sum(stats.mean) / 3
                    if mean < 2.0: dark += 1
                    if max(stats.stddev) < 1.0: blank += 1
                report["metrics"]["near_black_frames"] = dark
                report["metrics"]["visual_hashes"] = visual_hashes
                if len(set(visual_hashes)) == 1:
                    report['warnings'].append('sampled_viewport_looks_static:editorial_review_needed')
                if dark: report["errors"].append(f"near_black_frames:{dark}")
                report['metrics']['blank_frames'] = blank
                if blank: report['errors'].append(f'blank_frames:{blank}')
    except Exception as exc:
        report["errors"].append("audit_exception:" + str(exc))
    return _finish(report, report_path)


def _finish(report, report_path):
    report["passed"] = not report["errors"]
    if report_path:
        p = Path(report_path); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
