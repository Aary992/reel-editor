"""The dead-space cut for the story look: his raw video (or a folder of raw takes) in, one tight talking-head
video out, with no script needed. reel.py's `cut` command runs it; `prep` then works on the result.

What goes, in this order (his inspo's rules, 10-20):
  1. Fillers (um, uh ...).
  2. Restarts and stutters: the same 1-6 words said again straight after ("now I- now I", "step two, the
     financials ... step two, the financials"). The last go stays.
  3. Earlier takes: a sentence he says again later (in the same take or a later one) is an earlier take; only
     the last one stays ("he usually nails the last take").
  4. Claude's drops from the review (--drop): a whole take, a time range in a take, or a phrase.
  5. Dead space: every pause over --max-pause (0.35 s) shrinks to a cut, and the video starts on his first word.
Every cut lands on the quietest 10 ms between words with a 12 ms audio fade, picture and sound frame-locked.

Out: reels/<name>/cut.mp4 (1080x1920), cut.json (every piece, every jump cut, his face per piece) and
cut report.txt (what was cut and why). Landscape takes are cropped to 9:16 around his face.
"""
import json, re, shutil, sys
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lab"))
import reel as R            # noqa: E402
import face                 # noqa: E402
import assemble as A        # noqa: E402  (stretch-by-stretch transcription, envelopes, quiet points)

W, H = 1080, 1920
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv"}
HEAD, TAIL = 0.06, 0.09   # breathing room kept before the first and after the last word of each piece
SENT_GAP = 0.7            # a pause this long ends a sentence even without punctuation


def clips_of(paths):
    """Every take, in recording order (phone file names sort by time): files and/or folders of files."""
    files = []
    for path in paths:
        p = Path(path)
        files += sorted(f for f in p.iterdir() if f.suffix.lower() in VIDEO_EXT) if p.is_dir() else [p]
    if not files:
        sys.exit(f"no video in {paths}")
    missing = [f for f in files if not f.exists()]
    if missing:
        sys.exit(f"can't find {missing[0]}")
    return sorted(dict.fromkeys(files), key=lambda f: f.name.lower())


def display_size(cfg, path):
    """Width and height as the picture is shown (phone clips carry a rotation flag)."""
    out = R.run([R.ffprobe(cfg), "-v", "error", "-select_streams", "v:0", "-show_entries",
                 "stream=width,height:stream_side_data=rotation", "-of", "json", path], quiet=True)
    s = json.loads(out)["streams"][0]
    rot = next((abs(int(float(d.get("rotation", 0)))) for d in s.get("side_data_list", []) if "rotation" in d), 0)
    w, h = s["width"], s["height"]
    return (h, w) if rot in (90, 270) else (w, h)


# ---------------------------------------------------------------- mistakes

def same(a, b):
    return A.similar(a, b) > 0


def sentences(words):
    """Index ranges [a, b) of sentences: punctuation or a long pause ends one."""
    out, a = [], 0
    for i, w in enumerate(words):
        end = w["t"][-1:] in ".!?" or (i + 1 < len(words) and words[i + 1]["s"] - w["e"] >= SENT_GAP)
        if end or i == len(words) - 1:
            out.append((a, i + 1))
            a = i + 1
    return out


def find_mistakes(clips):
    """{(clip, word index): reason} for every word that goes."""
    cut = {}
    for ci, c in enumerate(clips):
        ws = c["words"]
        for i, w in enumerate(ws):
            if w["n"] in A.FILLERS:
                cut[(ci, i)] = "filler"
        # restarts: the same 1-6 words said again straight after ("now I- now I"), fillers in between ignored.
        # Only back to back: "the daily and the weekly" repeats "the" on purpose, so nothing may sit between.
        live = [i for i in range(len(ws)) if (ci, i) not in cut]
        p = 0
        while p < len(live):
            hit = 0
            for k in range(6, 0, -1):
                if p + 2 * k > len(live):
                    continue
                a_, b_ = live[p:p + k], live[p + k:p + 2 * k]
                if not all(same(ws[x]["n"], ws[y]["n"]) for x, y in zip(a_, b_)):
                    continue
                if ws[b_[0]]["s"] - ws[a_[-1]]["e"] > 2.5:
                    continue
                # one repeated word only counts for short words ("I I", "the the"), never "had had"-style words
                if k == 1 and (len(ws[a_[0]]["n"]) > 3 or ws[a_[0]]["n"] in {"had", "that", "very", "so", "bye"}):
                    continue
                hit = k
                break
            if hit:
                for x in live[p:p + hit]:
                    cut.setdefault((ci, x), "restart")
                p += hit
            else:
                p += 1
        # words Whisper "hears" in the silence after (or before) a take: a lone, unsure word set apart by a pause
        for i, w in enumerate(ws):
            alone_after = i > 0 and w["s"] - ws[i - 1]["e"] >= 0.6 and i >= len(ws) - 2
            alone_before = i + 1 < len(ws) and ws[i + 1]["s"] - w["e"] >= 0.6 and i <= 1
            if (alone_after or alone_before) and (w.get("p", 1) < 0.6 or w["n"] in {"you", "thank", "thanks"}):
                tail = range(i, len(ws)) if alone_after else range(0, i + 1)
                for x in tail:
                    cut.setdefault((ci, x), "noise (a word Whisper heard in the silence)")
    # earlier takes: a sentence (3+ words) that a later sentence repeats or completes
    flat = [(ci, a, b) for ci, c in enumerate(clips) for a, b in sentences(c["words"])]
    for k, (ci, a, b) in enumerate(flat):
        toks = [clips[ci]["words"][x]["n"] for x in range(a, b)]
        if len(toks) < 3 or all((ci, x) in cut for x in range(a, b)):
            continue
        for cj, a2, b2 in flat[k + 1:k + 7]:
            later = [clips[cj]["words"][x]["n"] for x in range(a2, b2)]
            head = later[:len(toks) + 2]
            m = SequenceMatcher(None, toks, head, autojunk=False)
            matched = sum(bl.size for bl in m.get_matching_blocks())
            if matched >= max(3, 0.7 * len(toks)):
                for x in range(a, b):
                    cut.setdefault((ci, x), "earlier take")
                break
    return cut


def apply_drops(clips, drops, cut):
    """Claude's review drops: CLIP (whole take), CLIP@S-E (seconds in that take) or a phrase in quotes."""
    for d in drops:
        d = d.strip()
        m = re.fullmatch(r"(.+?)@([\d.]+)-([\d.]+)", d)
        name, lo, hi = (m.group(1), float(m.group(2)), float(m.group(3))) if m else (d, None, None)
        hits = [ci for ci, c in enumerate(clips) if name.lower() in c["name"].lower()]
        if hits:
            for ci in hits:
                for i, w in enumerate(clips[ci]["words"]):
                    if lo is None or (w["s"] >= lo - 0.05 and w["e"] <= hi + 0.05):
                        cut[(ci, i)] = "dropped in review"
            continue
        toks = [A.norm(t) for t in d.split()]
        toks = [t for t in toks if t]
        found = False
        for ci, c in enumerate(clips):
            ns = [w["n"] for w in c["words"]]
            for i in range(len(ns) - len(toks) + 1):
                if all(same(toks[x], ns[i + x]) for x in range(len(toks))):
                    for x in range(i, i + len(toks)):
                        cut[(ci, x)] = "dropped in review"
                    found = True
        if not found:
            sys.exit(f"--drop {d!r} matches no take name and no phrase")


# ---------------------------------------------------------------- pieces

def pieces(clips, cut, max_pause, envs):
    """Runs of kept speech per take, each cut on quiet points: [(clip, a, b, word indices)]."""
    out = []
    for ci, c in enumerate(clips):
        ws, env = c["words"], envs[ci]
        kept = [i for i in range(len(ws)) if (ci, i) not in cut]
        if not kept:
            continue
        runs, cur = [], [kept[0]]
        for i in kept[1:]:
            if i != cur[-1] + 1 or ws[i]["s"] - ws[cur[-1]]["e"] > max_pause:
                runs.append(cur)
                cur = [i]
            else:
                cur.append(i)
        runs.append(cur)
        for r in runs:
            s, e = ws[r[0]]["s"], ws[r[-1]]["e"]
            prev_e = ws[r[0] - 1]["e"] if r[0] > 0 else 0.0
            next_s = ws[r[-1] + 1]["s"] if r[-1] + 1 < len(ws) else c["duration"]
            a = A.quiet_point(env, max(prev_e, s - 0.25), s, s - HEAD)
            b = A.quiet_point(env, e, min(next_s, e + 0.35), e + TAIL)
            out.append((ci, max(0.0, a), min(c["duration"], max(b, e + 0.02)), r))
    return out


def crop_filter(c):
    """Fill 1080x1920; a landscape take is cropped around his face, a portrait one centred."""
    w, h = c["size"]
    sw = round(w * H / h) if w / h > W / H else W
    sh = H if w / h > W / H else round(h * W / w)
    sw += sw % 2
    sh += sh % 2
    x = min(max(0, round(c.get("face_x", 0.5) * sw - W / 2)), sw - W)
    y = max(0, (sh - H) // 2)
    return f"scale={sw}:{sh}:flags=lanczos,crop={W}:{H}:{x}:{y},setsar=1"


def face_x(cfg, c, work):
    """Where his face is across a landscape take (median of 3 frames), as a fraction of the full width."""
    w, h = c["size"]
    if w / h <= W / H:
        return 0.5
    sw = round(w * H / h)
    xs = []
    for k in (0.25, 0.5, 0.75):
        png = work / f"face_{c['name']}_{k}.png"
        R.run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{c['duration'] * k:.2f}",
               "-i", c["path"], "-frames:v", "1", "-vf", f"scale={sw}:{H}:flags=bilinear,crop={W}:{H}", png])
        from PIL import Image
        f = face.locate(Image.open(png))
        png.unlink(missing_ok=True)
        if f:
            xs.append(((sw - W) / 2 + f["cx"] * W) / sw)
    return round(float(np.median(xs)), 4) if xs else 0.5


def render(cfg, segs, clips, fps, work, out):
    seg_dir = work / "segments"
    shutil.rmtree(seg_dir, ignore_errors=True)
    seg_dir.mkdir(parents=True)
    listing = []
    for k, sg in enumerate(segs):
        c = clips[sg["clip"]]
        frames = sg["frames"]
        d = frames / fps
        f = seg_dir / f"{k:03d}.mkv"
        R.run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{sg['a']:.3f}", "-i", c["path"],
               "-t", f"{d + 0.1:.4f}", "-map", "0:v:0", "-map", "0:a:0",
               "-vf", f"{crop_filter(c)},fps={fps},format=yuv420p",
               "-af", f"aresample=48000,aformat=channel_layouts=stereo,atrim=duration={d:.4f},"
                      f"afade=t=in:d=0.012,afade=t=out:st={max(0, d - 0.012):.4f}:d=0.012",
               "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
               "-c:a", "pcm_s16le", f])
        listing.append(f"file '{f.as_posix()}'")
    (work / "concat.txt").write_text("\n".join(listing), encoding="utf-8")
    # every piece is a whole number of frames with sample-exact sound, so re-time both streams end to end:
    # the concat demuxer's millisecond-rounded durations otherwise leave one-frame gaps at some joins
    R.run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
           "-i", work / "concat.txt", "-vf", f"setpts=N/({fps}*TB)", "-af", "asetpts=N/SR/TB",
           "-fps_mode", "cfr", "-r", f"{fps:g}", "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out])


# ---------------------------------------------------------------- main

def run_cut(cfg, srcs, name, drops=(), max_pause=0.35, fps=0):
    reel = R.REELS / name
    work = reel / "cut work"
    work.mkdir(parents=True, exist_ok=True)
    files = clips_of(srcs)
    print(f"[1/4] {len(files)} raw take(s); transcribing stretch by stretch (cached)")
    clips = []
    for f in files:
        info = A.probe(cfg, f)
        words = A.transcribe(cfg, f, work) if info["has_audio"] else []
        clips.append({"path": str(f), "name": f.stem, **info, "words": words, "size": display_size(cfg, f)})
        print(f"    {f.name:30} {info['duration']:6.1f}s  {len(words):4} words  {clips[-1]['size'][0]}x{clips[-1]['size'][1]}")

    print("[2/4] finding fillers, restarts, earlier takes and dead space")
    cut = find_mistakes(clips)
    apply_drops(clips, drops, cut)
    envs = [A.envelope(cfg, Path(c["path"]), work) for c in clips]
    runs = pieces(clips, cut, max_pause, envs)
    fps = fps or min(30.0, float(round(np.median([c["fps"] for c in clips]))))
    segs, t = [], 0.0
    for ci, a, b, idx in runs:
        frames = round((b - a) * fps)
        if frames < 3:
            continue
        segs.append({"clip": ci, "take": clips[ci]["name"], "a": round(a, 3), "b": round(b, 3), "frames": frames,
                     "t0": round(t, 4), "t1": round(t + frames / fps, 4),
                     "said": " ".join(clips[ci]["words"][i]["t"] for i in idx), "idx": idx})
        t += frames / fps
    if not segs:
        sys.exit("nothing left to keep: every word was cut")
    for ci in {s["clip"] for s in segs}:
        clips[ci]["face_x"] = face_x(cfg, clips[ci], work)

    print(f"[3/4] rendering {len(segs)} pieces at {fps:g} fps")
    out = reel / "cut.mp4"
    render(cfg, segs, clips, fps, work, out)
    total = segs[-1]["t1"]
    # his face in every piece of the finished cut, for the story look (UI above his head, captions off his mouth)
    spans = [(s["t0"], s["t1"]) for s in segs]
    faces = face.measure(cfg["ffmpeg"], out, spans, fps)
    for s, fc in zip(segs, faces):
        s["face"] = fc

    # the transcript of the cut, from the stretch-by-stretch transcription and moved onto the cut's clock:
    # better than transcribing the cut again (Whisper loses punctuation and names on a whole tight video)
    fixes = R.load(reel, "fixes.json", {})      # Claude's transcript fixes ("Complete": "Comment"), kept on re-cuts
    words_out = []
    for sg in segs:
        ws = clips[sg["clip"]]["words"]
        for i in sg.pop("idx"):
            w = ws[i]
            s0 = min(max(sg["t0"], sg["t0"] + w["s"] - sg["a"]), sg["t1"])
            e0 = min(max(s0, sg["t0"] + w["e"] - sg["a"]), sg["t1"])
            words_out.append({"w": " " + fixes.get(w["t"], w["t"]), "s": round(s0, 3), "e": round(e0, 3),
                              "p": w.get("p", 1.0)})
    R.save(reel, "words.json", {"lang": "en", "from": "cut", "words": words_out})
    raw = sum(c["duration"] for c in clips)
    rep = [f"CUT REPORT: {name}", "", f"{len(clips)} raw take(s), {raw:.1f}s raw -> {total:.1f}s "
           f"({raw - total:.1f}s of dead space and mistakes gone). Pauses over {max_pause}s cut.", ""]
    for ci, c in enumerate(clips):
        ws = c["words"]
        rep.append(f"{c['name']} ({c['duration']:.1f}s, {c['size'][0]}x{c['size'][1]}):")
        rep.append("    said: " + " ".join(w["t"] for w in ws))
        reasons = {}
        for (cj, i), why in sorted(cut.items()):
            if cj == ci:
                reasons.setdefault(why, []).append(i)
        for why, idx in reasons.items():
            groups, cur = [], [idx[0]]
            for i in idx[1:]:
                if i == cur[-1] + 1:
                    cur.append(i)
                else:
                    groups.append(cur)
                    cur = [i]
            groups.append(cur)
            for g in groups:
                rep.append(f"    cut ({why}) {ws[g[0]]['s']:.2f}-{ws[g[-1]]['e']:.2f}s: \"{' '.join(ws[i]['t'] for i in g)}\"")
        mine = [s for s in segs if s["clip"] == ci]
        if mine:
            rep.append(f"    kept in {len(mine)} piece(s), lead-in {ws[0]['s'] if ws else 0:.2f}s trimmed")
        elif ws:
            rep.append("    not used")
        rep.append("")
    rep.append(f"Jump cuts at: {', '.join(f'{s['t0']:.2f}' for s in segs[1:])}")
    rep.append("Fix with: reel.py cut ... --drop TAKE | --drop TAKE@S-E | --drop \"phrase\" | --max-pause 0.5")
    rep.append("Misheard words: put them in fixes.json ({\"heard\": \"said\"}) so every re-cut keeps them.")
    report = "\n".join(rep) + "\n"
    (reel / "cut report.txt").write_text(report, encoding="utf-8")
    R.save(reel, "cut.json", {"sources": [str(Path(x).resolve()) for x in srcs], "fps": fps, "max_pause": max_pause,
                              "drops": list(drops), "segments": segs,
                              "jumpcuts": [s["t0"] for s in segs[1:]],
                              "takes": [{"name": c["name"], "size": c["size"], "face_x": c.get("face_x", 0.5)}
                                        for c in clips]})
    print(report)
    return out
