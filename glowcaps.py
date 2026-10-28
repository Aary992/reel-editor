"""Glow captions (NEW 10-29): an optional caption style for any story or v2 reel, `--captions glow` on
reel.py preview / render. Never the default; his call 10-29: "one of the subtitle styles we offer, but it
shouldn't be the only one". Built with him from a creator reel (Video-6133), trial by trial:

  - SF Pro Display Bold (the iPhone font), white caps, 50 px on a 1080-wide frame, nothing else: no second
    font, no colour, no box. A soft dark shadow only so it reads on a light wall.
  - One line at a time, fixed in the middle of the frame (50% down), centred.
  - Words fade in one at a time on the exact spoken word, soft focus (a 3 px blur clearing over 0.35 s) with
    a faint white glow that swells and settles. "Too dramatic, looks like a typewriter" killed the pop-in.
  - The line is laid out once: every word has its own fixed spot from the start and nothing slides as words
    join ("if the text is aligned it should stay in that position").
  - The next line takes over the moment its first word is said: no blank gap, no lingering line.

Lines are short phrases (2 to 5 words), broken at punctuation, pauses and width, with no one-word orphans.
"""
import os
import re
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
Y = 0.50                 # the caps' visual middle
SIZE = 50
TRACK = -0.01            # tracking, as a fraction of the size
MAX_W = 720              # inside the right-hand app buttons (they start 180 px in between 50% and 80% down)
MAX_WORDS, PAUSE = 5, 0.30
IN_SECS = 0.35           # each word's soft-focus fade
BLUR0 = 3.0              # its starting blur (px)
GLOW_PEAK, GLOW_REST, GLOW_SETTLE = 0.45, 0.15, 0.5
LINGER = 0.6             # after a line's last word, when nothing follows for a while
CENSOR = {"fuck": "F*CK", "fucking": "F*CKING", "fucked": "F*CKED", "shit": "SH*T", "bitch": "B*TCH"}


def _font_path():
    """SF Pro is Apple's: it is installed on his machines, never committed to this repo."""
    dirs = [Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts", Path("C:/Windows/Fonts"),
            Path(__file__).parent / "fonts"]
    for d in dirs:
        for name in ("SFPRODISPLAYBOLD.OTF", "SF-Pro-Display-Bold.otf"):
            if (d / name).exists():
                return str(d / name)
    raise SystemExit("glow captions need SF Pro Display Bold installed (SF-Pro-Display-Bold.otf)")


@lru_cache(maxsize=1)
def _font():
    return ImageFont.truetype(_font_path(), SIZE)


def _text(w):
    s = re.sub(r"[^\w'*%$₹.]", "", w["t"].strip()).rstrip(".")
    return CENSOR.get(s.lower(), s.upper())


def _width(text):
    f = _font()
    return sum(f.getlength(c) for c in text) + SIZE * TRACK * (len(text) - 1)


def lines_of(words):
    """[[word, ...], ...]: phrases of 2-5 words, broken at punctuation, pauses and MAX_W."""
    space = _font().getlength(" ")
    items = [dict(w, text=_text(w)) for w in words if _text(w)]
    lines, cur = [], []
    for i, w in enumerate(items):
        if cur:
            width = sum(_width(x["text"]) for x in cur) + space * len(cur) + _width(w["text"])
            if len(cur) >= MAX_WORDS or width > MAX_W or w["s"] - cur[-1]["e"] > PAUSE:
                lines.append(cur)
                cur = []
        cur.append(w)
        if re.search(r"[.,!?;:]$", w["t"].strip()):
            lines.append(cur)
            cur = []
    if cur:
        lines.append(cur)
    # no one-word orphans: fold into a neighbour when it fits, else balance a split with the neighbour
    def fits(ws):
        return len(ws) <= MAX_WORDS and sum(_width(x["text"]) for x in ws) + space * (len(ws) - 1) <= MAX_W
    out = []
    for ln in lines:
        if out and (len(ln) == 1 or len(out[-1]) == 1) and fits(out[-1] + ln):
            out[-1] = out[-1] + ln
        else:
            out.append(ln)
    return out


@lru_cache(maxsize=1024)
def _word_layers(text):
    """The word, its shadow and its glow as same-size layers, plus the pad around them."""
    f = _font()
    pad = 50
    asc, desc = f.getmetrics()
    size = (int(_width(text)) + 2 * pad, asc + desc + 2 * pad)
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for c in text:
        d.text((x, pad + asc), c, font=f, fill=(255, 255, 255, 255), anchor="ls")
        x += f.getlength(c) + SIZE * TRACK
    alpha = im.getchannel("A")
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow.putalpha(alpha.point(lambda a: int(a * 0.45)).filter(ImageFilter.GaussianBlur(9)))
    shadow = shadow.transform(size, Image.AFFINE, (1, 0, 0, 0, 1, -3))
    glow = Image.new("RGBA", size, (255, 255, 255, 0))
    glow.putalpha(alpha.filter(ImageFilter.GaussianBlur(16)))
    return im, shadow, glow, pad


def _fade(im, k):
    if k >= 0.999:
        return im
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lambda v: int(v * max(0.0, k))))
    return out


def _entrance(age):
    """Seconds since the word was said -> (opacity, glow, blur)."""
    p = min(1.0, max(0.0, age / IN_SECS))
    op = p * p * (3 - 2 * p)
    rise = IN_SECS * 0.6
    if age < rise:
        g = GLOW_PEAK * age / rise
    else:
        g = GLOW_REST + (GLOW_PEAK - GLOW_REST) * max(0.0, 1 - (age - rise) / GLOW_SETTLE)
    return op, g, BLUR0 * (1 - p)


def plan(words, dur):
    """Per line: its words with their fixed x, and the window it is on screen."""
    space = _font().getlength(" ")
    lines = lines_of(words)
    out = []
    for i, ln in enumerate(lines):
        xs, x = [], 0.0
        for w in ln:
            xs.append(x)
            x += _width(w["text"]) + space
        left = (W - (x - space)) / 2
        start = ln[0]["s"]
        nxt = lines[i + 1][0]["s"] if i + 1 < len(lines) else dur + 1
        end = nxt if nxt - ln[-1]["e"] < 1.2 else ln[-1]["e"] + LINGER
        out.append({"start": start, "end": end, "words": [(w["text"], w["s"], left + dx) for w, dx in zip(ln, xs)]})
    return out


def draw(img, t, lines, hidden=()):
    if any(a <= t < b for a, b in hidden):
        return img
    line = next((ln for ln in lines if ln["start"] <= t + 0.01 < ln["end"]), None)
    if not line:
        return img
    f = _font()
    asc = f.getmetrics()[0]
    top, bottom = f.getbbox("H", anchor="ls")[1::2]
    base = Y * H - (top + bottom) / 2
    out = img.convert("RGBA")
    for text, s, x in line["words"]:
        if s > t + 0.01:
            continue
        im, shadow, glow, pad = _word_layers(text)
        op, g, blur = _entrance(t - s)
        px, py = int(round(x - pad)), int(round(base - asc - pad))
        out.alpha_composite(_fade(shadow, op), (px, py))
        out.alpha_composite(_fade(glow, g * op), (px, py))
        word = im.filter(ImageFilter.GaussianBlur(blur)) if blur > 0.3 else im
        out.alpha_composite(_fade(word, op), (px, py))
    return out.convert("RGB")
