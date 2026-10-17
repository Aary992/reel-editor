# Aarit's talking-head Reel style (LOCKED 2026-10-17)

He signed this look off on "hedge 1 final". Don't change any of it unless he asks. `reel.py` applies all of it.

## Captions
- Figtree ExtraBold (Fontsource 5.3.0, latin-800), white, size 82.8 on a 1080-wide frame (matched to his inspo).
- Soft drop shadow: black at about 62%, blur 8, 4 px down. No outline, no colour, no highlight.
- Sentence case as spoken, trailing punctuation removed. 2 to 3 words per caption (4 if short), max 21
  characters. Breaks come from the cost rules in talk_reel.py: no weak last word, keep a number with its
  noun, no "and" mid-caption.
- iOS-style motion: a 90 ms fade in, 8 px rise and 94% to 100% settle over 160 ms (ease-out), 70 ms fade out.
- Position: 70% down on face shots (just under the mouth, above the mic), 38.5% on split screens (on his
  shirt above the seam). Hidden on his own red text cards and during text cuts. Held through pauses
  shorter than 0.8 s.

## Zoom (approved: "feels right")
- Subtle keyframed drift on face shots only: each sentence eases 1.00 to 1.06 (or back) with smootherstep,
  over at most 3 s, anchored at mouth height (y 0.66). Never a punch-in.
- Done on the YUV planes with sub-pixel crop boxes. No ffmpeg zoompan (it shakes), no RGB round-trip
  (it darkens skin).

## Text cuts (see TEXT_CUTS.md)
- OPTIONAL per video (his rule 10-18): ask him every time whether he wants motion graphic text.
  `reel.py prep --text-cuts yes|no`; with no, the Reel has none.
- When yes: 2 to 3 per Reel (2 for about 30 s, 3 for about 45 s), numbers first, at least 8 s apart.
- One style only, the "17 TRADES" look: odometer count-up, word slides in, red card palette (#EDEBEC / #D43D29).
- Each cut lasts exactly the spoken words. The clip is auto-timed to land at 85% and sped up only, never
  slowed down. Nearest-frame retiming (no minterpolate mci, which tears letters).
- iOS-style soft cut: 0.1 s dissolve in, 0.07 s dissolve out.

## Money burn (in-scene Omni edit)
- Only on a line where he talks about losing money, at most once per Reel, on one continuous face shot.
- The prompt is locked in reel.py (MONEY_BURN_PROMPT). Reject any result where his lip sync drifts.

## Sound
- No music, ever.
- Whooshes only where the shot type changes (face / card / split screen), never on plain jump cuts.
  The 3 Mixkit whooshes cycle, each lap pitched down 2 semitones. Each one peaks at -10 dBFS, landing on
  the cut frame.
- A pop on each text cut and on his on-screen text. The 3 Mixkit pops cycle with varied pitch, peaking at
  -12 dBFS. No two sounds in a row are identical.
- Voice: two-pass loudnorm to -14 LUFS, limiter at -2.5 dB (measured -14.2 LUFS / -1.8 dB peak).

## His own text and the cover
- On-screen text is optional. He types it, and it shows for 1 to 4 s in an Instagram-text look (Figtree
  Bold, white, soft shadow, optional colour emoji), hidden on cards and cuts.
- Cover: his line exactly as he writes it, Figtree Bold, on the sharpest still face frame (cover_pick), kept
  inside the 3:4 grid area.

## Never (all tried and rejected)
- A persistent "POV" title.
- Code-drawn icons or pop-in visuals.
- Hard punch-in zooms.
- External B-roll cutaways (tried again 10-17 with Flow B-roll; he dropped it for good 10-18).
- Money "orbit", "rain" or "golden" variations.
- Slam, typewriter, bubble, pulse or glitch text animations.
- Big uppercase captions with a yellow highlight.
- Music.

## Every delivery is checked
- The final has the same frame count as his source (nothing drifted).
- Loudness is about -14 LUFS with peaks around -2 dB.
- Claude looks at frames from every text cut and the money edit, and checks each Flow clip's spelling.
- Clips are mapped by what is on screen, not by file name: his names have been swapped before.
