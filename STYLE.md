# Aarit's Reel look (LOCKED 2026-10-18, "v2")

He picked this from six side-by-side options on recording 55 and signed it off with the finished Reel.
Don't change any of it unless he asks. `render.py` applies all of it; the values live in `LOOKS["v2"]`.

## Captions
- **Font:** Segoe UI Variable, Bold Display, 76 px on a 1080-wide frame. Always bold, for the iOS look.
- **Colour:** white. Key words (numbers, crore, MarketPlay, VC, months...) take a colour, and **every caption
  with a key word gets the next colour**, so it changes each time: red #FF453A, yellow #FFD60A,
  blue #64D2FF, orange #FF9F0A, green #30D158, pink #FF375F, purple #BF5AF2 (iOS system colours).
- **Motion:** words appear one by one as he says them. Each one blurs into focus (blur 9 to 0), rises 16 px
  and settles from 97% to 100% over 0.26 s (ease-out). The caption fades out over 0.07 s.
- **Shadow:** black at about 51%, blur 10, 3 px down. No outline, no box.
- **Words:** sentence case as spoken, punctuation removed, 2 to 3 words per caption (the breaking rules in
  `talk_reel.chunk`), held through pauses under 0.8 s, two lines only if wider than 900 px.
- **Position:** 70% down. Hidden while a motion text clip is on screen.

## Cuts: the light-leak glow
- A soft glow washes over every hard cut, 0.32 s either side, peaking on the cut frame (screen blend, at
  most 55%). One glow from the top corner, a second from the opposite bottom corner; the side flips cut to cut.
- **The colour changes every video:** violet, amber, rose, teal, gold, crimson, in turn, so a new Reel never
  repeats the last one. Each Reel keeps its colour on re-renders (`leak_colors.json`).
- Cuts are found on the exact frame (`render.refine_cuts`): ffmpeg's scene score fires up to 0.3 s early on
  his edits, so every cut is snapped to the frame where the picture really changes.

## Picture
- Light grade: saturation +7%, contrast +4%, a touch warmer. No grain.
- The approved zoom: each sentence eases 1.00 to 1.06 (or back) with smootherstep, over at most 3 s,
  anchored at mouth height (y 0.66). Never a punch-in. Sub-pixel crop boxes; colour converted with explicit
  BT.709 matrices both ways.

## Flow clips (see FLOW.md)
- **Motion graphic text is optional, asked every time.** When yes: 2 to 3 per Reel, numbers first, the one
  "17 TRADES" style (red card #EDEBEC / #D43D29, odometer count-up, word slides in). Each lasts exactly the
  spoken words, with a 0.1 s dissolve in and 0.07 s out.
- **In-scene visuals:** Flow edits of his own shot (mood, light, weather, particles) on a line with feeling.
- **Money burn:** only on a line about losing money, at most once per Reel.
- **No B-roll, ever.**

## Sound
- **No music, ever.**
- Whooshes only where the shot type changes (face / card / split screen), peaking at -10 dBFS on the cut
  frame. The 3 Mixkit whooshes cycle with the pitch varied, so no two in a row sound the same.
- A pop on each motion text clip and on his on-screen text, peaking at -12 dBFS.
- **+20% accents:** for every five planned sounds, about one more: a soft impact (-12 dBFS) on a stakes or
  doubt line and a light ding (-15 dBFS) on a payoff line, alternating, placed in the longest stretches with
  no other sound and at least 2.5 s from any. Made in code (`render.ensure_sfx`), so nothing to download.
- Voice: two-pass loudnorm to -14 LUFS, limiter at -2.5 dB (recording 55: -14.1 LUFS, -2.3 dB peak).

## His own text and the cover
- On-screen text is optional. He types it; it shows for 1 to 4 s in an Instagram-text look (Figtree Bold,
  white, soft shadow, optional colour emoji), fades 0.09 s in and 0.07 s out, hidden during motion text.
- Cover: his line exactly as he writes it, Figtree Bold, on a still face frame (Claude recommends one of the
  3 picks or a better moment with `--cover t=SECONDS`), kept inside the 3:4 grid area.

## Never (all tried and rejected)
- B-roll cutaways (stock or Flow-made; tried again 10-17, dropped for good 10-18).
- A persistent "POV" title. Code-drawn icons or pop-in visuals. Hard punch-in zooms.
- Money "orbit", "rain" or "golden" variations.
- Slam, typewriter, bubble, pulse or glitch text animations.
- Big uppercase captions with a yellow highlight; key words only ever in one colour.
- The "spotlight" pill and "keynote" card looks (10-17 tests).
- Music.

## Every delivery is checked
- The final has the same frame count as his source, and loudness is about -14 LUFS with peaks near -2 dB.
- Claude looks at frames inside every motion text clip and visual, checks each Flow clip's spelling, and
  checks that a visual's cut lands where the source's does (Flow has drifted one by 0.68 s before).
- Clips are matched by what is on screen, never by file name.
- Sound is checked by measurement (Claude can't hear audio).

## The previous look (locked 10-17 to 10-18)
Figtree ExtraBold 82.8 px white captions with a fade-and-rise, no colour, no transitions, whooshes and pops
only. Still in `talk_reel.py` for reference.
