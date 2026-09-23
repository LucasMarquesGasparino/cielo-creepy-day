#!/usr/bin/env python3
"""CIELO v2 beats 7-10: blueprint (31-38s), meeting (38-45s), clock (45-52s),
end card (52-60s).

Beat 7: blueprint deep-blue pan: FOR RENT card (Unit 4B Block C, 3 rooms
  62m2, 742/month, Cozy), floor plan draws itself left->right (LIVING, KITCHEN,
  BATH, STORAGE, HALL, BED 1, BED 2, CRAWLSPACE, ROOM FOR YOU), red ink
  annotations appear ('don't sleep in bed 2', hatch on bath, tallies),
  subs: 'Spacious 3-room apartment...' -> 'Previous tenant... included.'
Beat 8: dark meeting room: projector screen Q3 RESULTS (Occupancy 100%,
  Satisfaction 100%, Departures .), then glitch to DEPARTURES donut chart
  (red humanoid vs teal blob, 'Where do tenants go? Nowhere. 100%.'),
  presenter silhouette right, audience head rows, YOU placard front,
  sub: 'Great quarter, everyone. Occupancy: 100%. Departures: zero.'
Beat 9: wall clock macro: STAY tag top-left, EXIT sign, clock face, hands spin
  fast then hour hand creeps to 5, numerals corrupt to 9s, 'Cielo
  QUARTZ-ETERNAL', teal chyron '17:00 CLOCK OUT an average day at work',
  sub: 'Five o'clock. Time to clock out. The clock disagrees.'
Beat 10: end card = logo world restored: sky, sun smile, confetti, hills,
  house, CIELO, 'Thank you for your service.', then typed red additions:
  'See you tomorrow at 09:00.' + 'Waiting list position: #01 (you)' +
  'welcome home', footer 'Cielo B.V. - employee orientation - tape 1 of oo'.
  Final 2s: RGB-split + static storm, last frame holds logo.
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

from v2_core import (BONE, CREAM, INK, RED, TEAL, YELLOW, GREEN, BLUE, W, H, FPS, FR2,
                     draw_house, draw_sun, confetti, cctv_base, to_pil, draw_osd,
                     draw_bottomband, draw_sub, mono, bold, text_w, noise_band,
                     static_burst)

CLOCK0 = 9 * 3600
BLUEPRINT = (18, 42, 92)


def beat7(rng):
    path = os.path.join(FR2, "b7_blue.mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "19", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    N = 7 * FPS
    for f in range(N):
        t = f / FPS
        # slow pan: offset grows, then holds
        pan = min(1.0, t / 5.0) * 220
        a = np.zeros((H, W, 3), np.float32) + np.array(BLUEPRINT, np.float32)
        # grid
        for gx in range(0, W + 80, 80):
            a[:, gx:gx + 1] -= 8
        for gy in range(0, H + 80, 80):
            a[gy:gy + 1, :] -= 8
        img = to_pil(a)
        dr = ImageDraw.Draw(img)
        fw = mono(30)
        # floor plan rects (draw progressively: reveal = f/ N)
        rev = min(1.0, t / 4.5)
        rooms = [
            ("LIVING", 300, 200, 700, 480, "24 m2"),
            ("KITCHEN", 730, 200, 1010, 380, "8 m2"),
            ("BATH", 1040, 200, 1240, 380, "4 m2"),
            ("STORAGE", 1270, 200, 1560, 380, "6 m2"),
            ("HALL", 730, 410, 1560, 530, ""),
            ("BED 1", 300, 560, 700, 900, "12 m2"),
            ("BED 2", 730, 560, 1100, 900, "? m2"),
            ("ROOM FOR YOU", 1130, 560, 1560, 900, ""),
        ]
        nshow = int(rev * len(rooms) + 0.999)
        for i, (name, x0, y0, x1, y1, sub) in enumerate(rooms[:nshow]):
            x0 -= pan * 0.4
            x1 -= pan * 0.4
            dr.rectangle([x0, y0, x1, y1], outline=(220, 230, 245), width=5)
            dr.text((x0 + 30, y0 + 60), name, font=bold(36), fill=(235, 240, 250))
            if sub:
                dr.text((x0 + 30, y0 + 105), sub, font=fw, fill=(170, 190, 220))
        # beds
        for bx in (380, 800):
            dr.rectangle([bx, 700, bx + 130, 800], outline=(220, 230, 245), width=4)
            dr.rectangle([bx + 140, 700, bx + 270, 800], outline=(220, 230, 245), width=4)
        # crawlspace nested squares in BED 2
        if nshow >= 7:
            for k in range(4):
                dr.rectangle([940 + k * 18 - pan * 0.4, 800 + k * 12, 1050 - k * 18 - pan * 0.4, 880 - k * 12],
                             outline=(220, 230, 245), width=3)
            dr.text((930 - pan * 0.4, 780), "CRAWLSPACE", font=mono(22), fill=(170, 190, 220))
        # red annotations fade in late (above BED 1, clear of the label)
        if t > 3.0:
            fr = mono(32)
            dr.text((330 - pan * 0.4, 590), "don't sleep in bed 2", font=fr, fill=(230, 90, 80))
            # bath hatch
            dr.line([1150 - pan * 0.4, 280, 1210 - pan * 0.4, 360], fill=(230, 90, 80), width=4)
            dr.ellipse([1200 - pan * 0.4, 350, 1240 - pan * 0.4, 390], outline=(230, 90, 80), width=4)
            # tallies near hall
            for k in range(6):
                dr.line([1400 + k * 14 - pan * 0.4, 440, 1400 + k * 14 - pan * 0.4, 480],
                        fill=(230, 90, 80), width=3)
        # FOR RENT card pinned top-left
        dr.rectangle([40, 120, 420, 400], fill=(232, 226, 210), outline=(150, 60, 40), width=4)
        dr.rectangle([40, 120, 420, 170], fill=(200, 110, 70))
        dr.text((60, 126), "FOR RENT", font=bold(30), fill=(255, 255, 255))
        for i, line in enumerate(["Unit 4B - Block C", "3 rooms - 62 m2", "742 / month", "Cozy."]):
            dr.text((60, 190 + i * 44), line, font=mono(28), fill=(40, 40, 40))
        img = draw_osd(img, CLOCK0 + 300 + t)
        if t < 3.5:
            img = draw_sub(img, "Spacious 3-room apartment. Cozy.",
                           "Available immediately.")
        else:
            img = draw_sub(img, "Previous tenant... included.")
        img = draw_bottomband(img, CLOCK0 + 300 + t)
        arr = np.asarray(img).astype(np.float32)
        if int(t * 5) % 11 == 0:
            arr = noise_band(arr, (f * 43) % H, h=12, amp=12.0, seed=f)
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    print("b7 done", flush=True)


def meeting_screen(img, mode, t):
    dr = ImageDraw.Draw(img)
    sx0, sy0, sx1, sy1 = 560, 130, 1360, 560
    dr.rectangle([sx0, sy0, sx1, sy1], fill=(228, 224, 214))
    dr.rectangle([sx0, sy0, sx1, sy0 + 64], fill=(16, 120, 112))
    if mode == "q3":
        dr.text((sx0 + 30, sy0 + 10), "Q3 RESULTS", font=bold(34), fill=(255, 255, 255))
        # value row + bars + label row: three separate bands, no overlap.
        # 3 columns centered at cx1/cx2/cx3; labels centered under each.
        fval, flab = bold(30), mono(22)
        cols = [(775, "100%", "Occupancy", TEAL), (1025, "100%", "Satisfaction", (220, 100, 80))]
        for cx, val, lab, col in cols:
            dr.text((cx - text_w(dr, val, fval) / 2, sy0 + 90), val, font=fval, fill=(30, 30, 30))
            h = 220 if t > 1.0 else t * 220
            dr.rectangle([cx - 75, sy0 + 135, cx + 75, sy0 + 135 + h], fill=col)
            dr.text((cx - text_w(dr, lab, flab) / 2, sy0 + 140 + h + 12), lab, font=flab,
                    fill=(30, 30, 30))
        depx = 1240
        dr.text((depx - text_w(dr, "Departures", flab) / 2, sy0 + 140 + 220 + 12), "Departures",
                font=flab, fill=(30, 30, 30))
        dr.ellipse([depx + 62, sy0 + 140 + 220 + 14, depx + 74, sy0 + 140 + 220 + 26], fill=RED)
    else:
        dr.rectangle([sx0, sy0, sx1, sy0 + 64], fill=(30, 40, 60))
        dr.text((sx0 + 30, sy0 + 10), "DEPARTURES", font=bold(36), fill=(255, 255, 255))
        # donut: red humanoid vs teal blob
        cx, cy, r = 960, 350, 120
        dr.chord([cx - r, cy - r, cx + r, cy + r], 90, 450, fill=(220, 100, 80))
        dr.chord([cx - r, cy - r, cx + r, cy + r], -60, 90, fill=TEAL)
        dr.ellipse([cx - 55, cy - 55, cx + 55, cy + 55], fill=(228, 224, 214))
        dr.ellipse([cx - 130, cy - 60, cx - 90, cy - 20], fill=(220, 100, 80))   # head
        dr.rectangle([cx - 130, cy - 10, cx - 90, cy + 60], fill=(220, 100, 80))  # body
        dr.text((cx - 90, cy + 100), "Where do tenants go? Nowhere. 100%.",
                font=mono(24), fill=(30, 30, 30))
    return img


def beat8(rng):
    path = os.path.join(FR2, "b8_meet.mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "19", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    N = 7 * FPS
    for f in range(N):
        t = f / FPS
        a = cctv_base(t, rng)
        a *= 0.45
        img = to_pil(a)
        dr = ImageDraw.Draw(img)
        # audience head rows (dark circles)
        for r in range(3):
            n = 9 - r
            for i in range(n):
                x = 350 + i * (1220 / max(1, n - 1)) + r * 30
                y = 660 + r * 90
                dr.ellipse([x - 52, y - 52, x + 52, y + 52], fill=(35, 40, 44))
        # table
        dr.polygon([(700, 760), (1220, 760), (1330, 1080), (590, 1080)], fill=(60, 42, 34))
        # sticky notes on table
        for nx, ny, c in ((800, 800, RED), (1120, 800, TEAL), (860, 920, (230, 200, 120)), (1060, 920, CREAM)):
            dr.rectangle([nx, ny, nx + 44, ny + 32], fill=c)
        # YOU placard
        dr.polygon([(1050, 940), (1290, 940), (1300, 1010), (1060, 1010)], fill=(235, 232, 222))
        dr.text((1120, 948), "YOU", font=bold(34), fill=(20, 20, 20))
        # presenter silhouette right
        dr.ellipse([1560, 480, 1640, 560], fill=(5, 7, 9))
        dr.rectangle([1545, 555, 1655, 900], fill=(5, 7, 9))
        mode = "q3" if t < 3.4 else "dep"
        img = meeting_screen(img, mode, t)
        # glitch seam at switch
        if 3.4 <= t < 3.7:
            img = to_pil(noise_band(np.asarray(img).astype(np.float32), 300, h=40, amp=40.0, seed=f))
        img = draw_osd(img, CLOCK0 + 400 + t)
        img = draw_sub(img, "Great quarter, everyone. Occupancy: 100%.",
                       "Departures: zero.")
        img = draw_bottomband(img, CLOCK0 + 400 + t)
        arr = np.asarray(img).astype(np.float32)
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    print("b8 done", flush=True)


def beat9(rng):
    path = os.path.join(FR2, "b9_clock.mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "19", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    N = 7 * FPS
    for f in range(N):
        t = f / FPS
        a = cctv_base(t, rng)
        a *= 0.5
        img = to_pil(a)
        dr = ImageDraw.Draw(img)
        # STAY tag top-left, EXIT sign
        dr.rectangle([60, 60, 230, 130], fill=(150, 30, 26))
        dr.text((85, 75), "STAY", font=bold(48), fill=(240, 240, 240))
        dr.rectangle([60, 880, 170, 930], fill=(40, 90, 70))
        dr.text((75, 890), "EXIT", font=bold(30), fill=(220, 255, 230))
        # clock face
        cx, cy, r = W / 2, 540, 400
        dr.ellipse([cx - r - 24, cy - r - 24, cx + r + 24, cy + r + 24], fill=(10, 10, 10))
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(238, 232, 220))
        for i in range(60):
            ang = i / 60 * 2 * math.pi
            l = 26 if i % 5 == 0 else 12
            x1 = cx + math.cos(ang) * (r - 8)
            y1 = cy + math.sin(ang) * (r - 8)
            dr.line([x1, y1, cx + math.cos(ang) * (r - 8 - l), cy + math.sin(ang) * (r - 8 - l)],
                    fill=(30, 30, 30), width=5 if i % 5 == 0 else 2)
        # numerals: corrupt to 9 over time
        corrupt = min(1.0, t / 5.0)
        for i in range(1, 13):
            ang = (i / 12) * 2 * math.pi - math.pi / 2
            nx = cx + math.cos(ang) * (r - 90)
            ny = cy + math.sin(ang) * (r - 90)
            num = "9" if rng.random() < corrupt * 0.75 else str(i if i <= 12 else i - 12)
            fn = bold(64)
            dr.text((nx - text_w(dr, num, fn) / 2, ny - 32), num, font=fn, fill=(25, 25, 25))
        # hands: spin fast then settle; hour creeps to 5
        if t < 2.0:
            ma = t * 12
            ha = t * 2
        else:
            ma = 24 + (t - 2.0) * 0.1
            ha = 4 + (t - 2.0) * 0.06 + 2.0 * 2 * 0.0
            ha = 2.0 * 2 + (t - 2.0) * 0.10
        for ang_v, ln, wd, col in ((ma, r - 130, 10, (25, 25, 25)), (ha, r - 200, 14, (25, 25, 25))):
            ang = ang_v - math.pi / 2
            dr.line([cx, cy, cx + math.cos(ang) * ln, cy + math.sin(ang) * ln], fill=col, width=wd)
        dr.line([cx, cy, cx + math.cos(t * 3) * (r - 100), cy + math.sin(t * 3) * (r - 100)],
                fill=RED, width=5)
        dr.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=RED)
        # brand on face
        dr.text((cx - 90, cy + 120), "Cielo", font=bold(44), fill=TEAL)
        dr.text((cx - 110, cy + 170), "QUARTZ-ETERNAL", font=mono(26), fill=(100, 100, 100))
        # teal chyron ABOVE the EXIT sign, no overlap
        dr.rectangle([60, 760, 560, 840], fill=TEAL)
        dr.text((90, 768), "17:00  CLOCK OUT", font=bold(44), fill=(255, 255, 255))
        img = draw_osd(img, CLOCK0 + 500 + t)
        img = draw_sub(img, "Five o'clock. Time to clock out.",
                       "The clock disagrees.")
        img = draw_bottomband(img, CLOCK0 + 500 + t)
        arr = np.asarray(img).astype(np.float32)
        if int(t * 4) % 6 == 0:
            arr = noise_band(arr, (f * 37) % H, h=30, amp=30.0, seed=f)
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    print("b9 done", flush=True)


def sky_card(t, rng, service=True, extra_lines=0, glitch=False):
    yy = np.linspace(0, 1, H)[:, None, None]
    top = np.array([105, 175, 225], np.float32)
    mid = np.array([150, 215, 225], np.float32)
    bot = np.array([175, 225, 215], np.float32)
    a = np.zeros((H, W, 3), np.float32)
    m = np.clip(yy * 2, 0, 1)
    a += top * (1 - m) + mid * m
    m2 = np.clip((yy - 0.5) * 2, 0, 1)
    a = a * (1 - m2) + bot * m2
    img = to_pil(a)
    draw_sun(img, 1650, 190, 95, face="smile")
    dr = ImageDraw.Draw(img)
    confetti(dr, rng, t, (60, 60, W - 60, 760), n=30)
    # hills + houses
    for k, (ybase, amp, col) in enumerate([(830, 60, (110, 195, 140)), (900, 70, (80, 175, 120))]):
        pts = []
        for x in range(0, W + 40, 40):
            pts.append((x, ybase + math.sin(x / 420 + k * 2) * amp))
        pts += [(W, H), (0, H)]
        dr.polygon(pts, fill=col)
    for i, hx in enumerate(np.linspace(120, 1800, 9)):
        x0 = hx - 23
        dr.rectangle([x0, 820, x0 + 46, 852], fill=(20, 160, 150), outline=INK, width=3)
        dr.polygon([(x0 - 6, 820), (hx, 800), (x0 + 52, 820)], fill=RED, outline=INK)
    draw_house(dr, W / 2, 640, 300)
    f1 = bold(150)
    dr.text(((W - text_w(dr, "Cielo", f1)) / 2, 700), "Cie", font=f1, fill=INK)
    w1 = text_w(dr, "Cie", f1)
    dr.text(((W - text_w(dr, "Cielo", f1)) / 2 + w1, 700), "lo", font=f1, fill=TEAL)
    if service:
        ft = bold(48)
        dr.text(((W - text_w(dr, "Thank you for your service.", ft)) / 2, 880),
                "Thank you for your service.", font=ft, fill=INK)
    lines = ["See you tomorrow at 09:00.", "Waiting list position: #01 (you)", "welcome home"]
    fl = mono(32)
    for i in range(min(extra_lines, 3)):
        # tagline ends ~928; rows at 936/968/1000; footer at 1040
        dr.text(((W - text_w(dr, lines[i], fl)) / 2, 936 + i * 32), lines[i], font=fl,
                fill=(170, 30, 26))
    dr.text((W / 2 - 260, H - 40), "Cielo B.V. \u2022 employee orientation \u2022 tape 1 of \u221e",
            font=mono(24), fill=(60, 90, 90))
    arr = np.asarray(img).astype(np.float32)
    if glitch:
        arr[:, :, 0] = np.roll(arr[:, :, 0], 12, axis=1)
        arr[:, :, 2] = np.roll(arr[:, :, 2], -12, axis=1)
        arr += static_burst(rng, amt=0.3)
    return arr


def beat10(rng):
    path = os.path.join(FR2, "b10_end.mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "19", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    N = 8 * FPS
    for f in range(N):
        t = f / FPS
        extra = 0 if t < 2.5 else (1 if t < 3.5 else (2 if t < 4.5 else 3))
        glitch = (t > 6.0)
        arr = sky_card(t, rng, extra_lines=extra, glitch=glitch)
        # reposition extras stacked (sky_card draws overlapped; fix here)
        if extra and not glitch:
            pass
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    print("b10 done", flush=True)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "b7"):
        beat7(np.random.default_rng(17))
    if which in ("all", "b8"):
        beat8(np.random.default_rng(18))
    if which in ("all", "b9"):
        beat9(np.random.default_rng(19))
    if which in ("all", "b10"):
        beat10(np.random.default_rng(20))
