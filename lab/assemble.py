"""EXPERIMENT (not wired into the engine yet): script + raw clips in, one assembled talking-head video out.

  py -3.14 lab/assemble.py NAME --script "C:\\...\\script.txt" --clips "C:\\...\\raw folder"
        [--max-pause 0.35] [--force "3=IMG_0042" --force "5=IMG_0040@12.5"] [--skip 7] [--fps 30]

What it does, in order:
  1. Transcribes every raw clip (cached), word by word.
  2. Splits the script into lines. A line "[show: graph]" puts the clip whose name contains "graph" over the
     next line's picture (his own footage; the voice stays).
  3. Finds every take of every line in every clip (local alignment that tolerates misheard words), scores
     them (complete, clean, later takes win) and picks one per line, preferring lines that flow on from the
     same clip.
  4. Cuts restarts and extra words out of the chosen takes, and pauses longer than --max-pause, at the
     quietest moment between words.
  5. Renders one 1080x1920 video and a line-by-line report, both into Downloads.

Then the normal process takes over: ask about motion text, `reel.py prep "<NAME> assembled.mp4" ...`.
Work files live in reels/<NAME> assembly/ (never committed). Details and limits: lab/ASSEMBLE.md.
"""
import argparse, hashlib, json, re, shutil, subprocess, sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import reel as R            # noqa: E402  (config, run, export helpers)
import talk_reel as tr      # noqa: E402  (tidy_words)

W, H = 1080, 1920
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv"}
NUMS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
        "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "fifteen": "15", "twenty": "20",
        "thirty": "30", "fifty": "50", "hundred": "100", "thousand": "1000"}
FILLERS = {"um", "uh", "umm", "uhh", "erm", "hmm", "ah", "eh"}
MATCH, NEAR, MISS, GAP = 2.0, 1.0, -1.0, -1.0
MIN_COVER = 0.5           # a take must say at least half the line's words
HEAD, TAIL = 0.06, 0.09   # breathing room kept before the first and after the last word of a run


# ---------------------------------------------------------------- text

def norm(word):
    w = word.lower().replace("₹", "").replace("’", "'")
    w = re.sub(r"[^\w']", "", w).strip("'")
    return NUMS.get(w, w)


def parse_script(text):
    """Script lines with their cues. Blank lines and sentence ends split lines; [show: x] cues the next line."""
    lines, cue = [], None
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        m = re.fullmatch(r"\[\s*show\s*:\s*(.+?)\s*\]", raw, re.I)
        if m:
            cue = m.group(1)
            continue
        for sent in re.split(r"(?<=[.!?])\s+", raw):
            toks = [norm(t) for t in sent.split()]
            toks = [t for t in toks if t]
            if toks:
                lines.append({"text": sent.strip(), "tokens": toks, "show": cue})
                cue = None
    return lines


# ---------------------------------------------------------------- clips

def probe(cfg, path):
    out = R.run([R.ffprobe(cfg), "-v", "error", "-show_entries",
                 "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", path], quiet=True)
    j = json.loads(out)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), {})
    num, den = (v.get("r_frame_rate", "30/1").split("/") + ["1"])[:2]
    return {"duration": float(j["format"]["duration"]), "fps": float(num) / float(den or 1),
            "has_audio": any(s["codec_type"] == "audio" for s in j["streams"])}


def clip_key(path):
    st = path.stat()
    return hashlib.md5(f"{path.resolve()}|{st.st_size}|{st.st_mtime}".encode()).hexdigest()[:12]


def transcribe(cfg, clip, work):
    """Words with times for one clip, cached by file identity. Transcribed stretch by stretch (split at
    pauses), because Whisper drops repeated words when a restart sits in the same stretch."""
    key = clip_key(clip)
    out = work / "words" / f"{clip.stem}.{key}.json"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        wav = work / "words" / f"{clip.stem}.wav"
        R.run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error", "-y", "-i", clip, "-vn", "-ar", "16000", "-ac", "1", wav])
        chunks = work / "words" / f"{clip.stem}.chunks.json"
        chunks.write_text(json.dumps(speech_stretches(envelope(cfg, clip, work))))
        R.run([cfg["whisper_python"], "-W", "ignore", Path(__file__).parent / "transcribe_chunks.py", wav, chunks, out],
              quiet=True)
        wav.unlink(missing_ok=True)
    words = tr.tidy_words(json.loads(out.read_text(encoding="utf-8"))["words"])
    for w in words:
        w["n"] = norm(w["t"])
    return [w for w in words if w["n"]]


def speech_stretches(env, min_pause=0.45, pad=0.15):
    """Stretches of speech in a clip, split wherever it goes quiet for min_pause or longer."""
    floor = float(np.percentile(env, 10))
    loud = env > floor + 12
    out, start, quiet = [], None, 0
    for i, v in enumerate(loud):
        if v:
            if start is None:
                start = i
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet * 0.01 >= min_pause:
                out.append([start / 100, (i - quiet + 1) / 100])
                start, quiet = None, 0
    if start is not None:
        out.append([start / 100, len(env) / 100])
    dur = len(env) / 100
    return [[round(max(0.0, s - pad), 2), round(min(dur, e + pad), 2)] for s, e in out if e - s >= 0.15]


def envelope(cfg, clip, work):
    """10 ms RMS of the clip's audio, in dB (cached), for finding the quiet moment between words."""
    out = work / "words" / f"{clip.stem}.{clip_key(clip)}.env.npy"
    if not out.exists():
        raw = subprocess.run([cfg["ffmpeg"], "-v", "error", "-i", str(clip), "-vn", "-ac", "1", "-ar", "16000",
                              "-f", "s16le", "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        n = len(x) // 160
        env = 20 * np.log10(np.sqrt((x[: n * 160].reshape(n, 160) ** 2).mean(axis=1)) + 1e-6)
        np.save(out, env)
    return np.load(out)


# ---------------------------------------------------------------- alignment

def similar(a, b):
    if a == b:
        return MATCH
    if len(a) > 2 and len(b) > 2 and SequenceMatcher(None, a, b).ratio() >= 0.75:
        return NEAR
    return MISS


def local_align(line, words, used):
    """Smith-Waterman of one script line against one clip's words; `used` words are off limits.
    Returns (score, path) where path is a list of (line_idx|None, word_idx|None)."""
    n, m = len(line), len(words)
    S = np.zeros((n + 1, m + 1), np.float32)
    T = np.zeros((n + 1, m + 1), np.int8)    # 0 stop, 1 diag, 2 up (script gap), 3 left (extra clip word)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d = S[i - 1, j - 1] + (similar(line[i - 1], words[j - 1]["n"]) if not used[j - 1] else -9)
            u = S[i - 1, j] + GAP
            l = S[i, j - 1] + GAP
            best = max(0.0, d, u, l)
            S[i, j] = best
            T[i, j] = 0 if best == 0 else (1 if best == d else (2 if best == u else 3))
    i, j = np.unravel_index(int(S.argmax()), S.shape)
    score = float(S[i, j])
    path = []
    while i > 0 and j > 0 and T[i, j] != 0:
        t = T[i, j]
        if t == 1:
            path.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif t == 2:
            path.append((i - 1, None))
            i -= 1
        else:
            path.append((None, j - 1))
            j -= 1
    return score, path[::-1]


def cut_or_keep(kept, extras, words):
    """Words he said that aren't in the script. Cut a run of them only when it's a filler, a restart (the
    same words come again straight after) or 3+ words long; a single natural extra word ("about a 50", or
    Whisper splitting "Market play") stays, because cutting it would leave a jump cut mid-sentence."""
    runs, cur = [], []
    for b in sorted(extras):
        if cur and b != cur[-1] + 1:
            runs.append(cur)
            cur = []
        cur.append(b)
    if cur:
        runs.append(cur)
    keep, cut = set(kept), []
    for r in runs:
        toks = [words[b]["n"] for b in r]
        after = [w["n"] for w in words[r[-1] + 1: r[-1] + 1 + len(toks)]]
        restart = len(after) == len(toks) and all(similar(x, y) > 0 for x, y in zip(toks, after))
        if all(t in FILLERS for t in toks) or restart or len(r) >= 3:
            cut += r
        else:
            keep.update(r)
    return sorted(keep), cut


def find_takes(line, clips):
    """Every take of one line across all clips (several per clip when he said it more than once)."""
    takes = []
    for ci, c in enumerate(clips):
        if not c["words"]:
            continue
        used = [False] * len(c["words"])
        for _ in range(6):
            score, path = local_align(line["tokens"], c["words"], used)
            hits = [(a, b) for a, b in path if a is not None and b is not None
                    and similar(line["tokens"][a], c["words"][b]["n"]) > 0]
            cover = len({a for a, _ in hits}) / len(line["tokens"])
            if not path or cover < MIN_COVER or len(hits) < min(2, len(line["tokens"])):
                break
            w_idx = [b for _, b in path if b is not None]
            for b in range(min(w_idx), max(w_idx) + 1):
                used[b] = True
            words = c["words"]
            kept = [b for a, b in path if a is not None and b is not None]
            kept, extras = cut_or_keep(kept, [b for a, b in path if a is None and b is not None], words)
            fillers = sum(1 for b in range(min(w_idx), max(w_idx) + 1) if words[b]["n"] in FILLERS)
            conf = float(np.mean([words[b].get("p", 1.0) for b in kept])) if kept else 0
            long_words = [b for b in kept if words[b]["e"] - words[b]["s"] > 1.2]
            takes.append({"clip": ci, "kept": kept, "extras": extras, "cover": round(cover, 3),
                          "score": round(score, 2), "fillers": fillers, "conf": conf, "long": long_words,
                          "s": words[kept[0]]["s"], "e": words[kept[-1]]["e"]})
    # rank: complete and clean first; among near-equal takes, the later one (he usually nails the last take)
    for t in takes:
        t["rank"] = t["cover"] * 10 - len(t["extras"]) * 0.4 - t["fillers"] * 0.5 + (t["conf"] - 0.8) * 2
    order = sorted(takes, key=lambda t: (t["clip"], t["s"]))
    for k, t in enumerate(order):
        t["rank"] += 0.05 * k / max(1, len(order))
    return sorted(takes, key=lambda t: -t["rank"])


FLOW_BONUS = 1.5   # a line that carries straight on from the previous line in the same clip


def choose(options):
    """One take per line (options[i] = that line's takes, best first). Dynamic programming over the lines:
    the best ranks overall, plus FLOW_BONUS when a line carries on from the previous one in the same clip,
    which keeps his natural delivery. Lines without takes are skipped over."""
    best = []                      # per line: {take index: (total score, take index on the previous line)}
    prev_line = None
    for i, opts in enumerate(options):
        cur = {}
        for k, t in enumerate(opts[:6]):
            if prev_line is None:
                cur[k] = (t["rank"], None)
                continue
            scored = []
            for pk, (ps, _) in best[prev_line].items():
                pt = options[prev_line][pk]
                flows = pt["clip"] == t["clip"] and 0 <= t["s"] - pt["e"] < 2.5
                scored.append((ps + (FLOW_BONUS if flows else 0.0), pk))
            s, back = max(scored, key=lambda x: x[0])
            cur[k] = (s + t["rank"], back)
        best.append(cur)
        if cur:
            prev_line = i
    picks = [None] * len(options)
    filled = [i for i, b in enumerate(best) if b]
    if not filled:
        return picks
    i = filled[-1]
    k = max(best[i], key=lambda kk: best[i][kk][0])
    while True:
        picks[i] = options[i][k]
        back = best[i][k][1]
        earlier = [j for j in filled if j < i]
        if back is None or not earlier:
            break
        i, k = earlier[-1], back
    return picks


# ---------------------------------------------------------------- cutting

def quiet_point(env, a, b, prefer):
    """The quietest 10 ms in [a, b] seconds (prefer ties near `prefer`)."""
    i0, i1 = max(0, int(a * 100)), min(len(env) - 1, int(b * 100))
    if i1 <= i0:
        return prefer
    seg = env[i0:i1 + 1]
    lo = seg.min()
    near = [i for i in range(len(seg)) if seg[i] <= lo + 3]
    j = min(near, key=lambda i: abs((i0 + i) / 100 - prefer))
    return (i0 + j) / 100


def runs_for(take, words, env, max_pause, clip_dur):
    """The take's kept words as runs of continuous speech, each a (start, end) cut on quiet points."""
    kept = sorted(take["kept"])
    runs, cur = [], [kept[0]]
    for b in kept[1:]:
        gap = words[b]["s"] - words[cur[-1]]["e"]
        if b != cur[-1] + 1 or gap > max_pause:      # an extra word or a long pause in between: cut here
            runs.append(cur)
            cur = [b]
        else:
            cur.append(b)
    runs.append(cur)
    out = []
    for r in runs:
        s, e = words[r[0]]["s"], words[r[-1]]["e"]
        prev_e = words[r[0] - 1]["e"] if r[0] > 0 else 0.0
        next_s = words[r[-1] + 1]["s"] if r[-1] + 1 < len(words) else clip_dur
        a = quiet_point(env, max(prev_e, s - 0.25), s, s - HEAD)
        b = quiet_point(env, e, min(next_s, e + 0.35), e + TAIL)
        out.append((max(0.0, a), min(clip_dur, max(b, e + 0.02))))
    return out


# ---------------------------------------------------------------- render

def render(cfg, segs, shows, fps, work, out):
    seg_dir = work / "segments"
    shutil.rmtree(seg_dir, ignore_errors=True)
    seg_dir.mkdir(parents=True)
    listing = []
    for k, sg in enumerate(segs):
        d = sg["dur"]                          # a whole number of frames, so sound and picture stay locked
        frames = round(d * fps)
        f = seg_dir / f"{k:03d}.mkv"
        R.run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{sg['a']:.3f}", "-i", sg["path"],
               "-t", f"{d:.4f}", "-map", "0:v:0", "-map", "0:a:0",
               "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,"
                      f"fps={fps},format=yuv420p",
               "-af", f"aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.012,"
                      f"afade=t=out:st={max(0, d - 0.012):.4f}:d=0.012",
               "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
               "-c:a", "pcm_s16le", f])
        listing.append(f"file '{f.as_posix()}'")
    (work / "concat.txt").write_text("\n".join(listing), encoding="utf-8")
    talk = work / "talk.mkv"
    R.run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
           "-i", work / "concat.txt", "-c", "copy", talk])
    inputs, fc, last = ["-i", str(talk)], "", "0:v"
    for k, sh in enumerate(shows):
        inputs += ["-i", sh["path"]]
        fc += (f"[{k + 1}:v]trim=start={sh['from']:.3f}:duration={sh['dur']:.3f},setpts=PTS-STARTPTS+{sh['t']:.3f}/TB,"
               f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,fps={fps},"
               f"format=yuv420p[f{k}];[{last}][f{k}]overlay=0:0:eof_action=pass:"
               f"enable='between(t,{sh['t']:.3f},{sh['t'] + sh['dur']:.3f})'[o{k}];")
        last = f"o{k}"
    fc += f"[{last}]format=yuv420p[v]"
    R.run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error", "-y", *inputs, "-filter_complex", fc,
           "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])


# ---------------------------------------------------------------- main

def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("--script", required=True, help="text file: one thought per line; [show: name] cues footage")
    ap.add_argument("--clips", required=True, help="folder with his raw clips, any names, any order")
    ap.add_argument("--max-pause", type=float, default=0.35, help="pauses longer than this are cut (seconds)")
    ap.add_argument("--force", action="append", default=[], help='"LINE=CLIP" or "LINE=CLIP@SECONDS" (lines from 1)')
    ap.add_argument("--skip", action="append", type=int, default=[], help="script line to leave out (from 1)")
    ap.add_argument("--fps", type=float, default=0, help="output frame rate (default: his clips', max 30)")
    ap.add_argument("--no-deliver", action="store_true")
    a = ap.parse_args()
    cfg = R.config()
    work = R.REELS / f"{a.name} assembly"
    work.mkdir(parents=True, exist_ok=True)

    lines = parse_script(Path(a.script).read_text(encoding="utf-8"))
    files = sorted(p for p in Path(a.clips).iterdir() if p.suffix.lower() in VIDEO_EXT)
    if not files or not lines:
        sys.exit("need a script with text and a folder with video clips")
    print(f"[1/5] {len(files)} clips, {len(lines)} script lines; transcribing (cached after the first time)")
    clips = []
    for f in files:
        info = probe(cfg, f)
        words = transcribe(cfg, f, work) if info["has_audio"] else []
        clips.append({"path": str(f), "name": f.stem, **info, "words": words})
        print(f"    {f.name:34} {info['duration']:6.1f}s  {len(words):4} words")

    print("[2/5] finding every take of every line")
    cands = [find_takes(ln, clips) for ln in lines]
    forced = {}
    for spec in a.force:
        m = re.fullmatch(r"(\d+)=(.+?)(?:@([\d.]+))?", spec.strip())
        if not m:
            sys.exit(f"bad --force {spec!r}; use LINE=CLIP or LINE=CLIP@SECONDS")
        i, name, at = int(m.group(1)) - 1, m.group(2).lower(), m.group(3)
        opts = [t for t in cands[i] if name in clips[t["clip"]]["name"].lower()]
        if at:
            opts.sort(key=lambda t: abs(t["s"] - float(at)))
        if not opts:
            sys.exit(f"line {i + 1}: no take found in a clip matching {name!r}")
        forced[i] = opts[:1]          # exactly that take: the flow bonus must not swap it for another
    for i in a.skip:
        forced[i - 1] = []
    options = [forced.get(i, cands[i]) for i in range(len(lines))]
    picks = choose(options)

    print("[3/5] cutting restarts, extra words and pauses")
    fps_votes = Counter(round(clips[pk["clip"]]["fps"]) for pk in picks if pk)
    fps = a.fps or min(30.0, float(fps_votes.most_common(1)[0][0]) if fps_votes else 30.0)
    envs = {}
    segs, line_spans, t_now = [], [], 0.0
    for i, (ln, pk) in enumerate(zip(lines, picks)):
        if pk is None:
            line_spans.append(None)
            continue
        c = clips[pk["clip"]]
        if pk["clip"] not in envs:
            envs[pk["clip"]] = envelope(cfg, Path(c["path"]), work)
        start = t_now
        for x, y in runs_for(pk, c["words"], envs[pk["clip"]], a.max_pause, c["duration"]):
            # never reuse a moment twice: trim against the previous piece from the same clip
            if segs and segs[-1]["clip"] == pk["clip"] and x < segs[-1]["b"]:
                x = segs[-1]["b"]
            frames = round((y - x) * fps)
            if frames < 2:
                continue
            segs.append({"clip": pk["clip"], "path": c["path"], "a": x, "b": y, "line": i, "dur": frames / fps})
            t_now += frames / fps
        line_spans.append((start, t_now))

    # footage cues: his own clips over a line's picture, voice untouched
    used_talk = {s["clip"] for s in segs}
    shows = []
    for i, ln in enumerate(lines):
        if ln["show"] and line_spans[i]:
            hit = next((c for c in clips if ln["show"].lower() in c["name"].lower()), None)
            if not hit:
                print(f"    [show: {ln['show']}] matches no clip name, skipped")
                continue
            t0, t1 = line_spans[i]
            dur = min(t1 - t0, max(0.0, hit["duration"] - 0.3))
            shows.append({"path": hit["path"], "t": t0, "dur": dur, "from": min(0.3, hit["duration"] / 4),
                          "name": hit["name"], "line": i})

    print(f"[4/5] rendering {len(segs)} pieces at {fps:g} fps")
    out = work / f"{a.name} assembled.mp4"
    render(cfg, segs, shows, fps, work, out)
    total = sum(s["dur"] for s in segs)

    print("[5/5] report")
    rep = [f"ASSEMBLY REPORT: {a.name}", "",
           f"{len(lines)} script lines from {len(clips)} clips -> {total:.1f}s "
           f"(raw talking footage {sum(c['duration'] for c in clips if c['words']):.1f}s). "
           f"Pauses over {a.max_pause}s cut.", ""]
    for i, (ln, pk) in enumerate(zip(lines, picks)):
        rep.append(f"{i + 1:>2}. {ln['text']}")
        if pk is None:
            rep.append("    skipped (--skip)" if i + 1 in a.skip else "    MISSING: no take found in any clip")
            continue
        c = clips[pk["clip"]]
        others = [t for t in options[i] if t is not pk][:3]
        cut_words = " ".join(c["words"][b]["t"] for b in pk["extras"])
        rep.append(f"    take: {c['name']} {pk['s']:.2f}-{pk['e']:.2f}s, said {pk['cover'] * 100:.0f}% of the line"
                   + (" (forced)" if i in forced else ""))
        if cut_words:
            rep.append(f"    cut out: \"{cut_words}\"")
        if pk["cover"] < 0.85:
            rep.append("    CHECK: this take skips some script words")
        for b in pk.get("long", []):
            w = c["words"][b]
            rep.append(f"    CHECK: \"{w['t']}\" runs {w['e'] - w['s']:.1f}s at {w['s']:.1f}s in the clip; "
                       "a restart or pause may be hiding in it")
        if others:
            rep.append("    other takes: " + ", ".join(f"{clips[t['clip']]['name']}@{t['s']:.1f}s "
                                                     f"({t['cover'] * 100:.0f}%)" for t in others))
        if line_spans[i]:
            rep.append(f"    in the video at {line_spans[i][0]:.2f}-{line_spans[i][1]:.2f}s")
        sh = next((s for s in shows if s["line"] == i), None)
        if sh:
            rep.append(f"    footage over it: {sh['name']} ({sh['dur']:.1f}s)")
    unused = [c["name"] for k, c in enumerate(clips) if k not in used_talk and c["name"] not in {s["name"] for s in shows}]
    if unused:
        rep += ["", "Not used: " + ", ".join(unused) + "  (footage gets placed with a [show: name] line in the script)"]
    rep += ["", f"Overrides: --force \"LINE=CLIP\" or \"LINE=CLIP@SECONDS\", --skip LINE, --max-pause SECONDS"]
    report = "\n".join(rep) + "\n"
    (work / "assembly report.txt").write_text(report, encoding="utf-8")
    R.save(work, "plan.json", {"fps": fps, "segments": segs, "shows": shows,
                               "lines": [{"text": ln["text"], "span": sp} for ln, sp in zip(lines, line_spans)]})
    print(report)
    if not a.no_deliver:
        dl = Path(cfg["deliver_dir"])
        shutil.copy2(out, dl / out.name)
        shutil.copy2(work / "assembly report.txt", dl / f"{a.name} assembly report.txt")
        print(f"delivered {dl / out.name}")


if __name__ == "__main__":
    main()
