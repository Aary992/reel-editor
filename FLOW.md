# Google Flow: what goes in, how it's prompted, how it comes back

Flow makes three kinds of clips for a Reel. Nothing else: **no B-roll, ever** (his call 10-18).

| Kind | Slot | When | How it's made |
|:-|:-|:-|:-|
| Motion graphic text | `T1.mp4`... | Only if he said yes for this video | Flow text to video, no upload |
| In-scene visual | `V1.mp4`... | Claude picks 0 to 2 lines with feeling | Flow edit of his own shot, uploaded |
| Money burn | `M1.mp4` | Only on a line about losing money | Flow edit of his own shot, uploaded |

## The Flow folder

Everything he needs is in **one folder: `Downloads\<name> Flow\`**. `reel.py` builds it at prep and refreshes
it after `repick` or `visual`. No folder means nothing to make in Flow.

- `flow prompts.txt`: the only copy of the prompts, in play order, with what to save each one as.
- `upload V1 (17.6-20.1s).mp4`...: the exact shots to upload for visuals and the money burn.
- `whole reel in 9s parts\`: his full video in pieces Flow can edit, in case he wants them.
- His results go back into this folder. `reel.py status` collects them; a file with Flow's own name is
  matched by its frames and assigned with `reel.py map`.

**Flow only edits clips of 10 s or less**, so nothing he uploads is ever longer than 9 s.

## Motion graphic text (optional)

**Ask him every time:** "Do you want motion graphic text in this video?" `reel.py prep` needs
`--text-cuts yes|no` and refuses to run without it. The answer is kept in `reels/<name>/options.json`.

**Picking** (`moments.py`, then Claude reviews and re-picks with `reel.py repick --only`):
- 2 to 3 per Reel (2 for about 30 s, 3 for about 45 s), at least 8 s apart, spread through the Reel.
- Numbers first: "Day N", counts ("17 TRADES"), money ("₹1 CRORE"). Bigger, more specific numbers win.
- 1 to 3 words, exactly what he says. Never invent a claim, no buy/sell language, no em dashes.
- Skip anything the screen already shows, his own text cards, and in-scene edits.
- The window is the spoken span: the first word's start to the last word's end.

**The one style**, the "17 TRADES" look: background #EDEBEC, red #D43D29, heavy rounded sans like Figtree
ExtraBold, flat 2D. The number counts up like an odometer; the word slides in beside it (from the left if it
comes first, "DAY 2"; from the right if after, "17 TRADES") with letters staggered; Easy Ease with a gentle
overshoot and motion blur; everything done within 0.8 s, then still. Never slam, typewriter, bubble, pulse
or glitch.

**Timing:** `fx.auto_time` finds where the Flow clip animates and speeds it up (never slows it) so the motion
lands at 85% of the spoken words, then holds. Retiming takes the nearest frame (no motion interpolation, it
tore letters). Captions step aside; each clip gets a pop.

## In-scene visuals

A Flow edit of **his own shot** that changes the mood, light, weather or adds particles, on a line with
feeling. Recording 55's V2: "That's not nothing", golden light and floating particles in the mirror shot.

- Pick a shot where he isn't talking to camera (side profile, from behind, a room), or check lip sync.
- One visual covers whole shots. `reel.py visual NAME START END "what changes"` snaps to the real cuts,
  numbers the slot, exports the upload clip and writes the prompt:
  "Edit the provided video. <what changes> Keep it subtle and cinematic. Keep the person ... exactly as he is
  ... the same length and exactly the same timing as the original, frame for frame ..."
- Describe the change so it's **visible from the first frame**. A change that builds slowly can come back
  too faint (recording 55's first V1).
- If the upload starts a few frames before the real cut, set `"on"` in `edits.json` to the cut, so only the
  edited shot is used.

## Money burn

Cash drifting up and burning into red sparks around him (`MONEY_BURN_PROMPT` in `reel.py`, word for word).
Only on a line about losing money, at most once per Reel, on one continuous face shot. Found automatically
at prep.

## Checking what comes back

For every clip, before rendering:
- **Motion text:** the spelling, letter by letter (₹, numbers, words).
- **Visuals and money burn:** that he is unchanged (face, body, phone, lip sync) and that **the cut inside the
  clip lands at the same moment as in the source**. Measure it frame by frame: Flow drifted recording 55's
  V1 by 0.68 s, and that clip had to be dropped. The render also skips any clip more than 20% off its slot.
- Match clips by what's in them, never by file name.
