#!/usr/bin/env python3
"""CIELO-CREEPY-DAY — synth audio: dark drone + narration via tts_selector route.

TTS: edge-tts (cloud, free) with espeak+sox robotic fallback mixed locally.
Music bed: numpy D-minor drone 60BPM + sub pulse + 120Hz hum + riser + stingers.
Mix: narration primary, music ducked ~-18dB under speech, -14 LUFS-ish, 48kHz.
"""
import asyncio
import json
import os
import subprocess

import numpy as np

PROJ = os.path.expanduser("~/projects/cielo-creepy-day")
AUD = os.path.join(PROJ, "assets", "audio")
SR = 48000

with open(os.path.join(PROJ, "pipeline", "script.json"), encoding="utf-8") as fh:
    SCRIPT = json.load(fh)

VOICE = "en-US-ChristopherNeural"
RATE = "-15%"

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)

async def edge_say(text, out):
    import edge_tts
    comm = edge_tts.Communicate(text, VOICE, rate=RATE)
    await comm.save(out)

def synth_fallback(text, out):
    """Robotic fallback: espeak formants via sox synth if edge-tts blocked."""
    tmp = out + ".tmp.wav"
    r = run(["espeak", "-v", "en", "-s", "110", "-p", "20", "-w", tmp, text])
    if r.returncode != 0 or not os.path.exists(tmp):
        # last resort: pure sox morse-ish blips encoding syllables (still creepy)
        dur = max(2.0, len(text) * 0.055)
        run(["sox", "-n", "-r", str(SR), tmp, "synth", f"{dur:.2f}", "sine", "110",
             "synth", f"{dur:.2f}", "sine", "55", "mix", "gain", "-6"])
    # slow + darken + add dread
    run(["sox", tmp, out, "speed", "0.92", "pitch", "-200",
         "reverb", "60", "gain", "-3"])
    if os.path.exists(tmp):
        os.remove(tmp)

async def make_narration():
    from edge_tts.exceptions import NoAudioReceived
    paths = []
    for s in SCRIPT["sections"]:
        out = os.path.join(AUD, f"narr_{s['id']}.mp3")
        if os.path.exists(out):
            paths.append((s, out))
            continue
        try:
            await edge_say(s["text"], out)
            print(f"edge-tts ok: {s['id']}", flush=True)
        except Exception as e:
            print(f"edge-tts failed for {s['id']} ({type(e).__name__}), synth fallback", flush=True)
            synth_fallback(s["text"], out)
        paths.append((s, out))
    return paths

def place_narration(paths):
    """Stretch/pad each narration to fill its 10s window; concat to 60s."""
    total = np.zeros(SR * 60, dtype=np.float32)
    for s, path in paths:
        w = os.path.join(AUD, f"narr_{s['id']}.wav")
        run(["ffmpeg", "-y", "-i", path, "-ar", str(SR), "-ac", "1",
             "-sample_fmt", "s16", w])
        import wave as wv
        with wv.open(w, "rb") as fh:
            assert fh.getsampwidth() == 2 and fh.getnchannels() == 1
            raw = fh.readframes(fh.getnframes())
        pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 2 ** 15
        start = int(s["start_seconds"] * SR) + int(SR * 0.7)
        win = SR * 10 - int(SR * 1.4)
        if len(pcm) > win:
            # slow down slightly instead of clipping
            idx = (np.arange(win) * len(pcm) / win).astype(int)
            pcm = pcm[np.clip(idx, 0, len(pcm) - 1)]
        total[start:start + len(pcm)] += pcm * 0.9
    # gentle limiter
    peak = np.abs(total).max() or 1.0
    total = np.tanh(total / peak * 1.2) * 0.85
    return total

def synth_bed():
    T = 60
    n = SR * T
    t = np.arange(n) / SR
    rng = np.random.default_rng(7)
    # D minor drone: D2 A2 D3 F3 + detune
    freqs = [73.42, 110.0, 146.83, 174.61]
    bed = sum(np.sin(2 * np.pi * f * t + rng.standard_normal() * 0.0) * a
              for f, a in zip(freqs, [0.30, 0.22, 0.15, 0.10]))
    bed += 0.06 * np.sin(2 * np.pi * 120.0 * t)          # fluorescent hum
    bed += 0.04 * np.sin(2 * np.pi * 240.0 * t + 0.5)
    # 60 BPM sub pulse (1 Hz), stronger in reveal (30-50s)
    env = np.ones(n)
    env[30 * SR:50 * SR] = 1.8
    pulse = (0.5 + 0.5 * np.sin(2 * np.pi * 1.0 * t)) ** 3 * 0.20 * env
    bed += pulse * np.sin(2 * np.pi * 55.0 * t)
    # riser 20-30s into reveal
    r0, r1 = 20 * SR, 30 * SR
    ramp = np.linspace(0, 1, r1 - r0)
    bed[r0:r1] += ramp ** 2 * 0.12 * np.sin(2 * np.pi * (200 + 600 * ramp) * (np.arange(r1 - r0) / SR))
    # impact hits at 30s and 40s
    for at, amp in ((30.0, 0.9), (40.0, 0.7), (50.0, 0.5)):
        i0 = int(at * SR)
        decay = np.exp(-np.arange(SR * 2) / (SR * 0.5)) * amp
        bed[i0:i0 + SR * 2] += decay * np.sin(2 * np.pi * 48.0 * np.arange(SR * 2) / SR)
    # dropout stinger: silence dip at 30s boundary
    bed[int(29.7 * SR):int(30.1 * SR)] *= 0.05
    # shimmer noise bed
    bed += rng.standard_normal(n).astype(np.float32) * 0.008
    # slow swell toward landing then hum tail
    swell = np.clip((t - 50) / 10, 0, 1)
    bed *= (0.8 + 0.4 * swell)
    bed[58 * SR:] *= np.linspace(1, 0.4, n - 58 * SR)
    return bed.astype(np.float32)

def main():
    os.makedirs(AUD, exist_ok=True)
    paths = asyncio.run(make_narration())
    narr = place_narration(paths)
    bed = synth_bed()
    # duck bed under narration: simple envelope follower
    win = SR // 10
    env = np.convolve(np.abs(narr), np.ones(win) / win, mode="same")
    duck = np.clip(1 - env * 4.0, 0.12, 1.0)
    mix = narr * 1.0 + bed * 0.35 * duck
    peak = np.abs(mix).max() or 1.0
    mix = (mix / peak * 0.89).astype(np.float32)
    import wave
    wav = os.path.join(AUD, "mix_60s.wav")
    with wave.open(wav, "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(SR)
        fh.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    mp3 = os.path.join(AUD, "mix_60s.mp3")
    run(["ffmpeg", "-y", "-i", wav, "-codec:a", "libmp3lame", "-b:a", "192k", mp3])
    print(f"mix done -> {wav} ({os.path.getsize(wav)/1e6:.1f} MB)", flush=True)

if __name__ == "__main__":
    main()
