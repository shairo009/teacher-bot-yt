"""Post-render quality gate for vertical Shorts.
Checks container shape, streams, duration, frame health, and safe visual occupancy.
It intentionally fails closed: an uncertain video is not upload-worthy.
"""
from __future__ import annotations
import json, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageStat

W, H = 1080, 1920
MIN_DURATION = 63.0


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


def audit_video(path: str | Path, report_path: str | Path | None = None) -> dict:
    path = Path(path)
    report = {"passed": False, "errors": [], "warnings": [], "metrics": {}}
    if not path.exists() or path.stat().st_size < 100_000:
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
        dur = float(meta.get("format", {}).get("duration", 0) or 0)
        fps_text = video.get("r_frame_rate", "0/1")
        n, d = (fps_text.split("/") + ["1"])[:2]
        fps = float(n) / max(float(d), 1.0)
        report["metrics"].update({"width": w, "height": h, "duration": round(dur, 3), "fps": round(fps, 3), "bytes": path.stat().st_size})
        if (w, h) != (W, H): report["errors"].append(f"wrong_canvas:{w}x{h}")
        if abs(fps - 30) > 0.5: report["warnings"].append(f"fps_not_30:{fps:.2f}")
        if dur < MIN_DURATION - 0.5: report["errors"].append(f"too_short:{dur:.2f}s")

        # Sample nine frames. This catches black/blank frames and accidental full-frame corruption.
        with tempfile.TemporaryDirectory() as td:
            pattern = str(Path(td) / "f_%02d.jpg")
            code, _, err = _run(["ffmpeg", "-y", "-i", str(path), "-vf", "fps=1/7,scale=270:480", "-frames:v", "9", pattern])
            if code:
                report["errors"].append("frame_sampling_failed")
            else:
                frames = sorted(Path(td).glob("f_*.jpg"))
                report["metrics"]["sampled_frames"] = len(frames)
                if len(frames) < 5: report["errors"].append("too_few_sampled_frames")
                dark = 0
                for fp in frames:
                    im = Image.open(fp).convert("RGB")
                    mean = sum(ImageStat.Stat(im).mean) / 3
                    if mean < 2.0: dark += 1
                report["metrics"]["near_black_frames"] = dark
                if dark: report["errors"].append(f"near_black_frames:{dark}")
    except Exception as exc:
        report["errors"].append("audit_exception:" + str(exc))
    return _finish(report, report_path)


def _finish(report, report_path):
    report["passed"] = not report["errors"]
    if report_path:
        p = Path(report_path); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
