# Aarit's Reel looks

Two looks. New reels get **story** (the default since 10-20, his ask); **v2** (locked 10-18) is one flag away:
`reel.py prep ... --look v2`. Don't change either unless he asks.

# The story look (NEW 2026-10-20, from his inspo; awaiting his verdict on the demo)

He sent two Reels by a creator who edits with Claude ("Claude just changed video editing forever" and the
"beginner tutorial") and asked for exactly that edit. The creator's own prompt, read off his on-screen cards:
"1. Captions: 2-3 words, white, no box, no animation. 2. Keep everything out of the TikTok button zones.
3. Real app UI above my head, never on my face. 4. Every graphic pops in on the exact word. 5. Voice 200%,
music 25% then 10%, vine boom on the punchline." Plus his three core things: perfect the dead space, the
classic TikTok captions, the storytelling style. Everything below was measured frame by frame on his videos.
`story.py`, `overlays.py`, `storycut.py` and `face.py` apply it.

## Dead space and mistakes (`reel.py cut`, no script needed)
- In: his raw video, several raw takes, or a folder. Out: one tight 1080x1920 video that starts on his first
  word. Landscape takes are cropped to 9:16 around his face.
- Cut: fillers, restarts and stutters ("now I- now I": the same 1-6 words said back to back, the last go
  stays), earlier takes of a sentence he says again (the last take stays), words Whisper "hears" in the
  silence, and every pause over 0.35 s (his inspo never leaves more than about 0.35 s between words).
- Claude reads `cut report.txt` and drops what the rules can't know: alternative hooks, a whole take, a
  range, a phrase (`--drop`). Every cut lands on the quietest 10 ms with a 12 ms audio fade.
- The cut's transcript comes from the takes (stretch by stretch), moved onto the cut's clock, so prep doesn't
  re-transcribe (that lost punctuation and heard "Claude" as "clod").

## Captions
- 2 to 3 words (the `talk_reel.chunk` rules), white, **no box, no outline, no animation**: each caption just
  appears and is replaced. Sentence case as spoken, punctuation off, swear words starred.
- Arial Bold, 63 px on a 1080-wide frame (his measured 240 px "sent Claude" on 720). Soft dark edge only
  (shadow 53%, blur 4, 2 px down).
- **Green #09F31C, 1.25x bigger, on two captions only:** the headline number in his first sentence and the CTA
  ("Comment X"). Override with `"green": [...]` in `story.json`.
- Centred, inside 720 px (the like/comment/save/share column starts 180 px from the right between 50% and 80%).
- Height: at chin level, like his (his sit at 55% on his framing, right on the chin line). On Aarit's
  framing that means just under his chin, one height per take, kept between 55% and 77.5%.

## Overlays: real app UI above his head
- Frosted dark-glass cards drawn like the apps: a Claude chat card (header, his message bubbles with a file or
  chart attachment, Claude's replies or ticks, reply bar), a file chip, a step tracker, a score that counts up,
  coloured word pills, a dark comments sheet that types the CTA word, posts it, likes it and gets a reply
  notification, a small toast, a progress card, plain chapter lines. Types and fields: `overlays.py`.
- Claude writes `overlays.json` after reading the transcript (`reel.py overlays NAME --suggest` drafts one).
  Every part is anchored to the word he says ("investor presentation", "skip"), never to a guessed time.
- **Pops in on the exact word:** 0.14 s in (opacity, blur 8 to 0, scale 94% to 100%, rises 12 px), 0.14 s
  out, measured on his card entrances (4 frames). Parts inside a card pop the same way, smaller. One overlay
  at a time; the next one replaces it.
- **Above his head, never on his face:** placed from his face in every piece it spans (`face.py`): at the top
  of the overlay band, 15% down, never higher (the top 15% is the app's). On a close-up with no headroom it
  covers his hair, shrinking to fit (down to 72%) so it never reaches his brows. The render log says which
  overlays cover hair.
- Never invent a claim: overlay text is what he says, or a plain label of it.
- **Real images, his call 10-20:** a wall of text cards reads as filler, especially in the first 10 s. Claude asks
  him for images where a real picture beats a card (a news headline, the chart he talks about, the thing he
  names): what each one shows, a Google search to find it, and the word it lands on. He saves them to
  `Downloads\<name> images\`; they go into `reels\<name>\images\` and in as `image` overlays (rounded
  corners, soft shadow, the same pop, above his head, shrinking down to 45% to stay off his brows). Wide
  pictures work best; a tall one sits on his head like a hat. Never show what the CTA withholds.

## Picture
- **Punch-in on every jump cut:** the framing alternates 100% / 115% (108% on a close-up) at each cut, and at
  a sentence start inside any piece longer than 4 s, so the rhythm is a change every 2 to 4 s like his.
  Anchored on his chin, so the captions under it stay clear. Hard cuts: no light leak, no transition.
- The light grade from v2 (saturation +7%, contrast +4%, a touch warmer).

## Zones (`reel.py preview NAME --zones` draws the map)
- Red zones, nothing of ours goes there: the top 15% ("Following | For You"), the bottom 20% (@handle,
  caption, sound) and the right-hand column from 50% to 80% (like, comment, save, share).
- Overlay band 15% to 28%; captions between 55% and 77.5%, inside 720 px.

## Sound
- Voice two-pass loudnorm to -14 LUFS, limiter -2.5 dB (as v2).
- A pop on every overlay (-14 dB) and a softer one on each part that pops in later (-19 dB), cycling the three
  pops and pitches.
- **Vine boom on the punchline:** one per reel, on the word Claude picks (`"boom": "skip"` in `story.json`).
  Made in code (`story.ensure_boom`), peak -9 dBFS.
- **Music ON for every story reel (his call 10-20):** his inspo's bed, 25% under the hook, then 10% for the
  rest. The track is the first audio file in `reel-editor\music\` (his pick, kept out of git); it's looped,
  loudnorm'd to -14 LUFS, eased from 25% to 10% over 0.6 s after the first sentence, faded out over the last
  0.8 s. Measured on a test tone: exactly 8.0 dB down after the hook. One reel can use another track
  (`"music": "<file>"` in `story.json`) or none (`"music": false`). No track in the folder means no music,
  and the render log says so.
- No whooshes on jump cuts.

## What the story look changes from v2 (his ask, 10-20)
Captions plain white and still instead of bold blur-in with rotating colours; one green accent instead of
seven; app UI overlays (code-drawn) where v2 had none; punch-ins on cuts where v2 had a slow 6% drift and
"never a punch-in"; hard cuts instead of the light-leak glow; a music bed under every reel (v2: no music,
ever). No B-roll, no cover, no caption pack: unchanged.

# The v2 look (LOCKED 2026-10-18)

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
- **No music, ever** (in v2; the story look has a music bed since 10-20).
- Whooshes only where the shot type changes (face / card / split screen), peaking at -10 dBFS on the cut
  frame. The 3 Mixkit whooshes cycle with the pitch varied, so no two in a row sound the same.
- A pop on each motion text clip and on his on-screen text, peaking at -12 dBFS.
- **+20% accents:** for every five planned sounds, about one more: a soft impact (-12 dBFS) on a stakes or
  doubt line and a light ding (-15 dBFS) on a payoff line, alternating, placed in the longest stretches with
  no other sound and at least 2.5 s from any. Made in code (`render.ensure_sfx`), so nothing to download.
- Voice: two-pass loudnorm to -14 LUFS, limiter at -2.5 dB (recording 55: -14.1 LUFS, -2.3 dB peak).

## His own text
- On-screen text is optional. He types it; it shows for 1 to 4 s in an Instagram-text look (Figtree Bold,
  white, soft shadow, optional colour emoji), fades 0.09 s in and 0.07 s out, hidden during motion text.
- **No cover (thumbnail) and no caption pack, for any reel** (his call 10-18).

## Never (all tried and rejected)
- B-roll cutaways (stock or Flow-made; tried again 10-17, dropped for good 10-18).
- A persistent "POV" title. Code-drawn icons or pop-in visuals. Hard punch-in zooms.
- Money "orbit", "rain" or "golden" variations.
- Slam, typewriter, bubble, pulse or glitch text animations.
- Big uppercase captions with a yellow highlight; key words only ever in one colour.
- The "spotlight" pill and "keynote" card looks (10-17 tests).
- Music (in v2).

## Every delivery is checked
- The final has the same frame count as his source, and loudness is about -14 LUFS with peaks near -2 dB.
- Claude looks at frames inside every motion text clip and visual, checks each Flow clip's spelling, and
  checks that a visual's cut lands where the source's does (Flow has drifted one by 0.68 s before).
- Clips are matched by what is on screen, never by file name.
- Sound is checked by measurement (Claude can't hear audio).

## The previous look (locked 10-17 to 10-18)
Figtree ExtraBold 82.8 px white captions with a fade-and-rise, no colour, no transitions, whooshes and pops
only. Still in `talk_reel.py` for reference.
