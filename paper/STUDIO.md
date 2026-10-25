# The studio look (LOCKED 2026-10-25)

From two Reels by a Hindi creator he sent 10-25 (`Downloads\Video-27200.mp4` "AI resume", `Video-3661.mp4`
"Creator AI") and asked to mimic. First reel: "story demo" (how I analyze any stock with Claude, 46 s),
`Downloads\story demo studio.mp4`, its beats kept in `examples\studio story demo.tsx`. His verdict: "great i
like this style lock this style in", with two notes, both built in: make the talking parts brighter (the
first cut graded them dark and moody like the reference), and add subtle face zooms while he talks. Built in
Remotion inside the paper project with its own entry point (`src\studio\`), so the paper look is untouched.

```
py -3.14 paper\studio.py prep "<name>" ["<edited video>"]
py -3.14 paper\studio.py still "<name>" 60 240 ...
py -3.14 paper\studio.py render "<name>"
```
Per reel, Claude rewrites `src\studio\beats.tsx` (first line `THIS REEL: "<name>"`). The kit is `kit.tsx`, the
generic engine `Studio.tsx`.

## What his reels do (measured frame by frame)

- **Structure:** face for the hook (2 to 3.5 s), the opinions and the CTA; everything that explains runs as
  full-screen graphics with his voice over them, 60 to 70% of the reel. Reel A: face 0-3.4, graphics 3.4-10.5,
  face 10.5-17.8, one 37 s graphics run, face CTA from 54.7.
- **Cuts:** face to graphics and back are hard cuts. Inside a graphics run there are no hard cuts: the camera
  moves between objects, and a new object comes out of a zoom-blur.
- **Backdrop:** a lit light-grey plane (#E8E5E9 in the middle) with faint ruled lines every 84 px (on 1920),
  under a heavy vignette: brightness 231 in the middle, 143 at the side edges, 137 near the top, 78 then 47 at
  the bottom. The lines move with the camera. Soft focus toward the edges.
- **Camera:** a 3D camera over the plane: slow pushes and tilts, whip pans with motion blur, dives into an
  object. Objects are tilted planes (pinned notes, documents, app screens).
- **Objects:** pinned notes on a board as the hub ("There is a four-step fix for this", camera visits a note per
  step and comes back); Claude's app (serif greeting with the orange mark, prompt box, answer in serif with
  peach highlights sweeping across phrases); documents panned across; a numbered list on a big thin arc,
  labels wiping in; one line of kinetic text the camera pans along, the key word in a black box; 3D pills
  on a dotted path; tables.
- **Captions (face only):** white, medium weight (DM Sans 500 here), about 78 px on 1080, tight tracking, no
  outline, soft shadow; two balanced lines on his chest just under the chin; the whole caption is laid out
  first and each word appears in place as he says it (from above-right, smaller and blurred, settling in 4
  frames). No captions over graphics: the graphics carry the words.
- **CTA:** caption "comment" over a white pill with the word in bold black and a black round arrow button.
- **Sound:** their reels have a bed (the floor never drops below about -31 dB); his rule stands: no music.
  Soft pops on objects, whooshes into graphics and on zoom-blurs, a click on send, a boom on the punchline.

## His footage vs theirs

Their face shots are medium shots in a dark room; his takes are tight close-ups on a grey wall.
- **Bright, not moody (his note 10-25):** brightness +8%, contrast +4%, saturation -7%, a touch warm, and only
  a light vignette (the first cut's dark grade averaged 68 brightness on his face shots, this one 98).
- **Subtle zooms while he talks (his note 10-25):** each phrase (a sentence, or up to a comma, a pause or about
  2.6 s) glides between 100% and 106%, in then out, smootherstep, centred on his face. Captions don't move.
- A take framed too low is lifted up to 13% (the gap filled with a feathered, blurred mirror of the take), and
  the wide CTA take gets its captions above his head instead.
