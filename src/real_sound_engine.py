"""
Real Draw ASMR Audio Engine
Synthesizes 100% code-generated audio:
- ASMR graphite pencil sketching & scratching on paper
- Soft watercolor brush whoosh swooshes
- Ambient relaxing art studio lo-fi chord drone
"""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44100

def _sin(freq: float, t: float) -> float:
    return math.sin(2 * math.pi * freq * t)

def _noise() -> float:
    return random.uniform(-1.0, 1.0)

def _clip(s: float) -> float:
    return math.tanh(s)

def _gen_pencil_scratch(duration: float = 0.08) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out = []
    f_center = random.uniform(1800, 3200)
    for i in range(n):
        t = i / SAMPLE_RATE
        decay = math.sin((i / n) * math.pi)
        # Texture paper friction noise
        scratch = (_noise() * 0.75 + _sin(f_center, t) * 0.25) * decay
        out.append(scratch * 0.28)
    return out

def _gen_brush_swoosh(duration: float = 0.5) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        env = math.sin(progress * math.pi) ** 1.8
        freq = 220 + math.sin(progress * math.pi) * 280
        sample = (_sin(freq, t) * 0.3 + _noise() * 0.7) * env * 0.25
        out.append(sample)
    return out

def _gen_ambient_art_drone(duration: float) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Soft D-Major warm chord (D3: 146.8Hz, F#3: 185Hz, A3: 220Hz)
        base = _sin(146.8, t) * 0.15 + _sin(185.0, t + 0.2) * 0.10 + _sin(220.0, t + 0.4) * 0.08
        swell = (math.sin(t * 0.8) * 0.5 + 0.5) * 0.04
        out.append((base + swell) * 0.6)
    return out

def generate_draw_audio(output_wav: Path, duration: float = 20.0, seed: int = 0) -> Path:
    rng = random.Random(seed)
    total_samples = int(SAMPLE_RATE * duration)
    master = _gen_ambient_art_drone(duration)

    # 1. Pencil Sketching SFX during outline phase (First 55% of duration)
    sketch_duration = duration * 0.55
    t_curr = 0.4
    while t_curr < sketch_duration:
        stroke_len = rng.uniform(0.06, 0.14)
        scratch = _gen_pencil_scratch(stroke_len)
        start_idx = int(t_curr * SAMPLE_RATE)
        for j, s in enumerate(scratch):
            if start_idx + j < len(master):
                master[start_idx + j] = _clip(master[start_idx + j] + s)
        t_curr += stroke_len + rng.uniform(0.02, 0.08)

    # 2. Watercolor Brush Swooshes during Color Fill phase (55% to 85%)
    brush_start = duration * 0.55
    brush_end = duration * 0.85
    t_brush = brush_start
    while t_brush < brush_end:
        swoosh = _gen_brush_swoosh(rng.uniform(0.35, 0.6))
        start_idx = int(t_brush * SAMPLE_RATE)
        for j, s in enumerate(swoosh):
            if start_idx + j < len(master):
                master[start_idx + j] = _clip(master[start_idx + j] + s * 0.35)
        t_brush += rng.uniform(1.2, 2.2)

    # Save to 16-bit PCM WAV
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_wav), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"".join(
            struct.pack("<h", max(-32767, min(32767, int(s * 32767))))
            for s in master
        ))
    return output_wav