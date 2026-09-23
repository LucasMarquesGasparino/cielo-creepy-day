# CIELO — An Average Day (That Stays) · v2

60-second creepy/surreal CCTV-horror trailer in the spirit of the Opus 5.5
one-shot reference (`Demawating`): a bright housing-company logo card that
rots into a security-camera workday — corridor that denies its own third
floor, a polite entity with a headlamp eye, a haunted inbox, a ringing red
phone, a blueprint that includes the previous tenant, a 100%-occupancy
meeting, a clock that refuses 17:00, and a logo card that welcomes YOU home.

Rendered **100% programmatically** on-device (Termux, ARM64, no GPU) with the
**OpenMontage cinematic pipeline**
([calesthio/OpenMontage](https://github.com/calesthio/OpenMontage)):
research → proposal → script → scene_plan → assets → edit → compose → publish.

## Pipeline artifacts (`pipeline/`)

research_brief, proposal_packet, script (+voice_performance), scene_plan,
asset_manifest, edit_decisions (render_runtime=ffmpeg), render_report,
publish_log, decision_log — v2 appends `*_v2.json` where the shape changed.

## v2 renderer (`v2_*.py`, 1920×1080 @ 30 fps)

| File | Beats |
|---|---|
| `v2_core.py` | palette, mascot house, CCTV grade, OSD, stickies, subtitles |
| `v2_beats13.py` | b1 logo 6s · b2 glitch 3s · b3 corridor 7s |
| `v2_beats46.py` | b4 entity 5s · b5 CieloMail 5s · b6 phone 5s |
| `v2_beats710.py` | b7 blueprint 7s · b8 meeting 7s · b9 clock 7s · b10 end card 8s |
| `v2_audio.py` | 9 PA narrations (edge-tts) + hum/drone/bells/stingers mix |

Beats: 6+3+7+5+5+5+7+7+7+8 = 60 s.

## Tools used (OpenMontage registry names)

- `tts_selector` → **edge-tts** (`en-US-ChristopherNeural`, −12%).
  `piper_tts` was requested but its aarch64 binary aborts on Termux Bionic.
- `image_gen` → local **numpy/Pillow** synthesis (10 beats × 1800 frames).
- `music_gen` → local **numpy** fluorescent-hum + D-minor drone + phone bells.
- `audio_mixer` → narration-first mix with ducking.
- `video_compose` / `video_stitch` / `color_grade` → **ffmpeg 8.1.2**
  (libx264 CRF 19, aac 192 k, 1080p30).

## Skills followed

`pipelines/cinematic/*` directors, `core/ffmpeg`, `creative/sound-design`,
`creative/cinematic`, `meta/voice-performance-director`, `meta/reviewer`
(frame QA of every beat, revision rounds until no text collisions).

## Reproduce

```sh
python3 v2_beats13.py b1  # ... b1/b2/b3
python3 v2_beats46.py b4  # ... b4/b5/b6
python3 v2_beats710.py b7 # ... b7/b8/b9/b10
python3 v2_audio.py
# concat + mux (see shell history / render_report_v2)
```

Hero output (git-ignored, ~110 MB): `output/cielo-average-day-v2.mp4`.
