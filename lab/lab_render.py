"""Style lab: render one Reel in an alternative look, to compare against the locked style.

Nothing here changes the locked engine (reel.py / talk_reel.py). Captions, transitions, grading,
framed B-roll and the code-made text cuts are all drawn per frame in Python, then encoded once.

  py -3.14 lab/lab_render.py --reel "reels/recording 55" --look glass --out "out.mp4"
"""
import argparse, json, math, subprocess, sys
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import talk_reel as tr   # noqa: E402

W, H = 1080, 1920
WF = "C:/Windows/Fonts/"
FIG = str(ROOT / "fonts" / "figtree-800" / "figtree-800.ttf")
SEG = WF + "SegUIVar.ttf"
SITKA_I = WF + "SitkaVF-Italic.ttf"
SEG_BLACK = WF + "seguibl.ttf"

EMPH = {"crore", "marketplay", "vc", "months", "two", "three", "200k", "followers", "nothing"}

# ---------------------------------------------------------------- looks

LOOKS = {
    # 1. iOS-clean: SF-like Segoe UI Variable Display, words blur in one by one as he says them
    "glass": dict(
        font=(SEG, "Semibold Display", 74), color=(255, 255, 255), emph_color=(255, 214, 10), emph_font=None,
        case="sentence", reveal="word", anim=dict(dur=0.26, rise=16, blur=9, scale0=0.97, back=False),
        shadow=(120, 10, 3), pill=None, y=0.70, maxw=900,
        transition="blur", span=0.18, grade="light", grain=0, frame=None, textcut=None,
        whoosh="sections", whoosh_db=-12),
    # 2. Spotlight: Figtree captions, a purple pill glides onto the word he is saying
    "spotlight": dict(
        font=(FIG, None, 84), color=(255, 255, 255), emph_color=None, emph_font=None,
        case="sentence", reveal="chunk", anim=dict(dur=0.2, rise=10, blur=0, scale0=0.9, back=True),
        shadow=(140, 9, 4), pill=(139, 92, 246), y=0.68, maxw=880,
        transition="whip", span=0.13, grade=None, grain=0, frame=None, textcut=None,
        whoosh="all", whoosh_db=-17),
    # 3. Cinematic vlog: small lowercase sans + gold serif italic key words, film grade, light leaks
    "cinematic": dict(
        font=(SEG, "Semibold Text", 64), color=(250, 246, 240), emph_color=(246, 208, 150),
        emph_font=(SITKA_I, "Display Semibold Italic", 1.45),
        case="lower", reveal="chunk", anim=dict(dur=0.34, rise=10, blur=7, scale0=1.0, back=False),
        shadow=(200, 11, 3), pill=None, y=0.74, maxw=900,
        transition="leak", span=0.32, grade="film", grain=4, frame=None, textcut=None,
        whoosh="sections", whoosh_db=-14),
    # 4. Keynote: B-roll framed as a rounded card over its own blur, code-made text cuts, purple accents
    "keynote": dict(
        font=(SEG, "Bold Display", 70), color=(255, 255, 255), emph_color=(190, 156, 255), emph_font=None,
        case="sentence", reveal="word", anim=dict(dur=0.24, rise=12, blur=8, scale0=0.97, back=False),
        shadow=(110, 10, 3), pill=None, y=0.80, maxw=900,
        transition="blur", span=0.16, grade="light", grain=0, frame="card", textcut="keynote",
        whoosh="sections", whoosh_db=-12),
    # 5. Kinetic: big Figtree words spring in, red key words, zoom-through cuts, red-card text cuts in code
    "kinetic": dict(
        font=(FIG, None, 90), color=(255, 255, 255), emph_color=(255, 84, 60), emph_font=None, emph_scale=1.18,
        case="sentence", reveal="word", anim=dict(dur=0.17, rise=0, blur=0, scale0=0.55, back=True),
        shadow=(170, 9, 5), pill=None, y=0.68, maxw=920,
        transition="zoom", span=0.14, grade=None, grain=0, frame=None, textcut="redcard",
        whoosh="all", whoosh_db=-16),
    # 6. "v2", his pick 10-17: glass captions in bold, key words in a new colour each time, a light-leak
    #    glow on every cut (colour changes per video), glass picture, +20% accent SFX, face zoom, Flow cuts
    "v2": dict(
        font=(SEG, "Bold Display", 76), color=(255, 255, 255), emph_color="rotate", emph_font=None,
        case="sentence", reveal="word", anim=dict(dur=0.26, rise=16, blur=9, scale0=0.97, back=False),
        shadow=(130, 10, 3), pill=None, y=0.70, maxw=900,
        transition="leak", span=0.32, grade="light", grain=0, frame=None, textcut=None,
        whoosh="sections", whoosh_db=-10, accents=0.2, flow_cuts=True, zoom=True),
}

# iOS dark-mode system colours, ordered so neighbours never look alike
EMPH_COLORS = [(255, 69, 58), (255, 214, 10), (100, 210, 255), (255, 159, 10),
               (48, 209, 88), (255, 55, 95), (191, 90, 242)]

# light-leak tints (main glow, second glow); every new video gets a different one from the last
LEAK_COLORS = {
    "violet": ((0.78, 0.45, 1.0), (1.0, 0.45, 0.75)),
    "amber": ((1.0, 0.55, 0.2), (1.0, 0.35, 0.25)),
    "rose": ((1.0, 0.42, 0.58), (1.0, 0.62, 0.4)),
    "teal": ((0.3, 0.85, 1.0), (0.55, 0.6, 1.0)),
    "gold": ((1.0, 0.8, 0.32), (1.0, 0.55, 0.22)),
    "crimson": ((1.0, 0.28, 0.22), (1.0, 0.52, 0.28)),
}

# shots that stay full-bleed in the keynote frame (his logo card and the face-to-camera shot)
FULL_BLEED = [(9.3, 11.08), (40.0, 43.2)]

# ---------------------------------------------------------------- helpers


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(u):
    u = clamp(u)
    return 1 - (1 - u) ** 3


def ease_back(u, s=1.6):
    u = clamp(u) - 1
    return 1 + (s + 1) * u ** 3 + s * u ** 2


def smooth(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


@lru_cache(maxsize=256)
def font(path, var, size):
    f = ImageFont.truetype(path, int(round(size)))
    if var:
        f.set_variation_by_name(var)
    return f


def is_emph(word):
    s = word.lower().strip(".,!?")
    return any(ch.isdigit() for ch in s) or s in EMPH


def cased(text, case):
    if case != "lower":
        return text
    return text if text in ("MarketPlay", "VC") else text.lower()


@lru_cache(maxsize=4096)
def word_tile(text, fspec, color, shadow):
    """(text tile, shadow tile, ascent, pad): RGBA tiles with the baseline at pad + ascent."""
    f = font(*fspec)
    asc, desc = f.getmetrics()
    pad = 34
    w = int(f.getlength(text)) + 2 * pad
    h = asc + desc + 2 * pad
    t = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(t).text((pad, pad + asc), text, font=f, fill=color + (255,), anchor="ls")
    sa, sb, _ = shadow
    s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(s).text((pad, pad + asc), text, font=f, fill=(0, 0, 0, sa), anchor="ls")
    s = s.filter(ImageFilter.GaussianBlur(sb))
    return t, s, asc, pad


def fade_alpha(img, a):
    if a >= 0.999:
        return img
    img = img.copy()
    img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    return img


# ---------------------------------------------------------------- captions


def caption_windows(chunks, L):
    """(start, end, words, key-word colour). With emph_color "rotate", each caption that has a key word
    takes the next colour in EMPH_COLORS, so the colour changes every time."""
    out, k = [], 0
    for ci, ch in enumerate(chunks):
        start, end = ch[0]["s"], ch[-1]["e"] + 0.15
        if ci + 1 < len(chunks):
            nxt = chunks[ci + 1][0]["s"]
            end = nxt if nxt - ch[-1]["e"] < tr.HOLD_GAP else min(end, nxt)
        color = L.get("emph_color")
        if color == "rotate":
            color = EMPH_COLORS[k % len(EMPH_COLORS)]
            k += any(is_emph(w["t"]) for w in ch)
        out.append((start, end, ch, color))
    return out


def layout(ch, L, emph_color=None):
    """Words with font spec, colour and position (x, baseline) inside a W x BAND band."""
    base = L["font"]
    items = []
    for w in ch:
        text = cased(tr.display(w["t"]), L["case"])
        emph = is_emph(w["t"])
        fspec, color = base, L["color"]
        if emph and L.get("emph_font"):
            p, v, k = L["emph_font"]
            fspec = (p, v, base[2] * k)
        elif emph and L.get("emph_scale"):
            fspec = (base[0], base[1], base[2] * L["emph_scale"])
        if emph and emph_color:
            color = emph_color
        f = font(*fspec)
        items.append(dict(w=w, text=text, fspec=fspec, color=color, width=f.getlength(text)))
    space = font(*base).getlength(" ")
    widths = [it["width"] for it in items]

    def line_w(a, b):
        return sum(widths[a:b]) + space * (b - a - 1)

    lines = [(0, len(items))]
    if line_w(0, len(items)) > L["maxw"] and len(items) > 1:
        k = min(range(1, len(items)), key=lambda k: max(line_w(0, k), line_w(k, len(items))))
        lines = [(0, k), (k, len(items))]
    lh = base[2] * 1.18
    for li, (a, b) in enumerate(lines):
        x = (W - line_w(a, b)) / 2
        baseline = BAND / 2 + (li - (len(lines) - 1) / 2) * lh + base[2] * 0.35
        for it in items[a:b]:
            it["x"], it["base"] = x, baseline
            x += it["width"] + space
    return items


BAND = 520


def draw_captions(frame, t, wins, L, hidden):
    if any(a <= t < b for a, b in hidden):
        return frame
    win = next((w for w in wins if w[0] <= t < w[1]), None)
    if not win:
        return frame
    start, end, ch, emph_color = win
    out_a = clamp((end - t) / 0.07)
    items = layout(ch, L, emph_color)
    an = L["anim"]
    band = Image.new("RGBA", (W, BAND), (0, 0, 0, 0))
    if L["pill"]:
        draw_pill(band, t, items, start, L)
    for it in items:
        appear = start if L["reveal"] == "chunk" else max(it["w"]["s"] - 0.04, start)
        u = (t - appear) / an["dur"]
        if u <= 0:
            continue
        e = ease_out(u)
        sc = an["scale0"] + (1 - an["scale0"]) * (ease_back(u) if an["back"] else e)
        alpha = clamp(u * 1.8) * out_a
        tile, sh, asc, pad = word_tile(it["text"], it["fspec"], it["color"], L["shadow"])
        if abs(sc - 1) > 0.004:
            nw, nh = max(1, int(tile.width * sc)), max(1, int(tile.height * sc))
            tile, sh = tile.resize((nw, nh), Image.BILINEAR), sh.resize((nw, nh), Image.BILINEAR)
        blur = an["blur"] * (1 - e)
        if blur > 0.3:
            tile = tile.filter(ImageFilter.GaussianBlur(blur))
        cx = it["x"] + it["width"] / 2
        cy = it["base"] - asc * 0.35 + an["rise"] * (1 - e)
        x0 = int(round(cx - tile.width / 2))
        y0 = int(round(cy - (pad + asc * 0.65) * sc))
        dy = L["shadow"][2]
        for img, ox, oy in ((sh, x0, y0 + dy), (tile, x0, y0)):
            img = fade_alpha(img, alpha)
            band.alpha_composite(img, (max(ox, 0), max(oy, 0)),
                                 (max(-ox, 0), max(-oy, 0)))
    y = int(H * L["y"] - BAND / 2)
    region = frame.crop((0, y, W, y + BAND)).convert("RGBA")
    region.alpha_composite(band)
    frame.paste(region.convert("RGB"), (0, y))
    return frame


def draw_pill(band, t, items, start, L):
    spoken = [i for i, it in enumerate(items) if it["w"]["s"] - 0.03 <= t]
    if not spoken:
        spoken = [0]
    cur = spoken[-1]
    prev = cur - 1 if cur > 0 else cur
    since = t - max(items[cur]["w"]["s"] - 0.03, start)
    k = ease_out(since / 0.14) if cur != prev else 1.0
    asc = font(*L["font"]).getmetrics()[0]

    def rect(it):
        return (it["x"] - 20, it["base"] - asc * 0.86, it["x"] + it["width"] + 20, it["base"] + asc * 0.2)

    r0, r1 = rect(items[prev]), rect(items[cur])
    r = [a + (b - a) * k for a, b in zip(r0, r1)]
    grow = ease_back((t - start) / 0.2)
    cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
    hw, hh = (r[2] - r[0]) / 2 * grow, (r[3] - r[1]) / 2 * grow
    a = int(240 * clamp((t - start) / 0.08))
    ImageDraw.Draw(band).rounded_rectangle((cx - hw, cy - hh, cx + hw, cy + hh), radius=int(hh * 0.55),
                                           fill=L["pill"] + (a,))


# ---------------------------------------------------------------- picture treatments


def blur_small(img, radius, scale=4):
    small = img.resize((W // scale, H // scale), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius / scale))
    return small.resize((W, H), Image.BILINEAR)


def nearest_cut(t, cuts, span):
    best = None
    for c in cuts:
        d = t - c
        if -span <= d < span and (best is None or abs(d) < abs(best[1])):
            best = (c, d)
    return best


LEAK = {}


def leak_layer(tint="amber"):
    if tint not in LEAK:
        main, second = LEAK_COLORS[tint]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        a = np.exp(-(((xx - W * 1.0) / (W * 0.55)) ** 2 + ((yy - H * 0.15) / (H * 0.45)) ** 2))
        b = np.exp(-(((xx - W * 0.0) / (W * 0.5)) ** 2 + ((yy - H * 0.85) / (H * 0.35)) ** 2)) * 0.6
        LEAK[tint] = (a[..., None] * np.array(main, np.float32) +
                      b[..., None] * np.array(second, np.float32)) * 255
    return LEAK[tint]


def pick_leak(reel_name, override=""):
    """Each video keeps its own leak colour across re-renders; a new video never repeats the last one."""
    path = Path(__file__).parent / "leak_colors.json"
    hist = json.loads(path.read_text()) if path.exists() else {}
    if override:
        hist[reel_name] = override
    elif reel_name not in hist:
        names = list(LEAK_COLORS)
        last = hist.get("_last")
        hist[reel_name] = names[(names.index(last) + 1) % len(names)] if last in names else names[0]
    hist["_last"] = hist[reel_name]
    path.write_text(json.dumps(hist, indent=1))
    return hist[reel_name]


def transition(img, t, cuts, L):
    hit = nearest_cut(t, cuts, L["span"])
    if not hit:
        return img
    c, d = hit
    u = 1 - abs(d) / L["span"]          # 1 at the cut, 0 at the edges of the window
    kind = L["transition"]
    if kind == "blur":
        k = smooth(u)
        return Image.blend(img, blur_small(img, 26 * k + 1), min(1.0, k * 1.3))
    if kind == "whip":
        k = smooth(u) ** 1.5
        side = -1 if d < 0 else 1       # old shot leaves to the left, new one arrives from the right
        a = np.asarray(img.resize((W // 4, H // 4), Image.BILINEAR), np.float32)
        n = max(1, int(60 * k))
        cs = np.cumsum(np.pad(a, ((0, 0), (n, n), (0, 0)), mode="edge"), axis=1)
        a = (cs[:, 2 * n:] - cs[:, :-2 * n]) / (2 * n)
        s = int(side * 90 * k)            # shift with the edge stretched, never wrapped around
        if s:
            a = np.pad(a, ((0, 0), (abs(s), abs(s)), (0, 0)), mode="edge")[:, abs(s) - s: abs(s) - s + W // 4]
        out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        return Image.blend(img, out, min(1.0, k * 1.6))
    if kind == "zoom":
        k = smooth(u) ** 1.4
        z = 1 + 0.16 * k
        layers = []
        for zz in (z, z * 1.03, z * 1.06):
            bw, bh = W / zz, H / zz
            box = ((W - bw) / 2, (H - bh) / 2, (W + bw) / 2, (H + bh) / 2)
            layers.append(np.asarray(img.resize((W, H), Image.BILINEAR, box=box), np.float32))
        mix = layers[0] * 0.5 + layers[1] * 0.3 + layers[2] * 0.2   # cheap radial blur
        out = layers[0] + (mix - layers[0]) * min(1.0, k * 1.5)
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    if kind == "leak":
        k = smooth(u) ** 1.3
        a = np.asarray(img, np.float32) / 255
        lk = leak_layer(L.get("leak_tint", "amber"))
        if cuts.index(c) % 2:                   # alternate the side the glow comes from, cut to cut
            lk = lk[:, ::-1]
        lk = lk / 255 * 0.55 * k               # screen blend: warms and glows, never blows out to white
        a = 1 - (1 - a) * (1 - lk)
        return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return img


VIG = None
GRAIN = None


def grade(img, L, n):
    global VIG, GRAIN
    g = L["grade"]
    if not g and not L["grain"]:
        return img
    a = np.asarray(img, np.float32) / 255
    if g == "light":
        lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        a = lum[..., None] + (a - lum[..., None]) * 1.07
        a = 0.5 + (a - 0.5) * 1.04
        a *= np.array([1.012, 1.0, 0.985], np.float32)
    elif g == "film":
        lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        a = lum[..., None] + (a - lum[..., None]) * 0.86
        a = 0.5 + (a - 0.5) * 1.1
        l3 = lum[..., None]
        a += (1 - l3) * np.array([-0.02, 0.012, 0.03], np.float32) + l3 * np.array([0.035, 0.012, -0.03], np.float32)
        a = 0.035 + a * 0.95
        if VIG is None:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
            VIG = (1 - 0.32 * np.clip(r - 0.35, 0, 1) ** 1.6)[..., None].astype(np.float32)
        a *= VIG
    if L["grain"]:
        if GRAIN is None:
            rng = np.random.default_rng(7)
            GRAIN = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32).repeat(2, 0).repeat(2, 1)[..., None]
                     for _ in range(6)]
        a += GRAIN[n % 6] * (L["grain"] / 255)
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


CARD = dict(w=int(W * 0.84), h=int(W * 0.84 * 5 / 4), top=250, r=46)
CARD_MASK = None


def card_mask():
    global CARD_MASK
    if CARD_MASK is None:
        s = 4
        m = Image.new("L", (CARD["w"] * s, CARD["h"] * s), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, CARD["w"] * s - 1, CARD["h"] * s - 1), radius=CARD["r"] * s, fill=255)
        m = m.resize((CARD["w"], CARD["h"]), Image.LANCZOS)
        sh = Image.new("L", (W, H), 0)
        sh.paste(m, ((W - CARD["w"]) // 2, CARD["top"] + 22))
        CARD_MASK = (m, sh.filter(ImageFilter.GaussianBlur(28)))
    return CARD_MASK


def keynote_bg(img):
    bg = blur_small(img, 60, scale=8)
    return Image.fromarray((np.asarray(bg, np.float32) * 0.42).astype(np.uint8))


def frame_card(img, t, shots):
    shot = next(((a, b) for a, b in shots if a <= t < b), None)
    if shot is None or any(a - 0.05 <= shot[0] and shot[1] <= b + 0.05 for a, b in FULL_BLEED):
        return img
    a, b = shot
    mask, shadow = card_mask()
    bg = keynote_bg(img)
    bg = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), bg, shadow.point(lambda v: int(v * 0.55)))
    # card shows the middle of the shot at 4:5, scaled down
    ch_src = W * 5 / 4
    y0 = H * 0.47 - ch_src / 2
    content = img.resize((CARD["w"], CARD["h"]), Image.LANCZOS, box=(0, y0, W, y0 + ch_src))
    u = ease_out((t - a) / 0.38)
    sc = 0.93 + 0.07 * u
    alpha = clamp((t - a) / 0.22)
    if sc < 0.999:
        cw, chh = int(CARD["w"] * sc), int(CARD["h"] * sc)
        content, mask = content.resize((cw, chh), Image.BILINEAR), mask.resize((cw, chh), Image.BILINEAR)
    m = mask.point(lambda v: int(v * alpha)) if alpha < 1 else mask
    x = (W - content.width) // 2
    y = CARD["top"] + (CARD["h"] - content.height) // 2
    bg.paste(content, (x, y), m)
    return bg


# ---------------------------------------------------------------- code-made text cuts

RED_BG, RED, INK = (237, 235, 236), (212, 61, 41), (22, 22, 22)


def split_cut(text):
    """'₹1 CRORE' -> ('₹', 1, 'CRORE', 'after'); 'DAY 2' -> ('', 2, 'DAY', 'before')."""
    parts = text.split()
    for i, p in enumerate(parts):
        digits = "".join(ch for ch in p if ch.isdigit())
        if digits:
            prefix = p[: p.index(digits[0])]
            word = " ".join(parts[:i] + parts[i + 1:])
            return prefix, int(digits), word, "before" if i > 0 else "after"
    return "", 0, text, "after"


def draw_number(d, x, base, n, v, f, color, lh):
    """Odometer: value v (0..n) rolls up digit by digit inside the line box (single digits here)."""
    dgt = int(math.floor(v))
    frac = v - dgt
    for k, off in ((dgt, -frac), (dgt + 1, 1 - frac)):
        if 0 <= k <= n and abs(off) < 1:
            d.text((x, base + off * lh), str(k), font=f, fill=color, anchor="ls")


def text_cut_frame(cut, t, frame, style):
    prefix, n, word, side = split_cut(cut["text"])
    dur = cut["end"] - cut["t"]
    anim = min(0.5, 0.75 * dur)
    if style == "redcard":
        bg = Image.new("RGB", (W, H), RED_BG)
        num_f, word_f, cur_f = (FIG, None, 250), (FIG, None, 250), (SEG_BLACK, None, 250)
        num_c, word_c = RED, INK
    else:
        bg = keynote_bg(frame)
        num_f, word_f, cur_f = (SEG, "Bold Display", 250), (SEG, "Semibold Display", 250), (SEG, "Bold Display", 250)
        num_c, word_c = (255, 255, 255), (190, 156, 255)
    # fit the line into 900 px
    probe_w = (font(*cur_f).getlength(prefix) + font(*num_f).getlength(str(n)) +
               font(*word_f).getlength(" " + word))
    s = min(1.0, 900 / probe_w)
    nf, wf, cf = (font(num_f[0], num_f[1], num_f[2] * s), font(word_f[0], word_f[1], word_f[2] * s),
                  font(cur_f[0], cur_f[1], cur_f[2] * s))
    pw, dw, ww, sp = cf.getlength(prefix), nf.getlength(str(n)), wf.getlength(word), wf.getlength(" ")
    total = pw + dw + sp + ww
    x0 = (W - total) / 2
    base = H * 0.5 + nf.getmetrics()[0] * 0.35
    lh = nf.getmetrics()[0] * 1.1

    def render(tt):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        u = (tt - cut["t"]) / anim
        if side == "after":
            num_x, word_x, wdir = x0, x0 + pw + dw + sp, 1
        else:
            word_x, num_x, wdir = x0, x0 + ww + sp, -1
        # number: rolls up from below inside its own clipped strip
        strip = Image.new("RGBA", (int(pw + dw + 40), int(lh * 1.4)), (0, 0, 0, 0))
        sd = ImageDraw.Draw(strip)
        sb = lh * 1.0
        nu = clamp(u / 0.7)
        roll = (1 - ease_out(nu)) * 1.0
        if prefix:
            sd.text((20, sb + roll * lh), prefix, font=cf, fill=num_c + (255,), anchor="ls")
        if n > 1:
            draw_number(sd, 20 + pw, sb, n, ease_out(nu) * n, nf, num_c + (255,), lh)
        else:
            sd.text((20 + pw, sb + roll * lh), str(n), font=nf, fill=num_c + (255,), anchor="ls")
        layer.alpha_composite(strip, (int(num_x - 20), int(base - sb)))
        # word: letters slide in from its side, staggered
        lx = word_x
        letters = list(word)
        for i, chr_ in enumerate(letters):
            j = i if wdir > 0 else len(letters) - 1 - i
            lu = clamp((u - 0.3 - j * 0.05) / 0.5)
            if lu > 0:
                off = (1 - ease_back(lu, 1.3)) * 120 * wdir
                a = int(255 * clamp(lu * 2.5))
                d.text((lx + off, base), chr_, font=wf, fill=word_c + (a,), anchor="ls")
            lx += wf.getlength(chr_)
        return layer

    # motion blur: average three sub-frame positions
    acc = None
    for k in range(3):
        lay = np.asarray(render(t - k / 75), np.float32)
        acc = lay if acc is None else acc + lay
    lay = Image.fromarray((acc / 3).astype(np.uint8), "RGBA")
    card = bg.convert("RGBA")
    card.alpha_composite(lay)
    card = card.convert("RGB")
    # soft dissolve in 0.1 s and out 0.07 s
    k = min(clamp((t - cut["t"]) / 0.1), clamp((cut["end"] - t) / 0.07))
    return Image.blend(frame, card, k) if k < 1 else card


# ---------------------------------------------------------------- accent SFX (+20%)
# How top short-form editors use SFX: whooshes carry the cuts, pops/clicks land text and graphics, and a
# few accents mark the story beats: a soft impact on the stakes or doubt line, a light ding on the win or
# result. Accents sit in the stretches with no other sound, never stack on a whoosh, and stay well under
# the voice. Both sounds are made here in code (no downloads), with harmonics so phone speakers carry them.

STAKES = {"messed", "failed", "lost", "wrong", "worth", "hit", "doubt", "broke", "scared", "quit", "stuck"}
WINS = {"got", "made", "won", "worked", "finally", "gained", "nothing"}


def write_wav(path, x, sr=48000):
    import wave
    x = np.clip(x / max(np.abs(x).max(), 1e-9) * 0.9, -1, 1)
    pcm = (np.stack([x, x], 1) * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm)


def ensure_sfx(sfx_dir):
    sr = 48000
    imp, ding = sfx_dir / "lab_impact.wav", sfx_dir / "lab_ding.wav"
    if not imp.exists():
        t = np.arange(int(0.9 * sr)) / sr
        f = 52 + (150 - 52) * np.exp(-t / 0.08)                 # pitch falls 150 -> 52 Hz
        ph = 2 * np.pi * np.cumsum(f) / sr
        body = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * (1 - np.exp(-t / 0.003)) * np.exp(-t / 0.22)
        rng = np.random.default_rng(3)
        noise = np.convolve(rng.normal(0, 1, len(t)), np.ones(24) / 24, "same") * np.exp(-t / 0.025)
        write_wav(imp, body + 0.6 * noise / max(np.abs(noise).max(), 1e-9))
    if not ding.exists():
        t = np.arange(int(1.2 * sr)) / sr
        f0 = 1318.5                                            # E6, a clean notification-style bell
        x = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t / tau)
                for r, a, tau in ((1, 1, 0.55), (2.0, 0.3, 0.3), (3.0, 0.12, 0.18), (4.2, 0.06, 0.1)))
        write_wav(ding, x * (1 - np.exp(-t / 0.002)))
    return imp, ding


def plan_accents(words, taken, n, hidden, min_gap=2.5):
    """Pick n accent moments, each as far as possible from every other sound, alternating impact / ding."""
    cands = []
    for i, w in enumerate(words):
        s = w["t"].lower().strip(".,!?")
        prev = words[i - 1]["t"].lower().strip(".,!?") if i else ""
        nxt = " ".join(x["t"] for x in words[i + 1:i + 4])
        if s in STAKES:
            cands.append((w["s"], "impact", w["t"]))
        elif s in WINS and (s != "nothing" or prev == "not") and (s != "got" or any(ch.isdigit() for ch in nxt)):
            cands.append((w["s"], "ding", w["t"]))
    cands = [c for c in cands if not any(x - 0.3 <= c[0] <= y + 0.3 for x, y in hidden)]
    chosen, times, last_kind = [], list(taken), None
    for _ in range(n):
        best = None
        for t, kind, word in cands:
            gap = min((abs(t - x) for x in times), default=99)
            if gap < min_gap or any(t == c[0] for c in chosen):
                continue
            score = gap + (1.5 if kind != last_kind else 0)
            if best is None or score > best[0]:
                best = (score, t, kind, word)
        if not best:
            break
        chosen.append(best[1:])
        times.append(best[1])
        last_kind = best[2]
    return chosen


# ---------------------------------------------------------------- B-roll


def broll_reader(ff, c, fps):
    """Frame source for one B-roll cutaway: the clip from `from`, at `speed`, cover-cropped to 9:16 at the
    Reel's frame rate. Returns a function that hands back the next frame (or the last one if it runs out)."""
    dur = (c["end"] - c["t"]) * c.get("speed", 1.0) + 0.5
    p = subprocess.Popen([ff, "-v", "error", "-ss", str(c.get("from", 0.0)), "-t", f"{dur:.3f}", "-i", str(c["path"]),
                          "-vf", f"setpts=PTS/{c.get('speed', 1.0)},fps={fps},scale={W}:{H}:force_original_aspect_ratio="
                          f"increase:flags=lanczos,crop={W}:{H},setsar=1,format=rgb24",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    last = [None]

    def nxt(fallback):
        buf = p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            last[0] = Image.frombytes("RGB", (W, H), buf)
        return last[0] if last[0] is not None else fallback
    nxt.proc = p
    return nxt


# ---------------------------------------------------------------- main


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # ₹ in cut names vs the Windows console
    ap = argparse.ArgumentParser()
    ap.add_argument("--reel", required=True)
    ap.add_argument("--look", required=True, choices=list(LOOKS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--cuts-at", default="", help="comma list of shot cut times (else detected)")
    ap.add_argument("--seconds", type=float, default=0, help="render only the first N seconds (test)")
    ap.add_argument("--leak", default="", choices=[""] + list(LEAK_COLORS), help="force this video's leak colour")
    a = ap.parse_args()
    L = dict(LOOKS[a.look])
    cfg = json.loads((ROOT / "config.json").read_text())
    ff = cfg["ffmpeg"]
    reel = Path(a.reel) if Path(a.reel).is_absolute() else ROOT / a.reel
    if L["transition"] == "leak" and a.look == "v2":
        L["leak_tint"] = pick_leak(reel.name, a.leak)
        print(f"  light leak colour for this video: {L['leak_tint']}")
    video = json.loads((reel / "source.json").read_text())["video"]
    words = tr.tidy_words(json.loads((reel / "words.json").read_text(encoding="utf-8"))["words"])
    wins = caption_windows(tr.chunk(words), L)
    sections = tr.load_sections(reel / "sections.json")
    from cuts import find_cuts
    scene = [float(x) for x in a.cuts_at.split(",")] if a.cuts_at else find_cuts(ff, video)
    fps = tr.probe(ff, video, "v:0", "r_frame_rate")
    num, den = (fps.split("/") + ["1"])[:2]
    fps_f = float(num) / float(den)
    dur = float(tr.probe(ff, video, "v:0", "duration"))
    shots = list(zip([0.0] + scene, scene + [dur + 1]))

    tcuts = []
    if L["textcut"]:
        for c in json.loads((reel / "cuts.json").read_text(encoding="utf-8")):
            tcuts.append({**c, "end": max(c["end"], c["t"] + 0.8)})   # a code card needs ~0.8 s to read
    # his Flow clips: typography cards are laid over everything by ffmpeg (auto-timed to the spoken words,
    # captions step aside); B-roll is laid in here in Python, under the captions, which keep running
    import fx
    flow, broll, planned_pops, planned_broll = [], [], [], []
    if L.get("flow_cuts"):
        for s in json.loads((reel / "cuts.json").read_text(encoding="utf-8")):
            is_broll = s.get("kind") == "broll"
            (planned_broll if is_broll else planned_pops).append(s["t"])
            p = reel / s["file"]
            if not p.exists():
                print(f"  cut:    {s['file']:8} not generated yet, {s['t']:.2f}s stays on the footage")
                continue
            c = {**s, "path": p.resolve()}
            if c.get("from") == "auto" or c.get("speed") == "auto":
                c = fx.auto_time(ff, c)
            (broll if is_broll else flow).append(c)
            print(f"  {'broll' if is_broll else 'cut'}:{'' if is_broll else '  '}  {s['file']:8} "
                  f"\"{s.get('text', '')}\" at {s['t']:.2f}-{s['end']:.2f}s")
    # in-scene visuals (Omni edits of his own shot), fitted to the exact segment he uploaded
    edits = []
    if L.get("flow_cuts") and (reel / "edits.json").exists():
        for e in json.loads((reel / "edits.json").read_text(encoding="utf-8")):
            path = reel / e["file"]
            if not path.exists():
                print(f"  visual: {e['file']:8} not generated yet, {e['t']:.2f}-{e['end']:.2f}s stays original")
                continue
            clip_dur = float(tr.probe(ff, path, "v:0", "duration"))
            seg = reel / e.get("segment", "")
            d = float(tr.probe(ff, seg, "v:0", "duration")) if e.get("segment") and seg.exists() else e["end"] - e["t"]
            if abs(clip_dur / d - 1) > 0.2:
                print(f"  visual: {e['file']:8} is {clip_dur:.2f}s for a {d:.2f}s slot, skipped (check it in Flow)")
                continue
            t_snap = math.ceil(e["t"] * fps_f - 1e-6) / fps_f
            edits.append({**e, "t": round(t_snap, 4), "path": path.resolve(), "dur": d, "clip_dur": clip_dur})
            print(f"  visual: {e['file']:8} at {e['t']:.2f}-{e['end']:.2f}s (fitted x{d / clip_dur:.3f})")
    hidden = [(c["t"], c["end"]) for c in tcuts + flow]
    covered = hidden + [(c["t"], c["end"]) for c in broll]
    trans_cuts = [c for c in scene if not any(x - 0.2 <= c <= y + 0.2 for x, y in covered)]
    trans_cuts = sorted(trans_cuts + [x for c in broll for x in (c["t"], c["end"])])   # glow into and out of B-roll
    keys = fx.plan_zoom(sections, scene, words) if L.get("zoom") else []

    # sound: whooshes and pops, each a different file or pitch from the one before
    sfx_dir = ROOT / "sfx"
    events = []
    wt = tr.whoosh_times(sections, scene) if L["whoosh"] == "sections" else trans_cuts
    # a B-roll cutaway gets its own whoosh unless another sound already sits on it
    bw = [t for t in planned_broll if all(abs(t - x) > 1.2 for x in list(wt) + planned_pops)]
    wt = sorted(list(wt) + bw)
    for k, t in enumerate(wt):
        events.append((t, sfx_dir / tr.WHOOSHES[k % 3], L["whoosh_db"], [0, -1, 1, -2, 2][k % 5]))
    for k, c in enumerate(sorted(tcuts + flow, key=lambda c: c["t"])):
        events.append((c["t"], sfx_dir / tr.POPS[k % 3], -12, [0, 2, -2][k % 3]))
    if L.get("accents"):
        # +20% on the planned sounds (whooshes + one pop per text cut, made or not, so the plan stays put)
        taken = list(wt) + (planned_pops or [c["t"] for c in tcuts])
        n_extra = max(1, round(L["accents"] * len(taken)))
        imp, ding = ensure_sfx(sfx_dir)
        for t, kind, word in plan_accents(words, taken, n_extra, hidden):
            events.append((t, imp if kind == "impact" else ding, -12 if kind == "impact" else -15, 0))
            print(f"  accent: {kind:6} on \"{word}\" at {t:.2f}s")
        print(f"  sfx: {len(taken)} planned + {n_extra} accents")

    out = Path(a.out).resolve()
    inputs = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-framerate", fps, "-i", "-", "-i", video]
    fc = "[0:v]scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[vb]"
    n_in, vlast = 2, "vb"
    if flow:
        bargs, bfc, vlast = fx.cut_filters(flow, n_in, fps, W, H, "vb")
        inputs += bargs
        n_in += len(flow)
        fc += bfc
    fc += f";[{vlast}]format=yuv420p[v]"
    fc += f";[1:a]{tr.loudnorm_filter(ff, video)},aformat=sample_rates=48000:channel_layouts=stereo[voice]"
    mix = ["[voice]"]
    for k, (t, path, db, semis) in enumerate(sorted(events, key=lambda e: e[0])):
        peak_t, peak_amp = tr.sfx_peak(ff, path)
        ratio = 2 ** (semis / 12)
        peak_t /= ratio
        gain = 10 ** (db / 20) / max(peak_amp, 1e-4)
        lead = t - peak_t
        trim = f"atrim=start={-lead:.3f},asetpts=PTS-STARTPTS," if lead < 0 else ""
        delay = max(lead, 0) * 1000
        sr = tr.probe(ff, path, "a:0", "sample_rate")
        pitch = f"asetrate={sr}*{ratio:.4f}," if abs(ratio - 1) > 1e-3 else ""
        inputs += ["-i", str(path)]
        fc += (f";[{n_in}:a]{pitch}aresample=48000,{trim}aformat=sample_rates=48000:channel_layouts=stereo,"
               f"volume={gain:.3f},adelay={delay:.0f}|{delay:.0f}[s{k}]")
        mix.append(f"[s{k}]")
        n_in += 1
    fc += (f";{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,{tr.LIMITER}[a]" if len(mix) > 1
           else f";[voice]{tr.LIMITER}[a]")
    limit = ["-t", str(a.seconds)] if a.seconds else []
    enc = subprocess.Popen([ff, "-hide_banner", "-loglevel", "error", "-y", *inputs, "-filter_complex", fc,
                            "-map", "[v]", "-map", "[a]", *limit, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                            "-color_range", "tv", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            str(out)], stdin=subprocess.PIPE)
    if edits:
        # his footage with the Omni-edited shots laid in at their exact slots, then to RGB
        eargs, efc, elast = fx.edit_filters(edits, W, H, fps)
        eargs[1] = video
        dcmd = [ff, "-v", "error", *eargs, "-filter_complex",
                efc + f";[{elast}]scale=in_color_matrix=bt709:in_range=tv,format=rgb24[o]", "-map", "[o]"]
    else:
        dcmd = [ff, "-v", "error", "-i", video, "-vf",
                f"scale={W}:{H}:flags=lanczos:in_color_matrix=bt709:in_range=tv,setsar=1,format=rgb24"]
    dec = subprocess.Popen(dcmd + [*limit, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    readers = {}
    size = W * H * 3
    n = 0
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        t = n / fps_f
        img = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1)
        z = fx.zoom_at(t, keys) if keys else 1.0
        if z > 1.0005:   # the approved subtle drift: 1.00 -> 1.06 per sentence, anchored at mouth height
            zw, zh = W / z, H / z
            x0, y0 = (W - zw) * 0.5, (H - zh) * fx.ZOOM_Y
            img = img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + zw, y0 + zh))
        b = next((c for c in broll if c["t"] <= t < c["end"]), None)
        if b:
            if b["file"] not in readers:
                readers[b["file"]] = broll_reader(ff, b, fps)
            frame_b = readers[b["file"]](img)
            k = min(clamp((t - b["t"]) / 0.1), clamp((b["end"] - t) / 0.07))   # same soft cut as text cuts
            img = Image.blend(img, frame_b, k) if k < 1 else frame_b
        if L["frame"] == "card":
            img = frame_card(img, t, shots)
        img = transition(img, t, trans_cuts, L)
        img = grade(img, L, n)
        cut = next((c for c in tcuts if c["t"] <= t < c["end"]), None)
        if cut:
            img = text_cut_frame(cut, t, img, L["textcut"])
        img = draw_captions(img, t, wins, L, hidden)
        enc.stdin.write(img.tobytes())
        n += 1
        if n % 250 == 0:
            print(f"  {a.look}: {n} frames", flush=True)
    for r in readers.values():   # each B-roll decoder only had to give up its window's frames
        r.proc.kill()
    enc.stdin.close()
    dec.wait()
    if enc.wait() != 0:
        raise SystemExit("encode failed")
    print(f"wrote {out} ({n} frames)")


if __name__ == "__main__":
    main()
