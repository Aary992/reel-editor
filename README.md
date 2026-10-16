# reel-editor

Aarit's talking-head Reel engine: one video in, his locked style out (captions, subtle zoom, 2-3 Google Flow
text cuts, money-burn edit, varied SFX, -14 LUFS audio, cover). The look is fixed in `STYLE.md`, and the
text-cut rules are in `TEXT_CUTS.md`. Claude runs it through the `reel-edit` skill (`skill/SKILL.md`).

## Setting it up on the PC

Step by step, with paths and fixes: **[PC_SETUP.md](PC_SETUP.md)**.

`setup.ps1` installs pinned versions of ffmpeg 9.0.2, the Whisper venv and Pillow/numpy. It also downloads
the fonts (Figtree, OFL) and the Mixkit sound effects. Neither is stored in this repo: Mixkit's licence
forbids redistribution. Finally it writes the machine's `config.json` and installs the Claude skill.

## Use

```
py -3.14 reel.py prep "C:\path\to\video.mp4" --name "short name"
py -3.14 reel.py status "short name"
py -3.14 reel.py map "short name" "his clip.mp4" "17 TRADES"
py -3.14 reel.py render "short name" --cover-line "his exact words" --cover 2
```
Each Reel's working files live in `reels/<name>/`. That folder is never committed: his videos stay local.
