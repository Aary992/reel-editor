# Raw clips to a first cut (EXPERIMENT)

Not part of the engine yet: `reel.py` doesn't know about it. If it holds up on his real raw clips, it gets
wired in as a step before `prep`.

**In:** his script (a text file) and a folder of raw clips: every take, any order, any file names.
**Out:** `Downloads\<name> assembled.mp4` (1080x1920) and `<name> assembly report.txt`. The assembled
video then goes through the normal process: ask about motion text, `reel.py prep`, and so on.

```
py -3.14 lab/assemble.py "<name>" --script "<script.txt>" --clips "<raw folder>"
```

## How it works

1. **Transcribes every clip**, stretch by stretch (split at pauses, `lab/transcribe_chunks.py`). Whisper
   drops repeated words when a restart sits in the same stretch, so this keeps every take visible.
   Cached in `reels\<name> assembly\words\`, so re-runs only redo the cutting.
2. **Splits the script into lines** (sentence by sentence). A line `[show: graph]` puts the clip whose name
   contains "graph" over the next line's picture; his voice stays.
3. **Finds every take of every line** in every clip with a local alignment that tolerates misheard words
   ("one" = "1", "cheque" ~ "check"). A take must say at least half the line.
4. **Picks one take per line:** most complete, cleanest, best heard, later takes win ties (the last take is
   usually the good one), with a bonus when a line carries straight on from the previous line in the same
   clip, so his natural delivery stays together.
5. **Cuts:** restarts (the same words said again straight after), fillers, runs of 3+ unscripted words, and
   pauses over 0.35 s. A single natural extra word stays, because cutting it would leave a jump cut
   mid-sentence. Every cut lands on the quietest 10 ms between words, with a 12 ms fade so nothing clicks.
6. **Renders** each piece frame-exact (sound and picture locked), joins them, lays any footage on top.

## The report

Line by line: which clip and take, how much of the line it says, what was cut out, the other takes, where
it sits in the video, and `CHECK` notes when a take skips script words or a word runs suspiciously long
(a hidden restart). Fix anything with:

| Option | What it does |
|:-|:-|
| `--force "3=IMG_0042"` | Line 3 from that clip's best take |
| `--force "3=IMG_0042@12.5"` | Line 3 from the take nearest 12.5 s in that clip |
| `--skip 7` | Leave line 7 out |
| `--max-pause 0.5` | Keep more breathing room |
| `--fps 30` | Output frame rate (default: his clips', max 30) |

## Tested (10-18) on fake raw takes built from recording 55

Five shuffled clips: a false start then the full take, an extra 1.4 s pause between lines, one line said
twice, the rest in one go, plus a silent graph-screen clip cued with `[show: graph]`. The script had wording
differences on purpose ("one crore cheque", "That is not nothing ... back to work").

- All 16 lines in script order; false start, duplicate take and the long pause gone; 54.4 s.
- Re-transcribing the result: 184 of 184 words, in order (ratio 0.995; Whisper heard one "that's" as "it's").
- Picture and sound end within 0.04 s; longest pause left 0.48 s.
- The graph footage sat on its line; `--force` and `--skip` worked.

## Limits (be honest with him about these)

- Claude can't hear delivery: takes are picked on words, completeness and cleanliness, not energy or tone.
  He should skim the assembled cut before the full render.
- A restart with no pause before it can still hide inside one long Whisper word; the report flags words
  over 1.2 s.
- Footage only goes where the script cues it. His Premiere-style red cards and split screens aren't made.
- Not yet tried on his real raw clips (different mics, rooms, long rambling takes, Hinglish).
