# CIELO — An Average Day (That Smiles Back)

60-second creepy/surreal corporate trailer, rendered **100% programmatically** on-device
(Termux, ARM64) with the **OpenMontage cinematic pipeline**
([calesthio/OpenMontage](https://github.com/calesthio/OpenMontage)):
research → proposal → script → scene_plan → assets → edit → compose → publish.

## Pipeline artifacts (`pipeline/`)

| Artifact | File |
|---|---|
| research_brief | `research_brief.json` |
| proposal_packet | `proposal_packet.json` |
| script (+voice_performance) | `script.json` |
| scene_plan (5-aspect hero frames) | `scene_plan.json` |
| asset_manifest | `asset_manifest.json` |
| edit_decisions (ffmpeg runtime) | `edit_decisions.json` |
| render_report | `render_report.json` |
| publish_log | `publish_log.json` |
| decision_log | `decision_log.json` |

Style playbook: `styles/cielo-creepy-noir.yaml` (custom, derived from
`flat-motion-graphics` + `clean-professional`).

## Tools used (OpenMontage registry names)

- `tts_selector` → routed to **edge-tts** (`en-US-ChristopherNeural`, rate −15%).
  `piper_tts` was requested but its aarch64 binary aborts on Termux Bionic
  (TLS underaligned), so the selector fell back per the asset-director skill.
- `image_gen` → local **numpy/Pillow** frame synthesis (6 scenes × 300 frames).
- `music_gen` → local **numpy** dark-drone synth (D minor, 60 BPM pulse, 120 Hz hum).
- `audio_mixer` → narration-first mix with ducking (~−18 dB bed under speech).
- `video_compose` / `video_stitch` / `color_grade` → **ffmpeg 8.1.2**
  (libx264 CRF 20, aac 192 k, 1280×720 @ 30 fps, letterbox + grain + CRT).

## Skills followed

`pipelines/cinematic/*` (executive-producer, script/scene/asset/edit/compose/publish
directors), `core/ffmpeg`, `creative/sound-design`, `meta/voice-performance-director`,
`meta/reviewer` (frame QA of all 6 scenes, two revision rounds).

## Reproduce

```sh
python3 render_frames.py   # renders assets/frames/sc{1..6}.mp4
python3 make_audio.py      # narration + drone -> assets/audio/mix_60s.wav
# concat + mux (see commands in render_report / shell history)
```

Hero output (git-ignored, 50 MB): `output/cielo-average-day-60s.mp4`.
Public copy: `/storage/emulated/0/Documents/cielo-average-day-60s.mp4`.
