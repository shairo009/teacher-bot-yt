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

def _gen_startup_chime() -> list[float]:
    """Futuristic UI startup harmonic chime (C-major triad: 523Hz, 659Hz, 784Hz, 1046Hz)."""
    duration = 0.8
    n = int(SAMPLE_RATE * duration)
    out = []
    freqs = [523.25, 659.25, 783.99, 1046.50]
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 4.5)
        sample = sum(_sin(f, t) * (0.25 / (idx + 1)) for idx, f in enumerate(freqs)) * env
        out.append(sample * 0.5)
    return out

def _gen_key_click(duration: float = 0.045) -> list[float]:
    """Crisp two-stage mechanical switch click (Cherry MX Blue style)."""
    n = int(SAMPLE_RATE * duration)
    out = []
    freq1 = random.uniform(2800, 3600)
    freq2 = random.uniform(1400, 1800)
    for i in range(n):
        t = i / SAMPLE_RATE
        decay1 = math.exp(-i / (SAMPLE_RATE * 0.005))
        decay2 = math.exp(-max(0, i - int(SAMPLE_RATE * 0.015)) / (SAMPLE_RATE * 0.008))
        sample = (_sin(freq1, t) * 0.5 + _noise() * 0.5) * decay1 + (_sin(freq2, t) * 0.3 + _noise() * 0.4) * decay2
        out.append(sample * 0.40)
    return out

def _gen_whoosh(duration: float = 0.5) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        env = math.sin(progress * math.pi) ** 2
        freq = 200 + math.sin(progress * math.pi) * 450
        sample = (_sin(freq, t) * 0.35 + _noise() * 0.65) * env * 0.38
        out.append(sample)
    return out

def _gen_ambient_drone(duration: float) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Low warm tech chord (F# base: 92.5Hz, 185Hz, 277.5Hz, 370Hz)
        base = _sin(92.5, t) * 0.16 + _sin(185.0, t + 0.1) * 0.11 + _sin(277.5, t + 0.3) * 0.07 + _sin(370.0, t + 0.5) * 0.04
        pulse = (math.sin(t * 1.8) * 0.5 + 0.5) * 0.04
        sample = (base + pulse) * 0.55
        out.append(sample)
    return out

def generate_reel_audio(output_wav: Path, duration: float = 25.0, typing_events: int = 24, seed: int = 0) -> Path:
    rng = random.Random(seed)
    total_samples = int(SAMPLE_RATE * duration)
    master = _gen_ambient_drone(duration)

    # 1. Futuristic UI startup chime at t=0.2s
    chime = _gen_startup_chime()
    chime_idx = int(0.2 * SAMPLE_RATE)
    for j, s in enumerate(chime):
        if chime_idx + j < len(master):
            master[chime_idx + j] = _clip(master[chime_idx + j] + s * 0.55)

    whoosh = _gen_whoosh(0.50)

    # Periodic whooshes when cursor turns
    whoosh_interval = 4.0
    t_w = 1.8
    while t_w < duration - 1.0:
        start_idx = int(t_w * SAMPLE_RATE)
        for j, s in enumerate(whoosh):
            if start_idx + j < len(master):
                master[start_idx + j] = _clip(master[start_idx + j] + s * 0.35)
        t_w += whoosh_interval + rng.uniform(-0.4, 0.6)

    # Periodic mechanical typing clicks during code window scrolling
    t_start = 0.8
    t_step = (duration - 2.0) / max(1, typing_events)
    for k in range(typing_events):
        k_time = t_start + k * t_step + rng.uniform(-0.03, 0.03)
        k_idx = int(k_time * SAMPLE_RATE)
        click = _gen_key_click(0.045)
        for j, s in enumerate(click):
            if k_idx + j < len(master):
                master[k_idx + j] = _clip(master[k_idx + j] + s * 0.32)

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


