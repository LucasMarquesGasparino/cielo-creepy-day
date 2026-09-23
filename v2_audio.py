#!/usr/bin/env python3
"""CIELO v2 audio: corporate PA narration + fluorescent hum + phone + stingers.

Voice plan (mirrors Opus subtitle script, corporate PA tone):
 b1 (0-6):   'Good morning. Welcome to Cielo Housing. Where every tenant stays.'
 b2 (6-9):   [no narration: glitch storm only]
 b3 (9-16):  'Good morning, staff. Please remember: the third floor does not exist.'
 b4 (16-21): 'A tenant is approaching. Please be polite.'
 b5 (21-26): 'Nine new messages. Zero tenants can leave.'
 b6 (26-31): 'The walls are breathing again. Hello? It is unit 4B. Again.'
 b7 (31-38): 'Spacious three-room apartment. Cozy. Available immediately. Previous tenant... included.'
 b8 (38-45): 'Great quarter, everyone. Occupancy one hundred percent. Departures zero.'
 b9 (45-52): 'Five o'clock. Time to clock out. The clock disagrees.'
 b10 (52-60):'Thank you for your service. See you tomorrow at nine. Waiting list position zero one. You. Welcome home.'

Bed: fluorescent hum (120Hz + harmonics) + D-minor drone + sub pulse 60BPM,
phone bell on b6 ring pulses, riser into entity (b4), impacts at glitch cuts,
tape-stop wobble into end card. Mix: narration primary, bed ducked, -14 LUFS-ish.
"""
import asyncio
import os
import subprocess

import numpy as np

PROJ = os.path.expanduser("~/projects/cielo-creepy-day")
AUD2 = os.path.join(PROJ, "assets", "audio2")
os.makedirs(AUD2, exist_ok=True)
SR = 48000

LINES = [
    ("n1", 0.5, "Good morning. Welcome to Cielo Housing. Where every tenant stays."),
    ("n3", 9.5, "Good morning, staff. Please remember: the third floor does not exist."),
    ("n4", 16.5, "A tenant is approaching. Please be polite."),
    ("n5", 21.5, "Nine new messages. Zero tenants can leave."),
    ("n6", 26.5, "The walls are breathing again. Hello? It is unit 4B. Again."),
    ("n7", 31.5, "Spacious three-room apartment. Cozy. Available immediately. Previous tenant... included."),
    ("n8", 38.5, "Great quarter, everyone. Occupancy one hundred percent. Departures zero."),
    ("n9", 45.5, "Five o'clock. Time to clock out. The clock disagrees."),
    ("n10", 52.5, "Thank you for your service. See you tomorrow at nine. Waiting list position zero one. You. Welcome home."),
]

VOICE = "en-US-ChristopherNeural"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)


async def make_tts():
    import edge_tts
    for nid, _, text in LINES:
        out = os.path.join(AUD2, f"{nid}.mp3")
        if os.path.exists(out):
            continue
        try:
            await edge_tts.Communicate(text, VOICE, rate="-12%").save(out)
            # edge-tts can write 0-byte files on transient failures: verify
            if os.path.getsize(out) < 1024:
                raise RuntimeError("empty edge-tts output")
            print(f"edge-tts ok: {nid}", flush=True)
        except Exception as e:
            print(f"edge-tts failed {nid}: {type(e).__name__}; retry once", flush=True)
            await asyncio.sleep(3)
            try:
                if os.path.exists(out):
                    os.remove(out)
                await edge_tts.Communicate(text, VOICE, rate="-12%").save(out)
                if os.path.getsize(out) < 1024:
                    raise RuntimeError("empty edge-tts output on retry")
                print(f"edge-tts ok on retry: {nid}", flush=True)
            except Exception as e2:
                print(f"edge-tts failed twice {nid}: {type(e2).__name__}; sox synth beep track", flush=True)
                if os.path.exists(out):
                    os.remove(out)
                dur = max(2.0, len(text) * 0.06)
                run(["sox", "-n", "-r", str(SR), out, "synth", f"{dur:.2f}", "sine", "110",
                     "synth", f"{dur:.2f}", "sine", "55", "mix", "gain", "-8"])


def load_mono_48k(path):
    w = os.path.join(AUD2, "_c.wav")
    run(["ffmpeg", "-y", "-i", path, "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", w])
    import wave as wv
    with wv.open(w, "rb") as fh:
        raw = fh.readframes(fh.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def phone_bell(dur=1.6):
    """Classic dual-frequency phone bell w/ decay (UK-style double ring)."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.zeros(n)
    for start, length in ((0.0, 0.4), (0.5, 0.4), (1.0, 0.4)):
        i0, i1 = int(start * SR), min(n, int((start + length) * SR))
        env[i0:i1] = np.exp(-(np.arange(i1 - i0) / SR) * 4)
    bell = (np.sin(2 * np.pi * 1000 * t) * 0.5 + np.sin(2 * np.pi * 1400 * t) * 0.35) * env
    return bell.astype(np.float32) * 0.5


def bed():
    n = SR * 60
    t = np.arange(n) / SR
    rng = np.random.default_rng(7)
    sig = np.zeros(n, dtype=np.float32)
    sig += 0.10 * np.sin(2 * np.pi * 120 * t)            # fluorescent hum
    sig += 0.05 * np.sin(2 * np.pi * 240 * t + 0.4)
    sig += 0.03 * np.sin(2 * np.pi * 360 * t + 1.1)
    for f, a in ((73.42, 0.20), (110.0, 0.15), (146.83, 0.10), (174.61, 0.07)):
        sig += a * np.sin(2 * np.pi * f * t)              # D-minor drone
    pulse = (0.5 + 0.5 * np.sin(2 * np.pi * 1.0 * t)) ** 3
    sig += (pulse * 0.16 * np.sin(2 * np.pi * 55 * t)).astype(np.float32)
    # riser into entity (12-16s)
    i0, i1 = 12 * SR, 16 * SR
    ramp = np.linspace(0, 1, i1 - i0)
    sig[i0:i1] += (ramp ** 2 * 0.14 * np.sin(2 * np.pi * (200 + 600 * ramp)
                   * (np.arange(i1 - i0) / SR))).astype(np.float32)
    # impacts: entity hit 16s, glitch cuts 6/9s, departures 41s, clock 45s
    for at, amp in ((6.0, 0.5), (9.0, 0.6), (16.0, 1.0), (21.0, 0.5), (41.5, 0.6), (45.0, 0.5)):
        k0 = int(at * SR)
        m = min(SR * 2, n - k0)
        sig[k0:k0 + m] += (np.exp(-np.arange(m) / (SR * 0.5)) * amp
                           * np.sin(2 * np.pi * 48 * np.arange(m) / SR)).astype(np.float32)
    # signal-loss dips at hard cuts
    for at in (6.0, 9.0, 16.0, 20.8, 41.5):
        a0, a1 = int((at - 0.25) * SR), int((at + 0.1) * SR)
        sig[max(0, a0):a1] *= 0.08
    # phone bells on b6 ring pulses (26-31s)
    for at in (26.5, 28.5, 30.0):
        b = phone_bell()
        k0 = int(at * SR)
        sig[k0:k0 + len(b)] += b
    # tape-stop wobble into end card (51.5-52.5s)
    w0, w1 = int(51.5 * SR), int(52.5 * SR)
    sig[w0:w1] *= np.linspace(1, 0.5, w1 - w0).astype(np.float32)
    sig += rng.standard_normal(n).astype(np.float32) * 0.007
    sig[58 * SR:] *= np.linspace(1, 0.5, n - 58 * SR).astype(np.float32)
    return sig


def main():
    asyncio.run(make_tts())
    total = np.zeros(SR * 60, dtype=np.float32)
    for nid, start, _ in LINES:
        pcm = load_mono_48k(os.path.join(AUD2, f"{nid}.mp3"))
        win = int(SR * 6.5)
        if len(pcm) > win:  # gentle time-compress, never clip
            idx = (np.arange(win) * len(pcm) / win).astype(int)
            pcm = pcm[np.clip(idx, 0, len(pcm) - 1)]
        i0 = int(start * SR)
        total[i0:i0 + len(pcm)] += pcm * 0.95
    peak = np.abs(total).max() or 1.0
    total = (np.tanh(total / peak * 1.2) * 0.85).astype(np.float32)
    music = bed()
    win = SR // 10
    env = np.convolve(np.abs(total), np.ones(win) / win, mode="same")
    duck = np.clip(1 - env * 4.0, 0.12, 1.0)
    mix = total + music * 0.32 * duck
    peak = np.abs(mix).max() or 1.0
    mix = (mix / peak * 0.89).astype(np.float32)
    import wave
    wav = os.path.join(AUD2, "mix_60s.wav")
    with wave.open(wav, "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(SR)
        fh.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"mix done ({os.path.getsize(wav)/1e6:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
