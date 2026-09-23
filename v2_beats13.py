#!/usr/bin/env python3
"""CIELO v2 beats 1-3: logo card (0-6s), logo glitch (6-9s), corridor (9-16s).

1920x1080 @ 30fps. Each beat renders its own mp4 via ffmpeg rawvideo pipe.
Beat 1: sky gradient, sun smile, confetti, hills + house row, big house hero,
  CIELO two-tone wordmark typing, tagline 'Where every tenant stays.',
  bottom black bar 'AN AVERAGE DAY AT CIELO HOUSING CO.' rises at 2.5s.
  At 5.2s: sun grin + red flash 2 frames (subliminal), wordmark C??LO.
Beat 2: RGB-split glitch storm on frozen logo frame + 'AN AVERAGE DAY AT WORK'
  typing fast, then signal loss to black.
Beat 3: CCTV corridor cool grade, doors both sides, PA sub, figure silhouette
  far end that VANISHES on cut (Opus t15: empty hall). OSD + clock + stickies.
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

from v2_core import (BONE, CREAM, INK, RED, TEAL, YELLOW, W, H, FPS, FR2, draw_house,
                     draw_sun, confetti, cctv_base, to_pil, draw_osd, draw_bottomband,
                     draw_sub, sticky, mono, bold, text_w, noise_band, static_burst)

BRAND = "Cielo"


def sky(t):
    yy = np.linspace(0, 1, H)[:, None, None]
    top = np.array([105, 175, 225], np.float32)
    mid = np.array([150, 215, 225], np.float32)
    bot = np.array([175, 225, 215], np.float32)
    a = np.zeros((H, W, 3), np.float32)
    m = np.clip(yy * 2, 0, 1)
    a += top * (1 - m) + mid * m
    m2 = np.clip((yy - 0.5) * 2, 0, 1)
    a = a * (1 - m2) + bot * m2
    return a


def hills(dr, t):
    for k, (ybase, amp, col) in enumerate([(830, 60, (110, 195, 140)), (900, 70, (80, 175, 120))]):
        pts = []
        for x in range(0, W + 40, 40):
            y = ybase + math.sin(x / 420 + k * 2 + t * 0.15) * amp
            pts.append((x, y))
        pts += [(W, H), (0, H)]
        dr.polygon(pts, fill=col)


def mini_house(dr, cx, base, s=46):
    x0, x1 = cx - s / 2, cx + s / 2
    y0 = base - s * 0.62
    dr.rectangle([x0, y0, x1, base], fill=(20, 160, 150), outline=INK, width=3)
    dr.polygon([(x0 - 6, y0), (cx, y0 - s * 0.42), (x1 + 6, y0)], fill=RED, outline=INK)
    dr.rectangle([cx - 7, base - 22, cx + 7, base], fill=INK)


def beat1(rng):
    path = os.path.join(FR2, "b1_logo.mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "19", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    N = 6 * FPS
    for f in range(N):
        t = f / FPS
        grin = (5.2 <= t < 6.0)
        a = sky(t)
        img = to_pil(a)
        draw_sun(img, 1650, 190, 95, face="grin" if grin else "smile")
        dr = ImageDraw.Draw(img)
        confetti(dr, rng, t, (60, 60, W - 60, 760), n=30)
        hills(dr, t)
        for i, hx in enumerate(np.linspace(120, 1800, 9)):
            mini_house(dr, hx, 850 + math.sin(i * 1.3) * 22)
        draw_house(dr, W / 2, 640, 300)
        # wordmark typing
        full1, full2 = "Cie", "lo"
        nchars = min(5, int(t * 4) + 1)
        w1 = full1[:min(3, nchars)]
        w2 = full2[:max(0, nchars - 3)] if nchars > 3 else ""
        if 5.3 <= t < 5.7:
            w1, w2 = "C??", "LO"
        f1, f2 = bold(150), bold(150)
        ywm = 700
        ww1 = text_w(dr, w1, f1)
        ww2 = text_w(dr, w2, f2)
        tot = text_w(dr, "Cielo", f1)
        x0 = (W - tot) / 2
        dr.text((x0, ywm), w1, font=f1, fill=INK)
        dr.text((x0 + ww1, ywm), w2, font=f2, fill=TEAL)
        # tagline
        if t > 1.2:
            ft = bold(44)
            tag = "Where every tenant stays."
            if 5.3 <= t < 5.7:
                tag = "Where every tenant sta_s."
            dr.text(((W - text_w(dr, tag, ft)) / 2, 880), tag, font=ft, fill=INK)
        # bottom bar rises
        if t > 2.5:
            by = int(H - min(1.0, (t - 2.5) * 2) * 120)
            dr.rectangle([0, by, W, H], fill=(10, 12, 14))
            fb = mono(40)
            bar = "AN AVERAGE DAY AT CIELO HOUSING CO."
            dr.text(((W - text_w(dr, bar, fb)) / 2, by + 32), bar, font=fb, fill=BONE)
        arr = np.asarray(img).astype(np.float32)
        # subliminal red flash
        if 5.2 <= t < 5.27:
            arr = arr * 0.3 + np.array([200, 20, 20], np.float32) * 0.7
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    print("b1 done", flush=True)


def rgb_split(arr, px=14):
    out = arr.copy()
    out[:, :, 0] = np.roll(arr[:, :, 0], px, axis=1)
    out[:, :, 2] = np.roll(arr[:, :, 2], -px, axis=1)
    return out


def beat2(rng):
    # frozen logo frame: rebuild a static logo then storm it
    a = sky(5.9)
    img = to_pil(a)
    draw_sun(img, 1650, 190, 95, face="grin")
    dr = ImageDraw.Draw(img)
    confetti(dr, rng, 5.9, (60, 60, W - 60, 760), n=30)
    hills(dr, 5.9)
    for i, hx in enumerate(np.linspace(120, 1800, 9)):
        mini_house(dr, hx, 850 + math.sin(i * 1.3) * 22)
    draw_house(dr, W / 2, 640, 300)
    f1 = bold(150)
    dr.text(((W - text_w(dr, "Cielo", f1)) / 2, 700), "Cielo", font=f1, fill=INK)
    base = np.asarray(img).astype(np.float32)
    path = os.path.join(FR2, "b2_glitch.mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "19", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    N = 3 * FPS
    for f in range(N):
        t = f / FPS
        arr = base.copy()
        if t < 2.2:
            arr = rgb_split(arr, px=int(6 + 22 * abs(math.sin(t * 9))))
            arr += static_burst(rng, amt=0.35)
            # slice displacement
            for _ in range(4):
                y0 = rng.integers(0, H - 60)
                arr[y0:y0 + 30] = np.roll(arr[y0:y0 + 30], rng.integers(-120, 120), axis=1)
            img2 = to_pil(arr)
            d2 = ImageDraw.Draw(img2)
            fb = mono(44)
            msg = "AN AVERAGE DAY AT WORK"[:min(22, int(t * 14) + 1)]
            d2.rectangle([0, H - 130, W, H], fill=(10, 12, 14))
            d2.text(((W - text_w(d2, msg, fb)) / 2, H - 100), msg, font=fb, fill=BONE)
            arr = np.asarray(img2).astype(np.float32)
        else:
            # signal loss to black
            k = min(1.0, (t - 2.2) * 2)
            arr = arr * (1 - k) + static_burst(rng, amt=0.5 * (1 - k))
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    print("b2 done", flush=True)


def corridor(t, rng, figure=True):
    """True one-point-perspective CCTV hallway: vanishing point at eye level,
    ceiling plane + floor plane + side walls, doors planted on the floor on
    both walls shrinking toward the vp, ceiling light bars growing toward
    camera, red extinguisher + posters + clock, silhouette figure far end."""
    a = cctv_base(t, rng)
    img = to_pil(a)
    dr = ImageDraw.Draw(img)
    vpx, vpy = W / 2, 470
    # --- planes: wall base, ceiling, floor ---
    dr.rectangle([0, 0, W, H], fill=(74, 90, 92))                       # wall tone
    dr.polygon([(0, 0), (W, 0), (vpx + 130, vpy - 55), (vpx - 130, vpy - 55)],
               fill=(52, 64, 66))                                        # ceiling
    dr.polygon([(0, H), (W, H), (vpx + 130, vpy + 70), (vpx - 130, vpy + 70)],
               fill=(26, 36, 38))                                        # floor
    # wainscot: darker band along walls down to floor
    dr.polygon([(0, 700), (0, H), (vpx - 130, vpy + 70), (vpx - 130, vpy + 40)],
               fill=(34, 48, 52))
    dr.polygon([(W, 700), (W, H), (vpx + 130, vpy + 70), (vpx + 130, vpy + 40)],
               fill=(34, 48, 52))
    # chair-rail lines converging to vp
    for y0 in (700, 300):
        dr.line([0, y0, vpx - 130, vpy + (40 if y0 > 500 else -30)], fill=(60, 74, 76), width=3)
        dr.line([W, y0, vpx + 130, vpy + (40 if y0 > 500 else -30)], fill=(60, 74, 76), width=3)
    # ceiling tile seams radiating from vp
    for k in range(-5, 6):
        dr.line([vpx + k * 14, vpy - 55, vpx + k * 330, 0], fill=(62, 74, 76), width=2)
    # floor boards converging to vp
    for k in range(-9, 10):
        dr.line([vpx + k * 12, vpy + 70, vpx + k * 190, H], fill=(22, 31, 33), width=2)
    # floor sheen
    dr.polygon([(vpx - 130, vpy + 70), (vpx + 130, vpy + 70), (vpx + 420, H), (vpx - 420, H)],
               fill=(44, 60, 62))
    # ceiling light bars: far/small near vp, near/big toward camera
    for i in range(6):
        tt = i / 5.0                       # 0 far .. 1 near
        y = vpy - 55 - (1 - tt) ** 1.7 * 330
        hw = 14 + tt ** 1.6 * 330
        hh = 3 + tt * 20
        tone = int(140 + tt * 90)
        dr.rectangle([vpx - hw / 2, y, vpx + hw / 2, y + hh],
                     fill=(min(255, tone), min(255, tone + 10), tone))
    # doors: interpolate near (big, frame edge, floor) -> far (small, near vp)
    for sgn in (-1, 1):
        for i in range(4):
            tt = i / 3.0                   # 0 near .. 1 far
            far = tt
            w = 230 * (1 - far) + 34
            h = 640 * (1 - far) + 110
            edge = 30 if sgn < 0 else W - 30
            x_in = edge + sgn * (w + 8)
            # push toward center with distance
            cx = x_in - sgn * far * 560
            y_base = 1040 - far * 400
            x0, x1 = (cx - w, cx) if sgn < 0 else (cx, cx + w)
            y0, y1 = y_base - h, y_base
            dr.rectangle([x0, y0, x1, y1], fill=(40, 58, 60),
                         outline=(16, 24, 26), width=max(2, int(5 * (1 - far) + 1)))
            # brass number plate top-outer corner
            pw, phh = w * 0.40, 22 + (1 - far) * 16
            px0 = x0 + 10 if sgn < 0 else x1 - 10 - pw
            dr.rectangle([px0, y0 + 12, px0 + pw, y0 + 12 + phh], fill=(198, 176, 92))
            # knob on inner edge
            kx = x1 - 16 if sgn < 0 else x0 + 16
            kr = 3 + (1 - far) * 5
            dr.ellipse([kx - kr, (y0 + y1) / 2 - kr, kx + kr, (y0 + y1) / 2 + kr],
                       fill=(185, 172, 140))
    # red extinguisher cabinet + canister, left wall mid-ground
    dr.rectangle([300, 330, 400, 470], outline=RED, width=7)
    dr.rectangle([330, 500, 372, 700], fill=(168, 38, 32))
    dr.rectangle([338, 478, 364, 502], fill=(20, 20, 20))
    # posters on right wall
    for px, py, pw, phh in ((1330, 350, 110, 150), (1480, 440, 95, 130)):
        dr.rectangle([px, py, px + pw, py + phh], fill=(205, 200, 185),
                     outline=(30, 30, 30), width=3)
        dr.line([px + 12, py + 24, px + pw - 12, py + 24], fill=(120, 120, 120), width=3)
        dr.line([px + 12, py + 40, px + pw - 12, py + 40], fill=(140, 140, 140), width=3)
    # wall clock right
    dr.ellipse([1600, 270, 1675, 345], outline=(205, 205, 200), width=5)
    dr.line([1637, 307, 1637, 284], fill=(205, 205, 200), width=4)
    dr.line([1637, 307, 1654, 314], fill=(205, 205, 200), width=4)
    # figure far end: small silhouette at vp + white badge, swaying
    if figure:
        fx = vpx + math.sin(t * 0.8) * 5
        fy = vpy + 78
        s = 0.85
        dr.ellipse([fx - 20 * s, fy - 150 * s, fx + 20 * s, fy - 106 * s], fill=(6, 8, 10))
        dr.rectangle([fx - 30 * s, fy - 106 * s, fx + 30 * s, fy + 10 * s], fill=(6, 8, 10))
        dr.rectangle([fx - 26 * s, fy + 10 * s, fx - 8 * s, fy + 105 * s], fill=(6, 8, 10))
        dr.rectangle([fx + 8 * s, fy + 10 * s, fx + 26 * s, fy + 105 * s], fill=(6, 8, 10))
        dr.rectangle([fx - 13, fy - 78, fx + 13, fy - 46], fill=(225, 225, 225))
    return to_pil(np.asarray(img).astype(np.float32))


def beat3(rng):
    path = os.path.join(FR2, "b3_corr.mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "19", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    N = 7 * FPS
    for f in range(N):
        t = f / FPS
        # figure vanishes at 4.5s (Opus: empty hall on cut)
        img = corridor(t, rng, figure=(t < 4.5))
        img = draw_osd(img, 9 * 3600 + t)
        img = sticky(img, 40, 300, ["DON'T", "ANSWER", "4B"], (250, 230, 130), rot_deg=-4)
        img = sticky(img, W - 230, 300, ["3rd floor", "= NO"], (170, 230, 170), rot_deg=3)
        img = sticky(img, W - 260, 800, ["count", "the doors"], (245, 180, 200), rot_deg=-2)
        img = draw_sub(img, "[PA] Good morning, staff. Please remember:",
                       "the third floor does not exist.")
        img = draw_bottomband(img, 9 * 3600 + t)
        arr = np.asarray(img).astype(np.float32)
        if int(t * 7) % 9 == 0:
            arr = noise_band(arr, (f * 37) % H, seed=f)
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    print("b3 done", flush=True)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    rng = np.random.default_rng(11)
    if which in ("all", "b1"):
        beat1(np.random.default_rng(11))
    if which in ("all", "b2"):
        beat2(np.random.default_rng(12))
    if which in ("all", "b3"):
        beat3(np.random.default_rng(13))
