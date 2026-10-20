"""Real-app-UI overlays for the story look. His inspo's rules (10-20): "Real app UI above my head, never on my
face" and "Every graphic pops in on the exact word". Claude writes reels/<name>/overlays.json after reading
the transcript (`reel.py overlays NAME --suggest` starts a draft); render.py draws them over the footage.

Every overlay is a list item with a "type" and an "at" anchor; most have inner anchors for the parts that
appear later (a message, a step, a pill). An anchor is seconds (12.4), a word or phrase as he says it
("investor presentation"), optionally "#2" for its second time from there on. "end" can also be "+2.5"
(seconds after "at"); left out, an overlay stays until the next one pops in (at most 5 s after its last part).

  chat      Claude-style chat card: {"title", "subtitle", "badge", "messages": [{"from": "you"|"claude",
            "text", "at", "file": {"name", "meta", "kind"}, "charts": ["1D", "1W"], "check": true}],
            "reply": true, "typing": "text typed into the reply bar", "typing_at"}
  file      a file chip: {"name", "meta", "kind": "PDF"|"XLS"|"CSV"|"ZIP"|"PNG", "check_at"}
  steps     step tracker pills: {"steps": [{"text", "at"} | {"text", "done": true}, ...]}; each lights up on
            its word ("done" = already ticked when the tracker pops in again later)
  score     a number that counts up with a bar: {"label", "value", "max", "suffix", "note", "count_at"}
  pills     coloured word pills, one per word: {"items": [{"text", "color": "yellow|blue|red|green|purple", "at"}]}
  comments  dark comments sheet: {"handle", "word", "post_at", "reply", "reply_at", "app": "Instagram"}
  toast     a small reply pill: {"text", "sign", "icon": "claude"|"bookmark"}
  progress  a working card: {"title", "file", "states": [{"text", "pct", "at"}], "done_at"}
  list      plain lines of text, no card: {"lines": ["0:18 Step one", ...]}
  image     a real picture he sends (a headline, a chart): {"src": "images/1.png" (from the reel folder),
            "max_h": 560}; fitted inside 1000 x max_h, rounded corners, shrinks further than a card to stay
            off his brows

Each pop: 0.14 s in (opacity, blur 8 -> 0, scale 94% -> 100%, rises 12 px), 0.14 s out, measured frame by
frame on his inspo. Inner parts pop the same way, smaller. Everything is drawn at 2x and scaled down.
"""
import math, re
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
SS = 2                      # supersampling
SEG = "C:/Windows/Fonts/SegUIVar.ttf"
POP_IN, POP_OUT = 0.14, 0.14
PART_IN = 0.16
BANNER_UP = 30              # the notification's top sits this far above the comments sheet, covering its title
CARD_W = 1000               # 40 px either side on a 1080 frame, like his overlay section
IMG_MAX_H = 560             # an image's tallest before placing; place() shrinks it off his brows
TINT = (20, 24, 44)         # the frosted card's dark blue-grey
CLAUDE_ORANGE = (217, 119, 87)
CREAM = (245, 236, 226)
GREEN, BLUE, RED, YELLOW, PURPLE = (48, 209, 88), (10, 132, 255), (255, 69, 58), (255, 214, 10), (191, 90, 242)
PILL_COLORS = {"yellow": (YELLOW, (28, 28, 30)), "blue": (BLUE, (255, 255, 255)), "red": (RED, (255, 255, 255)),
               "green": (GREEN, (255, 255, 255)), "purple": (PURPLE, (255, 255, 255))}
NUMS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
        "eight": "8", "nine": "9", "ten": "10"}


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(u):
    u = clamp(u)
    return 1 - (1 - u) ** 3


def ease_back(u, s=1.4):
    u = clamp(u) - 1
    return 1 + (s + 1) * u ** 3 + s * u ** 2


@lru_cache(maxsize=128)
def F(weight, size):
    f = ImageFont.truetype(SEG, int(round(size * SS)))
    f.set_variation_by_name(weight)
    return f


# ---------------------------------------------------------------- anchors

def norm(w):
    w = w.lower().replace("’", "'")
    w = re.sub(r"[^\w']", "", w).strip("'")
    return NUMS.get(w, w)


def find(words, spec, after, edge="s"):
    """Seconds for an anchor: a number, or a word/phrase (optionally "#k") from `after` on."""
    if isinstance(spec, (int, float)):
        return float(spec)
    m = re.fullmatch(r"(.+?)\s*#(\d+)", spec.strip())
    phrase, nth = (m.group(1), int(m.group(2))) if m else (spec, 1)
    toks = [norm(t) for t in phrase.split()]
    toks = [t for t in toks if t]
    ns = [norm(w["t"]) for w in words]
    hits = 0
    for i in range(len(ns) - len(toks) + 1):
        if words[i]["s"] < after - 0.01:
            continue
        if ns[i:i + len(toks)] == toks:
            hits += 1
            if hits == nth:
                return words[i]["s"] if edge == "s" else words[i + len(toks) - 1]["e"]
    raise ValueError(f"anchor {spec!r} not found after {after:.2f}s")


INNER = {"chat": ("messages",), "steps": ("steps",), "pills": ("items",), "progress": ("states",)}


def resolve(items, words, dur, base=None):
    """overlays.json items -> the same items with every anchor in seconds ("at", "end", inner "at"s), and an
    image's "src" made absolute from `base` (the reel folder)."""
    out, after = [], 0.0
    for k, ov in enumerate(items):
        ov = {**ov, "id": k}
        if ov["type"] == "image":
            src = Path(ov.get("src", ""))
            if base is not None and not src.is_absolute():
                src = Path(base) / src
            if not src.is_file():
                raise ValueError(f"overlay {k} (image): {src} not found")
            ov["src"] = str(src)
        ov["at"] = find(words, ov["at"], after)
        after = ov["at"]
        last = ov["at"]
        for key in INNER.get(ov["type"], ()):
            parts = []
            for p in ov.get(key, []):
                p = dict(p)
                if p.get("done"):                     # a step already done when this tracker pops in
                    p["at"] = ov["at"] - 10.0
                    parts.append(p)
                    continue
                p["at"] = find(words, p["at"], ov["at"]) if "at" in p else ov["at"]
                last = max(last, p["at"])
                parts.append(p)
            ov[key] = parts
        for key in ("check_at", "post_at", "reply_at", "typing_at", "done_at", "count_at"):
            if key in ov:
                ov[key] = find(words, ov[key], ov["at"])
                last = max(last, ov[key])
        if ov["type"] == "comments":
            ov.setdefault("post_at", ov["at"] + 0.25 + 0.07 * len(ov.get("word", "")) + 0.35)
            last = max(last, ov["post_at"], ov.get("reply_at", 0))
        ov["_last"] = last
        out.append(ov)
    for k, ov in enumerate(out):
        nxt = out[k + 1]["at"] if k + 1 < len(out) else dur
        e = ov.get("end")
        if isinstance(e, str) and e.strip().startswith("+"):
            end = ov["at"] + float(e)
        elif e is not None:
            end = find(words, e, ov["at"], edge="e")
        else:
            end = min(max(ov["at"] + 2.5, ov["_last"] + 1.8), ov["_last"] + 5.0)
        ov["end"] = round(min(end, nxt, dur), 3)
        if ov["end"] - ov["at"] < 0.4:
            raise ValueError(f"overlay {k} ({ov['type']}) is up for only {ov['end'] - ov['at']:.2f}s")
    return out


def pop_times(ov):
    """When this overlay makes a sound: its own pop, plus the parts that pop in later (not the first)."""
    out = [(ov["at"], "pop")]
    for key in INNER.get(ov["type"], ()):
        for p in ov.get(key, []):
            if ov["at"] + 0.25 < p["at"] < ov["end"] - 0.05:
                out.append((p["at"], "part"))
    if ov["type"] == "comments":
        out.append((ov["post_at"], "part"))
        if "reply_at" in ov:
            out.append((ov["reply_at"], "pop"))
    if "check_at" in ov:
        out.append((ov["check_at"], "part"))
    return out


# ---------------------------------------------------------------- drawing helpers (all at SS scale)

def S(v):
    return int(round(v * SS))


def rrect(d, box, r, fill, outline=None, width=1):
    d.rounded_rectangle([S(box[0]), S(box[1]), S(box[2]), S(box[3])], radius=S(r), fill=fill,
                        outline=outline, width=S(width) if outline else 0)


def text(d, xy, s, weight, size, fill, anchor="la"):
    d.text((S(xy[0]), S(xy[1])), s, font=F(weight, size), fill=fill, anchor=anchor)


def tlen(s, weight, size):
    return F(weight, size).getlength(s) / SS


def wrap(s, weight, size, maxw):
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if tlen(trial, weight, size) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def starburst(d, cx, cy, r, color):
    """A hand-drawn style starburst like the Claude mark: 11 tapered rays of slightly different lengths."""
    n = 11
    for i in range(n):
        a = -math.pi / 2 + i * 2 * math.pi / n
        ln = r * (0.92 if i % 3 else 1.0) * (0.86 if i % 2 else 1.0)
        wdt = r * 0.16
        tip = (cx + math.cos(a) * ln, cy + math.sin(a) * ln)
        bx, by = cx + math.cos(a) * r * 0.1, cy + math.sin(a) * r * 0.1
        px, py = -math.sin(a) * wdt / 2, math.cos(a) * wdt / 2
        d.polygon([(S(bx + px), S(by + py)), (S(tip[0] + px * 0.35), S(tip[1] + py * 0.35)),
                   (S(tip[0] - px * 0.35), S(tip[1] - py * 0.35)), (S(bx - px), S(by - py))], fill=color)
    d.ellipse([S(cx - r * 0.2), S(cy - r * 0.2), S(cx + r * 0.2), S(cy + r * 0.2)], fill=color)


def app_icon(d, x, y, s):
    """Claude-style app icon: cream rounded square with the orange starburst."""
    rrect(d, (x, y, x + s, y + s), s * 0.24, CREAM + (255,))
    starburst(d, x + s / 2, y + s / 2, s * 0.36, CLAUDE_ORANGE + (255,))


def check_circle(d, cx, cy, r, color=GREEN, alpha=255):
    d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=color + (alpha,))
    d.line([(S(cx - r * 0.45), S(cy + r * 0.02)), (S(cx - r * 0.1), S(cy + r * 0.38)), (S(cx + r * 0.48), S(cy - r * 0.36))],
           fill=(255, 255, 255, alpha), width=S(max(2.0, r * 0.22)), joint="curve")


def doc_icon(d, x, y, w, h, kind):
    colors = {"PDF": (229, 72, 77), "XLS": (48, 164, 108), "CSV": (48, 164, 108), "ZIP": (142, 142, 147),
              "PNG": (10, 132, 255), "MOV": (175, 82, 222)}
    c = colors.get(kind, (142, 142, 147))
    rrect(d, (x, y, x + w, y + h), 8, (250, 250, 252, 255))
    fold = w * 0.3
    d.polygon([(S(x + w - fold), S(y)), (S(x + w), S(y + fold)), (S(x + w - fold), S(y + fold))], fill=(205, 205, 212, 255))
    rrect(d, (x + 6, y + h * 0.55, x + w - 6, y + h * 0.55 + 22), 5, c + (255,))
    text(d, (x + w / 2, y + h * 0.55 + 11), kind, "Bold Text", 14, (255, 255, 255, 255), anchor="mm")


def mini_chart(d, x, y, w, h, label, seed):
    rrect(d, (x, y, x + w, y + h), 12, (12, 14, 22, 255), outline=(255, 255, 255, 40), width=1)
    rng = np.random.default_rng(seed)
    n = 22
    v = np.cumsum(rng.normal(0.15, 1.0, n))
    v = (v - v.min()) / max(1e-6, v.max() - v.min())
    cw = (w - 24) / n
    for i in range(1, n):
        up = v[i] >= v[i - 1]
        col = (48, 209, 88, 255) if up else (255, 69, 58, 255)
        x0 = x + 12 + i * cw
        y0 = y + 12 + (1 - max(v[i], v[i - 1])) * (h - 46)
        y1 = y + 12 + (1 - min(v[i], v[i - 1])) * (h - 46)
        rrect(d, (x0, y0, x0 + cw * 0.62, max(y1, y0 + 2)), 1, col)
    text(d, (x + 12, y + h - 10), label, "Semibold Text", 18, (255, 255, 255, 170), anchor="lb")


# ---------------------------------------------------------------- painters
# Each painter returns (content RGBA at SS scale, glass shape mask L at SS scale or None, glass style).
# The card is laid out at its full size; parts that haven't popped yet are simply not drawn (or eased in).

def part_k(t, at):
    return ease_out((t - at) / PART_IN) if t >= at else 0.0


def paint_chat(ov, t):
    pad, w = 30, CARD_W
    msgs = []
    y = pad + 50 + 22
    for m in ov.get("messages", []):
        mine = m.get("from", "you") == "you"
        maxw = 640 if mine else 830
        lines = wrap(m.get("text", ""), "Regular", 29, maxw - (44 if mine else 0)) if m.get("text") else []
        tw = max([tlen(ln, "Regular", 29) for ln in lines] + [0])
        hh = len(lines) * 38
        extra = 0
        if m.get("file"):
            extra += 96 + (12 if lines else 0)
            tw = max(tw, 520)
        if m.get("charts"):
            extra += 128 + (12 if lines else 0)
            tw = max(tw, len(m["charts"]) * 198 - 18)
        bw = tw + (44 if mine else 0)
        bh = hh + extra + (30 if mine else 0)
        msgs.append(dict(m=m, mine=mine, lines=lines, y=y, w=bw, h=bh))
        y += bh + 18
    if ov.get("reply", True):
        reply_y = y + 4
        y = reply_y + 66 + pad
    else:
        reply_y = None
        y += pad - 18
    full_h = y
    # the card grows as messages arrive: height follows the last visible message, eased
    def visible_bottom():
        bottom = pad + 50 + 22 - 18
        for mm in msgs:
            k = part_k(t, mm["m"]["at"]) if mm["m"]["at"] > ov["at"] + 0.05 else 1.0
            if k <= 0:
                break
            bottom = mm["y"] + (mm["h"] + 18) * k - 18 * k
        return bottom
    if ov.get("grow", True):
        cur_h = visible_bottom() + (18 + 4 + 66 + pad if reply_y is not None else pad)
    else:
        cur_h = full_h
    cur_h = min(full_h, cur_h)
    img = Image.new("RGBA", (S(w), S(full_h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # header
    app_icon(d, pad, pad + 2, 46)
    tx = pad + 46 + 16
    text(d, (tx, pad + 25), ov.get("title", "Claude"), "Semibold Text", 32, (255, 255, 255, 255), anchor="lm")
    if ov.get("subtitle"):
        text(d, (tx + tlen(ov.get("title", "Claude"), "Semibold Text", 32) + 14, pad + 25), ov["subtitle"],
             "Regular", 30, (255, 255, 255, 140), anchor="lm")
    if ov.get("badge"):
        bw = tlen(ov["badge"], "Semibold Text", 24) + 36
        rrect(d, (w - pad - bw, pad + 5, w - pad, pad + 45), 12, (255, 255, 255, 26))
        text(d, (w - pad - bw / 2, pad + 25), ov["badge"], "Semibold Text", 24, (255, 255, 255, 220), anchor="mm")
    for mm in msgs:
        m = mm["m"]
        k = part_k(t, m["at"]) if m["at"] > ov["at"] + 0.05 else 1.0
        if k <= 0:
            continue
        a = int(255 * k)
        dy = (1 - k) * 10
        y0 = mm["y"] + dy
        if mm["mine"]:
            x0 = w - pad - mm["w"]
            rrect(d, (x0, y0, w - pad, y0 + mm["h"]), 24, (255, 255, 255, int(24 * k)))
            cy = y0 + 15
            if m.get("file"):
                fx, fy = x0 + 16, cy
                rrect(d, (fx, fy, w - pad - 16, fy + 84), 16, (255, 255, 255, int(16 * k)))
                doc_icon(d, fx + 14, fy + 10, 52, 64, m["file"].get("kind", "PDF"))
                text(d, (fx + 84, fy + 26), m["file"]["name"], "Semibold Text", 27, (255, 255, 255, a), anchor="lm")
                text(d, (fx + 84, fy + 60), m["file"].get("meta", ""), "Regular", 23, (255, 255, 255, int(140 * k)),
                     anchor="lm")
                cy += 96
            if m.get("charts"):
                for i, lab in enumerate(m["charts"]):
                    mini_chart(d, x0 + 16 + i * 198, cy, 180, 116, lab, seed=7 + i)
                cy += 128
            for i, ln in enumerate(mm["lines"]):
                text(d, (x0 + 22, cy + i * 38), ln, "Regular", 29, (255, 255, 255, a))
        else:
            if m.get("check"):
                check_circle(d, pad + 16, y0 + 19, 15, alpha=a)
            else:
                starburst(d, pad + 16, y0 + 19, 15, CLAUDE_ORANGE + (a,))
            for i, ln in enumerate(mm["lines"]):
                text(d, (pad + 48, y0 + i * 38), ln, "Regular", 29, (255, 255, 255, int(235 * k)))
    if reply_y is not None:
        ry = cur_h - pad - 66
        rrect(d, (pad, ry, w - pad, ry + 66), 22, (255, 255, 255, 18), outline=(255, 255, 255, 22), width=1)
        typed = ""
        if ov.get("typing") and t >= ov.get("typing_at", ov["at"]):
            n = int((t - ov.get("typing_at", ov["at"])) / 0.055)
            typed = ov["typing"][:n]
        if typed:
            text(d, (pad + 24, ry + 33), typed, "Regular", 28, (255, 255, 255, 240), anchor="lm")
        else:
            text(d, (pad + 24, ry + 33), ov.get("placeholder", "Reply to Claude..."), "Regular", 28,
                 (255, 255, 255, 105), anchor="lm")
        bx = w - pad - 10 - 46
        rrect(d, (bx, ry + 10, bx + 46, ry + 56), 12, CLAUDE_ORANGE + (255,) if typed else (255, 255, 255, 40))
        cx = bx + 23
        d.line([(S(cx), S(ry + 44)), (S(cx), S(ry + 22))], fill=(255, 255, 255, 255), width=S(3.5))
        d.line([(S(cx - 9), S(ry + 31)), (S(cx), S(ry + 22)), (S(cx + 9), S(ry + 31))], fill=(255, 255, 255, 255),
               width=S(3.5), joint="curve")
    img = img.crop((0, 0, S(w), S(cur_h)))
    mask = Image.new("L", img.size, 0)
    rrect(ImageDraw.Draw(mask), (0, 0, w, cur_h), 34, 255)
    return img, mask, "dark"


def paint_file(ov, t):
    name, meta = ov.get("name", "file.pdf"), ov.get("meta", "")
    w = max(560, min(CARD_W, 30 + 64 + 22 + max(tlen(name, "Semibold Text", 29), tlen(meta, "Regular", 24)) + 100))
    h = 110
    img = Image.new("RGBA", (S(w), S(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    doc_icon(d, 26, 18, 60, 74, ov.get("kind", "PDF"))
    text(d, (108, 40), name, "Semibold Text", 29, (255, 255, 255, 255), anchor="lm")
    text(d, (108, 76), meta, "Regular", 24, (255, 255, 255, 140), anchor="lm")
    if "check_at" in ov:
        k = part_k(t, ov["check_at"])
        if k > 0:
            check_circle(d, w - 46, h / 2, 17 * ease_back(k), alpha=int(255 * k))
    mask = Image.new("L", img.size, 0)
    rrect(ImageDraw.Draw(mask), (0, 0, w, h), 30, 255)
    return img, mask, "dark"


def paint_steps(ov, t):
    steps = ov.get("steps", [])
    seg = []
    for i, s in enumerate(steps):
        lab = s.get("text", "")
        seg.append(14 + 34 + 12 + tlen(lab, "Semibold Text", 25) + 18)
    gap = 8
    w = sum(seg) + gap * (len(seg) - 1) + 16
    h = 70
    img = Image.new("RGBA", (S(w), S(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    active = max([i for i, s in enumerate(steps) if t >= s["at"]], default=-1)
    xs, x = [], 8
    for sw in seg:
        xs.append(x)
        x += sw + gap
    if active >= 0:
        # the blue pill slides from the previous step to the new one
        k = ease_out((t - steps[active]["at"]) / 0.22)
        prev = active - 1 if active > 0 else active
        ax = xs[prev] + (xs[active] - xs[prev]) * k
        aw = seg[prev] + (seg[active] - seg[prev]) * k
        alpha = int(235 * (k if active == 0 else 1.0))
        rrect(d, (ax, 8, ax + aw, h - 8), 27, BLUE + (alpha,))
    for i, s in enumerate(steps):
        x0 = xs[i]
        cx, cy = x0 + 14 + 17, h / 2
        done, on = i < active, i == active
        if done:
            check_circle(d, cx, cy, 15)
        else:
            col = (255, 255, 255, 255) if on else (255, 255, 255, 110)
            if on:
                d.ellipse([S(cx - 15), S(cy - 15), S(cx + 15), S(cy + 15)], fill=(255, 255, 255, 70))
            else:
                d.ellipse([S(cx - 15), S(cy - 15), S(cx + 15), S(cy + 15)], outline=col, width=S(2))
            text(d, (cx, cy), str(i + 1), "Bold Text", 19, col, anchor="mm")
        tc = (255, 255, 255, 255) if (on or done) else (255, 255, 255, 120)
        text(d, (x0 + 14 + 34 + 12, cy), s.get("text", ""), "Semibold Text", 25, tc, anchor="lm")
    mask = Image.new("L", img.size, 0)
    rrect(ImageDraw.Draw(mask), (0, 0, w, h), h / 2, 255)
    return img, mask, "dark"


def paint_score(ov, t):
    w, h = 760, 210
    img = Image.new("RGBA", (S(w), S(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    val, mx = float(ov.get("value", 6)), float(ov.get("max", 10))
    k = ease_out((t - ov.get("count_at", ov["at"] + 0.05)) / 0.6)
    v = val * k
    shown = f"{v:.0f}" if val == int(val) else f"{v:.1f}"
    text(d, (34, 44), ov.get("label", "Score"), "Semibold Text", 30, (255, 255, 255, 255), anchor="lm")
    if ov.get("note"):
        text(d, (34, 84), ov["note"], "Regular", 24, (255, 255, 255, 140), anchor="lm")
    big = shown if t >= ov.get("count_at", ov["at"]) else "–"     # no "0/10" while he hasn't said the number
    suf = ov.get("suffix", f"/{mx:g}")
    sw = tlen(suf, "Semibold Display", 40)
    text(d, (w - 34 - sw, 82), big, "Bold Display", 88, (255, 255, 255, 255), anchor="rs")
    text(d, (w - 34, 82), suf, "Semibold Display", 40, (255, 255, 255, 150), anchor="rs")
    bx0, bx1, by = 34, w - 34, 150
    rrect(d, (bx0, by, bx1, by + 16), 8, (255, 255, 255, 34))
    fill_w = (bx1 - bx0) * clamp(v / mx)
    if fill_w > 4:
        rrect(d, (bx0, by, bx0 + fill_w, by + 16), 8, GREEN + (255,))
    tx = bx0 + (bx1 - bx0) * clamp(val / mx)
    d.line([(S(tx), S(by - 10)), (S(tx), S(by + 26))], fill=(255, 255, 255, 230), width=S(3))
    text(d, (tx, by + 34), ov.get("tick", f"{val:g}"), "Semibold Text", 20, (255, 255, 255, 190), anchor="mt")
    mask = Image.new("L", img.size, 0)
    rrect(ImageDraw.Draw(mask), (0, 0, w, h), 34, 255)
    return img, mask, "dark"


def paint_pills(ov, t):
    items = ov.get("items", [])
    ws = [tlen(it["text"], "Bold Display", 38) + 64 for it in items]
    gap, h = 18, 84
    w = sum(ws) + gap * (len(ws) - 1) + 24
    img = Image.new("RGBA", (S(w), S(h + 24)), (0, 0, 0, 0))
    x = 12
    for it, pw in zip(items, ws):
        k = clamp((t - it["at"]) / 0.2)
        if k > 0:
            sc = 0.55 + 0.45 * ease_back(k, 1.8)
            bg, fg = PILL_COLORS.get(it.get("color", "blue"), PILL_COLORS["blue"])
            layer = Image.new("RGBA", (S(pw), S(h)), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            rrect(ld, (0, 0, pw, h), h / 2, bg + (255,))
            text(ld, (pw / 2, h / 2 + 1), it["text"], "Bold Display", 38, fg + (255,), anchor="mm")
            nw, nh = max(1, int(layer.width * sc)), max(1, int(layer.height * sc))
            layer = layer.resize((nw, nh), Image.BILINEAR)
            if k < 1:
                layer.putalpha(layer.getchannel("A").point(lambda a, kk=k: int(a * min(1, kk * 2))))
            img.alpha_composite(layer, (int(S(x + pw / 2) - nw / 2), int(S(12 + h / 2) - nh / 2)))
        x += pw + gap
    return img, None, None


def paint_comments(ov, t):
    w, pad = CARD_W, 28
    word, handle = ov.get("word", ""), ov.get("handle", "you")
    posted = t >= ov["post_at"]
    pk = part_k(t, ov["post_at"]) if posted else 0.0
    row_h = 110 * pk
    h = int(round(64 + row_h + 96 + 10))
    img = Image.new("RGBA", (S(w), S(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rrect(d, (0, 0, w, h), 30, (28, 28, 30, 250))
    rrect(d, (w / 2 - 36, 12, w / 2 + 36, 19), 4, (255, 255, 255, 70))
    text(d, (w / 2, 44), "Comments", "Semibold Text", 27, (255, 255, 255, 255), anchor="mm")
    if posted:
        a = int(255 * pk)
        y0 = 70 + (1 - pk) * 10
        d.ellipse([S(pad), S(y0 + 6), S(pad + 52), S(y0 + 58)], fill=(72, 72, 78, a))
        text(d, (pad + 26, y0 + 32), (ov.get("you", "you")[:1] or "y").upper(), "Semibold Text", 24, (255, 255, 255, a),
             anchor="mm")
        text(d, (pad + 70, y0 + 16), ov.get("you", "you"), "Semibold Text", 23, (255, 255, 255, a), anchor="lm")
        text(d, (pad + 70 + tlen(ov.get("you", "you"), "Semibold Text", 23) + 10, y0 + 16), "now", "Regular", 22,
             (255, 255, 255, int(120 * pk)), anchor="lm")
        text(d, (pad + 70, y0 + 50), word, "Regular", 29, (255, 255, 255, a), anchor="lm")
        text(d, (pad + 70, y0 + 86), "Reply", "Semibold Text", 21, (255, 255, 255, int(120 * pk)), anchor="lm")
        liked = t >= ov["post_at"] + 0.45
        hx, hy = w - pad - 22, y0 + 34
        heart(d, hx, hy, 15, RED + (a,) if liked else None, (255, 255, 255, int(150 * pk)))
    iy = h - 96
    d.ellipse([S(pad), S(iy + 22), S(pad + 48), S(iy + 70)], fill=(72, 72, 78, 255))
    rrect(d, (pad + 64, iy + 18, w - pad - 92, iy + 74), 28, (44, 44, 46, 255))
    typed = ""
    t0 = ov["at"] + 0.25
    if not posted and t >= t0:
        typed = word[:int((t - t0) / 0.07) + 1]
    if typed:
        text(d, (pad + 88, iy + 46), typed, "Regular", 28, (255, 255, 255, 255), anchor="lm")
        cw = tlen(typed, "Regular", 28)
        if int(t * 2.2) % 2 == 0:
            d.line([(S(pad + 90 + cw), S(iy + 30)), (S(pad + 90 + cw), S(iy + 62))], fill=(0, 149, 246, 255), width=S(2))
    else:
        text(d, (pad + 88, iy + 46), f"Add a comment for {handle}...", "Regular", 27, (255, 255, 255, 110),
             anchor="lm")
    text(d, (w - pad - 8, iy + 46), "Post", "Semibold Text", 27, (0, 149, 246, 255 if typed else 110), anchor="rm")
    return img, None, None


def heart(d, cx, cy, r, fill, outline):
    pts = []
    for i in range(48):
        a = i / 48 * 2 * math.pi
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((S(cx + x / 16 * r), S(cy + y / 16 * r)))
    if fill:
        d.polygon(pts, fill=fill)
    else:
        d.line(pts + pts[:1], fill=outline, width=S(2.4), joint="curve")


def paint_banner(ov, t):
    """The notification that drops in over the comments sheet ("withaarit: here are the prompts")."""
    w, h = 960, 104
    img = Image.new("RGBA", (S(w), S(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rrect(d, (0, 0, w, h), 28, (242, 242, 247, 246))
    # a generic gradient app icon with a paper plane (a DM)
    ic = Image.new("RGBA", (S(60), S(60)), (0, 0, 0, 0))
    g = np.zeros((S(60), S(60), 4), np.uint8)
    yy, xx = np.mgrid[0:S(60), 0:S(60)] / S(60)
    u = (xx + (1 - yy)) / 2
    for c, (a0, a1) in enumerate(((254, 131), (218, 58), (117, 180))):
        g[..., c] = (a0 + (a1 - a0) * u).astype(np.uint8)
    g[..., 3] = 255
    ic = Image.fromarray(g, "RGBA")
    m = Image.new("L", ic.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, S(60) - 1, S(60) - 1], radius=S(15), fill=255)
    ic.putalpha(m)
    idr = ImageDraw.Draw(ic)
    idr.polygon([(S(14), S(30)), (S(46), S(16)), (S(36), S(46)), (S(29), S(34))], outline=(255, 255, 255, 255),
                width=S(3))
    img.alpha_composite(ic, (S(22), S(22)))
    text(d, (100, 36), ov.get("app", "Instagram"), "Semibold Text", 25, (20, 20, 22, 255), anchor="lm")
    text(d, (w - 24, 36), "now", "Regular", 22, (60, 60, 67, 150), anchor="rm")
    text(d, (100, 70), ov.get("reply", ""), "Regular", 25, (20, 20, 22, 230), anchor="lm")
    return img


def paint_toast(ov, t):
    s, sign = ov.get("text", ""), ov.get("sign", "")
    w = 30 + 34 + 16 + tlen(s, "Regular", 27) + (14 + tlen(sign, "Regular", 21) if sign else 0) + 30
    h = 64
    img = Image.new("RGBA", (S(w), S(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if ov.get("icon") == "bookmark":
        d.polygon([(S(28), S(16)), (S(50), S(16)), (S(50), S(50)), (S(39), S(41)), (S(28), S(50))],
                  fill=(255, 255, 255, 245))
    else:
        rrect(d, (22, 15, 56, 49), 9, CREAM + (255,))
        starburst(d, 39, 32, 12, CLAUDE_ORANGE + (255,))
    text(d, (72, h / 2), s, "Regular", 27, (255, 255, 255, 250), anchor="lm")
    if sign:
        text(d, (72 + tlen(s, "Regular", 27) + 14, h / 2 + 2), sign, "Regular", 21, (255, 255, 255, 120),
             anchor="lm")
    mask = Image.new("L", img.size, 0)
    rrect(ImageDraw.Draw(mask), (0, 0, w, h), h / 2, 255)
    return img, mask, "dark"


def paint_progress(ov, t):
    w, pad = CARD_W, 30
    states = ov.get("states", [])
    cur = max([i for i, s in enumerate(states) if t >= s["at"]], default=0)
    done = "done_at" in ov and t >= ov["done_at"]
    h = 168
    img = Image.new("RGBA", (S(w), S(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    app_icon(d, pad, pad, 44)
    text(d, (pad + 60, pad + 22), ov.get("title", "Claude"), "Semibold Text", 30, (255, 255, 255, 255), anchor="lm")
    if ov.get("file"):
        text(d, (pad + 60 + tlen(ov.get("title", "Claude"), "Semibold Text", 30) + 12, pad + 22), ov["file"],
             "Regular", 28, (255, 255, 255, 140), anchor="lm")
    if states:
        s = states[cur]
        p0 = states[cur - 1].get("pct", 0) if cur > 0 else 0
        k = ease_out((t - s["at"]) / 0.5)
        pct = 100 if done else p0 + (s.get("pct", 0) - p0) * k
        label = "Done" if done else s.get("text", "")
        text(d, (pad, 108), label, "Regular", 26, (255, 255, 255, 200), anchor="lm")
        if done:
            d.ellipse([S(w - pad - 18), S(99), S(w - pad), S(117)], fill=GREEN + (255,))
        else:
            text(d, (w - pad, 108), f"{pct:.0f}%", "Semibold Text", 24, (255, 255, 255, 170), anchor="rm")
        rrect(d, (pad, 134, w - pad, 144), 5, (255, 255, 255, 36))
        fw = (w - 2 * pad) * clamp(pct / 100)
        if fw > 3:
            rrect(d, (pad, 134, pad + fw, 144), 5, (GREEN if done else CLAUDE_ORANGE) + (255,))
    mask = Image.new("L", img.size, 0)
    rrect(ImageDraw.Draw(mask), (0, 0, w, h), 34, 255)
    return img, mask, "dark"


def paint_list(ov, t):
    lines = ov.get("lines", [])
    lh = 46
    w = max(tlen(ln, "Semibold Display", 34) for ln in lines) + 40
    h = lh * len(lines) + 20
    img = Image.new("RGBA", (S(w), S(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for i, ln in enumerate(lines):
        text(sd, (20, 10 + i * lh + 3), ln, "Semibold Display", 34, (0, 0, 0, 150))
        text(d, (20, 10 + i * lh), ln, "Semibold Display", 34, (255, 255, 255, 255))
    out = sh.filter(ImageFilter.GaussianBlur(S(4)))
    out.alpha_composite(img)
    return out, None, None


@lru_cache(maxsize=16)
def picture(src, max_h):
    """His picture at SS scale, fitted inside CARD_W x max_h (aspect kept), rounded corners, hairline rim."""
    im = Image.open(src)
    im.load()
    im = im.convert("RGBA")
    k = min(CARD_W / im.width, max_h / im.height)
    w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    im = im.resize((S(w), S(h)), Image.LANCZOS)
    mask = Image.new("L", im.size, 0)
    rrect(ImageDraw.Draw(mask), (0, 0, w, h), 26, 255)
    im.putalpha(Image.fromarray(np.minimum(np.asarray(im.getchannel("A")), np.asarray(mask))))
    rim = Image.new("RGBA", im.size, (0, 0, 0, 0))
    rrect(ImageDraw.Draw(rim), (0, 0, w, h), 26, None, outline=(255, 255, 255, 56), width=1.5)
    im.alpha_composite(rim)
    return im


def paint_image(ov, t):
    return picture(ov["src"], int(ov.get("max_h", IMG_MAX_H))), None, None


PAINT = {"chat": paint_chat, "file": paint_file, "steps": paint_steps, "score": paint_score, "pills": paint_pills,
         "comments": paint_comments, "toast": paint_toast, "progress": paint_progress, "list": paint_list,
         "image": paint_image}


def full_size(ov):
    """(w, h) the overlay reaches at its biggest, for placing it before it's drawn."""
    probe = dict(ov)
    t = max(ov.get("_last", ov["at"]), ov["at"]) + 1.0
    img, _, _ = PAINT[ov["type"]](probe, t)
    w, h = img.width / SS, img.height / SS
    if ov["type"] == "comments" and ov.get("reply"):
        h += BANNER_UP   # the notification banner hangs over the top of the sheet
    return w, h


# ---------------------------------------------------------------- compositing

def glass(frame, box, mask, style):
    """Frosted card background from the frame under it: blurred, darkened, tinted, with a hairline rim."""
    region = frame.crop(box).convert("RGB")
    small = region.resize((max(1, region.width // 6), max(1, region.height // 6)), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(4))
    blur = np.asarray(small.resize(region.size, Image.BILINEAR), np.float32)
    out = blur * 0.42 + np.array(TINT, np.float32) * 0.58
    g = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")
    m = mask.resize(region.size, Image.LANCZOS)
    g.putalpha(m.point(lambda v: int(v * 0.94)))
    rim_a = np.clip(np.asarray(m, np.int16) - np.asarray(m.filter(ImageFilter.MinFilter(3)), np.int16), 0, 255)
    rim = Image.new("RGBA", region.size, (255, 255, 255, 0))
    rim.putalpha(Image.fromarray((rim_a * 0.18).astype(np.uint8)))
    g.alpha_composite(rim)
    return g


def draw(frame, t, ov, place):
    """Composite one overlay onto frame (RGB PIL, 1080x1920) at time t. place = {"x", "y", "scale"}."""
    if t < ov["at"] or t >= ov["end"]:
        return frame
    u_in = clamp((t - ov["at"]) / POP_IN)
    u_out = clamp((ov["end"] - t) / POP_OUT)
    k = min(ease_out(u_in), ease_out(u_out))
    content, mask, style = PAINT[ov["type"]](ov, t)
    sc = place["scale"]
    cw, ch = content.width / SS * sc, content.height / SS * sc
    cw_i, ch_i = max(1, int(round(cw))), max(1, int(round(ch)))
    content = content.resize((cw_i, ch_i), Image.LANCZOS)
    x = place["x"] + (place["w"] - cw) / 2 if ov["type"] in ("steps", "pills", "file", "toast", "score", "list") else place["x"]
    y = place["y"]
    if ov["type"] == "comments" and ov.get("reply"):
        y += BANNER_UP * sc
    m = 40
    layer = Image.new("RGBA", (cw_i + 2 * m, ch_i + 2 * m), (0, 0, 0, 0))
    if mask is not None:
        mk = mask.resize((cw_i, ch_i), Image.LANCZOS)
        sh = Image.new("L", layer.size, 0)
        sh.paste(mk.point(lambda v: int(v * 0.4)), (m, m + 8))
        layer.putalpha(sh.filter(ImageFilter.GaussianBlur(16)))
        box = (int(x), int(y), int(x) + cw_i, int(y) + ch_i)
        layer.alpha_composite(glass(frame, box, mask, style), (m, m))
    elif ov["type"] in ("comments", "image"):
        sh = Image.new("L", layer.size, 0)
        sh.paste(content.getchannel("A").point(lambda v: int(v * 0.45)), (m, m + 10))
        layer.putalpha(sh.filter(ImageFilter.GaussianBlur(18)))
    layer.alpha_composite(content, (m, m))
    if ov["type"] == "comments" and ov.get("reply") and t >= ov["reply_at"]:
        bk = ease_out((t - ov["reply_at"]) / 0.28)
        ban = paint_banner(ov, t)
        bw, bh = int(ban.width / SS * sc), int(ban.height / SS * sc)
        ban = ban.resize((bw, bh), Image.LANCZOS)
        bl = Image.new("RGBA", (bw + 2 * m, bh + 2 * m), (0, 0, 0, 0))
        bs = Image.new("L", bl.size, 0)
        bs.paste(ban.getchannel("A").point(lambda v: int(v * 0.35)), (m, m + 8))
        bl.putalpha(bs.filter(ImageFilter.GaussianBlur(14)))
        bl.alpha_composite(ban, (m, m))
        bl.putalpha(bl.getchannel("A").point(lambda v: int(v * bk)))
        by = int(-BANNER_UP * sc - (1 - bk) * 70 * sc)
        big = Image.new("RGBA", (layer.width, layer.height + int(140 * sc)), (0, 0, 0, 0))
        big.alpha_composite(layer, (0, int(140 * sc)))
        big.alpha_composite(bl, (int((layer.width - bl.width) / 2), max(0, int(140 * sc) + by)))
        layer = big
        y -= 140 * sc
    # the pop: scale 94% -> 100%, blur 8 -> 0, rise 12 px, opacity
    if k < 0.999:
        s = 0.94 + 0.06 * k
        nw, nh = max(1, int(layer.width * s)), max(1, int(layer.height * s))
        lay = layer.resize((nw, nh), Image.BILINEAR)
        b = 8 * (1 - k)
        if b > 0.4:
            small = lay.resize((max(1, nw // 3), max(1, nh // 3)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(b / 3))
            lay = small.resize((nw, nh), Image.BILINEAR)
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * k)))
        ox = x - m + (layer.width - nw) / 2
        oy = y - m + (layer.height - nh) / 2 + 12 * (1 - k)
    else:
        lay, ox, oy = layer, x - m, y - m
    out = frame.convert("RGBA")
    out.alpha_composite(lay, (int(round(ox)), int(round(oy))))
    return out.convert("RGB")


# ---------------------------------------------------------------- suggestions

def suggest(words):
    """A first draft for Claude to edit: a step tracker when he counts steps, a chat card on lines where he
    hands Claude something, and the comments sheet on "comment X". Claude rewrites it after reading."""
    ns = [norm(w["t"]) for w in words]
    out = []
    steps = [i for i, n in enumerate(ns) if n == "step" and i + 1 < len(ns) and ns[i + 1] in {"1", "2", "3", "4", "5"}]
    if len(steps) >= 2:
        first = steps[0]
        out.append({"type": "steps", "at": words[max(0, first)]["t"].strip(".,!?"),
                    "steps": [{"text": f"Step {ns[i + 1]}", "at": f"step {ns[i + 1]}"} for i in steps]})
    for i, n in enumerate(ns):
        if n in {"upload", "send", "give", "paste", "ask"} and "claude" in ns[max(0, i - 6): i + 7]:
            a = i
            while a > 0 and words[a - 1]["t"][-1:] not in ".,!?":
                a -= 1
            b = i
            while b < len(words) - 1 and words[b]["t"][-1:] not in ".,!?":
                b += 1
            line = " ".join(w["t"] for w in words[a:b + 1]).strip(" .,")
            out.append({"type": "chat", "at": words[i]["t"].strip(".,!?"), "title": "Claude",
                        "messages": [{"from": "you", "text": line}]})
        if n == "comment" and i + 1 < len(words):
            out.append({"type": "comments", "at": "comment", "handle": "withaarit",
                        "word": words[i + 1]["t"].strip(".,!?'\""), "reply": "withaarit: sent you the link"})
    out.sort(key=lambda o: find(words, o["at"], 0.0))
    return out
