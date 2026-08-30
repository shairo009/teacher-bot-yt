"""
Procedural Audio & SFX Engine
Synthesizes 100% code-generated audio from mathematical waveforms using standard Python (wave & struct):
- Mechanical keyboard clicks for code typing
- Cyber swoosh / whoosh for pointer motion
- Ambient futuristic tech hum drone
No external audio files or internet download needed!
"""
from __future__ import annotations

import math
import os
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

def _gen_key_click(duration: float = 0.04) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out = []
    freq = random.uniform(2200, 3400)
    for i in range(n):
        t = i / SAMPLE_RATE
        decay = math.exp(-i / (SAMPLE_RATE * 0.008))
        sample = (_sin(freq, t) * 0.4 + _noise() * 0.6) * decay
        out.append(sample * 0.45)
    return out

def _gen_whoosh(duration: float = 0.6) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        env = math.sin(progress * math.pi) ** 2
        freq = 180 + math.sin(progress * math.pi) * 350
        sample = (_sin(freq, t) * 0.4 + _noise() * 0.6) * env * 0.35
        out.append(sample)
    return out

def _gen_ambient_drone(duration: float) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Low warm tech chord (F# base: 92.5Hz, 185Hz, 277.5Hz)
        base = _sin(92.5, t) * 0.18 + _sin(185.0, t + 0.1) * 0.12 + _sin(277.5, t + 0.3) * 0.08
        pulse = (math.sin(t * 1.5) * 0.5 + 0.5) * 0.05
        sample = (base + pulse) * 0.6
        out.append(sample)
    return out

def generate_reel_audio(output_wav: Path, duration: float = 58.0, typing_events: int = 40, seed: int = 0) -> Path:
    rng = random.Random(seed)
    total_samples = int(SAMPLE_RATE * duration)
    master = _gen_ambient_drone(duration)

    whoosh = _gen_whoosh(0.55)

    # Periodic whooshes when cursor changes trajectory
    whoosh_interval = 4.5
    t_w = 1.0
    while t_w < duration - 1.0:
        start_idx = int(t_w * SAMPLE_RATE)
        for j, s in enumerate(whoosh):
            if start_idx + j < len(master):
                master[start_idx + j] = _clip(master[start_idx + j] + s * 0.35)
        t_w += whoosh_interval + rng.uniform(-0.5, 0.8)

    # Periodic mechanical typing clicks during code window scrolling
    t_start = 0.5
    t_step = (duration - 1.5) / max(1, typing_events)
    for k in range(typing_events):
        k_time = t_start + k * t_step + rng.uniform(-0.03, 0.03)
        k_idx = int(k_time * SAMPLE_RATE)
        click = _gen_key_click(0.04)
        for j, s in enumerate(click):
            if k_idx + j < len(master):
                master[k_idx + j] = _clip(master[k_idx + j] + s * 0.30)

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

