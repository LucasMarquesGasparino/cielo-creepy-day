#!/usr/bin/env python3
"""CIELO v2 — shared core: 1920x1080 helpers, mascot, CCTV grade, OSD, grain.

CCTV truth (from Opus analysis):
- cool green-grey grade, NOT warm orange; red reserved for accents
- OSD: REC top-left, CAM 03 - FLOOR 3 top-right (pixel font, cyan-grey)
- bottom band: CIELO B.V. left, SEP 22 2026 HH:MM:SS right (clock runs)
- bottom-center subtitles: white on translucent black bar (corporate PA voice)
- sticky notes: DON'T ANSWER 4B (yellow, left), 3rd floor = NO (green, right),
  count the doors (pink, bottom-right)
- CRT: vignette + scanlines + tracking noise band + luma flicker; static
  bursts on transitions; red EXIT tag on clock beat; end card returns to logo.
"""
import glob
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30

PROJ = os.path.expanduser("~/projects/cielo-creepy-day")
FR2 = os.path.join(PROJ, "assets", "frames2")
os.makedirs(FR2, exist_ok=True)

# ---------- palette ----------
INK = (26, 42, 58)            # dark navy ink
TEAL = (13, 148, 136)         # brand teal
TEAL_DK = (10, 110, 100)
RED = (226, 60, 48)           # brand red
RED_DK = (150, 30, 26)
CREAM = (248, 243, 232)
PAPER = (235, 228, 214)
YELLOW = (250, 215, 90)
GREEN = (110, 200, 140)
BLUE = (140, 175, 220)
GREY = (120, 130, 140)
BONE = (240, 235, 220)
OSD_CYAN = (150, 230, 220)

# CCTV cool grade base
CCTV_BG = np.array([16, 22, 20], dtype=np.float32)
CCTV_WALL_TOP = (88, 104, 96)
CCTV_WALL_BOT = (38, 52, 58)

# ---------- fonts ----------
def _candidates():
    out = []
    for pat in ("/system/fonts/*.ttf", "/system/fonts/*.otf"):
        out.extend(glob.glob(pat))
    return sorted(out)

_FONTS = _candidates()

def _pick(names):
    for p in _FONTS:
        b = os.path.basename(p).lower()
        if any(n in b for n in names):
            return p
    return None

MONO = _pick(["cutive", "droidsansmono", "mono"]) or (_FONTS[0] if _FONTS else None)
BOLD = _pick(["droidsans-bold", "roboto-bold", "bold"]) or MONO
PLAIN = _pick(["droidsans", "roboto-regular"]) or MONO

def font(path, size):
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def mono(size):
    return font(MONO, size)

def bold(size):
    return font(BOLD, size)

# ---------- masks (computed once) ----------
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_nx = (_xx / W - 0.5) * 2
_ny = (_yy / H - 0.5) * 2
VIGN = np.clip(1.0 - 0.34 * (_nx ** 2 + _ny ** 2), 0.45, 1.0)[..., None].astype(np.float32)
SCAN = np.ones((H, 1, 1), dtype=np.float32)
SCAN[::3] = 0.90
SCAN[1::3] = 0.96

def to_pil(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def text_w(dr, s, f):
    b = dr.textbbox((0, 0), s, font=f)
    return b[2] - b[0]

def cctv_base(t, rng, flicker=True):
    """Cool CCTV room tone: vertical gradient + vignette + scanlines + noise."""
    fl = (_yy / H)[..., None]
    a = np.zeros((H, W, 3), np.float32) + CCTV_BG
    a += (np.array(CCTV_WALL_TOP, np.float32) - CCTV_BG) * (1 - fl) * 0.55
    a += (np.array(CCTV_WALL_BOT, np.float32) - CCTV_BG) * fl * 0.6
    a = a * SCAN
    if flicker:
        a *= 0.97 + 0.03 * math.sin(t * 47.0) * math.sin(t * 13.7)
    a += rng.standard_normal((H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1) * 4.2
    a *= VIGN
    return a

def noise_band(arr, y, h=26, amp=26.0, seed=0):
    rng = np.random.default_rng(seed)
    y0 = max(0, min(H - h, int(y)))
    arr[y0:y0 + h] = np.clip(
        arr[y0:y0 + h] + rng.standard_normal((h, W, 3)).astype(np.float32) * amp, 0, 255)
    return arr

def static_burst(shape_rng, amt=1.0):
    return (shape_rng.integers(0, 256, (H, W, 3)).astype(np.float32) - 128) * amt

def draw_osd(img, clock_s, cam="CAM 03 \u2022 FLOOR 3", rec=True):
    dr = ImageDraw.Draw(img)
    f = mono(30)
    if rec:
        dr.text((60, 36), "REC", font=f, fill=(235, 235, 235),
                stroke_width=1, stroke_fill=(0, 0, 0))
        dr.ellipse([36, 42, 50, 56], fill=(220, 40, 30))
    dr.text((W - 60 - text_w(dr, cam, f), 36), cam, font=f, fill=(200, 215, 210),
            stroke_width=1, stroke_fill=(0, 0, 0))
    return img

def draw_bottomband(img, clock_s, left="CIELO B.V."):
    dr = ImageDraw.Draw(img)
    f = mono(28)
    hh = int(clock_s // 3600) % 24
    mm = int(clock_s // 60) % 60
    ss = int(clock_s) % 60
    right = "SEP 22 2026  %02d:%02d:%02d" % (hh, mm, ss)
    dr.text((60, H - 56), left, font=f, fill=(150, 170, 165),
            stroke_width=1, stroke_fill=(0, 0, 0))
    dr.text((W - 60 - text_w(dr, right, f), H - 56), right, font=f,
            fill=(150, 170, 165), stroke_width=1, stroke_fill=(0, 0, 0))
    return img

def draw_sub(img, line1, line2=None):
    dr = ImageDraw.Draw(img)
    f = mono(32)
    lines = [line1] if line2 is None else [line1, line2]
    widths = [text_w(dr, s, f) for s in lines]
    bw = max(widths) + 56
    bh = 52 * len(lines) + 24
    y0 = H - 150 - bh
    x0 = (W - bw) / 2
    dr.rectangle([x0, y0, x0 + bw, y0 + bh], fill=(0, 0, 0, 170))
    # PIL has no alpha on RGB base; emulate with dark bar
    dr.rectangle([x0, y0, x0 + bw, y0 + bh], fill=(8, 10, 12))
    for i, s in enumerate(lines):
        dr.text(((W - widths[i]) / 2, y0 + 12 + i * 52), s, font=f, fill=(245, 245, 245))
    return img

def sticky(img, x, y, lines, bg, rot_deg=0, fsize=30):
    f = mono(fsize)
    dr0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    wmax = max(text_w(dr0, s, f) for s in lines)
    bw, bh = wmax + 44, 40 * len(lines) + 28
    note = Image.new("RGB", (int(bw), int(bh)), bg)
    dn = ImageDraw.Draw(note)
    for i, s in enumerate(lines):
        dn.text((22, 14 + i * 40), s, font=f, fill=(40, 40, 40))
    if rot_deg:
        note = note.rotate(rot_deg, expand=True, fillcolor=(10, 10, 10))
    img.paste(note, (int(x), int(y)))
    return img

# ---------- mascot: teal house, red roof (frame-filling hero OK) ----------
def draw_house(dr, cx, base_y, s, ink_w=None):
    """Flat mascot house centered at cx, base at base_y, scale s (body w)."""
    ink_w = ink_w or max(6, int(s * 0.045))
    bw, bh = s, s * 0.72
    x0, x1 = cx - bw / 2, cx + bw / 2
    y0, y1 = base_y - bh, base_y
    # body
    dr.rounded_rectangle([x0, y0, x1, y1], radius=int(s * 0.06), fill=TEAL, outline=INK, width=ink_w)
    # roof
    peak = y0 - s * 0.52
    dr.polygon([(x0 - s * 0.09, y0 + 6), (cx, peak), (x1 + s * 0.09, y0 + 6)],
               fill=RED, outline=INK)
    # redraw roof outline thick
    dr.line([x0 - s * 0.09, y0 + 6, cx, peak], fill=INK, width=ink_w)
    dr.line([cx, peak, x1 + s * 0.09, y0 + 6], fill=INK, width=ink_w)
    # round window
    wr = s * 0.14
    wy = y0 - s * 0.20
    dr.ellipse([cx - wr, wy - wr, cx + wr, wy + wr], fill=CREAM, outline=INK, width=max(4, ink_w - 2))
    dr.line([cx - wr, wy, cx + wr, wy], fill=INK, width=max(3, ink_w - 3))
    dr.line([cx, wy - wr, cx, wy + wr], fill=INK, width=max(3, ink_w - 3))
    # chimney
    chx = x1 - s * 0.16
    dr.rectangle([chx, peak + s * 0.10, chx + s * 0.12, y0 - s * 0.02], fill=RED, outline=INK, width=max(4, ink_w - 2))
    # door
    dw, dh = s * 0.20, bh * 0.52
    dr.rounded_rectangle([cx - dw / 2, y1 - dh, cx + dw / 2, y1 + 4], radius=int(dw * 0.25),
                         fill=INK)
    dr.ellipse([cx + dw * 0.22, y1 - dh * 0.45, cx + dw * 0.32, y1 - dh * 0.35], fill=YELLOW)
    # side windows
    for sx in (x0 + bw * 0.24, x1 - bw * 0.24):
        ww = s * 0.11
        wyy = y0 + bh * 0.30
        dr.rounded_rectangle([sx - ww, wyy - ww, sx + ww, wyy + ww], radius=int(ww * 0.3),
                             fill=CREAM, outline=INK, width=max(4, ink_w - 2))
    return (x0, peak, x1, y1)

def draw_sun(img, cx, cy, r, face="smile"):
    dr = ImageDraw.Draw(img)
    n = 12
    for i in range(n):
        ang = i / n * 2 * math.pi
        x1 = cx + math.cos(ang) * (r + 8)
        y1 = cy + math.sin(ang) * (r + 8)
        x2 = cx + math.cos(ang) * (r + 34)
        y2 = cy + math.sin(ang) * (r + 34)
        dr.line([x1, y1, x2, y2], fill=(245, 180, 60), width=10)
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(250, 200, 80), outline=(230, 150, 40), width=5)
    if face == "smile":
        dr.arc([cx - r * 0.4, cy - r * 0.3, cx - r * 0.05, cy + r * 0.05], 200, 340, fill=(120, 70, 20), width=5)
        dr.arc([cx + r * 0.05, cy - r * 0.3, cx + r * 0.4, cy + r * 0.05], 200, 340, fill=(120, 70, 20), width=5)
        dr.arc([cx - r * 0.35, cy, cx + r * 0.35, cy + r * 0.6], 20, 160, fill=(120, 70, 20), width=6)
    elif face == "grin":
        dr.ellipse([cx - r * 0.42, cy - r * 0.25, cx - r * 0.18, cy - r * 0.05], fill=(60, 30, 10))
        dr.ellipse([cx + r * 0.18, cy - r * 0.25, cx + r * 0.42, cy - r * 0.05], fill=(60, 30, 10))
        dr.chord([cx - r * 0.55, cy - r * 0.1, cx + r * 0.55, cy + r * 0.62], 0, 180, fill=(70, 20, 15),
                 outline=(120, 70, 20), width=4)
        for tx in np.linspace(cx - r * 0.4, cx + r * 0.4, 6):
            dr.line([tx, cy + r * 0.22, tx, cy + r * 0.42], fill=(240, 240, 240), width=3)
    return img

def confetti(dr, rng, t, area, n=26, cols=None):
    cols = cols or [TEAL, RED, YELLOW, BLUE, (120, 90, 200), GREEN]
    x0, y0, x1, y1 = area
    for i in range(n):
        x = x0 + (rng.random() * (x1 - x0) + t * (20 + (i % 5) * 12)) % (x1 - x0)
        y = y0 + (rng.random() * (y1 - y0) + t * (10 + (i % 3) * 8)) % (y1 - y0)
        c = cols[i % len(cols)]
        k = i % 5
        if k == 0:
            dr.ellipse([x - 9, y - 9, x + 9, y + 9], outline=c, width=5)
        elif k == 1:
            dr.line([x - 10, y - 10, x + 10, y + 10], fill=c, width=6)
            dr.line([x - 10, y + 10, x + 10, y - 10], fill=c, width=6)
        elif k == 2:
            dr.line([x - 14, y, x + 14, y, x + 6, y - 12], fill=c, width=5)
        elif k == 3:
            dr.arc([x - 12, y - 12, x + 12, y + 12], 0, 270, fill=c, width=5)
        else:
            r = int(6 + rng.random() * 6)
            dr.ellipse([x - r, y - r, x + r, y + r], fill=c)
