---
name: reel-edit
description: "Aarit's Reel engine. Use whenever Aarit sends or points to a video/Reel to edit (an .mp4/.mov, usually in Downloads), says 'edit this reel', 'make this reel', 'do the usual edit', 'Flow clips are in', gives on-screen text for a Reel, or sends a script with raw clips to assemble. Runs reel-editor/reel.py in his locked look: bold iOS captions with rotating key-word colours, light-leak cuts, optional Flow motion text, in-scene visuals, SFX, loudness. No cover, no caption pack."
---

# Reel edit (Aarit's locked look)

Engine: `C:\Users\Aaru\Documents\reel-editor` on the laptop, `D:\My Data\Documents\cc\reel-editor` on the
PC. Run `git pull` there first. Read `README.md`, `STYLE.md` and `FLOW.md` before the first run in a session.
Python is `py -3.14`. Never change the look unless he asks.

## 1. He sends a video: ask first

Ask him one question before anything else: **"Do you want motion graphic text in this video?"**
Never assume, never reuse the last answer. Prep refuses to run without it.

## 2. Prep

```
py -3.14 reel.py prep "<video>" --text-cuts yes|no --name "<short name>"
```
It transcribes, finds the exact shot cuts, picks motion text (if yes), finds a money-burn line and builds
`Downloads\<name> Flow\` when there is anything to make in Flow.

## 3. Review (Claude)

- **Transcript:** look for misheard words, especially Hinglish and brand names. Fix them in `words.json` and
  tell him what you changed or what you're unsure of.
- **Motion text** (if yes): check the picks against FLOW.md. Re-pick with
  `py -3.14 reel.py repick "<name>" --only "TEXT|TEXT"`.
- **Visuals:** look at the shots. On 0 to 2 lines with feeling, where he isn't talking to camera, add one:
  `py -3.14 reel.py visual "<name>" START END "what changes, visible from the first frame"`.
- **No B-roll, ever.** No cover (thumbnail) and no caption pack either (his call 10-18).

## 4. Hand over

Tell him, briefly:
- what to make in Flow: the folder `Downloads\<name> Flow\`, how many clips, and that each one says how to
  make it in `flow prompts.txt`. If nothing is needed, say so and go straight to step 6.
- any words you're unsure Whisper heard right.

Ask whether he wants on-screen text.

## 5. "Flow clips are in"

```
py -3.14 reel.py status "<name>"
```
It collects correctly named clips from the Flow folder and lists the rest. For every clip, look at frames:
- motion text: spelling, letter by letter.
- visuals / money burn: he's unchanged, and the cut inside the clip lands at the same time as the source
  (measure it frame by frame). Drop a drifted clip with `reel.py visual "<name>" --drop V1`.

Assign Flow-named files by content: `py -3.14 reel.py map "<name>" "<file>.mp4" T2`.

## 6. Render

```
py -3.14 reel.py render "<name>" [--text "..." --text-start S --text-secs 1-4]
```
About 0.5 s per frame, so run it in the background. It checks frame count and loudness and delivers
`<name> final.mp4` to Downloads. Then look at frames inside every Flow window and around a few cuts before
you say it's done. That's the whole delivery: no cover, no caption pack.

## Raw clips instead of an edited video (experiment, not in the engine yet)

If he sends a script and raw takes instead of an edited video, see `lab/ASSEMBLE.md`: `lab/assemble.py`
picks the best take per script line and assembles one video, which then goes through step 1 as usual.

## Hard rules
- No music, ever. No B-roll, ever. No cover or caption pack.
- Don't post, commit or push anything without his yes.
- Report honestly what was checked and what wasn't. Sound is checked by measurement only.
