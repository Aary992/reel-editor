# reel-editor

Aarit's Reel engine: his raw takes (or one edited video) in, his look out. Claude runs it through the
`reel-edit` skill (`skill/SKILL.md`). Three looks, and every reel starts by asking him which one: **story**
(approved 10-22) and **v2** (locked 10-18) are in **[STYLE.md](STYLE.md)**, **paper** (locked 10-25, built in
Remotion) is in **[paper/README.md](paper/README.md)**. Everything about Google Flow is in
**[FLOW.md](FLOW.md)**. No music on any reel since 10-25.

## The process

| Step | Who | What happens |
|:-|:-|:-|
| 0. Cut | Claude | Raw footage only: `reel.py cut` takes out dead space, fillers, stutters and earlier takes, no script needed. Claude reads `cut report.txt` and drops alternative hooks with `--drop`. |
| 1. Ask | Claude | "Which look: story, paper or v2?" first, then (story, v2) "Do you want motion graphic text in this video?" Asked every time, never assumed. Paper reels go to `paper\paper.py` from here. |
| 2. Prep | Claude | `reel.py prep`: transcript, exact shot cuts, motion text picks (if yes), money-burn line, the Flow folder in Downloads, and (story look) a first draft of `overlays.json`. |
| 3. Review | Claude | Fixes misheard words in `words.json`, re-picks motion text if needed, adds in-scene visuals (`reel.py visual`). Story look: writes `overlays.json` (app UI cards on his exact words) and `story.json` (vine boom word, green override), checks them with `reel.py overlays`. |
| 4. Flow | Aarit | Makes the clips listed in `Downloads\<name> Flow\flow prompts.txt` and saves them back into that folder. Skipped when there is nothing to make. |
| 5. Render | Claude | `reel.py render`: the final Reel into Downloads, checked for frame count and loudness. Claude looks at frames inside every Flow window. No cover and no caption pack (his call 10-18). |

## Commands

```
py -3.14 reel.py cut "C:\raw\take 1.mp4" "C:\raw\take 2.mp4" --name "short name" [--drop TAKE | --drop "a phrase"]
py -3.14 reel.py prep "reels\short name\cut.mp4" --text-cuts yes|no --name "short name" [--look story|v2]
py -3.14 reel.py prep "C:\path\to\video.mp4" --text-cuts yes|no --name "short name"
py -3.14 reel.py overlays "short name" [--suggest]
py -3.14 reel.py preview "short name" --seconds 8 --zones
py -3.14 reel.py repick "short name" --only "₹1 CRORE|DAY 2"
py -3.14 reel.py visual "short name" 17.6 20.1 "the sunny garden turns grey and stormy"
py -3.14 reel.py visual "short name" --drop V1
py -3.14 reel.py status "short name"
py -3.14 reel.py map "short name" "<flow file>.mp4" T2
py -3.14 reel.py render "short name"
py -3.14 reel.py preview "short name"
py -3.14 reel.py split "short name"
py -3.14 paper\paper.py prep "short name" ["C:\path\to\edited video.mp4"]
py -3.14 paper\paper.py still "short name" 60 240 420
py -3.14 paper\paper.py render "short name"
```
A v2 render takes about 0.5 s per frame (a 55 s Reel is about 11 minutes), a story render about 0.15 s, so
Claude runs it in the background.

## Where things live

| Path | What |
|:-|:-|
| `reels\<name>\` | A Reel's working files: transcript, shots, picks, his Flow clips, preview, final. Never committed. |
| `Downloads\<name> Flow\` | The one folder he works from in Flow: `flow prompts.txt` (the only copy), the `upload ...` clips, `whole reel in 9s parts\`, and his results. |
| `Downloads\<name> final.mp4` | What he posts. |
| `reel.py` | The commands above. |
| `render.py` | The renderer for both looks (and the 10-17 style tests in `LOOKS`). |
| `storycut.py` | `reel.py cut`: dead space and mistakes out of raw takes, no script needed. |
| `story.py`, `overlays.py`, `face.py` | The story look: captions, punch-ins, sound; the app UI overlays; where his face is in the frame. |
| `moments.py` | Picks the motion text moments and writes their Flow prompts. |
| `talk_reel.py`, `fx.py`, `cuts.py`, `sections.py`, `transcribe.py` | Building blocks: captions, zoom, Flow clip timing, shot detection, transcript. |
| `lab\compare.py` | Side-by-side of look tests, for when he wants to compare styles again. |
| `lab\assemble.py` | EXPERIMENT, not in the engine yet: his script + raw clips in, a first cut out ([lab/ASSEMBLE.md](lab/ASSEMBLE.md)). |
| `leak_colors.json` | Which light-leak colour each Reel got, so the next one never repeats it. |
| `paper\` | The paper look: a Remotion project (`src\art.tsx` kit, `src\beats.tsx` = the current reel, `examples\` = finished reels' beats) and `paper.py`. |
| `music\` | His tracks. Not used by default since 10-25 (no music); a reel he asks music for names one in `story.json`. Not committed. |

## Setting it up on the PC

Step by step, with paths and fixes: **[PC_SETUP.md](PC_SETUP.md)**. `setup.ps1` installs pinned ffmpeg, the
Whisper venv and Pillow/numpy, downloads the fonts (Figtree, OFL) and the Mixkit sound effects (neither is
stored here: Mixkit's licence forbids redistribution), writes `config.json` and installs the Claude skill.
The captions (v2) and the overlays (story) use Segoe UI Variable, and the story captions Arial Bold; both ship
with Windows 11.
