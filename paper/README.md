# The paper look (LOCKED 2026-10-25)

(The **studio** look lives in this same Remotion project with its own entry point, `src\studio\`: see
[STUDIO.md](STUDIO.md).)

Copied from a creator's "edit your video with AI" tutorial (he sent it 10-25 and asked for his exact style,
motion graphics included). First reel: "claude edits" (`Downloads\claude edits motion.mp4`), approved 10-25:
"Good, I like this. Let's lock this style in." Built in Remotion (React), not in render.py.

## How a reel gets made

```
py -3.14 reel.py cut "<take 1>" "<take 2>" ... --name "<name>"     dead space out, words.json + cut.json
py -3.14 paper\paper.py prep "<name>"                              the cut, its words and his face boxes in
  (Claude writes paper\src\beats.tsx for this reel, see below)
py -3.14 paper\paper.py still "<name>" 60 240 420 ...              check frames, as often as needed
py -3.14 paper\paper.py render "<name>"                            "<name> final.mp4" into Downloads
```
An edited video instead of raw takes: `paper.py prep "<name>" "<video>"` transcribes it and measures one face
box for the whole video. Check `reels\<name>\words.json` for misheard words before writing the beats.

`paper.py prep` copies the video, the sound effects and `reels\<name>\paper\*` (pictures and clips the beats
use, served as `assets/<file>`) into `paper\public\`, and writes `paper\src\reel.json`. None of that is
committed. A render is about 2 minutes for 34 s; run it in the background.

**beats.tsx is the only per-reel file.** Its first line names the reel (`THIS REEL: "<name>"`); `paper.py`
refuses to render another reel with it. It holds one component per beat, then `SCENES` (layout and graphic per
time range), `SFX` and `NAMES` (words that keep their capital in the captions). Before rewriting it, copy the
finished one to `paper\examples\<name>.tsx`. Start from the newest example; the kit is in `src\art.tsx`.

## The three layouts (hard cuts, no transitions)

| Layout | What's on screen | Use it for |
|---|---|---|
| **face** | Full talking head. Captions under the chin. | Hook, opinions, the CTA, lines with nothing to show |
| **split** | Top half: paper panel with the graphic. Bottom half: his head, hair just under the seam. Captions on the seam. | Most "here's how" lines |
| **full** | Paper only, no face. Captions in the lower middle (`captionY`). | Folder trees, the recap, a screen take with no face |

Switch layout on almost every sentence, always where a take starts (`clips` in reel.json). The tutorial runs
about 30% face, 45% split, 25% full.

## Colours (sampled from his frames)

| Token | Hex | For |
|---|---|---|
| Paper | `#DFD6C4` | Background, plus a faint 54 px grid and paper grain |
| Terracotta | `#CB603E` | "Step N.", the active label, dotted lines, checks, the Claude mark |
| Ink | `#1C1814` | Header titles, labels |
| Folder blue | `#76CDF2` | macOS folders, timeline clips |
| Card white | `#FFFFFF` | UI cards and the CTA pill, soft shadow, 26 px radius |

## Type

- Inter Tight only (his looks like SF Pro), letter spacing pulled in hard (about -0.04em).
- **Header:** `Step 1.` in terracotta + the title in ink, 800, 60 px, near the top of the panel.
- **Captions:** white, 800, 78 px, dark outline and a soft shadow. 1 to 3 words, lowercase (names in `NAMES`,
  "I" and ALL CAPS words such as the comment word stay). No colours, no emoji, only a tiny pop.
- **Hook title:** white, 700, two lines at the top over the face for the whole opening. Asked for like the
  story look's hook line.

## Motion graphics kit (`src/art.tsx`)

- **Objects, not text.** Each line becomes one picture: a folder, an app icon, a timeline, a card. Text only
  labels things.
- `Folder`: macOS-style blue folder tilted in 3D, `solid` takes it from the pale ghost to the full folder,
  `open` drops the front flap, children peek out of it.
- `ClaudeIcon` / `Starburst`: the Claude mark. `DottedPath`: a terracotta dotted line that draws itself, with
  an arrowhead. `Card`, `Check`, `Label`, `StepHeader`, `Paper`.
- Every element lands on the exact word that names it (`at("word", afterSecond)`), with a small overshoot.
- **Recap:** the main object in the middle, every step in a corner, dotted arrows pointing in.
- **CTA:** a white pill with the Claude mark types the comment word, then the arrow button goes dark.
- **Hook:** may show a row of his earlier reels under the title for the first sentence (it covers his hair,
  as in the tutorial; never his eyes).

## Sound

- Voice two-pass loudnorm to -14 LUFS, limiter -2.5 dB.
- Soft pops on graphics, a light whoosh into full-paper scenes, key clicks on the typed CTA.
- **No music** (his call 10-25, for every look: "too distracting").

## Open (his notes, not done yet)

- "We could make the transition between the voiceover smoother": the voice still hard-cuts at every take
  change. Try short audio crossfades at the joins when he asks; he said to lock the look in first (10-25).
