"""Find the punchy moments in any talking-head transcript and draft Flow prompts for text cutaways.

Picks 2-3 moments per Reel (about one per 15-20 s), strongly preferring numbers ("Day N", money,
counts) because the one approved animation is the "17 TRADES" count-up + slide. Each cut lasts
exactly as long as he is saying those words. Writes:
  cuts.json         slots the renderer cuts to   {file, t, end, from, speed, text, kind}
  text cuts.txt     one Flow prompt per slot, all in the same style pack
Claude reviews both before Aarit spends Flow credits; see FLOW.md for the rules."""
import argparse, json, re
from pathlib import Path

NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
             "nine": 9, "ten": 10, "hundred": 100, "thousand": 1000}
MONEY_UNITS = {"crore": "CRORE", "crores": "CRORE", "lakh": "LAKH", "lakhs": "LAKH", "k": "K"}
LOSS = {"lose", "lost", "losing", "down", "minus", "burned", "burnt"}
CLAIMS = {"automated": "AUTOMATED", "automatic": "AUTOMATIC", "free": "FREE", "illegal": "ILLEGAL",
          "insane": "INSANE", "secret": "SECRET", "nobody": "NOBODY", "never": "NEVER", "zero": "ZERO"}
LIVE = re.compile(r"\b(real time|live)\b", re.I)
# numbers first: the approved look is a count-up, which only shines when there is a number to count
SCORE = {"stamp": 5, "count": 4, "money": 4, "cta": 3, "live": 1, "claim": 1}
MIN_GAP = 8.0             # with only 2-3 cuts, keep them well apart
MIN_LEN, MAX_LEN = 0.4, 1.6   # the cut is the spoken span; the floor only stops a one-frame flicker
SECS_PER_CUT = 16         # 33 s Reel -> 2 cuts, 45 s -> 3


def cuts_for(duration):
    return max(2, min(3, round(duration / SECS_PER_CUT)))


def clean(w):
    return w["t"].strip().strip(".,!?\"").lower()


def number(w):
    t = clean(w).replace(",", "")
    if t.isdigit():
        return int(t)
    return NUM_WORDS.get(t)


def fmt(n):
    return f"{n:,}"


def phrase_end(words, i, max_words=4):
    """End time of the phrase that starts at word i: stop at punctuation or after a few words."""
    j = i
    while j < len(words) - 1 and j - i < max_words - 1 and words[j]["t"][-1:] not in ".,!?":
        j += 1
    return words[j]["e"]


def candidates(words):
    out = []
    joined = " ".join(clean(w) for w in words)
    for i, w in enumerate(words):
        c, n = clean(w), number(w)
        nxt = clean(words[i + 1]) if i + 1 < len(words) else ""
        prev = clean(words[i - 1]) if i else ""
        if c == "day" and i + 1 < len(words) and number(words[i + 1]) is not None:
            out.append(("stamp", f"DAY {number(words[i + 1])}", w["s"], words[i + 1]["e"]))
        elif n is not None and prev != "day":
            if nxt in MONEY_UNITS:
                out.append(("money", f"₹{fmt(n)} {MONEY_UNITS[nxt]}", w["s"], phrase_end(words, i, 3)))
            elif nxt in {"rupees", "rupee"} or n >= 1000:
                sign = "-" if prev in LOSS or (i > 1 and clean(words[i - 2]) in LOSS) else ""
                out.append(("money", f"{sign}₹{fmt(n)}", words[i - 1]["s"] if sign else w["s"], phrase_end(words, i, 3)))
            elif nxt and nxt.isalpha() and nxt not in {"of", "to", "and", "in", "on", "the", "a"} and n > 1:
                raw = words[i + 1]["t"].strip().strip(".,!?\"")
                noun = raw if any(ch.isupper() for ch in raw) else raw.upper()   # keep "AIs", don't make "AIS"
                out.append(("count", f"{fmt(n)} {noun}", w["s"], words[i + 1]["e"]))
        elif c in CLAIMS:
            out.append(("claim", CLAIMS[c], w["s"], w["e"]))
        if c == "comment" and i + 3 < len(words) and clean(words[i + 1]) in {"the", "word"}:
            k = i + 3 if clean(words[i + 2]) == "word" else i + 2
            out.append(("cta", f"COMMENT {clean(words[k]).upper()}", w["s"], words[k]["e"]))
    for m in LIVE.finditer(joined):
        idx = joined[: m.start()].count(" ")
        if idx < len(words):
            out.append(("live", "LIVE", words[idx]["s"], words[min(idx + 1, len(words) - 1)]["e"]))
    return out


def score(c):
    kind, text, s, e = c
    bonus = 1 if kind == "count" and int(re.sub(r"\D", "", text.split()[0]) or 0) >= 10 else 0   # "17 TRADES" > "3 AIs"
    return SCORE[kind] + bonus


def pick(cands, blocked, n_max, only=None):
    """Highest-scoring moments first, at least MIN_GAP apart, never on his own cards or in-scene edits.
    `only` lets Claude override after review: keep exactly these texts (first occurrence of each)."""
    if only:
        seen, chosen = set(), []
        for c in sorted(cands, key=lambda c: c[2]):
            if c[1] in only and c[1] not in seen:
                seen.add(c[1])
                chosen.append(c)
        return chosen
    chosen = []
    for kind, text, s, e in sorted(cands, key=lambda c: (-score(c), c[2])):
        if any(a - 0.2 < s < b for a, b in blocked):
            continue
        if any(abs(s - c[2]) < MIN_GAP for c in chosen):
            continue
        chosen.append((kind, text, s, e))
        if len(chosen) == n_max:
            break
    return sorted(chosen, key=lambda c: c[2])


# ---------- prompts ----------

STYLE_PACKS = {
    # matches the red-on-white cards already in his Premiere edits (sampled from hedge 1)
    "red_card": ("clean flat warm off-white background (#EDEBEC), text in a heavy, slightly rounded modern "
                 "sans-serif in the style of Figtree ExtraBold, in a warm brand red (#D43D29), any secondary "
                 "element in near-black (#161616), flat 2D design with crisp edges, no gradients, no 3D, "
                 "smooth motion blur on fast moves"),
}

def animation(text):
    """The one approved look (the "17 TRADES" cut): the number counts up, the words slide in beside it.
    Text without a number gets the same slide, word by word, so every cut feels like one system."""
    parts = text.split()
    nums = [p for p in parts if re.search(r"\d", p)]
    words = [p for p in parts if not re.search(r"\d", p)]
    if nums:
        n = nums[0]
        count = (f"the number \"{n}\" counts up smoothly from zero to {n.lstrip('-')}, its digits rolling vertically "
                 f"like an odometer and easing to a stop") if re.sub(r"\D", "", n) not in {"0", "1"} else \
                f"the \"{n}\" rolls up into place from below like an odometer digit and eases to a stop"
        if not words:
            return count
        before = parts.index(words[0]) < parts.index(n)          # "DAY 1": the word sits left of the number
        many = len(words) > 1
        slide = (f"; as the number lands, the word{'s' if many else ''} \"{' '.join(words)}\" "
                 f"slide{'' if many else 's'} in from the {'left' if before else 'right'} "
                 f"{'before' if before else 'beside'} it, letters staggered a couple of frames apart, and "
                 f"settle{'' if many else 's'} into place")
        return count + slide
    return (f"the words \"{text}\" slide in from the right one after another, staggered a couple of frames "
            f"apart, each easing into place") if len(parts) > 1 else \
        f"the word \"{text}\" slides in from the right, its letters staggered a couple of frames apart, and settles"


AE_FEEL = ("Every move uses smooth After Effects Easy Ease curves (slow in, slow out) with a gentle overshoot and "
           "settle, natural motion blur on fast movement, and nothing moves linearly, so it feels buttery smooth "
           "and premium like a polished After Effects template, never jerky.")


def spelled(text):
    return " ".join("space" if ch == " " else ("the Indian rupee sign" if ch == "₹" else ch) for ch in text)


def prompt(kind, text, style):
    return (f"Vertical 9:16 motion graphics clip, a polished After Effects kinetic typography animation, about "
            f"3 seconds. {STYLE_PACKS[style][0].upper() + STYLE_PACKS[style][1:]}. The only text on screen is "
            f"\"{text}\", spelled exactly: {spelled(text)}. Centred in the frame, large, filling about two thirds "
            f"of the width, on one line. Animation, all finished within the first 0.8 seconds: {animation(text)}. "
            f"{AE_FEEL} After that the text holds perfectly still until the end. Nothing else on screen: no other "
            f"words, letters, numbers, logos, watermarks, people or objects.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reel", required=True, help="reels/<name> folder with words.json and sections.json")
    ap.add_argument("--n", type=int, default=0, help="number of cuts; default 2-3 from the Reel's length")
    ap.add_argument("--style", default="red_card", choices=sorted(STYLE_PACKS))
    ap.add_argument("--only", default="", help="after review: exact texts to keep, separated by |")
    a = ap.parse_args()
    reel = Path(a.reel)
    words = [{"t": (w["w"] if "w" in w else w["t"]), "s": w["s"], "e": w["e"]}
             for w in json.loads((reel / "words.json").read_text(encoding="utf-8"))["words"]]
    # Whisper splits "47,000" into "47" + ",000"
    merged = []
    for w in words:
        if merged and re.fullmatch(r"\s*[,.]\d+[.,]?", w["t"]):
            merged[-1] = {**merged[-1], "t": merged[-1]["t"].strip() + w["t"].strip(), "e": w["e"]}
        else:
            merged.append({**w, "t": w["t"].strip()})
    sections = json.loads((reel / "sections.json").read_text())["sections"]
    blocked = [(s["start"], s["end"]) for s in sections if s["kind"] == "card" and s["end"] - s["start"] > 0.4]
    edits = reel / "edits.json"
    if edits.exists():
        blocked += [(e["t"], e["end"]) for e in json.loads(edits.read_text(encoding="utf-8"))]

    cands = candidates(merged)
    for c in cands:
        print(f"  candidate {c[0]:6} {c[1]:18} {c[2]:6.2f}s")
    n = a.n or cuts_for(sections[-1]["end"])
    chosen = pick(cands, blocked, n, [t.strip() for t in a.only.split("|")] if a.only else None)
    cuts, lines = [], [f"TEXT CUTAWAYS FOR \"{reel.name}\" | style: {a.style} | {len(chosen)} cuts\n",
                       "Generate each in Flow (text to video), download into this folder with the exact name, "
                       "then tell Claude. Check the spelling before saving: AI video sometimes garbles letters.\n"
                       "The renderer times each clip automatically so its animation finishes just as you finish "
                       "saying the words, so the clip's own length doesn't matter.\n"]
    for k, (kind, text, s, e) in enumerate(chosen, 1):
        # exactly the span he is saying it: from the first word's start to the last word's end
        t0 = round(max(0.0, s), 2)
        t1 = round(min(max(e, t0 + MIN_LEN), t0 + MAX_LEN), 2)
        name = f"T{k}.mp4"
        cuts.append({"file": name, "t": t0, "end": t1, "from": "auto", "speed": "auto", "text": text, "kind": kind})
        lines.append(f"\n{name}   cuts in at {t0:.2f}s for {t1 - t0:.1f}s   ({kind}: \"{text}\")\n\n{prompt(kind, text, a.style)}\n")
        print(f"  PICK {name} {kind:6} {text:18} {t0:6.2f}-{t1:.2f}s")
    (reel / "cuts.json").write_text(json.dumps(cuts, indent=1, ensure_ascii=False), encoding="utf-8")
    (reel / "text cuts.txt").write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
