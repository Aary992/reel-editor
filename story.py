"""The story look (NEW 10-20): his inspo's storytelling-reel edit, rebuilt from two of that creator's videos.
render.py calls it when the reel's look is "story". The rules, in that creator's own words:

  1. Captions: 2-3 words, white, no box, no animation.
  2. Keep everything out of the TikTok button zones.
  3. Real app UI above my head, never on my face.
  4. Every graphic pops in on the exact word.
  5. Voice 200%, music 25% then 10%, vine boom on the punchline.
  Plus: perfect the dead space (storycut.py), and a punch-in on every jump cut.

Measured on his videos: captions Arial-Bold-like at 63 px (1080 wide), centred, at chin height (55% on his
framing); the one headline number and the CTA in green #09F31C at 1.25x. Zones: top 15% and bottom 20% are
the app's, the right edge from 50% to 80% holds like/comment/save/share, so captions stay inside 720 px.
Overlays sit in the band above his head (his "overlay section", from 15% down, never higher); on a close-up
with no headroom they may cover his hair but never his face. Punch-ins alternate 100% / 115% (108% on a close-up) at every
jump cut, anchored on his chin so the captions never land on his mouth.

Music is ON for every story reel (his call 10-20): the track in the reel-editor "music" folder (the first by name),
25% under the hook, then 10%. No track there yet means no music, and the render says so.

Per-reel choices live in reels/<name>/story.json (all optional):
  {"green": ["10 minutes", "Comment Claude"], "boom": "skip", "music": "C:\\\\path\\\\other track.mp3"}
  "music": false leaves this one reel without music.
"""
import json, math
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import face as facemod
import overlays as O

W, H = 1080, 1920
ARIAL_BOLD = "C:/Windows/Fonts/arialbd.ttf"
CAP_PX, GREEN_SCALE = 63, 1.25
WHITE, GREEN = (255, 255, 255), (9, 243, 28)
CAP_MAXW = 720                    # the right-hand buttons start 180 px in from the edge between 50% and 80%
CAP_SHADOW = (135, 4, 2)          # alpha, blur, px down: a soft dark edge, no outline, no box
CAP_Y_MIN, CAP_Y_MAX = 0.55, 0.775
TOP_SAFE = OVERLAY_TOP = 0.15     # the top 15% is the app's (his zone map); nothing of ours above it
PUNCH_WIDE, PUNCH_CLOSE = 1.15, 1.08
CLOSE_UP_W = 0.65                 # a face wider than this fraction of the frame is a close-up
BEAT_MAX, BEAT_MIN = 4.0, 2.0     # a punch change at a sentence start when a piece runs longer than BEAT_MAX
CENSOR = {"fuck": "f*ck", "fucking": "f*cking", "fucked": "f*cked", "shit": "sh*t", "bitch": "b*tch"}
MUSIC_DIR = Path(__file__).resolve().parent / "music"     # his track(s); kept out of git like the SFX
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}

# the app's own buttons and labels (TikTok and Instagram Reels); nothing of ours goes in these
ZONES = [("top", (0, 0, W, int(0.15 * H)), "Following | For You"),
         ("bottom", (0, int(0.80 * H), W, H), "@handle · caption · sound"),
         ("right", (int(W - 180), int(0.50 * H), W, int(0.80 * H)), "like comment save share")]


# ---------------------------------------------------------------- planning

def load_json(path, default):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def pieces_of(reel, video, dur, fps, ff, scene):
    """[(t0, t1, take, face)] for the video: from the cut (exact jump cuts and faces) when the reel was made by
    `reel.py cut`, otherwise from the shot cuts with faces measured here (cached in faces.json)."""
    cut = load_json(reel / "cut.json", None)
    if cut and Path(video).resolve() == (reel / "cut.mp4").resolve():
        return [(s["t0"], s["t1"], s["take"], s.get("face")) for s in cut["segments"]]
    edges = [0.0] + [c for c in scene if 0.3 < c < dur - 0.3] + [dur]
    spans = list(zip(edges, edges[1:]))
    cache = load_json(reel / "faces.json", {})
    key = f"{len(spans)}:{dur:.2f}"
    if cache.get("key") != key:
        cache = {"key": key, "faces": facemod.measure(ff, video, spans, fps)}
        (reel / "faces.json").write_text(json.dumps(cache, indent=1), encoding="utf-8")
    return [(a, b, f"shot{i}", f) for i, ((a, b), f) in enumerate(zip(spans, cache["faces"]))]


def beats(pieces, words):
    """Where the framing changes: every jump cut, plus sentence starts inside long pieces (his inspo's cut
    rhythm is a change every 2-4 s). Returns [(t0, t1, piece index)]."""
    out = []
    for k, (a, b, _, _) in enumerate(pieces):
        marks = [a]
        if b - a > BEAT_MAX:
            starts = [w2["s"] - 0.03 for w1, w2 in zip(words, words[1:])
                      if a + BEAT_MIN <= w2["s"] <= b - 1.5 and w1["t"][-1:] in ".,!?"]
            for s in starts:
                if s - marks[-1] >= BEAT_MIN:
                    marks.append(s)
        marks.append(b)
        out += [(x, y, k) for x, y in zip(marks, marks[1:])]
    return out


def zoomed(f, z, anchor_y):
    """A face's lines after a zoom of z anchored at anchor_y."""
    if not f:
        return None
    g = dict(f)
    for k in ("hair", "top", "eyes", "chin", "cy"):
        g[k] = anchor_y + (f[k] - anchor_y) * z
    g["w"] = f["w"] * z
    return g


def plan(reel, words, dur, fps, ff, scene, video, log=print, music=""):
    opts = load_json(reel / "story.json", {})
    pcs = pieces_of(reel, video, dur, fps, ff, scene)
    bts = beats(pcs, words)
    # punch-ins: alternate 1.00 / P, anchored on his chin (captions sit just below it)
    punch = []
    for i, (a, b, k) in enumerate(bts):
        f = pcs[k][3]
        p = PUNCH_CLOSE if (f and f["w"] > CLOSE_UP_W) else PUNCH_WIDE
        z = 1.0 if i % 2 == 0 else p
        ax = f["cx"] if f else 0.5
        ay = min(f["chin"], 0.8) if f else 0.62
        punch.append({"t0": a, "t1": b, "z": z, "ax": ax, "ay": ay, "face": zoomed(f, z, ay), "take": pcs[k][2]})
    # captions: one height per take, just under his chin, inside the safe band
    cap_y = {}
    for take in dict.fromkeys(p["take"] for p in punch):
        chins = [p["face"]["chin"] for p in punch if p["take"] == take and p["face"]]
        cap_y[take] = min(CAP_Y_MAX, max(CAP_Y_MIN, (float(np.median(chins)) + 0.02) if chins else CAP_Y_MIN))
    log("  story: captions at " + ", ".join(f"{t[-6:]} {y:.3f}" for t, y in cap_y.items()))
    # overlays
    ovs = O.resolve(load_json(reel / "overlays.json", []), words, dur, base=reel)
    places = {}
    for ov in ovs:
        places[ov["id"]] = place(ov, punch, log)
    # green captions: the headline number and the CTA (or his own picks)
    green = [g.lower() for g in opts.get("green", [])]
    boom = None
    if opts.get("boom"):
        boom = O.find(words, opts["boom"], 0.0)
        log(f"  story: vine boom on \"{opts['boom']}\" at {boom:.2f}s")
    pops = sorted(pt for ov in ovs for pt in O.pop_times(ov))
    music = music or pick_music(opts.get("music"), log)     # a track given to render.py wins
    return {"punch": punch, "cap_y": cap_y, "overlays": ovs, "places": places, "green": green,
            "boom": boom, "pops": pops, "music": music}


def pick_music(choice, log):
    """This reel's music bed: its own track from story.json, none if it says false, else his default track."""
    if choice is False:
        log("  story: no music for this reel (story.json)")
        return None
    if choice:
        if not Path(choice).exists():
            raise SystemExit(f"story.json music track not found: {choice}")
        return str(choice)
    tracks = sorted(p for p in MUSIC_DIR.glob("*") if p.suffix.lower() in AUDIO_EXT) if MUSIC_DIR.exists() else []
    if not tracks:
        log(f"  story: NO MUSIC: no track in {MUSIC_DIR} yet")
        return None
    return str(tracks[0])


def place(ov, punch, log):
    """Where an overlay goes: at the top of the overlay band (15% down, never into the app's top zone), above his
    head on every beat it spans. On a close-up without that room it covers his hair and, if it would reach his
    brows, shrinks (a card to 72%, a picture to 45%): never his brows, eyes or anything lower."""
    span = [p for p in punch if p["t0"] < ov["end"] and p["t1"] > ov["at"] and p["face"]]
    fw, fh = O.full_size(ov)
    hair = min((p["face"]["hair"] for p in span), default=0.30) - 0.012
    brows = min((p["face"]["top"] + 0.10 * (p["face"]["chin"] - p["face"]["top"]) for p in span), default=0.4) - 0.008
    scale = 1.0
    if OVERLAY_TOP * H + fh <= hair * H:
        y = OVERLAY_TOP * H
    else:
        y = max(TOP_SAFE * H, hair * H - fh)
        if y + fh > brows * H:
            scale = max(0.45 if ov["type"] == "image" else 0.72, min(1.0, (brows * H - TOP_SAFE * H) / fh))
            y = TOP_SAFE * H
    wide = ov["type"] in ("chat", "comments", "progress", "image")
    x = (W - fw * scale) / 2 if wide else 40
    note = ""
    if y + fh * scale > hair * H + 2:
        note = " (over his hair: no headroom in this shot)"
    if y + fh * scale > brows * H + 2:
        note = " (TOUCHES HIS FACE: shorten it or move it)"
    log(f"  overlay {ov['id']}: {ov['type']:8} {ov['at']:6.2f}-{ov['end']:6.2f}s  y {y / H:.3f}  "
        f"scale {scale:.2f}{note}")
    return {"x": x, "y": y, "w": W - 80 if not wide else fw * scale, "scale": scale}


# ---------------------------------------------------------------- per frame

def punch_frame(img, t, sp):
    p = next((p for p in sp["punch"] if p["t0"] <= t < p["t1"]), None)
    if not p or p["z"] <= 1.0005:
        return img
    z = p["z"]
    bw, bh = W / z, H / z
    x0 = min(max(0.0, p["ax"] * W - p["ax"] * bw), W - bw)
    y0 = min(max(0.0, p["ay"] * H - p["ay"] * bh), H - bh)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + bw, y0 + bh))


def caption_text(ch):
    out = []
    for w in ch:
        s = w["t"].rstrip(".,;:!?")
        low = s.lower()
        out.append(CENSOR.get(low, s) if low in CENSOR else s)
    return " ".join(out)


@lru_cache(maxsize=512)
def caption_tile(text, green):
    size = CAP_PX * (GREEN_SCALE if green else 1.0)
    f = ImageFont.truetype(ARIAL_BOLD, int(round(size)))
    width = f.getlength(text)
    if width > CAP_MAXW:
        f = ImageFont.truetype(ARIAL_BOLD, int(size * CAP_MAXW / width))
        width = f.getlength(text)
    asc, desc = f.getmetrics()
    pad = 20
    tile = Image.new("RGBA", (int(width) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    sa, sb, dy = CAP_SHADOW
    sh = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((pad, pad + dy), text, font=f, fill=(0, 0, 0, sa))
    sh = sh.filter(ImageFilter.GaussianBlur(sb))
    ImageDraw.Draw(sh).text((pad, pad), text, font=f, fill=(GREEN if green else WHITE) + (255,))
    # visual centre of the letters (x-height band), so captions of any height sit on the same line
    _, top, _, bottom = f.getbbox("x")
    return sh, pad + (top + bottom) / 2


def is_green(ch, sp, first_sentence_end):
    text = caption_text(ch).lower()
    if sp["green"]:
        return any(g in text or text in g for g in sp["green"])
    first = ch[0]["s"] < first_sentence_end and any(c.isdigit() for c in text)
    return first or text.startswith("comment")


def draw_captions(img, t, wins, sp, hidden, words):
    if any(a <= t < b for a, b in hidden):
        return img
    win = next((w for w in wins if w[0] <= t < w[1]), None)
    if not win:
        return img
    ch = win[2]
    if "first_end" not in sp:
        sp["first_end"] = next((w["e"] for w in words if w["t"][-1:] in ".!?"), 1e9)
    tile, mid = caption_tile(caption_text(ch), is_green(ch, sp, sp["first_end"]))
    p = next((p for p in sp["punch"] if p["t0"] <= t < p["t1"]), None)
    y = sp["cap_y"].get(p["take"], CAP_Y_MIN) if p else CAP_Y_MIN
    x0 = int(round(W / 2 - tile.width / 2))
    y0 = int(round(y * H - mid))
    out = img.convert("RGBA")
    out.alpha_composite(tile, (x0, y0))
    return out.convert("RGB")


def draw_overlays(img, t, sp):
    for ov in sp["overlays"]:
        if ov["at"] <= t < ov["end"]:
            img = O.draw(img, t, ov, sp["places"][ov["id"]])
    return img


def draw_zones(img):
    """The safe-zone map from his inspo (for checking a layout): red app zones, the overlay band, captions."""
    out = img.convert("RGBA")
    lay = Image.new("RGBA", out.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = ImageFont.truetype(ARIAL_BOLD, 30)
    for _, box, label in ZONES:
        d.rectangle(box, fill=(255, 40, 40, 70), outline=(255, 60, 60, 230), width=4)
        d.text((box[0] + 16, box[1] + 12), "RED ZONE · AVOID", font=f, fill=(255, 255, 255, 255))
        d.text((box[0] + 16, box[1] + 50), label, font=ImageFont.truetype(ARIAL_BOLD, 24), fill=(255, 255, 255, 230))
    d.rectangle((40, int(OVERLAY_TOP * H), W - 40, int(0.284 * H)), outline=(60, 160, 255, 255), width=4)
    d.text((56, int(0.284 * H) - 40), "OVERLAY SECTION", font=ImageFont.truetype(ARIAL_BOLD, 24), fill=(60, 160, 255, 255))
    d.rectangle(((W - CAP_MAXW) // 2, int(CAP_Y_MIN * H) - 45, (W + CAP_MAXW) // 2, int(CAP_Y_MAX * H) + 45),
                outline=(40, 210, 90, 255), width=4)
    d.text(((W - CAP_MAXW) // 2 + 12, int(CAP_Y_MIN * H) - 85), "AUTOCAPTIONS", font=ImageFont.truetype(ARIAL_BOLD, 24),
           fill=(40, 210, 90, 255))
    out.alpha_composite(lay)
    return out.convert("RGB")


# ---------------------------------------------------------------- sound

def ensure_boom(sfx_dir):
    """A vine-boom style hit, made in code: a fast-falling 808 thump, driven into soft clipping, short tail."""
    import render
    path = sfx_dir / "lab_boom.wav"
    if not path.exists():
        sr = 48000
        t = np.arange(int(1.4 * sr)) / sr
        f = 46 + (190 - 46) * np.exp(-t / 0.035)
        ph = 2 * np.pi * np.cumsum(f) / sr
        body = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)) * np.exp(-t / 0.42)
        body *= 1 - np.exp(-t / 0.002)
        rng = np.random.default_rng(11)
        click = np.convolve(rng.normal(0, 1, len(t)), np.ones(12) / 12, "same") * np.exp(-t / 0.012) * 0.8
        x = np.tanh(2.6 * (body + click))
        # a little room: a few quiet, low-passed echoes
        tail = np.zeros_like(x)
        for d_ms, g in ((37, 0.22), (71, 0.15), (113, 0.1), (167, 0.06)):
            n = int(sr * d_ms / 1000)
            tail[n:] += x[:-n] * g
        render.write_wav(path, x + np.convolve(tail, np.ones(40) / 40, "same"))
    return path


def music_filter(idx, first_end, dur):
    """His inspo's mix: music at 25% under the hook, easing to 10% for the rest (voice stays on top), out at the end."""
    a, b = first_end, first_end + 0.6
    return (f"[{idx}:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo,"
            f"loudnorm=I=-14:TP=-2:LRA=11,aresample=48000,atrim=duration={dur:.3f},"
            f"volume='if(lt(t,{a:.3f}),0.25,if(lt(t,{b:.3f}),0.25-0.15*(t-{a:.3f})/0.6,0.10))':eval=frame,"
            f"afade=t=out:st={max(0, dur - 0.8):.3f}:d=0.8[music]")
