#!/usr/bin/env python3
"""CIELO-CREEPY-DAY — programmatic frame renderer (OpenMontage cinematic pipeline).

Runtime: ffmpeg (templated). 1280x720 @ 30fps, 6 scenes x 10s = 60s.
Techniques: numpy/Pillow synthesis, liminal fluorescent grids, corridor loops,
VHS/CRT overlays (scanlines, tracking bar, chromatic split, grain, vignette),
letterbox 2.35:1, monospace title cards. Deterministic (seeded RNG).
"""
import glob
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = 30
SCENE_S = 10
N = FPS * SCENE_S

BG = np.array([10, 10, 12], dtype=np.float32)
BONE = (245, 240, 220)
MUSTARD = (232, 197, 71)
RED = (193, 18, 31)
DIMRED = (122, 12, 20)

PROJ = os.path.expanduser("~/projects/cielo-creepy-day")
FR = os.path.join(PROJ, "assets", "frames")

# ---------- fonts ----------
def find_font():
    cands = (glob.glob("/system/fonts/*Mono*.ttf") + glob.glob("/system/fonts/DroidSans*.ttf")
             + glob.glob("/system/fonts/CutiveMono.ttf") + glob.glob("/system/fonts/Roboto*.ttf"))
    for c in cands:
        if os.path.exists(c):
            return c
    return None

FONT_PATH = find_font()

def font(size):
    if FONT_PATH:
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except Exception:
            pass
    return ImageFont.load_default()

F_TITLE = font(54)
F_SMALL = font(26)
F_OSD = font(22)

# ---------- precomputed masks ----------
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_nx = (_xx / W - 0.5) * 2
_ny = (_yy / H - 0.5) * 2
VIGNETTE = np.clip(1.0 - 0.42 * (_nx ** 2 + _ny ** 2), 0.42, 1.0)[..., None].astype(np.float32)
SCAN = np.ones((H, 1, 1), dtype=np.float32)
SCAN[::3] = 0.86

def text_size(dr, s, f):
    b = dr.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1]

def fit_font(s, max_w, start):
    sz = start
    while sz > 14:
        f = font(sz)
        img = Image.new("RGB", (8, 8))
        dr = ImageDraw.Draw(img)
        w, _ = text_size(dr, s, f)
        if w <= max_w:
            return f
        sz -= 4
    return font(14)

def draw_center(base, s, y, f, fill=BONE):
    dr = ImageDraw.Draw(base)
    w, h = text_size(dr, s, f)
    dr.text(((W - w) / 2, y), s, font=f, fill=fill,
            stroke_width=2, stroke_fill=(0, 0, 0))
    return base

def to_pil(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ---------- overlays ----------
def apply_crt(arr, rng, flick=1.0, grain=5.0):
    a = arr * SCAN * flick
    if grain > 0:
        a = a + rng.standard_normal((H, W, 1)).astype(np.float32) * grain
    a = a * VIGNETTE
    return a

def letterbox(arr):
    arr[:90] = 0
    arr[-90:] = 0
    return arr

def tracking_bar(arr, y, h=7, alpha=0.35):
    y0 = max(0, int(y) % H)
    band = arr[y0:y0 + h].astype(np.float32)
    band = band * (1 - alpha) + np.array([200, 200, 200], np.float32) * alpha
    arr[y0:y0 + h] = band
    return arr

def chroma_split(arr, px=6):
    r = np.roll(arr[:, :, 0], px, axis=1)
    b = np.roll(arr[:, :, 2], -px, axis=1)
    out = arr.copy()
    out[:, :, 0] = r
    out[:, :, 2] = b
    return out

def osd(base, sec):
    dr = ImageDraw.Draw(base)
    dr.text((36, 104), "PLAY \u25b6  SP  09:%02d:%02d" % (sec // 60, sec % 60), font=F_OSD, fill=(230, 230, 230))
    dr.text((W - 150, 104), "CIELO-CAM", font=F_OSD, fill=(230, 230, 230))
    return base

# ---------- scenes (each returns float32 HxWx3) ----------
def sc1_base(t, rng):
    a = np.zeros((H, W, 3), np.float32) + BG
    # floor gradient (brighter near viewer)
    fl = np.linspace(0, 1, H)[:, None, None]
    a += np.array([22, 20, 16], np.float32) * (fl ** 3)
    # converging corridor edges: dark walls left/right, light shaft center
    shaft = np.clip(1 - np.abs(_nx) * 1.6, 0, 1)[..., None]
    a += np.array([30, 27, 20], np.float32) * shaft * (1 - fl * 0.5)
    side = np.clip(np.abs(_nx) - 0.55, 0, 1)[..., None]
    a += np.array([26, 24, 20], np.float32) * side * (1 - fl)
    # wall/ceiling edge lines converging to vanishing point
    img_lin = to_pil(a)
    dl = ImageDraw.Draw(img_lin)
    vpx, vpy = W / 2, 300
    for k in range(1, 5):
        off = k * 130
        dl.line([vpx - 40 - k * 8, vpy, off * 0.4, H], fill=(45, 42, 34), width=2)
        dl.line([vpx + 40 + k * 8, vpy, W - off * 0.4, H], fill=(45, 42, 34), width=2)
    a = np.asarray(img_lin).astype(np.float32)
    # ceiling light bars: thin, perspective-spaced, streaming toward viewer
    spd = 0.10
    for i in range(16):
        ph = ((i / 16.0) + t * spd) % 1.0
        depth = ph ** 3.0
        y = 150 + depth * 210
        hh = 1 + depth * 7
        halfw = 3 + depth * 150
        bright = 0.35 + 0.65 * (1 - depth)
        y0, y1 = int(max(0, y - hh)), int(min(H, y + hh))
        x0, x1 = int(max(0, W / 2 - halfw)), int(min(W, W / 2 + halfw))
        core = np.array([232, 197, 71], np.float32) * bright
        hgt = max(1, y1 - y0)
        a[y0:y1, x0:x1] = np.maximum(a[y0:y1, x0:x1], core * 0.85)
        # soft halo above/below, thin
        gy0, gy1 = max(0, y0 - 5), min(H, y1 + 5)
        a[gy0:gy1, x0:x1] = np.maximum(a[gy0:gy1, x0:x1], core * 0.18)
    # vanishing glow
    d = np.sqrt(_nx ** 2 * 0.7 + ((_yy / H - 0.42) * 2) ** 2)[..., None]
    a += np.array([60, 52, 30], np.float32) * np.clip(1 - d * 2.2, 0, 1)
    return a

def sc2_base(t, rng):
    a = np.zeros((H, W, 3), np.float32) + np.array([13, 16, 24], np.float32)
    img = to_pil(a)
    dr = ImageDraw.Draw(img)
    cols = [300, 640, 980]
    labels = ["COFFEE 09:15", "KEYS 10:00", "SMILES 24/7"]
    drift = int(math.sin(t * 1.3) * 6)
    # triptych cards ABOVE the title band; titles live at y 185-320, so keep
    # all pictograms clear: cards y 360-590, labels inside card bottom.
    for cx, lb in zip(cols, labels):
        dr.rounded_rectangle([cx - 130 + drift, 360, cx + 130 + drift, 590], 18, outline=(124, 116, 200), width=3)
        dr.text((cx - 95 + drift, 548), lb, font=F_SMALL, fill=(180, 180, 200))
    # coffee cup
    dr.rounded_rectangle([252 + drift, 410, 348 + drift, 500], 10, outline=BONE, width=4)
    dr.arc([348 + drift, 425, 392 + drift, 475], -80, 80, fill=BONE, width=4)
    dr.line([268 + drift, 390, 268 + drift, 372], fill=(150, 150, 160), width=3)
    dr.line([300 + drift, 390, 300 + drift, 372], fill=(150, 150, 160), width=3)
    dr.line([332 + drift, 390, 332 + drift, 372], fill=(150, 150, 160), width=3)
    # key
    dr.ellipse([592 + drift, 405, 648 + drift, 461], outline=MUSTARD, width=5)
    dr.rectangle([648 + drift, 428, 730 + drift, 440], fill=MUSTARD)
    dr.rectangle([700 + drift, 440, 710 + drift, 462], fill=MUSTARD)
    dr.rectangle([718 + drift, 440, 728 + drift, 462], fill=MUSTARD)
    # smiles — INSIDE the third card (cx 980, card x 850-1110, y 360-590):
    # three faces in a row at y 435, fully inside.
    for k in range(3):
        sx = 905 + k * 75 + drift
        sy = 445
        wrong = (k == 2)
        col = RED if wrong else BONE
        blink = wrong and (int(t * 7) % 4 == 0)
        dr.ellipse([sx - 26, sy - 26, sx + 26, sy + 26], outline=col, width=4)
        if not blink:
            dr.ellipse([sx - 12, sy - 10, sx - 4, sy - 2], fill=col)
            dr.ellipse([sx + 4, sy - 10, sx + 12, sy - 2], fill=col)
        else:
            dr.line([sx - 14, sy - 6, sx - 2, sy - 6], fill=RED, width=4)
            dr.line([sx + 2, sy - 6, sx + 14, sy - 6], fill=RED, width=4)
        dr.arc([sx - 14, sy - 4, sx + 14, sy + 22], 10, 170, fill=col, width=4)
    # bottom repeating smile strip — parks BELOW the cards, clear of titles
    for k in range(16):
        sx = 90 + k * 72
        sy = 610 + int(math.sin(t * 2 + k) * 3)
        c = RED if (k == 11 and int(t * 2) % 3 == 0) else (120, 120, 130)
        dr.ellipse([sx - 14, sy - 14, sx + 14, sy + 14], outline=c, width=2)
        dr.arc([sx - 8, sy - 2, sx + 8, sy + 12], 10, 170, fill=c, width=2)
    return np.asarray(img).astype(np.float32)

def sc3_base(t, rng):
    a = np.zeros((H, W, 3), np.float32) + np.array([8, 8, 10], np.float32)
    fl = np.linspace(0, 1, H)[:, None, None]
    a += np.array([20, 18, 14], np.float32) * (fl ** 3)
    # titles own y 155-330: keep the light-strip stream BELOW the band.
    # ceiling light strip rushing (lower half only)
    spd = 0.22
    for i in range(10):
        ph = ((i / 10.0) + t * spd) % 1.0
        depth = ph ** 2.2
        y = 350 + depth * 180
        hh = 2 + depth * 10
        halfw = 4 + depth * 150
        y0, y1 = int(max(0, y - hh)), int(min(H, y + hh))
        x0, x1 = int(max(0, W / 2 - halfw)), int(min(W, W / 2 + halfw))
        a[y0:y1, x0:x1] = np.maximum(a[y0:y1, x0:x1], np.array([210, 190, 150], np.float32) * (0.3 + 0.7 * (1 - depth)))
    # doors both sides, perspective crawl — parked in the lower half
    for i in range(7):
        ph = ((i / 7.0) + t * spd) % 1.0
        depth = ph ** 1.8
        y = 360 + depth * 260
        dh = 20 + depth * 190
        dw = 12 + depth * 90
        shimmer = 0.75 + 0.25 * math.sin(t * 3 + i * 1.7)
        for sgn in (-1, 1):
            cx = W / 2 + sgn * (60 + depth * 480)
            x0, x1 = int(cx - dw / 2), int(cx + dw / 2)
            y0, y1 = int(y - dh / 2), int(y + dh / 2)
            if x1 < 0 or x0 >= W:
                continue
            x0c, x1c = max(0, x0), min(W, x1)
            y0c, y1c = max(0, y0), min(H, y1)
            door = np.array([52, 46, 38], np.float32) * shimmer + BG.reshape(1, 1, 3) * 0.4
            # one door is slightly open: black slit
            a[y0c:y1c, x0c:x1c] = np.maximum(a[y0c:y1c, x0c:x1c], np.broadcast_to(door, (y1c - y0c, x1c - x0c, 3)))
            if i == 4 and sgn == 1:
                a[y0c:y1c, x0c:x0c + 4] = 2.0
    return a

def sc4_base(t, rng, burst_frames=0, frame_in_scene=0):
    if frame_in_scene < burst_frames:
        # signal-loss static burst
        return rng.integers(0, 256, (H, W, 3)).astype(np.float32)
    a = np.zeros((H, W, 3), np.float32) + np.array([6, 6, 8], np.float32)
    fl = np.linspace(0, 1, H)[:, None, None]
    a += np.array([14, 12, 12], np.float32) * (fl ** 3)
    # red glow behind door
    breathe = 1 + 0.03 * math.sin(t * 2 * math.pi * 0.5)
    dw, dh = int(150 * breathe), int(330 * breathe)
    cx, cy = W // 2, 360
    gx0, gx1 = max(0, cx - dw * 2), min(W, cx + dw * 2)
    gy0, gy1 = max(0, cy - dh), min(H, cy + dh)
    yy = ((_yy[gy0:gy1, gx0:gx1] - cy) / dh) ** 2
    xx = ((_xx[gy0:gy1, gx0:gx1] - cx) / dw) ** 2
    glowm = np.clip(1 - (xx + yy), 0, 1)[..., None]
    a[gy0:gy1, gx0:gx1] += np.array([120, 10, 16], np.float32) * glowm
    # door
    x0, x1 = cx - dw // 2, cx + dw // 2
    y0, y1 = cy - dh // 2, cy + dh // 2
    door = np.array([150, 12, 22], np.float32) * (0.85 + 0.15 * math.sin(t * 4))
    a[y0:y1, x0:x1] = door
    # door panels
    a[y0 + 20:y1 - 20, x0 + 18:x0 + 24] = np.array([90, 8, 14], np.float32)
    a[y0 + 20:y1 - 20, x1 - 24:x1 - 18] = np.array([90, 8, 14], np.float32)
    # knob
    kx, ky = x1 - 34, cy + 10
    a[ky - 5:ky + 5, kx - 5:kx + 5] = np.array([220, 200, 150], np.float32)
    # pulse ring
    rp = ((t * 0.5) % 1.0)
    rr = int(40 + rp * 260)
    alpha = (1 - rp) * 60
    yyr = np.abs(np.sqrt((_nx) ** 2 + ((_yy / H - 0.5) * 2) ** 2) * 560 - rr) < 3
    a[yyr] += np.array([alpha * 2.4, alpha * 0.12, alpha * 0.16], np.float32)
    return a

def sc5_base(t, rng):
    a = np.zeros((H, W, 3), np.float32) + np.array([12, 10, 8], np.float32)
    img = to_pil(a)
    dr = ImageDraw.Draw(img)
    sway = math.sin(t * 1.8) * 8
    kid = 0
    # key wall lives in the BOTTOM half (y 330-560); titles own y 155-290.
    for ry in range(3):
        for cx in range(10):
            kid += 1
            if (ry * 10 + cx) % 7 == 0:
                continue  # missing key: someone took it. someone never came back.
            x = 130 + cx * 105
            y = 340 + ry * 75
            ox = sway if kid == 23 else 0
            dr.line([x + ox, y, x + ox, y + 26], fill=(150, 130, 90), width=2)
            dr.ellipse([x + ox - 8, y + 26, x + ox + 8, y + 42], outline=(190, 160, 100), width=3)
            dr.line([x + ox + 8, y + 34, x + ox + 22, y + 34], fill=(190, 160, 100), width=3)
            if kid == 23:
                dr.rectangle([x + ox - 14, y + 46, x + ox + 14, y + 62], fill=(193, 18, 31))
            else:
                dr.rectangle([x + ox - 14, y + 46, x + ox + 14, y + 62], outline=(150, 140, 120))
    # chairs silhouette foreground
    for cx in (430, 850):
        dr.rounded_rectangle([cx - 90, 520, cx + 90, 560], 8, fill=(5, 5, 7))
        dr.rectangle([cx - 78, 560, cx - 66, 660], fill=(5, 5, 7))
        dr.rectangle([cx + 66, 560, cx + 78, 660], fill=(5, 5, 7))
        dr.rounded_rectangle([cx - 90, 430, cx + 90, 525], 14, fill=(8, 8, 10))
    # dust
    for k in range(40):
        x = (k * 173 + int(t * 12 * (1 + k % 3))) % W
        y = (k * 311 - int(t * 7 * (1 + k % 2))) % H
        if 90 < y < 630:
            dr.point((x, y), fill=(110, 100, 80))
    return np.asarray(img).astype(np.float32)

def sc6_base(t, rng):
    a = np.zeros((H, W, 3), np.float32)
    # flicker pattern: on, with dropouts; dies at t>8
    if t > 8.2:
        on = 0.0
    else:
        drop = (int(t * 9) % 11 == 0) or (4.0 < t < 4.35)
        on = 0.0 if drop else (0.75 + 0.25 * math.sin(t * 40))
    if on > 0:
        cx, cy, hw, hh = W // 2, 300, 330, 13
        gy = np.clip(1 - (np.abs(_yy - cy) / 130.0), 0, 1)[..., None]
        gx = np.clip(1 - (np.abs(_xx - cx) / 460.0), 0, 1)[..., None]
        a += np.array([200, 190, 160], np.float32) * (gy * gx) * on * 0.8
        a[cy - hh:cy + hh, cx - hw:cx + hw] = np.array([245, 244, 235], np.float32) * (0.3 + 0.7 * on)
    return a

TITLES = {
    "sc1": [("AN AVERAGE DAY AT CIELO", 200, 54, BONE), ("CIELO HOUSING CO. \u2014 9:00 AM", 285, 26, (170, 170, 180))],
    "sc2": [("EVERY SMILE.", 165, 54, BONE), ("HELD TOO LONG.", 245, 54, BONE)],
    "sc3": [("9:00 AM.", 155, 60, BONE), ("AGAIN.", 240, 60, (232, 197, 71))],
    "sc4": [("DO NOT MIND THE DOORS.", 545, 44, BONE)],
    "sc5": [("THE HOMES KEEP", 155, 50, BONE), ("THEIR PEOPLE.", 225, 50, (255, 60, 70))],
    "sc6": [("CIELO. FOREVER.", 420, 58, BONE), ("an average day.", 495, 26, (140, 140, 150))],
}

def render_scene(sid, base_fn, seed, extra=None):
    rng = np.random.default_rng(seed)
    path = os.path.join(FR, sid + ".mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "20", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    titles = TITLES[sid]
    for f in range(N):
        t = f / FPS
        sec = f // FPS
        if sid == "sc4":
            arr = base_fn(t, rng, burst_frames=14, frame_in_scene=f)
        else:
            arr = base_fn(t, rng)
        flick = 1.0
        if sid == "sc6":
            flick = 1.0
        elif int(t * 9) % 13 == 0 and sid in ("sc2", "sc3"):
            flick = 0.55
        arr = apply_crt(arr, rng, flick=flick, grain=6.0 if sid == "sc4" else 5.0)
        # periodic chroma glitch
        if sid in ("sc2", "sc3") and int(t * 2.2) % 5 == 0 and (f % FPS) < 4:
            arr = chroma_split(np.clip(arr, 0, 255), px=7)
        if sid == "sc4" and 14 <= f < 20:
            arr = chroma_split(np.clip(arr, 0, 255), px=10)
        # VHS tracking bar sweep
        if sid in ("sc1", "sc3", "sc4"):
            y = (f * 9) % (H + 120) - 60
            arr = tracking_bar(np.clip(arr, 0, 255), y)
        img = to_pil(arr)
        img = osd(img, sec)
        for txt, y, size, col in titles:
            ff = fit_font(txt, 1080, size)
            # red card behind reveal line in sc5
            if sid == "sc5" and col != BONE:
                dr0 = ImageDraw.Draw(img)
                w0, h0 = text_size(dr0, txt, ff)
                dr0.rectangle([(W - w0) / 2 - 24, y - 8, (W + w0) / 2 + 24, y + h0 + 8], fill=(90, 8, 14))
            draw_center(img, txt, y, ff, fill=col)
        arr = np.asarray(img).astype(np.float32)
        arr = letterbox(arr)
        try:
            proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
        except BrokenPipeError:
            break
    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed for {sid}")
    print(f"{sid} done -> {path}", flush=True)

def main():
    os.makedirs(FR, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    jobs = [("sc1", sc1_base, 11), ("sc2", sc2_base, 22), ("sc3", sc3_base, 33),
            ("sc4", sc4_base, 44), ("sc5", sc5_base, 55), ("sc6", sc6_base, 66)]
    for sid, fn, seed in jobs:
        if only and sid != only:
            continue
        render_scene(sid, fn, seed)

if __name__ == "__main__":
    main()
