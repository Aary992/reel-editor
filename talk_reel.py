"""The previous locked look (until 10-18), kept for reference. Its helpers (transcript tidy-up, caption
chunking, sections, loudness, SFX, his on-screen text) are what render.py builds on, so keep this file."""
import argparse, json, math, os, re, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from cuts import find_cuts
import fx

W, H = 1080, 1920
CAP_FONT = "Figtree Light ExtraBold"   # Fontsource's (odd) full name for Figtree 800
CAP_SIZE = 82.8                        # 55.2 per 720 width, matched against the inspo
CAP_Y = {"face": 0.70, "split": 0.385}  # just under the mouth / above the split seam
MAX_WORDS, MAX_CHARS = 3, 21
HOLD_GAP = 0.8                         # keep a caption up through pauses shorter than this
CAP_FADE_IN, CAP_FADE_OUT = 90, 70     # ms; soft iOS-style in/out instead of a hard pop
CAP_SETTLE, CAP_RISE = 160, 8          # ms to settle, px the caption rises while it settles
TITLE_Y = 0.13
TITLE_FONT = str(Path(__file__).parent / "fonts" / "figtree-700" / "figtree-700.ttf")   # same family as captions
EMOJI_FONT = r"C:\Windows\Fonts\seguiemj.ttf"
TITLE_PX = 60                          # inspo title line spans ~62.5% of the frame width
KEEP_CAPS = {"I", "AIs", "AI", "Crore", "Claude"}


def ts(t):
    t = max(t, 0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def load_sections(path, min_len=0.4):
    secs = json.loads(Path(path).read_text())["sections"]
    out, pending = [], None
    for idx, s in enumerate(secs):
        s = dict(s)
        if s["end"] - s["start"] < min_len:
            # flash frames at a cut belong to the shot that follows (or the last shot, at the very end)
            pending = pending if pending is not None else s["start"]
            if idx == len(secs) - 1 and out:
                out[-1]["end"] = s["end"]
            continue
        if pending is not None:
            s["start"], pending = pending, None
        if out and out[-1]["kind"] == s["kind"]:
            out[-1]["end"] = s["end"]
        else:
            out.append(s)
    merged = []
    for s in out:
        k = "face" if s["kind"] == "black" else s["kind"]
        if merged and merged[-1]["kind"] == k:
            merged[-1]["end"] = s["end"]
        else:
            merged.append({**s, "kind": k})
    return merged


def tidy_words(raw):
    words = []
    for x in raw:
        text = x["w"].strip()
        # Whisper splits "83,000" into "83" + ",000"
        if words and re.fullmatch(r"[,.]\d+[.,]?", text):
            words[-1]["t"] += text
            words[-1]["e"] = x["e"]
            continue
        if words and words[-1]["t"].endswith(",") and text[:1].isupper() and text not in KEEP_CAPS and not text.isupper():
            text = text[0].lower() + text[1:]
        words.append({"t": text, "s": x["s"], "e": x["e"], "p": x.get("p", 1.0)})
    return words


def display(t):
    return t.rstrip(".,;:")


WEAK_END = {"the", "a", "an", "of", "to", "in", "on", "at", "for", "and", "or", "but", "my", "your",
            "our", "their", "his", "her", "is", "are", "was", "were", "be", "i", "i'm", "i've", "i'll",
            "that", "this", "by", "with", "from", "as", "if", "so", "than", "any", "all", "each",
            "very", "really", "literally", "barely", "don't", "can", "will", "just"}
PHRASE_START = WEAK_END | {"then", "it", "when", "because", "who", "which", "today",
                           "barely", "completely", "absolutely", "never", "always"}
FLOATING = {"each", "all", "any"}  # "1 Crore each | to trade" is fine, "that each | AI" is not


def chunk_cost(ws, j, i, clause):
    """Cost of showing clause[j:i] as one caption; None if it doesn't fit."""
    n = len(clause)
    text = " ".join(display(w["t"]) for w in ws)
    if len(ws) > MAX_WORDS + 1 or (len(ws) > 1 and len(text) > MAX_CHARS):
        return None
    cost = 1                                     # every extra caption costs a little: favour full lines
    cost += {1: 0 if n == 1 else 3, 2: 0, 3: 0, 4: 1}[len(ws)]
    if len(text) > 17:
        cost += 0.5
    for a, b in zip(ws, ws[1:]):
        if b["s"] - a["e"] >= 0.35:              # never hold a caption across a real pause
            cost += 3
    if any(display(w["t"]).lower() in {"and", "or", "but", "then", "so"} for w in ws[1:]):
        cost += 3                                # "curve and all" straddles two phrases
    if i < n:                                    # the break after this chunk
        last, nxt = ws[-1], clause[i]
        last_word, nxt_word = display(last["t"]).lower(), display(nxt["t"]).lower()
        if last_word in WEAK_END and not (last_word in FLOATING and nxt_word in PHRASE_START):
            cost += 4
        if re.fullmatch(r"[\d,.]+", last_word) and nxt["t"][:1].isalpha() and nxt_word not in WEAK_END:
            cost += 6                            # keep "3 AIs", "17 trades" together
        if nxt_word in PHRASE_START:
            cost -= 0.5                          # spoken phrases tend to start on these
        if nxt["s"] - last["e"] >= 0.25:
            cost -= 2                            # break where he actually pauses
    return cost


def chunk(words):
    """2-3 word captions (4 if short), broken at clause ends and natural phrase edges."""
    clauses, cur = [], []
    for w in words:
        cur.append(w)
        if w["t"][-1:] in ".,!?":
            clauses.append(cur)
            cur = []
    if cur:
        clauses.append(cur)
    out = []
    for clause in clauses:
        n = len(clause)
        best = [(0, None)] + [(float("inf"), None)] * n
        for i in range(1, n + 1):
            # shortest last chunk first, so ties keep words with the phrase before ("The second one | lost")
            for j in range(i - 1, max(0, i - MAX_WORDS - 1) - 1, -1):
                c = chunk_cost(clause[j:i], j, i, clause)
                if c is not None and best[j][0] + c < best[i][0]:
                    best[i] = (best[j][0] + c, j)
        cuts, i = [], n
        while i > 0:
            j = best[i][1]
            cuts.append(clause[j:i])
            i = j
        out.extend(reversed(cuts))
    return out


def pieces(start, end, sections, blocked=()):
    """Split [start, end) at section boundaries; drop the parts that fall on text cards or text cutaways."""
    for s in sections:
        a, b = max(start, s["start"]), min(end, s["end"])
        if b - a <= 0.05 or s["kind"] == "card":
            continue
        spans = [(a, b)]
        for x, y in blocked:   # a cutaway already shows the word, so the caption steps aside
            spans = [p for lo, hi in spans for p in ((lo, min(hi, x)), (max(lo, y), hi)) if p[1] - p[0] > 0.05]
        for lo, hi in spans:
            yield lo, hi, s["kind"]


def build_ass(chunks, sections, blocked=()):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{CAP_FONT},{CAP_SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for ci, ch in enumerate(chunks):
        start, end = ch[0]["s"], ch[-1]["e"] + 0.15
        if ci + 1 < len(chunks):
            nxt = chunks[ci + 1][0]["s"]
            end = nxt if nxt - ch[-1]["e"] < HOLD_GAP else min(end, nxt)
        text = " ".join(display(w["t"]) for w in ch)
        for a, b, kind in pieces(start, end, sections, blocked):
            y = round(H * CAP_Y[kind])
            x = W // 2
            # iOS-style entrance: quick fade, 8 px rise and a 94% -> 100% settle on an ease-out curve
            spring = f"\\fad({CAP_FADE_IN},{CAP_FADE_OUT})\\fscx94\\fscy94\\t(0,{CAP_SETTLE},0.5,\\fscx100\\fscy100)"
            ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\move({x},{y + 4 + CAP_RISE},{x},{y + 4},0,{CAP_SETTLE})"
                      f"{spring}\\c&H000000&\\1a&H60&\\blur8}}{text}")
            ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\move({x},{y + CAP_RISE},{x},{y},0,{CAP_SETTLE})"
                      f"{spring}}}{text}")
    return head + "\n".join(ev) + "\n"


def build_title(lines, emoji, out_png):
    """Full-frame transparent PNG: IG-Classic-style title, thin dark edge + soft shadow, colour emoji."""
    font = ImageFont.truetype(TITLE_FONT, TITLE_PX)
    efont = ImageFont.truetype(EMOJI_FONT, 109)          # Segoe UI Emoji renders colour at 109px
    line_h = round(TITLE_PX * 1.18)    # inspo title lines sit tight together
    top = round(H * TITLE_Y - line_h * len(lines) / 2)
    e_img = None
    if emoji:
        e_img = Image.new("RGBA", (320, 320), (0, 0, 0, 0))   # roomy canvas so nothing clips
        ImageDraw.Draw(e_img).text((40, 40), emoji, font=efont, embedded_color=True)
        e_img = e_img.crop(e_img.getbbox())
        eh = round(TITLE_PX * 0.95)
        e_img = e_img.resize((round(e_img.width * eh / e_img.height), eh), Image.LANCZOS)
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td, sd = ImageDraw.Draw(text_layer), ImageDraw.Draw(shadow)
    emoji_pos = None
    for i, line in enumerate(lines):
        tw = font.getlength(line)
        gap = round(TITLE_PX * 0.25)
        extra = (e_img.width + gap) if (e_img and i == len(lines) - 1) else 0
        x = (W - tw - extra) / 2
        y = top + i * line_h
        sd.text((x, y + 3), line, font=font, fill=(0, 0, 0, 150), stroke_width=3, stroke_fill=(0, 0, 0, 150))
        td.text((x, y), line, font=font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 90))
        if extra:
            _, y0, _, y1 = font.getbbox(line)          # centre the emoji on the drawn glyphs
            emoji_pos = (round(x + tw + gap), round(y + (y0 + y1) / 2 - e_img.height / 2))
    canvas = shadow.filter(ImageFilter.GaussianBlur(5))
    canvas.alpha_composite(text_layer)
    if emoji_pos:
        canvas.alpha_composite(e_img, emoji_pos)
    canvas.save(out_png)


LOUDNESS = "I=-14:TP=-1.5:LRA=11"    # what Instagram and YouTube normalise speech towards


def loudnorm_filter(ffmpeg, video):
    """Two-pass loudnorm: measure first, then correct with the measured values."""
    r = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-i", video, "-vn",
                        "-af", f"loudnorm={LOUDNESS}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"): r.stderr.rindex("}") + 1])
    print(f"  loudness in: {m['input_i']} LUFS, true peak {m['input_tp']} dBTP")
    return (f"loudnorm={LOUDNESS}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
            f"offset={m['target_offset']}:linear=true,aresample=48000")


LIMITER = "alimiter=limit=0.75:attack=5:release=50:level=false"   # -2.5 dB, leaves room for AAC overshoot
WHOOSHES = ["whoosh_fast_1490.wav", "whoosh_cinematic_1492.wav", "whoosh_air_1489.wav"]
POPS = ["pop_light_3005.wav", "pop_dry_2356.wav", "pop_hard_click_2364.wav"]
TEXT_POP = "pop_light_3005.wav"
SFX_PEAK_DB = {"whoosh": -10, "pop": -12}  # well under the voice, which peaks around -2.5 dB


def sfx_peak(ffmpeg, path):
    """Where a sound effect hits hardest, so that moment can land exactly on the cut."""
    raw = subprocess.run([ffmpeg, "-v", "error", "-i", str(path), "-map", "0:a", "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = np.abs(np.frombuffer(raw, np.int16).astype(np.float32) / 32768)
    hop = 160
    env = x[: len(x) // hop * hop].reshape(-1, hop).max(axis=1)
    i = int(env.argmax())
    return i * hop / 16000, float(env[i])


def probe(ffmpeg, path, stream, field):
    """One stream field via the ffprobe that sits next to ffmpeg (e.g. probe(ff, v, 'v:0', 'r_frame_rate'))."""
    p = Path(ffmpeg)
    ffprobe = str(p.with_name(p.name.replace("ffmpeg", "ffprobe"))) if p.parent != Path(".") else "ffprobe"
    r = subprocess.run([ffprobe, "-v", "error", "-select_streams", stream, "-show_entries", f"stream={field}",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return r.stdout.strip().splitlines()[0].strip(",")


def whoosh_times(sections, scene_cuts):
    """Whoosh only where the shot type changes (face -> card -> split ...), snapped to the real cut frame."""
    out = []
    for prev, cur in zip(sections, sections[1:]):
        t = cur["start"]
        near = [c for c in scene_cuts if abs(c - t) <= 0.3]
        out.append(min(near, key=lambda c: abs(c - t)) if near else t)
    return out


def sfx_events(ffmpeg, sfx_dir, sections, scene_cuts, text_start, cut_starts):
    """Every sound gets a different file or pitch from the one before it, so nothing repeats.
    Shot changes get whooshes; text cutaways get pops, cycling files and stepping the pitch."""
    events = []
    for k, t in enumerate(whoosh_times(sections, scene_cuts)):
        # cycle the whooshes; on a second lap shift the pitch so it still sounds different
        events.append((t, sfx_dir / WHOOSHES[k % len(WHOOSHES)], "whoosh", -2.0 * (k // len(WHOOSHES))))
    for k, t in enumerate(sorted(cut_starts)):
        events.append((t, sfx_dir / POPS[k % len(POPS)], "pop", [0, 2, -2, 4, -1][k % 5]))
    if text_start is not None:
        events.append((text_start, sfx_dir / TEXT_POP, "pop", 0.0))
    for t, path, kind, semis in sorted(events, key=lambda e: e[0]):
        peak_t, peak_amp = sfx_peak(ffmpeg, path)
        ratio = 2 ** (semis / 12)
        gain = 10 ** (SFX_PEAK_DB[kind] / 20) / max(peak_amp, 1e-4)
        yield t, path, peak_t / ratio, gain, kind, ratio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--words", required=True)
    ap.add_argument("--sections", required=True)
    ap.add_argument("--text", default="", help="Aarit's own on-screen text, lines separated by |; omit for none")
    ap.add_argument("--text-start", type=float, default=0.0)
    ap.add_argument("--text-secs", type=float, default=3.0, help="clamped to 1-4 seconds")
    ap.add_argument("--emoji", default="")
    ap.add_argument("--fontsdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ffmpeg", default="ffmpeg")
    ap.add_argument("--sfx-dir", default=str(Path(__file__).parent / "sfx"))
    ap.add_argument("--no-sfx", action="store_true")
    ap.add_argument("--cuts", default="", help="cuts.json from moments.py: text cutaways {file, t, end, from, speed}")
    ap.add_argument("--edits", default="", help="JSON list of Flow-edited segments: {file, t, end}; files next to it")
    ap.add_argument("--no-zoom", action="store_true")
    a = ap.parse_args()

    out = Path(a.out).resolve()
    video = str(Path(a.video).resolve())
    sections = load_sections(a.sections)
    for s in sections:
        print(f"  {s['kind']:6} {s['start']:6.2f} -> {s['end']:6.2f}")
    words = tidy_words(json.loads(Path(a.words).read_text(encoding="utf-8"))["words"])
    chunks = chunk(words)
    print("  captions:", " | ".join(" ".join(display(w["t"]) for w in c) for c in chunks))
    scene_cuts = find_cuts(a.ffmpeg, video)
    fps = probe(a.ffmpeg, video, "v:0", "r_frame_rate")
    num, den = (fps.split("/") + ["1"])[:2]
    fps_f = float(num) / float(den)
    cuts = []
    for s in (json.loads(Path(a.cuts).read_text(encoding="utf-8")) if a.cuts else []):
        path = Path(a.cuts).parent / s["file"]
        if path.exists():
            c = {**s, "path": path.resolve()}
            if c.get("from") == "auto" or c.get("speed") == "auto":
                c = fx.auto_time(a.ffmpeg, c)
            cuts.append(c)
            anim = f" (clip animates {c['anim'][0]}-{c['anim'][1]}s -> from {c['from']}s at x{c['speed']})" if "anim" in c else ""
            print(f"  cut:    {s['file']:8} \"{s.get('text', '')}\" at {s['t']:6.2f}-{s['end']:.2f}s{anim}")
        else:
            print(f"  cut:    {s['file']:8} not generated yet, {s['t']:.2f}s stays on you")

    ass = out.with_suffix(".ass")
    ass.write_text(build_ass(chunks, sections, [(c["t"], c["end"]) for c in cuts]), encoding="utf-8")
    fontsdir = Path(os.path.relpath(Path(a.fontsdir).resolve(), out.parent)).as_posix()
    edits = []
    for e in (json.loads(Path(a.edits).read_text(encoding="utf-8")) if a.edits else []):
        path = Path(a.edits).parent / e["file"]
        if not path.exists():
            print(f"  edit:   {e['file']:8} not downloaded yet, {e['t']:.2f}-{e['end']:.2f}s stays original")
            continue
        clip_dur = float(probe(a.ffmpeg, path, "v:0", "duration"))
        seg = Path(a.edits).parent / e.get("segment", "")
        # fit to the length of the segment he uploaded (frame-rounded), not the nominal slot
        dur = float(probe(a.ffmpeg, seg, "v:0", "duration")) if e.get("segment") and seg.exists() else e["end"] - e["t"]
        if abs(clip_dur / dur - 1) > 0.2:
            # much longer or shorter than the slot means Omni changed the timing; stretching would wreck lip sync
            print(f"  edit:   {e['file']:8} is {clip_dur:.2f}s for a {dur:.2f}s slot, skipped (check it in Flow)")
            continue
        # the uploaded segment began on the first whole frame at or after t, so the edit must too
        t_snap = math.ceil(e["t"] * fps_f - 1e-6) / fps_f
        edits.append({**e, "t": round(t_snap, 4), "path": path.resolve(), "dur": dur, "clip_dur": clip_dur})
        print(f"  edit:   {e['file']:8} at {e['t']:6.2f}-{e['end']:.2f}s (clip {clip_dur:.2f}s, fitted x{dur / clip_dur:.3f})")

    keys = [] if a.no_zoom else fx.plan_zoom(sections, scene_cuts, words)
    for k0 in keys:
        print(f"  zoom: {k0[0]:6.2f} -> {k0[1]:6.2f}  {k0[2]:.2f} -> {k0[3]:.2f}")

    # input 0: the zoomed picture, piped in from Python as raw YUV; input 1: the original file, for its audio
    inputs = ["-f", "rawvideo", "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709",
              "-s", f"{W}x{H}", "-framerate", fps, "-i", "-", "-i", video]
    n_in = 2
    bargs, bfc, last = fx.cut_filters(cuts, n_in, fps, W, H, "0:v")
    inputs += bargs
    n_in += len(cuts)
    fc = bfc.lstrip(";") + (";" if bfc else "") + f"[{last}]ass={ass.name}:fontsdir={fontsdir}[cap]"
    last = "cap"

    if a.text:
        # on-screen text is Aarit's call each time, and only stays up for 1-4 seconds
        secs = min(max(a.text_secs, 1.0), 4.0)
        start, end = a.text_start, a.text_start + secs
        title = out.with_name(out.stem + "_text.png")
        emoji = chr(int(a.emoji[2:], 16)) if a.emoji.upper().startswith("U+") else a.emoji
        build_title(a.text.split("|"), emoji, title)
        cards = [s for s in sections if s["kind"] == "card"]
        hide = "".join(f"+between(t,{s['start']},{s['end']})" for s in cards)
        hide += "".join(f"+between(t,{c['t']},{c['end']})" for c in cuts)
        inputs += ["-i", title.name]
        fc += f";[{last}][{n_in}:v]overlay=0:0:enable='between(t,{start},{end})*not(0{hide})'[txt]"
        last = "txt"
        n_in += 1
    fc += f";[{last}]format=yuv420p[vout]"
    last = "vout"

    fc += f";[1:a]{loudnorm_filter(a.ffmpeg, video)},aformat=sample_rates=48000:channel_layouts=stereo[voice]"
    mix = ["[voice]"]
    if not a.no_sfx:
        events = list(sfx_events(a.ffmpeg, Path(a.sfx_dir), sections, scene_cuts,
                                 a.text_start if a.text else None, [c["t"] for c in cuts]))
        for k, (t, path, peak_t, gain, kind, ratio) in enumerate(events):
            lead = t - peak_t                     # start early so the loudest moment hits the beat
            trim = f"atrim=start={-lead:.3f},asetpts=PTS-STARTPTS," if lead < 0 else ""
            delay = max(lead, 0) * 1000
            sr = probe(a.ffmpeg, path, "a:0", "sample_rate")
            pitch = f"asetrate={sr}*{ratio:.4f}," if abs(ratio - 1) > 1e-3 else ""
            inputs += ["-i", str(path)]
            fc += (f";[{n_in}:a]{pitch}aresample=48000,{trim}aformat=sample_rates=48000:channel_layouts=stereo,"
                   f"volume={gain:.3f},adelay={delay:.0f}|{delay:.0f}[s{k}]")
            mix.append(f"[s{k}]")
            n_in += 1
            print(f"  sfx: {kind:6} {path.name:26} at {t:6.2f}s" + (f" pitch x{ratio:.2f}" if pitch else ""))
    if len(mix) > 1:
        fc += f";{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,{LIMITER}[a]"
    else:
        fc += f";[voice]{LIMITER}[a]"
    enc = subprocess.Popen([a.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", *inputs,
                            "-filter_complex", fc, "-map", f"[{last}]", "-map", "[a]",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                            "-color_range", "tv", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            out.name], stdin=subprocess.PIPE, cwd=out.parent)
    frames = fx.pipe_zoom(a.ffmpeg, video, W, H, fps_f, keys, enc.stdin, edits=edits, fps_str=fps)
    enc.stdin.close()
    if enc.wait() != 0:
        raise SystemExit("encode failed")
    print(f"wrote {out} ({frames} frames)")


if __name__ == "__main__":
    main()
