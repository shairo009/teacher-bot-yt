"""Production wrapper for the Teacher Bot video pipeline.

It intentionally wraps main.py instead of replacing it, so YouTube auth, history,
analytics, topic rotation, and upload behavior stay intact.

Quality targets:
- true 1080x1920 (9:16) output with square pixels
- no crop/overflow: every frame is scaled/padded into the exact canvas
- 9-step narration/video timing with a 7s minimum per step
- 576 deterministic visual directions
- same core visual language as the supplied reference: animated concept above,
  code below, but with controlled motion/particle differences per video
"""

import asyncio
import math
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from src.visual_variant_bank import variant_for

MIN_STEP_SECONDS = 7.0
WIDTH, HEIGHT, FPS = 1080, 1920, 30
VIZ_BOX = (28, 212, 1052, 1048)  # strict safe area inside the existing visual panel


def _seed(text: str) -> int:
    return sum((i + 1) * ord(ch) for i, ch in enumerate(str(text))) & 0xFFFFFFFF


def _secondary(accent):
    # Stable complementary-ish accent without changing the base engine palette.
    r, g, b = accent
    return (min(255, 255 - r // 3), min(255, 255 - g // 4), min(255, 255 - b // 5))


def _overlay_variant(img: Image.Image, variant: str, global_frame: int, step_idx: int) -> Image.Image:
    """Add a restrained, phone-safe visual signature inside the visual zone only."""
    if img.size != (WIDTH, HEIGHT):
        img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    x0, y0, x1, y1 = VIZ_BOX
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    s = _seed(variant)
    accent = (
        70 + (s * 17) % 170,
        70 + (s * 31) % 170,
        70 + (s * 47) % 170,
    )
    secondary = _secondary(accent)
    effect, motif = variant.split(" ", 1)
    t = global_frame / FPS

    # Everything below stays within VIZ_BOX and uses low alpha so the actual
    # algorithm visualization remains the focal point.
    if effect == "orbit":
        r = 250 + int(20 * math.sin(t * 2.0))
        d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(*accent, 48), width=2)
        a = t * 1.7 + (s % 360) * math.pi / 180
        px, py = cx + int(r * math.cos(a)), cy + int(r * math.sin(a))
        d.ellipse((px-7, py-7, px+7, py+7), fill=(*secondary, 105))
    elif effect == "pulse":
        r = 70 + int((t * 55 + s) % 240)
        d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(*accent, 65), width=3)
    elif effect == "scan":
        y = y0 + 80 + int((t * 180) % max(1, y1-y0-160))
        d.line((x0+15, y, x1-15, y), fill=(*accent, 48), width=3)
    elif effect == "flow":
        for i in range(9):
            yy = y0 + 120 + i * 105
            shift = int((t * (40 + i*5) + s % 100) % 120)
            x = x0 + 35 + shift
            d.line((x, yy, min(x+150, x1-20), yy), fill=(*accent, 42), width=2)
            d.polygon([(min(x+150, x1-20), yy), (min(x+138, x1-20), yy-6), (min(x+138, x1-20), yy+6)], fill=(*secondary, 70))
    elif effect == "radar":
        r = 300
        a = t * 1.4
        ex, ey = cx + int(r*math.cos(a)), cy + int(r*math.sin(a))
        d.line((cx, cy, ex, ey), fill=(*accent, 65), width=3)
        d.arc((cx-r, cy-r, cx+r, cy+r), start=0, end=int((a*180/math.pi)%360), fill=(*accent, 35), width=2)
    elif effect == "wave":
        pts = []
        for xx in range(x0+20, x1-20, 18):
            yy = cy + int(45 * math.sin(xx/75 + t*2.4 + s%17))
            pts.append((xx, yy))
        d.line(pts, fill=(*accent, 55), width=3)
    elif effect == "constellation":
        pts = []
        rng = __import__("random").Random(s)
        for i in range(14):
            px = rng.randint(x0+50, x1-50)
            py = rng.randint(y0+100, y1-50)
            py += int(15 * math.sin(t + i))
            pts.append((px, py))
            d.ellipse((px-3, py-3, px+3, py+3), fill=(*secondary, 95))
        for i in range(len(pts)-1):
            if i % 2 == 0:
                d.line((*pts[i], *pts[i+1]), fill=(*accent, 28), width=1)
    elif effect == "matrix":
        rng = __import__("random").Random(s)
        for i in range(18):
            xx = x0 + 35 + (i * 59) % (x1-x0-70)
            yy = y0 + 55 + int((t*(90+i*7) + rng.randint(0,900)) % (y1-y0-100))
            d.text((xx, yy), motif[:1].upper(), fill=(*accent, 48))
    elif effect == "glitch":
        for i in range(5):
            yy = y0 + 70 + ((s + i*137) % (y1-y0-140))
            off = int(8 * math.sin(t*8+i))
            d.rectangle((x0+80+off, yy, x1-80+off, yy+2), fill=(*accent, 40))
    elif effect == "circuit":
        rng = __import__("random").Random(s)
        for i in range(8):
            yy = y0 + 80 + i*115
            start = x0 + rng.randint(30, 140)
            mid = start + 90 + (s+i*31)%110
            end = min(x1-30, mid + 150)
            d.line((start, yy, mid, yy), fill=(*accent, 45), width=2)
            d.line((mid, yy, mid, yy+35), fill=(*accent, 45), width=2)
            d.line((mid, yy+35, end, yy+35), fill=(*secondary, 45), width=2)
            d.ellipse((end-4, yy+31, end+4, yy+39), fill=(*accent, 85))
    elif effect == "rings":
        for i in range(4):
            r = 90 + i*75 + int(10*math.sin(t*1.7+i))
            d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(*accent, 28+i*8), width=2)
    elif effect == "particles":
        rng = __import__("random").Random(s)
        for i in range(45):
            px = x0 + 25 + rng.randrange(max(1, x1-x0-50))
            py = y0 + 60 + int((rng.randrange(max(1, y1-y0-120)) + t*(20+i%7)) % max(1, y1-y0-120))
            rr = 1 + (i % 3)
            d.ellipse((px-rr,py-rr,px+rr,py+rr), fill=(*accent, 25 + i%4*8))
    elif effect == "trail":
        for j in range(6):
            xx = cx + int(300*math.sin(t*1.3-j*0.15))
            yy = cy + int(220*math.cos(t*1.1-j*0.12))
            d.ellipse((xx-j*5-4, yy-j*3-4, xx+j*5+4, yy+j*3+4), outline=(*secondary, max(15,70-j*9)), width=2)
    elif effect == "signal":
        base = y0 + 180
        pts=[]
        for xx in range(x0+20, x1-20, 12):
            yy = base + int(28*math.sin(xx/18+t*5)) if (xx//12)%5 else base-60
            pts.append((xx,yy))
        d.line(pts, fill=(*accent, 60), width=3)
    elif effect == "gridwarp":
        for k in range(5):
            yy = y0+130+k*170
            d.line((x0+20, yy, x1-20, yy+int(20*math.sin(t+k))), fill=(*accent, 28), width=2)
    elif effect == "heatmap":
        for k in range(7):
            r = 35 + k*38
            alpha = max(15, 65-k*7)
            d.ellipse((cx-r,cy-r,cx+r,cy+r), outline=(*accent,alpha), width=2)
    elif effect == "spiral":
        pts=[]
        for i in range(150):
            a=i*0.16+t*1.7
            r=1.6*i
            x=cx+r*math.cos(a); y=cy+r*math.sin(a)*0.55
            if x0<x<x1 and y0<y<y1: pts.append((int(x),int(y)))
        if len(pts)>1: d.line(pts,fill=(*accent,45),width=2)
    elif effect == "nodes":
        rng=__import__("random").Random(s)
        pts=[]
        for i in range(10):
            px=x0+70+rng.randrange(x1-x0-140); py=y0+90+rng.randrange(y1-y0-150)
            pts.append((px,py))
        for i in range(1,len(pts)):
            d.line((*pts[i-1],*pts[i]),fill=(*accent,32),width=2)
            d.ellipse((pts[i][0]-6,pts[i][1]-6,pts[i][0]+6,pts[i][1]+6),fill=(*secondary,70))
    elif effect == "beams":
        for i in range(4):
            yy=y0+120+i*210
            d.line((x0+40,yy,x1-40,yy+int(70*math.sin(t+i))),fill=(*accent,42),width=3)
    elif effect == "spectrum":
        for i in range(9):
            h=20+int(50*(0.5+0.5*math.sin(t*2+i*0.8)))
            xx=x0+100+i*90
            d.rectangle((xx,cy-h,xx+35,cy+h),fill=(*secondary,28))
    elif effect == "dots":
        for i in range(60):
            a=(i*0.73+t*0.5); rr=120+(i%10)*28
            px=cx+int(rr*math.cos(a)); py=cy+int(rr*math.sin(a)*0.65)
            if x0<px<x1 and y0<py<y1: d.ellipse((px-2,py-2,px+2,py+2),fill=(*accent,45))
    elif effect == "arcs":
        for i in range(5):
            r=80+i*70
            d.arc((cx-r,cy-r,cx+r,cy+r),start=int(t*60+i*40)%360,end=(int(t*60+i*40)%360)+80,fill=(*accent,55),width=3)
    elif effect == "shards":
        rng=__import__("random").Random(s)
        for i in range(12):
            px=x0+50+rng.randrange(x1-x0-100); py=y0+80+rng.randrange(y1-y0-160)
            sz=8+(i%5)*3
            d.polygon([(px,py-sz),(px+sz,py+sz//2),(px-sz//2,py+sz)],fill=(*secondary,32),outline=(*accent,55))
    elif effect == "comet":
        a=t*1.1+(s%360)*math.pi/180
        px=cx+int(380*math.cos(a)); py=cy+int(280*math.sin(a))
        for j in range(8):
            tx=px-int(j*22*math.cos(a)); ty=py-int(j*22*math.sin(a))
            d.ellipse((tx-3,ty-3,tx+3,ty+3),fill=(*accent,max(8,65-j*7)))

    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


class VariantPuzzleEngine:
    """Wrap the existing engine and add controlled variant motion."""
    def __init__(self, series: str, variant: str):
        from src.puzzle_visual_engine import PuzzleEngine
        self.base = PuzzleEngine(series=series)
        self.variant = variant

    def render_frame(self, scene, step_idx, step_progress, global_frame, total_steps):
        scene = dict(scene)
        scene["visual_variant"] = self.variant
        img = self.base.render_frame(scene, step_idx, step_progress, global_frame, total_steps)
        return _overlay_variant(img, self.variant, global_frame, step_idx)

    def render_thumbnail(self, scene):
        scene = dict(scene)
        scene["visual_variant"] = self.variant
        img = self.base.render_thumbnail(scene)
        return _overlay_variant(img, self.variant, 90, 3)


def _puzzle_number(prompt: str) -> int:
    m = re.search(r"PUZZLE #(\d+)", prompt or "")
    return int(m.group(1)) if m else 1


def install():
    """Monkey-patch main.py with the production-quality wrappers."""
    import main as base

    original_call_llm = base.call_llm
    original_build_prompt = base.build_llm_prompt

    def build_prompt(topic, game_mechanic, game_tag, puzzle_num):
        variant = variant_for(puzzle_num)
        prompt = original_build_prompt(topic, game_mechanic, game_tag, puzzle_num)
        return prompt + f"\n\nMANDATORY VISUAL DIRECTION: {variant}. Keep the same core composition as the supplied reference: a large animated concept in the upper visual zone and a readable code panel below. Make the motion/objects/layout details express this direction. Do not use the exact same visual composition as another puzzle.\n"

    async def call_llm(prompt, api_key):
        variant = variant_for(_puzzle_number(prompt))
        scene = await original_call_llm(prompt, api_key)
        scene["visual_variant"] = variant
        narr = scene.get("narration") or []
        if len(narr) < base.N_STEPS or sum(len(str(x).split()) for x in narr[:base.N_STEPS]) < 180:
            retry_prompt = prompt + "\nQUALITY RETRY: narration must contain exactly 9 strings and each string must be 30-40 words. Return only JSON."
            try:
                retry = await original_call_llm(retry_prompt, api_key)
                if len(retry.get("narration", [])) >= base.N_STEPS:
                    scene = retry
                    scene["visual_variant"] = variant
            except Exception as exc:
                print(f"  ⚠ Narration retry skipped: {exc}")
        return scene

    def render_frames(scene, series, output_dir):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        variant = str(scene.get("visual_variant") or variant_for(scene.get("puzzle_num", 1)))
        engine = VariantPuzzleEngine(series, variant)
        frames=[]
        total_steps=base.N_STEPS
        total=total_steps*base.FRAMES_PER_STEP
        print(f"  🎨 Rendering {total} frames with visual variant: {variant}")
        for step_idx in range(total_steps):
            for fi in range(base.FRAMES_PER_STEP):
                global_frame=step_idx*base.FRAMES_PER_STEP+fi
                progress=fi/base.FRAMES_PER_STEP
                img=engine.render_frame(scene,step_idx,progress,global_frame,total_steps)
                if img.size != (WIDTH,HEIGHT):
                    img=img.resize((WIDTH,HEIGHT),Image.Resampling.LANCZOS)
                frame_path=output_dir/f"frame_{global_frame:06d}.jpg"
                img.save(str(frame_path),"JPEG",quality=92,optimize=True)
                frames.append(frame_path)
            print(f"    Step {step_idx+1}/{total_steps} ✓")
        return frames

    def _probe(path):
        r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True)
        try: return float(r.stdout.strip())
        except: return 0.0

    def _pad_audio(src: Path, dst: Path, target: float):
        r=subprocess.run(["ffmpeg","-y","-i",str(src),"-af","apad","-t",f"{target:.3f}","-c:a","aac","-b:a","128k",str(dst)],capture_output=True,text=True,timeout=180)
        if r.returncode != 0: raise RuntimeError(r.stderr[-800:])

    def compose_video(frames, audio_paths, durations, output_path):
        if not frames: return None
        output_path=Path(output_path); tmp=output_path.parent
        target_durations=[]
        for i in range(base.N_STEPS):
            actual=float(durations[i]) if i < len(durations) else 0.0
            target_durations.append(max(MIN_STEP_SECONDS, actual))

        concat=tmp/"frame_list_quality.txt"
        with open(concat,"w",encoding="utf-8") as f:
            for i,frame in enumerate(frames):
                step=i//base.FRAMES_PER_STEP
                dur=target_durations[step]/base.FRAMES_PER_STEP
                f.write(f"file '{Path(frame).resolve().as_posix()}'\n")
                f.write(f"duration {dur:.6f}\n")
            f.write(f"file '{Path(frames[-1]).resolve().as_posix()}'\n")

        raw=tmp/"raw_video_quality.mp4"
        vf="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30"
        r=subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-vf",vf,"-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(raw)],capture_output=True,text=True,timeout=900)
        if r.returncode!=0:
            print(f"❌ Quality video render error: {r.stderr[-1000:]}")
            return None

        padded=[]
        for i in range(base.N_STEPS):
            dst=tmp/f"audio_quality_{i:02d}.m4a"
            if i < len(audio_paths) and Path(audio_paths[i]).exists():
                _pad_audio(Path(audio_paths[i]),dst,target_durations[i])
            else:
                rr=subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=48000:cl=stereo","-t",f"{target_durations[i]:.3f}","-c:a","aac","-b:a","128k",str(dst)],capture_output=True,text=True,timeout=120)
                if rr.returncode!=0: raise RuntimeError(rr.stderr[-800:])
            padded.append(dst)

        audio_list=tmp/"audio_quality_list.txt"
        with open(audio_list,"w",encoding="utf-8") as f:
            for p in padded: f.write(f"file '{p.resolve().as_posix()}'\n")
        merged=tmp/"merged_audio_quality.m4a"
        r=subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(audio_list),"-c","copy",str(merged)],capture_output=True,text=True,timeout=180)
        if r.returncode!=0: raise RuntimeError(r.stderr[-800:])

        r=subprocess.run(["ffmpeg","-y","-i",str(raw),"-i",str(merged),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(output_path)],capture_output=True,text=True,timeout=600)
        if r.returncode!=0:
            print(f"❌ Final compose error: {r.stderr[-1000:]}")
            return None

        # Hard postcondition checks. Never upload an incorrectly shaped video.
        probe=subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height,sample_aspect_ratio","-of","csv=p=0",str(output_path)],capture_output=True,text=True)
        vals=probe.stdout.strip().split(",")
        if len(vals)>=2:
            w,h=int(vals[0]),int(vals[1])
            if (w,h)!=(1080,1920):
                raise RuntimeError(f"Output canvas check failed: {w}x{h}; expected 1080x1920")
        duration=_probe(output_path)
        if duration < MIN_STEP_SECONDS*base.N_STEPS-0.5:
            raise RuntimeError(f"Output duration check failed: {duration:.2f}s")
        size_mb=output_path.stat().st_size/1e6
        print(f"✅ 10/10 quality gate passed: 1080x1920 • 9:16 • {duration:.1f}s • {size_mb:.1f}MB")
        return str(output_path)

    def generate_thumbnail(scene, series, output_path):
        try:
            variant=str(scene.get("visual_variant") or variant_for(scene.get("puzzle_num",1)))
            img=VariantPuzzleEngine(series,variant).render_thumbnail(scene)
            img.save(str(output_path),"JPEG",quality=96)
            return str(output_path)
        except Exception as exc:
            print(f"  ⚠ Thumbnail error: {exc}")
            return None

    base.build_llm_prompt=build_prompt
    base.call_llm=call_llm
    base.render_frames=render_frames
    base.compose_video=compose_video
    base.generate_thumbnail=generate_thumbnail

    return base


if __name__ == "__main__":
    base=install()
    asyncio.run(base.main())
