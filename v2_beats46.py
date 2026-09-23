#!/usr/bin/env python3
"""CIELO v2 beats 4-6: entity approach (16-21s), CieloMail (21-26s), phone (26-31s).

Beat 4: same corridor geometry feel + CRT, but the figure is CLOSE: tall thin
  silhouette fills center, headlamp eye (white ellipse + glow), ID badge
  readable 'HELLO', PA sub: 'A tenant is approaching. Please be polite.'
  Ends with white flash + static burst (entity takes camera).
Beat 5: CieloMail 3.1 CRT window: sidebar (Inbox 9, Block A 12, Block B 40,
  Waiting List 1,048,576, Basement ?, Third Floor 0), message rows (Viewing
  confirmed 03:33 / hallway longer at night / Heating fixed. It now wants to
  be fed. / mold has formed a face / third floor does not exist / scratching
  is spelling my name / Coffee machine fixed don't use cup #3), open message
  from Tenant Unit 4B, scrolling highlight, stickies, footer '0 tenants can leave'.
Beat 6: phone desk: September 2026 calendar all X, line-monitor oscilloscope,
  EMPLOYEE OF THE MONTH 'YOU every month since 1986', red rotary phone with
  coiled cord, caller-ID 'UNIT 4B', sub 'The walls are breathing again.' +
  'Hello? It's unit 4B. Again.' Phone shakes on ring pulses.
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

from v2_core import (BONE, CREAM, INK, RED, TEAL, RED_DK, YELLOW, W, H, FPS, FR2,
                     cctv_base, to_pil, draw_osd, draw_bottomband, draw_sub, sticky,
                     mono, bold, text_w, noise_band, static_burst)

CLOCK0 = 9 * 3600


def beat4(rng):
    path = os.path.join(FR2, "b4_entity.mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "19", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    N = 5 * FPS
    for f in range(N):
        t = f / FPS
        a = cctv_base(t, rng)
        # close-up hallway walls rushing past (dark, fast seams)
        for k in range(-4, 5):
            x = W / 2 + k * 260 + math.sin(t * 3) * 14
            a[:, int(max(0, x)):int(max(0, x)) + 8] = np.array([30, 40, 42], np.float32)
        a *= 0.55  # darker: entity blocks the light
        img = to_pil(a)
        dr = ImageDraw.Draw(img)
        cx = W / 2 + math.sin(t * 1.1) * 10
        breathe = 1 + 0.02 * math.sin(t * 2.4)
        # towering thin figure: head top ~120, feet ~1080
        hw = int(150 * breathe)
        dr.ellipse([cx - 90, 60, cx + 90, 240], fill=(5, 7, 9))                    # head
        dr.rectangle([cx - hw, 220, cx + hw, 760], fill=(5, 7, 9))                 # torso
        dr.rectangle([cx - hw, 740, cx - hw + 90, 1080], fill=(5, 7, 9))           # legs
        dr.rectangle([cx + hw - 90, 740, cx + hw, 1080], fill=(5, 7, 9))
        # long arms hanging
        dr.rectangle([cx - hw - 55, 260, cx - hw - 5, 830], fill=(5, 7, 9))
        dr.rectangle([cx + hw + 5, 260, cx + hw + 55, 830], fill=(5, 7, 9))
        # headlamp eye: white ellipse + halo
        ex, ey, er = cx + 40, 150, 46
        for rr, al in ((110, 30), (80, 60), (60, 110)):
            dr.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], outline=(200, 210, 200 + al % 60), width=3)
        dr.ellipse([ex - er, ey - er, ex + er, ey - er + 70], fill=(235, 240, 235))
        dr.ellipse([ex - 12, ey - 14, ex + 12, ey + 14], fill=(10, 10, 10))
        # ID badge, readable up close: HELLO
        dr.rectangle([cx - 70, 380, cx + 70, 470], fill=(220, 220, 215), outline=(30, 30, 30), width=3)
        fb = bold(44)
        dr.text((cx - text_w(dr, "HELLO", fb) / 2, 398), "HELLO", font=fb, fill=(20, 20, 20))
        # lanyard
        dr.line([cx - 60, 240, cx - 70, 380], fill=(60, 60, 60), width=5)
        dr.line([cx + 60, 240, cx + 70, 380], fill=(60, 60, 60), width=5)
        img = draw_osd(img, CLOCK0 + 9 + t)
        img = draw_sub(img, "[PA] A tenant is approaching.",
                       "Please be polite.")
        img = draw_bottomband(img, CLOCK0 + 9 + t)
        arr = np.asarray(img).astype(np.float32)
        if int(t * 6) % 7 == 0:
            arr = noise_band(arr, (f * 53) % H, seed=f)
        # final white flash into static (entity takes the camera)
        if t > 4.3:
            k = min(1.0, (t - 4.3) * 2.2)
            arr = arr * (1 - k) + 235 * k + static_burst(rng, amt=0.6 * k)
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    print("b4 done", flush=True)


MAIL_ROWS = [
    ("Viewings", "Viewing confirmed: 03:33 (bring nothing)", "10:20"),
    ("Tenant, Unit 4B", "why is my hallway longer at night", "10:04"),
    ("Maintenance", "Heating fixed. It now wants to be fed.", "10:03"),
    ("Tenant, Unit 7C", "The mold has formed a face. It is polite.", "09:47"),
    ("Waiting List", "Your position: 1,048,576", "09:31"),
    ("HR", "Reminder: the third floor does not exist", "09:30"),
    ("Tenant, Unit 4B", "Re: the scratching is spelling my name", "09:15"),
    ("Tenant, Unit 4B", "Noise complaint: scratching inside the walls", "09:14"),
    ("Facilities", "Coffee machine fixed (don't use cup #3)", "09:02"),
]

OPEN_BODY = [
    "From: Tenant, Unit 4B",
    "Subject: Re: the scratching is spelling my name",
    "",
    "It is getting better at it. Yesterday it got the surname right.",
    "Please send someone who hasn't been here before.",
    "If there is anyone left who hasn't been here before.",
]


def mail_frame(t, rng, scroll=0):
    a = cctv_base(t, rng)
    a *= 0.5
    img = to_pil(a)
    dr = ImageDraw.Draw(img)
    # CRT bezel
    dr.rounded_rectangle([180, 60, W - 180, H - 130], radius=40, fill=(38, 40, 42),
                         outline=(15, 15, 15), width=10)
    # window
    wx0, wy0, wx1, wy1 = 260, 130, W - 260, H - 200
    dr.rectangle([wx0, wy0, wx1, wy1], fill=(215, 220, 218))
    # title bar
    dr.rectangle([wx0, wy0, wx1, wy0 + 56], fill=(16, 120, 112))
    ft = bold(30)
    dr.text((wx0 + 20, wy0 + 10), "CieloMail 3.1 — Inbox (9 unread)", font=ft, fill=(255, 255, 255))
    # menu row: two lines, no overlap (File..Help / action buttons)
    fm = mono(24)
    for i, m in enumerate(["File", "Edit", "View", "Tenants", "Waiting List", "Help"]):
        dr.text((wx0 + 20 + i * 200, wy0 + 62), m, font=fm, fill=(40, 40, 40))
    for i, b in enumerate(["Reply", "Reply All", "Forward", "Delete", "Evict"]):
        dr.rounded_rectangle([wx0 + 20 + i * 175, wy0 + 94, wx0 + 160 + i * 175, wy0 + 128],
                             radius=6, outline=(120, 120, 120), width=2)
        dr.text((wx0 + 34 + i * 175, wy0 + 98), b, font=fm, fill=(40, 40, 40))
    # sidebar (wide enough: 'Waiting List' label + '1,048,576' value side by side)
    sx0, sx1 = wx0, wx0 + 330
    dr.rectangle([sx0, wy0 + 140, sx1, wy1], fill=(30, 90, 110))
    fs = mono(22)
    side = [("Inbox", "9"), ("Outbox", "0"), ("Sent", "0"), ("Tenants", ""),
            ("Block A", "12"), ("Block B", "40"), ("Block C", "–"),
            ("Waiting List", "1,048,576"), ("Basement", "?"), ("Third Floor", "0")]
    for i, (k, v) in enumerate(side):
        y = wy0 + 160 + i * 44
        dr.text((sx0 + 16, y), k, font=fs, fill=(235, 235, 235))
        if v:
            dr.text((sx1 - 16 - text_w(dr, v, fs), y), v, font=fs, fill=(250, 200, 120))
    # message list (shifted right to clear the wider sidebar)
    lx = sx1 + 10
    fr = mono(22)
    dr.text((lx + 10, wy0 + 150), "From", font=fr, fill=(100, 100, 100))
    dr.text((lx + 250, wy0 + 150), "Subject", font=fr, fill=(100, 100, 100))
    dr.text((wx1 - 110, wy0 + 150), "Received", font=fr, fill=(100, 100, 100))
    hi = int(t * 1.4) % len(MAIL_ROWS)
    for i, (fro, sub, rcv) in enumerate(MAIL_ROWS):
        y = wy0 + 185 + i * 40
        if i == hi:
            dr.rectangle([lx, y - 4, wx1, y + 30], fill=(20, 90, 120))
            col = (255, 255, 255)
        else:
            col = (30, 30, 30)
        dr.text((lx + 10, y), fro[:18], font=fr, fill=col)
        dr.text((lx + 250, y), sub, font=fr, fill=col)
        dr.text((wx1 - 105, y), rcv, font=fr, fill=col)
    # open message
    oy = wy0 + 185 + 9 * 40 + 16
    dr.line([lx, oy - 8, wx1, oy - 8], fill=(150, 150, 150), width=2)
    for i, line in enumerate(OPEN_BODY):
        dr.text((lx + 10, oy + i * 34), line[:72], font=fr, fill=(30, 30, 30))
    # status footer
    dr.text((wx0 + 20, wy1 - 34), "Connected to CIELO-SRV-01  |  9 new  |  0 tenants can leave.",
            font=mono(22), fill=(90, 90, 90))
    img = sticky(img, 40, 300, ["DON'T", "ANSWER", "4B"], (250, 230, 130), rot_deg=-4)
    img = sticky(img, W - 230, 300, ["3rd floor", "= NO"], (170, 230, 170), rot_deg=3)
    img = sticky(img, W - 260, 760, ["count", "the doors"], (245, 180, 200), rot_deg=-2)
    return img


def beat5(rng):
    path = os.path.join(FR2, "b5_mail.mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "19", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    N = 5 * FPS
    for f in range(N):
        t = f / FPS
        img = mail_frame(t, rng)
        img = draw_osd(img, CLOCK0 + 120 + t)
        img = draw_sub(img, "Nine new messages. Zero tenants can leave.")
        img = draw_bottomband(img, CLOCK0 + 120 + t)
        arr = np.asarray(img).astype(np.float32)
        if t > 4.0:  # signal wobble before cut
            arr[:, :, 0] = np.roll(arr[:, :, 0], 8, axis=1)
            arr = noise_band(arr, (f * 61) % H, seed=f)
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    print("b5 done", flush=True)


def phone_frame(t, rng):
    a = cctv_base(t, rng)
    a = a * 0.6 + np.array([30, 18, 10], np.float32) * 0.4  # warm desk tint
    img = to_pil(a)
    dr = ImageDraw.Draw(img)
    # back wall diagonal hazard stripes (subtle)
    for i in range(-4, 20):
        x = i * 160 + 400
        dr.polygon([(x, 60), (x + 80, 60), (x - 200, 560), (x - 280, 560)], fill=(60, 50, 40))
    # --- calendar September 2026, all X ---
    cx0, cy0 = 150, 180
    dr.rectangle([cx0, cy0, cx0 + 420, cy0 + 420], fill=(232, 226, 210), outline=(20, 20, 20), width=4)
    dr.rectangle([cx0, cy0, cx0 + 420, cy0 + 64], fill=(16, 120, 112))
    fh = bold(34)
    dr.text((cx0 + 60, cy0 + 10), "SEPTEMBER 2026", font=fh, fill=(255, 255, 255))
    fx = mono(34)
    for r in range(5):
        for c in range(7):
            if r == 4 and c > 1:
                continue
            x = cx0 + 40 + c * 52
            y = cy0 + 100 + r * 62
            dr.text((x, y), "X", font=fx, fill=(190, 40, 30))
    # --- line monitor oscilloscope ---
    ox0, oy0 = 680, 180
    dr.rectangle([ox0, oy0, ox0 + 560, oy0 + 260], fill=(8, 14, 10), outline=(40, 80, 60), width=3)
    dr.text((ox0 + 16, oy0 + 8), "LINE MONITOR \u2022 CH 4B", font=mono(24), fill=(80, 200, 130))
    for gx in range(1, 7):
        dr.line([ox0 + gx * 80, oy0, ox0 + gx * 80, oy0 + 260], fill=(20, 40, 28), width=1)
    pts = []
    for x in range(560):
        v = (math.sin(x / 18 + t * 6) * 0.5 + math.sin(x / 7 - t * 11) * 0.3
             + math.sin(x / 3 + t * 23) * 0.2)
        # ring spikes
        if int(t * 2) % 4 == 0 and 200 < x < 360:
            v *= 2.2
        pts.append((ox0 + x, oy0 + 150 - v * 70))
    dr.line(pts, fill=(90, 230, 140), width=3)
    # --- employee of the month ---
    ex0, ey0 = 1330, 180
    dr.rectangle([ex0, ey0, ex0 + 420, ey0 + 420], fill=(232, 226, 210),
                 outline=(150, 110, 60), width=6)
    dr.text((ex0 + 40, ey0 + 12), "EMPLOYEE OF THE MONTH", font=bold(30), fill=(30, 30, 30))
    dr.rectangle([ex0 + 110, ey0 + 70, ex0 + 310, ey0 + 300], fill=(150, 155, 165))
    dr.ellipse([ex0 + 165, ey0 + 110, ex0 + 255, ey0 + 210], fill=(225, 200, 185))
    dr.chord([ex0 + 150, ey0 + 220, ex0 + 270, ey0 + 320], 180, 360, fill=(30, 50, 90))
    dr.text((ex0 + 175, ey0 + 315), "YOU", font=bold(40), fill=(30, 30, 30))
    dr.text((ex0 + 60, ey0 + 360), "every month since 1986", font=mono(25), fill=(80, 80, 80))
    # --- red wavy cord from monitor down to phone (left of phone) ---
    cordx = 560
    cord = [(cordx + math.sin(y / 40 + t * 2) * 18, y) for y in range(440, 760)]
    dr.line(cord, fill=(190, 40, 34), width=10)
    # --- red rotary phone ---
    shake = 8 if (int(t * 2) % 4 == 0) else 0
    px0, py0 = 640 + shake, 740
    dr.rounded_rectangle([px0, py0, px0 + 640, py0 + 240], radius=120, fill=(190, 70, 60),
                         outline=(120, 30, 26), width=5)
    dr.ellipse([px0 + 200, py0 + 60, px0 + 440, py0 + 240], fill=(235, 228, 214))
    # rotary holes 0-9
    for i in range(10):
        ang = -140 + i * 30
        hx = px0 + 320 + math.cos(math.radians(ang)) * 80
        hy = py0 + 150 + math.sin(math.radians(ang)) * 80
        dr.ellipse([hx - 26, hy - 26, hx + 26, hy + 26], fill=(60, 30, 25))
        dr.text((hx - 12, hy - 20), str((i + 1) % 10), font=bold(30), fill=(240, 240, 240))
    # tiny house at dial center
    dr.polygon([(px0 + 310, py0 + 150), (px0 + 320, py0 + 140), (px0 + 330, py0 + 150)], fill=RED)
    dr.rectangle([px0 + 312, py0 + 150, px0 + 328, py0 + 164], fill=TEAL)
    # caller ID box
    dr.rounded_rectangle([200, 740, 560, 900], radius=14, fill=(40, 44, 48),
                         outline=(20, 20, 20), width=4)
    dr.rectangle([220, 760, 540, 850], fill=(140, 190, 130))
    dr.text((240, 768), "UNIT 4B", font=bold(36), fill=(20, 30, 20))
    dr.text((240, 810), "DUR 00:00:%02d" % int(t), font=mono(30), fill=(20, 30, 20))
    return img


def beat6(rng):
    path = os.path.join(FR2, "b6_phone.mp4")
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "19", "-preset", "veryfast", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    N = 5 * FPS
    for f in range(N):
        t = f / FPS
        img = phone_frame(t, rng)
        img = draw_osd(img, CLOCK0 + 240 + t)
        if t < 2.2:
            img = draw_sub(img, "The walls are breathing again.")
        else:
            img = draw_sub(img, "Hello? It's unit 4B. Again.")
        img = draw_bottomband(img, CLOCK0 + 240 + t)
        arr = np.asarray(img).astype(np.float32)
        if int(t * 2) % 4 == 0:  # ring pulse: luma pump + band
            arr *= 1.06
            arr = noise_band(arr, (f * 47) % H, h=14, amp=14.0, seed=f)
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    print("b6 done", flush=True)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "b4"):
        beat4(np.random.default_rng(14))
    if which in ("all", "b5"):
        beat5(np.random.default_rng(15))
    if which in ("all", "b6"):
        beat6(np.random.default_rng(16))
