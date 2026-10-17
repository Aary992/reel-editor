# Text cutaways: how Claude picks moments and writes Flow prompts

Aarit's talking-head Reels get **2 to 3 After Effects-style motion-graphic text cutaways** (2 for ~30 s,
3 for ~45 s). Each is a hard cut from his face to a full-screen animated word that lasts **exactly as long
as he is saying those words**, never longer. The Flow clip is generated per Reel from the prompts that
`moments.py` writes. These are not random visuals: every cut shows the words he is saying at that moment.

## UPDATE 10-17, his rule: Flow moments are a MIX, never typography only

He said it plainly: "a mix of typography and b rolls and visuals". Every Reel's Flow plan has all three kinds,
about one moment every 7 to 8 s, alternating kinds, at least ~2 s apart:

- **TYPOGRAPHY** (`T1.mp4`...): the red-card number cuts below. Numbers only ("₹1 CRORE", "DAY 2").
  Full-screen, captions step aside, a pop on each. Lasts the spoken words.
- **B-ROLL** (`B1.mp4`...): Flow text-to-video, a cinematic shot of the concrete image or metaphor in the line
  ("it was just an idea in my head" -> a pencil app sketch that glows into a real screen). Goes on his weakest
  footage (empty rooms, filler), never on his best face moment. Captions KEEP RUNNING over it. A whoosh on the
  way in unless another sound is within 1.2 s. In `cuts.json` with `"kind": "broll", "from": 0.3, "speed": 1.0`.
  Prompt: vertical 9:16, 35mm shallow depth of field, warm natural vlog colour, action starts in the first
  second and is done within 2 s, no faces, no text or logos.
- **VISUAL** (`V1.mp4`...): an Omni in-scene edit of HIS OWN shot (mood shift, light, weather, particles) on a
  line with feeling. He uploads the exact shot (shot-boundary to shot-boundary, max 9 s), exported to
  `Downloads\<name> flow uploads\`. In `edits.json` with `"segment"`. Only on shots where he is not talking to
  camera, or check lip sync. Prompt carries the "keep the person exactly as he is" block.

moments.py still auto-picks typography only: Claude adds the B-roll and visuals by hand from the transcript
and shot frames, writes ONE prompts file in play order, and renders with `lab/lab_render.py --look v2`, which
lays in all three kinds. First done on recording 55 (3 typography, 3 B-roll, 2 visuals in 55 s).

## Per Reel

1. `python transcribe.py ...` and `python sections.py ...` into `reels/<name>/`
2. `python moments.py --reel reels/<name>` drafts candidates and picks 2-3 (count set by the Reel's length).
3. **Claude reviews the picks** and re-runs with `--only "TEXT|TEXT"` when it knows better (e.g. skip a
   number the screen is already showing).
3b. Prep also splits his Reel into parts of at most 9 s (Flow only edits clips of 10 s or less) in `Downloads\<name> flow parts\`
   (`reel.py split <name>` redoes it). Nothing sent to Flow is ever longer than 9 s.
4. Aarit generates each prompt in `text cuts.txt` in Flow, checks the spelling, and saves `T1.mp4`, `T2.mp4`...
5. `python talk_reel.py ... --cuts reels/<name>/cuts.json --edits reels/<name>/edits.json`

## Picking rules

- 2 to 3 cuts, at least 8 s apart, spread through the Reel.
- **Numbers first.** The one approved animation is a count-up, so prefer "Day N", counts ("17 TRADES")
  and money ("₹1 CRORE"). Bigger, more specific numbers beat small ones. CTA, "live" and one-word claims
  only when there is no good number.
- On-screen text is 1 to 3 words, taken from what he actually says. Never invent a claim.
- The cut window is the spoken span: the first word's start to the last word's end.
- Never cut over his own text cards or an in-scene Omni edit (the money burn on a loss line).
- No financial tips or buy/sell language in any text. No em dashes.

## The one style (approved: the "17 TRADES" cut)

- **Colours:** the `red_card` pack is sampled from his edits: background #EDEBEC, red #D43D29, heavy
  rounded sans like Figtree ExtraBold, flat 2D.
- **Number:** counts up like an odometer (a lone "1" just rolls into place).
- **Words:** slide in beside the number, from the left if they come first ("DAY 1"), from the right if
  they come after ("17 TRADES"), with letters staggered by a couple of frames.
- **Motion:** every move uses After Effects Easy Ease with a gentle overshoot and motion blur, never
  linear. Everything finishes within 0.8 s, then holds still.
- **Rejected looks, never use them:** slam with shake, typewriter, bubble pop, pulse dot, glitch crack.

## How the renderer makes it exact and smooth

- `fx.auto_time` measures where the Flow clip actually animates (frame differences, relative threshold),
  skips dead frames at the start, and speeds the clip up (never slows it down) so the motion lands at about
  85% of the spoken span, then holds.
- `minterpolate` (motion-compensated) re-times the clip to 29.97 fps, so a 24 fps or sped-up clip glides
  with no duplicated frames. Verified on an animated stand-in: 0 repeated positions, at rest at 79%.
- Captions step aside during a cut. Each cut gets a pop that varies by file and pitch.

## In-scene effect (separate from cutaways)

The money-burn edit (cash drifting up and burning into red sparks around him, made with Omni edit mode on his
own clip) is approved for lines about losing money. Use it at most once per Reel.
