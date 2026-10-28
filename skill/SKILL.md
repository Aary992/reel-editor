---
name: reel-edit
description: "Aarit's Reel engine. Use whenever Aarit sends or points to a video/Reel to edit (an .mp4/.mov, usually in Downloads), sends raw takes to cut, says 'edit this reel', 'make this reel', 'do the usual edit', 'Flow clips are in', gives on-screen text for a Reel, or sends a script with raw clips to assemble. Asks him first which look: story (dead space cut, plain white TikTok captions, real app UI overlays above his head on the exact word, punch-ins on jump cuts, vine boom), paper (cream paper split screens, Step N. headers, folder and Claude-icon motion graphics, built in Remotion), studio (full-screen motion graphics on a lit grey ruled backdrop with a moving 3D camera, pinned-note step board, Claude app mockups, word-by-word chest captions, face only for hook and CTA, built in Remotion) or v2 (bold iOS captions, light-leak cuts). Runs reel-editor/reel.py, paper/paper.py and paper/studio.py. Optional Flow motion text, in-scene visuals, SFX, loudness. No music, no cover, no caption pack."
---

# Reel edit (Aarit's looks: story, paper, studio and v2)

Engine: `C:\Users\Aaru\Documents\reel-editor` on the laptop, `D:\My Data\Documents\cc\reel-editor` on the
PC. Run `git pull` there first. Read `README.md`, `STYLE.md` and `FLOW.md` before the first run in a session.
Python is `py -3.14`. Four looks: **story** (his approved style since 10-22), **paper** (locked 10-25, the
creator tutorial's step-by-step look, everything in `paper\README.md`), **studio** (locked 10-25, full-screen
graphics on a lit grey backdrop with a 3D camera, everything in `paper\STUDIO.md`) and **v2**. **Before every reel, ask
him which one** (his call 10-25); never assume, never reuse the last answer. Never change a look unless he
asks. **No music on any reel, in any look** (his call 10-25: "too distracting").

**His approved story style (10-22, "good i like this style"): the engine does all of it by default, don't undo
it:** no dead space (each clip trimmed to where his voice starts and stops), captions under his real chin and
never on his mouth (the picture lifts up to 8% to make room), and where one clip hands over to the next a
small amber light leak, a 0.2 s soft dissolve and a 0.3 s zoom glide (cuts inside one clip stay hard, with the
punch-in). Details in STYLE.md.

## 0. Raw footage: cut it first

If he sends raw takes (pauses, retakes, several hooks) rather than an edited video:
```
py -3.14 reel.py cut "<take 1>" "<take 2>" ... --name "<short name>"
```
Read `reels\<name>\cut report.txt`: what was cut and why, and every take's words. Drop what the rules can't
know (alternative hooks, a take that doesn't belong, a phrase) and re-run with `--drop TAKE` or
`--drop "phrase"`. The result, `reels\<name>\cut.mp4`, goes through step 1; its transcript comes from the cut.
- **Order:** the cut sorts takes by file name. When his script wants another order, copy the takes into
  `reels\<name>\takes\` as `01 <take>.mp4`, `02 ...` and cut that folder.
- **Fillers:** drop a filler ("literally") only where it starts a clip ("And literally all you need" becomes
  "All you need"). Cut out of the middle of a short clip, it leaves a half-second piece that reads as a
  stutter (his note 10-22). Run Whisper on the new cut to make sure no word fragment survived.

## 1. Ask for everything first, in one message (his call 10-21)

Before building anything, read what he says: the cut's transcript, or for an edited video a quick Whisper
pass (`<whisper_python from config.json> transcribe.py "<video>" "<scratch>.json"`). Then send **one** message
with every ask, so he can gather it all at once. Build only after he answers; then render once.
- **Look:** "Which look do you want: story, paper, studio or v2?" Always the first ask. For paper, skip motion
  text and images below: ask for the hook title (two lines over his opening, offer 2 or 3 options) and anything
  real the beats should show (screenshots, his earlier reels), then follow **Paper look** below. For studio,
  skip motion text, hook line and images: ask only for anything real the graphics should show (screenshots,
  a document, a chart), then follow **Studio look** below.
- **Captions** (story, v2): "Which captions: the look's own, or glow?" Glow (approved 10-29) is SF Pro white
  caps, one line fixed in the middle, each word fading in softly with a faint glow (STYLE.md, `glowcaps.py`).
  It is one option, never the default; never reuse the last answer. If glow, add `--captions glow` to every
  `reel.py preview` and `render` of that reel.
- **Motion text** (story, v2): "Do you want motion graphic text in this video?" Never assume, never reuse the last
  answer. Prep refuses to run without it. If he wants one of each, make two reels from the one cut: copy
  `cut.mp4`, `cut.json`, `words.json` and `fixes.json` into `reels\<name> motion\` and prep that copy's
  `cut.mp4` with `--text-cuts yes` (story.py only uses the cut's faces when the video is the reel's own cut).
- **Hook line for the first 3 s:** the on-screen text over his opening (`render --text "..." --text-start 0
  --text-secs 3`). Offer 2 or 3 options drawn from his own hook; he picks one or writes his own.
- **Images:** a table: #, the word it lands on (with its second), what it shows, a Google search to find it.
  He saves them as 1, 2, 3... in `Downloads\<name> images\`. Never a wall of text cards, above all in the
  first 10 s. Ask for wide pictures, and nothing that gives away what the CTA withholds.
- **Anything else the edit needs:** screenshots or screen recordings of what he shows or names, takes that look missing or doubled (check Downloads for the same timestamps and his
  `_1.mp4` phone rough edit), words Whisper may have misheard.

When they arrive, check each image against its line before using it. Watch for a headline that says the
opposite of his line, a green "↑" badge on a "down" line, his mouse hover left in the shot, or someone else's
name or folder path in a screenshot he grabbed off Google (crop or blank it, and tell him). Ask again for
anything that doesn't fit.

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
  punchline word (`"green"` only to override the headline number and CTA; `"music"` only when he asks for
  music on this reel, naming the track). Check
  with `py -3.14 reel.py overlays "<name>"` and `reel.py preview "<name>" --seconds 8 --zones`.
- **Images** (asked for in step 1): `{"type": "image", "at": "<word>", "src": "images/1.png", "end": "+5"}`.
  Copy his files into `reels\<name>\images\`. `"end": "+5"` holds one picture until the next overlay pops in.
- **Open on an overlay (his call 10-22):** his first line gets one too, pinned just under his hook text with
  `"y": 0.185` and ending with it (`"end": "+3.0"`), e.g. a Claude progress card that fills up and turns to
  "Done" on his words. His `--text` sits 13% down, inside the overlay band, so every other overlay starts
  after the hook text is gone (3 s). Look at those frames.
- **Step trackers:** give every step an `"at"`. A step without one lights up when the tracker pops in and
  marks all the earlier steps done.
- **No B-roll, ever.** No cover (thumbnail) and no caption pack either (his call 10-18).

## 4. Hand over

Tell him, briefly:
- what to make in Flow: the folder `Downloads\<name> Flow\`, how many clips, and **every prompt pasted in
  chat** as a copyable block, with what to save it as and the word it lands on (he asked "where's the flow
  prompt?" when he only got the file path). If nothing is needed, say so and go straight to step 6.
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
any overlay that covers his hair or face. At a few clip changes pull the exact frames
(`select='between(n,A,B)'`): the dissolve has to start on the cut frame, with no frame of the old zoom on the
new clip. That's the whole delivery: no cover, no caption pack.

## Paper look (instead of steps 2 to 6)

Read `paper\README.md` first: layouts, colours, type, the graphics kit and the commands.
```
py -3.14 paper\paper.py prep "<name>" ["<edited video>"]
py -3.14 paper\paper.py still "<name>" 60 240 420 ...
py -3.14 paper\paper.py render "<name>"
```
- After the cut (step 0) or with an edited video, `prep` copies the video, words and his face boxes into the
  Remotion project. Fix misheard words in `reels\<name>\words.json` first, then re-run prep.
- Copy the current `paper\src\beats.tsx` to `paper\examples\<its reel>.tsx`, then rewrite it for this reel:
  first line `THIS REEL: "<name>"`, one graphic per beat landing on his exact words, `SCENES` switching
  face / split / full where takes start (a take with no face never gets the face layout), `SFX`, `NAMES`.
  Pictures and clips the beats use go in `reels\<name>\paper\` (served as `assets/<file>`).
- Check stills at every beat's pop and full state before rendering, then render in the background (about 2
  min for 34 s). It delivers `<name> final.mp4` to Downloads at -14 LUFS, no music. Look at the frames
  around every scene change (`select='between(n,A,B)'`): no caption or graphic carried into the next scene.
- Open, his note 10-25: smoother voice joins between takes. Not built; only when he asks.

## Studio look (instead of steps 2 to 6)

Read `paper\STUDIO.md` first: what the reference reels do, the backdrop, camera, objects, captions and sound.
```
py -3.14 paper\studio.py prep "<name>" ["<edited video>"]
py -3.14 paper\studio.py still "<name>" 60 240 420 ...
py -3.14 paper\studio.py render "<name>"
```
- Same inputs as paper: after the cut (step 0) or with an edited video. Fix misheard words in
  `reels\<name>\words.json` first, then re-run prep. Media goes to `paper\public\studio\`, so a paper prep
  never clobbers it.
- Copy the current `paper\src\studio\beats.tsx` to `paper\examples\studio <its reel>.tsx`, then rewrite it:
  first line `THIS REEL: "<name>"`. Face only for the hook, opinion lines and the CTA (hard cuts, about 25% of
  the reel); everything that explains is a graphics set with its own camera (`World` + keys), each object
  landing on his exact word. Use the kit: the pinned-note board as the step hub (the camera visits one note per
  step, done steps get a check), Claude's app (greeting, prompt box, attachments flying in, send, whip pan to
  the answer with highlights sweeping), documents to pan across, the numbered arc, one kinetic line with the
  key word in the black box, the comment pill CTA (`CTA`). Never a number or claim he didn't say.
- Check stills, then render in the background (about 5 min for 46 s). It delivers `<name> studio.mp4` to
  Downloads at -14 LUFS, no music. Look at frames inside every set and around every face cut.
- His notes 10-25 (built in): talking parts bright, not moody; subtle 100 to 106% zooms on every phrase while
  he talks.

## Raw clips instead of an edited video (experiment, not in the engine yet)

If he sends a script and raw takes instead of an edited video, see `lab/ASSEMBLE.md`: `lab/assemble.py`
picks the best take per script line and assembles one video, which then goes through step 1 as usual.

## Hard rules
- No B-roll, ever. No cover or caption pack. **No music on any reel, in any look** (his call 10-25: "too
  distracting"; story reels had a bed from 10-20 to 10-24). Only if he asks for music on one reel, name the
  track in its `story.json`.
- Ask which look (story, paper, studio or v2) before every reel.
- For story and v2, ask which captions too (the look's own or glow); glow is an option, never the default.
- Don't post, commit or push anything without his yes.
- Report honestly what was checked and what wasn't. Sound is checked by measurement only.
