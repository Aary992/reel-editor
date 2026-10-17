---
name: reel-edit
description: "Aarit's talking-head Reel engine. Use whenever Aarit sends or points to a talking-head video/Reel to edit (an .mp4/.mov, usually in Downloads), says 'edit this reel', 'make this reel', 'do the usual edit', 'Flow clips are in', or gives a cover line or on-screen text for a Reel. Runs reel-editor/reel.py: captions, subtle zoom, 2-3 Flow text cuts, money-burn edit, SFX, loudness, cover, caption pack, all in his locked style."
---

# Reel edit (Aarit's locked style)

Engine folder: `C:\Users\Aaru\Documents\reel-editor` on the laptop, `D:\My Data\Documents\cc\reel-editor`
on the PC (see `PC_SETUP.md`). Run `git pull` in it first so both machines use the same engine. Read `STYLE.md` and `TEXT_CUTS.md` there before the first run in a session.
Run Python with `py -3.14` (system Python has Pillow and numpy; transcription uses the venv set in
`config.json`). Never change the locked look unless he asks for a change.

## 1. He sends a video → prep

```
py -3.14 reel.py prep "<video path>" [--name "<short name>"]
```
This transcribes the video and finds his cards and split screens. If he talks about losing money, it cuts
that segment for the money burn. It picks 2-3 text cuts, writes `reels/<name>/flow prompts.txt`, saves
3 cover frames (`covers/cover_1..3.png`) and renders `<name> preview.mp4`.

Then **review the picks yourself** (the TEXT_CUTS.md rules):
- Numbers first, spread out, the words must be what he actually says.
- Skip anything the screen already shows.
- Re-pick with `py -3.14 reel.py repick "<name>" --only "TEXT|TEXT"` when you know better.

Check the transcript for mis-heard words, especially Hinglish. If Whisper got a key word wrong, tell him.

**Flow takes at most 30 s of video per clip.** Prep also cuts his whole Reel into parts of at most 30 s in
`Downloads\<name> flow parts\` (part 1 (0-30s).mp4, part 2 (30-55s).mp4 ...), so he can upload them to Flow
straight away. Redo it with `py -3.14 reel.py split "<name>"`. Never hand him anything for Flow longer than 30 s.

Give him:
- The prompts file.
- The 30 s Flow parts folder in Downloads.
- The preview.
- The 3 cover frames (recommend one).
- What to save where (exact file names).

Ask for his cover line and whether he wants any on-screen text.

## 2. "Flow clips are in" → check, then render

```
py -3.14 reel.py status "<name>"
```
- **Look at frames of every clip before rendering:** check the spelling, and that the content matches the
  cut. His file names have been swapped before. Map by content with
  `py -3.14 reel.py map "<name>" "<his file>.mp4" "<TEXT>"`.
- **Money clip:** check his face and lip sync are unchanged.

```
py -3.14 reel.py render "<name>" --cover-line "<his exact words>" [--cover 2] [--text "..." --text-start S --text-secs 1-4]
```
The script checks that the frame count matches the source and that loudness lands around -14 LUFS.
Then look at frames inside every text cut and the money window yourself before you say it's done.

## 3. Caption pack

Write `<name> caption pack.txt` next to the final in Downloads:
- **Instagram:** caption plus 3-5 hashtags.
- **YouTube Shorts:** title and description.
- **LinkedIn:** a version that is finance/business only, Gen-Z tone, and educational.

Rules for all three:
- Plain human tone. No em dashes, no `---`.
- No buy/sell advice. If it's about trading: "Not SEBI registered. Not financial advice", plus "virtual
  money" when that's the case.
- Use real numbers from what he says or what's on screen. Never invent any.

## Hard rules
- **No music, ever.**
- Don't post, commit or push anything without his yes.
- Report honestly what was verified and what wasn't. You can't hear audio, so sound checks are by
  measurement.
