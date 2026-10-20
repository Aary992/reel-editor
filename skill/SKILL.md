---
name: reel-edit
description: "Aarit's Reel engine. Use whenever Aarit sends or points to a video/Reel to edit (an .mp4/.mov, usually in Downloads), sends raw takes to cut, says 'edit this reel', 'make this reel', 'do the usual edit', 'Flow clips are in', gives on-screen text for a Reel, or sends a script with raw clips to assemble. Runs reel-editor/reel.py: the story look (dead space cut, plain white TikTok captions, real app UI overlays above his head on the exact word, punch-ins on jump cuts, vine boom) or the v2 look (bold iOS captions, light-leak cuts). Optional Flow motion text, in-scene visuals, SFX, loudness. No cover, no caption pack."
---

# Reel edit (Aarit's looks: story, and v2)

Engine: `C:\Users\Aaru\Documents\reel-editor` on the laptop, `D:\My Data\Documents\cc\reel-editor` on the
PC. Run `git pull` there first. Read `README.md`, `STYLE.md` and `FLOW.md` before the first run in a session.
Python is `py -3.14`. The look is **story** (default since 10-20) unless he asks for v2. Never change a look
unless he asks.

## 0. Raw footage: cut it first

If he sends raw takes (pauses, retakes, several hooks) rather than an edited video:
```
py -3.14 reel.py cut "<take 1>" "<take 2>" ... --name "<short name>"
```
Read `reels\<name>\cut report.txt`: what was cut and why, and every take's words. Drop what the rules can't
know (alternative hooks, a take that doesn't belong, a phrase) and re-run with `--drop TAKE` or
`--drop "phrase"`. The result, `reels\<name>\cut.mp4`, goes through step 1; its transcript comes from the cut.

## 1. Ask for everything first, in one message (his call 10-21)

Before building anything, read what he says: the cut's transcript, or for an edited video a quick Whisper
pass (`<whisper_python from config.json> transcribe.py "<video>" "<scratch>.json"`). Then send **one** message
with every ask, so he can gather it all at once. Build only after he answers; then render once.
- **Motion text:** "Do you want motion graphic text in this video?" Never assume, never reuse the last
  answer. Prep refuses to run without it.
- **Hook line for the first 3 s:** the on-screen text over his opening (`render --text "..." --text-start 0
  --text-secs 3`). Offer 2 or 3 options drawn from his own hook; he picks one or writes his own.
- **Images:** a table: #, the word it lands on (with its second), what it shows, a Google search to find it.
  He saves them as 1, 2, 3... in `Downloads\<name> images\`. Never a wall of text cards, above all in the
  first 10 s. Ask for wide pictures, and nothing that gives away what the CTA withholds.
- **Anything else the edit needs:** screenshots or screen recordings of what he shows or names, a different
  music track, takes that look missing or doubled (check Downloads for the same timestamps and his
  `_1.mp4` phone rough edit), words Whisper may have misheard.

When they arrive, check each image against its line before using it. Watch for a headline that says the
opposite of his line, a green "↑" badge on a "down" line, or his mouse hover left in the shot. Ask again
for anything that doesn't fit.

## 2. Prep

```
py -3.14 reel.py prep "<video>" --text-cuts yes|no --name "<short name>" [--look story|v2]
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
- **Story look:** rewrite the drafted `overlays.json`: app UI cards that show what he says (his file going to
  Claude, Claude's answer, a step tracker, a score, word pills, the comments sheet on the CTA), each part
  anchored to his exact word, one at a time, nothing he didn't say. Write `story.json` with `"boom"`: the
  punchline word (`"green"` only to override the headline number and CTA; `"music"` only for a different
  track than his default, or `false` if he wants this one without). Check
  with `py -3.14 reel.py overlays "<name>"` and `reel.py preview "<name>" --seconds 8 --zones`.
- **Images** (asked for in step 1): `{"type": "image", "at": "<word>", "src": "images/1.png", "end": "+5"}`.
  Copy his files into `reels\<name>\images\`. `"end": "+5"` holds one picture until the next overlay pops in.
- **Hook line:** his `--text` sits 13% down, inside the overlay band, so start the first overlay after the
  hook text is gone (3 s), and look at those frames.
- **No B-roll, ever.** No cover (thumbnail) and no caption pack either (his call 10-18).

## 4. Hand over

Tell him, briefly:
- what to make in Flow: the folder `Downloads\<name> Flow\`, how many clips, and that each one says how to
  make it in `flow prompts.txt`. If nothing is needed, say so and go straight to step 6.
- any words you're unsure Whisper heard right.

Everything else (hook line, images, other assets) was asked for in step 1, so don't ask again here.

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
About 0.5 s per frame (v2) or 0.15 s (story), so run it in the background. It checks frame count and
loudness and delivers `<name> final.mp4` to Downloads. Then look at frames inside every Flow window, around a
few cuts and (story) at every overlay's pop and full state, before you say it's done: the render log flags
any overlay that covers his hair or face. That's the whole delivery: no cover, no caption pack.

## Raw clips instead of an edited video (experiment, not in the engine yet)

If he sends a script and raw takes instead of an edited video, see `lab/ASSEMBLE.md`: `lab/assemble.py`
picks the best take per script line and assembles one video, which then goes through step 1 as usual.

## Hard rules
- No B-roll, ever. No cover or caption pack. Music: every story reel gets his music bed (25% under the hook,
  then 10%) from the track in `reel-editor\music\` (his call 10-20). If the render log says "NO MUSIC",
  that folder is empty: ask him for a track. v2 reels have no music, ever.
- Don't post, commit or push anything without his yes.
- Report honestly what was checked and what wasn't. Sound is checked by measurement only.
