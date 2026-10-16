"""Aarit's talking-head Reel engine: one video in, his locked style out.

  python reel.py prep "C:\\path\\to\\video.mp4" [--name NAME]
      transcribe, sections, money-burn segment (if he talks about losing money), 2-3 text-cut picks,
      one "flow prompts.txt", 3 cover frames and a preview render. No input needed from him.
  python reel.py repick NAME --only "DAY 1|17 TRADES"     (Claude's review override)
  python reel.py map NAME "his clip name.mp4" "17 TRADES" (when his file names don't match)
  python reel.py status NAME
  python reel.py render NAME --cover-line "his words" [--cover 2] [--text "..." --text-start 0 --text-secs 3]
      final Reel + cover, checked for sync and loudness, copied to Downloads.

The look is fixed in STYLE.md; TEXT_CUTS.md has the text-cut rules. Paths live in config.json."""
import argparse, glob, json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REELS = ROOT / "reels"
CAP_FONTS = ROOT / "fonts" / "figtree-800"

# the one in-scene effect he approved, word for word (option 4 on hedge 1, made with Omni edit mode)
MONEY_BURN_PROMPT = (
    "Edit the provided video. Make glowing cash banknotes drift slowly upward in the air around the young man "
    "like floating embers, and as they rise past his head they burn away into small red sparks and ash that fade "
    "near the top of the frame. A faint red glow pulses on the wall behind him. Keep it subtle and cinematic: the "
    "notes stay around the edges and behind him, never covering his face or the microphone. Keep the person in the "
    "provided video exactly as he is: same face, same lip movements, same expressions, same hands, same microphone, "
    "same clothes. Keep the camera framing and movement unchanged, the same length and timing as the original, "
    "vertical 9:16. No text, letters, numbers, logos or watermarks anywhere.")
LOSS_WORDS = {"lose", "lost", "losing", "lossed", "burned", "burnt", "blew"}


# ---------- config ----------

def find_ffmpeg():
    found = shutil.which("ffmpeg")
    if found:
        return found
    pattern = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe")
    hits = sorted(glob.glob(pattern))
    if hits:
        return hits[-1]
    sys.exit("ffmpeg not found: run setup.ps1 or set \"ffmpeg\" in config.json")


def config():
    path = ROOT / "config.json"
    cfg = json.loads(path.read_text()) if path.exists() else {}
    cfg.setdefault("ffmpeg", find_ffmpeg())
    cfg.setdefault("whisper_python", str(Path.home() / ".venvs" / "autoclipper" / "Scripts" / "python.exe"))
    cfg.setdefault("python", sys.executable)
    cfg.setdefault("deliver_dir", str(Path.home() / "Downloads"))
    if not path.exists():
        path.write_text(json.dumps(cfg, indent=1))
    return cfg


def run(cmd, quiet=False):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        sys.exit(f"step failed: {' '.join(map(str, cmd[:3]))}...\n{out[-2000:]}")
    if out and not quiet:
        print("\n".join("    " + ln for ln in out.splitlines() if ln.strip()))
    return out


def ffprobe(cfg):
    p = Path(cfg["ffmpeg"])
    return str(p.with_name(p.name.replace("ffmpeg", "ffprobe"))) if p.parent != Path(".") else "ffprobe"


# ---------- prep pieces ----------

def loss_segment(reel, cfg):
    """The first clause where he talks about losing money, clipped to one continuous face shot.
    Returns (start, end) or None. This is the only place the money-burn edit goes."""
    sys.path.insert(0, str(ROOT))
    from talk_reel import load_sections, tidy_words
    from cuts import find_cuts
    words = tidy_words(json.loads((reel / "words.json").read_text(encoding="utf-8"))["words"])
    sections = load_sections(reel / "sections.json")
    src = json.loads((reel / "source.json").read_text())["video"]
    scene = find_cuts(cfg["ffmpeg"], src)
    for i, w in enumerate(words):
        if w["t"].strip(".,!?").lower() not in LOSS_WORDS:
            continue
        nxt = [x["t"].strip(".,!?").lower() for x in words[i + 1:i + 4]]
        money = any(re.fullmatch(r"\d{1,3}(,\d{2,3})+|\d{4,}|\d+k", t) or t in {"crore", "lakh", "rupees"} for t in nxt)
        if not money:
            continue
        a = i
        while a > 0 and words[a - 1]["t"][-1:] not in ".,!?":
            a -= 1
        b = i
        while b < len(words) - 1 and words[b]["t"][-1:] not in ".,!?":
            b += 1
        face = next((s for s in sections if s["kind"] == "face" and s["start"] <= w["s"] < s["end"]), None)
        if not face:
            continue
        edges = sorted({face["start"], face["end"], *[c for c in scene if face["start"] < c < face["end"]]})
        lo = max(e for e in edges if e <= w["s"])
        hi = min(e for e in edges if e > w["s"])
        t, end = max(words[a]["s"], lo), min(words[b]["e"], hi)
        # snap to the shot's edges when close, so the edit never switches look in the middle of a shot
        t = lo if t - lo < 0.5 else t
        end = hi if hi - end < 0.5 else end
        if end - t >= 1.2:
            return round(t, 2), round(min(end, t + 4.0), 2)
    return None


def export_segment(cfg, src, t, end, out):
    run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-ss", f"{t}", "-to", f"{end}",
         "-vf", "scale=1080:1920:flags=lanczos,setsar=1", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
         "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])


def write_flow_prompts(reel):
    sys.path.insert(0, str(ROOT))
    import moments
    cuts = json.loads((reel / "cuts.json").read_text(encoding="utf-8"))
    edits = json.loads((reel / "edits.json").read_text()) if (reel / "edits.json").exists() else []
    out = [f"FLOW PROMPTS FOR \"{reel.name}\"\n\n",
           "Generate each one in Google Flow, then save the result into THIS folder with the exact file name shown.\n",
           "Check the spelling on text clips and the lip sync on the money clip. Then tell Claude \"Flow clips are in\".\n",
           "Timing is automatic: the renderer fits every clip to the exact moment you say the words.\n"]
    for c in cuts:
        out.append(f"\n\nTEXT CUT  ·  save as {c['file']}  ·  at {c['t']:.2f}s while you say \"{c['text']}\"\n"
                   f"(Flow: text to video)\n\n{moments.prompt(c['kind'], c['text'], 'red_card')}\n")
    for e in edits:
        out.append(f"\n\nMONEY BURN  ·  save as {e['file']}  ·  {e['t']:.2f}-{e['end']:.2f}s\n"
                   f"(Flow: upload \"{e['segment']}\" from this folder as the video, then paste this)\n\n"
                   f"{MONEY_BURN_PROMPT}\n")
    (reel / "flow prompts.txt").write_text("".join(out).replace("·", "|"), encoding="utf-8")
    stale = reel / "text cuts.txt"
    if stale.exists():
        stale.unlink()


def cmd_prep(a, cfg):
    src = str(Path(a.video).resolve())
    name = a.name or Path(src).stem
    reel = REELS / name
    reel.mkdir(parents=True, exist_ok=True)
    (reel / "source.json").write_text(json.dumps({"video": src}))
    print(f"[1/6] transcribing {Path(src).name}")
    if not (reel / "words.json").exists():
        wav = reel / "audio16k.wav"
        run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-vn", "-ar", "16000", "-ac", "1", wav])
        run([cfg["whisper_python"], "-W", "ignore", ROOT / "transcribe.py", wav, reel / "words.json"])
        wav.unlink()
    print("[2/6] finding shots, his text cards and split screens")
    run([cfg["python"], ROOT / "sections.py", cfg["ffmpeg"], src, reel / "sections.json"])
    print("[3/6] looking for a money-loss line for the money-burn edit")
    seg = loss_segment(reel, cfg)
    if seg:
        t, end = seg
        segname = f"money segment {t:.2f}-{end:.2f}s.mp4"
        export_segment(cfg, src, t, end, reel / segname)
        (reel / "edits.json").write_text(json.dumps([{"file": "money.mp4", "segment": segname, "t": t, "end": end}], indent=1))
        print(f"    money burn at {t:.2f}-{end:.2f}s")
    else:
        (reel / "edits.json").write_text("[]")
        print("    no loss line, no money burn this time")
    print("[4/6] picking text-cut moments")
    cmd = [cfg["python"], ROOT / "moments.py", "--reel", reel]
    if a.only:
        cmd += ["--only", a.only]
    out = run(cmd, quiet=True)
    print("\n".join("    " + ln.strip() for ln in out.splitlines() if "PICK" in ln))
    write_flow_prompts(reel)
    print("[5/6] picking cover frames")
    run([cfg["python"], ROOT / "cover_pick.py", "--video", src, "--sections", reel / "sections.json",
         "--outdir", reel / "covers", "--ffmpeg", cfg["ffmpeg"]])
    print("[6/6] rendering a preview (no Flow clips yet)")
    render(reel, cfg, reel / f"{name} preview.mp4")
    print(f"\nready: {reel}\n  give him: flow prompts.txt, covers\\cover_1..3.png, {name} preview.mp4")


def cmd_repick(a, cfg):
    reel = REELS / a.name
    run([cfg["python"], ROOT / "moments.py", "--reel", reel, "--only", a.only])
    write_flow_prompts(reel)


def cmd_map(a, cfg):
    reel = REELS / a.name
    cuts = json.loads((reel / "cuts.json").read_text(encoding="utf-8"))
    hit = [c for c in cuts if c["text"] == a.text]
    if not hit:
        sys.exit(f"no cut with text {a.text!r}; cuts are {[c['text'] for c in cuts]}")
    hit[0]["file"] = a.file
    (reel / "cuts.json").write_text(json.dumps(cuts, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{a.text} -> {a.file}")


KNOWN = re.compile(r"(segment|preview|final)", re.I)


def cmd_status(a, cfg):
    reel = REELS / a.name
    cuts = json.loads((reel / "cuts.json").read_text(encoding="utf-8"))
    edits = json.loads((reel / "edits.json").read_text())
    wanted = {c["file"] for c in cuts} | {e["file"] for e in edits}
    for c in cuts:
        print(f"  text cut  {c['text']:16} {c['file']:20} {'OK' if (reel / c['file']).exists() else 'missing'}")
    for e in edits:
        print(f"  money     {e['t']:.2f}-{e['end']:.2f}s      {e['file']:20} {'OK' if (reel / e['file']).exists() else 'missing'}")
    extra = [p.name for p in reel.glob("*.mp4") if p.name not in wanted and not KNOWN.search(p.name)]
    if extra:
        print("  unassigned clips (check their frames, then `reel.py map`):", extra)


# ---------- render ----------

def render(reel, cfg, out, text=None):
    src = json.loads((reel / "source.json").read_text())["video"]
    cmd = [cfg["python"], ROOT / "talk_reel.py", "--video", src, "--words", reel / "words.json",
           "--sections", reel / "sections.json", "--fontsdir", CAP_FONTS, "--cuts", reel / "cuts.json",
           "--edits", reel / "edits.json", "--out", out, "--ffmpeg", cfg["ffmpeg"]]
    if text and text.text:
        cmd += ["--text", text.text, "--text-start", str(text.text_start), "--text-secs", str(text.text_secs)]
        if text.emoji:
            cmd += ["--emoji", text.emoji]
    log = run(cmd, quiet=True)
    print("\n".join("    " + ln.strip() for ln in log.splitlines() if re.search(r"cut:|edit:|wrote", ln)))


def check(cfg, src, out):
    """Same frame count as his source (nothing drifted) and loudness on target."""
    count = lambda p: run([ffprobe(cfg), "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                           "stream=nb_read_frames", "-of", "csv=p=0", p], quiet=True).strip()
    loud = run([cfg["ffmpeg"], "-hide_banner", "-nostats", "-i", out, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"],
               quiet=True)
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)
    pk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud)
    a, b = count(src), count(out)
    print(f"    frames {b} (source {a}){'' if a == b else '  MISMATCH'}, loudness {i[-1] if i else '?'} LUFS, "
          f"peak {pk[-1] if pk else '?'} dB")


def deliver(path, cfg, name):
    dst = Path(cfg["deliver_dir"]) / name
    k = 2
    while dst.exists():
        dst = dst.with_name(f"{Path(name).stem} v{k}{Path(name).suffix}")
        k += 1
    shutil.copy2(path, dst)
    return dst


def cmd_render(a, cfg):
    reel = REELS / a.name
    cmd_status(a, cfg)
    final = reel / f"{a.name} final.mp4"
    print("rendering")
    render(reel, cfg, final, a)
    src = json.loads((reel / "source.json").read_text())["video"]
    check(cfg, src, final)
    outs = [final]
    if a.cover_line:
        times = json.loads((reel / "covers" / "covers.json").read_text())
        t = float(a.cover[2:]) if a.cover.startswith("t=") else times[int(a.cover) - 1]
        cover = reel / f"{a.name} cover.jpg"
        run([cfg["python"], ROOT / "cover.py", "--video", src, "--t", t, "--line", a.cover_line, "--out", cover,
             "--ffmpeg", cfg["ffmpeg"]])
        outs.append(cover)
    if not a.no_deliver:
        for p in outs:
            print(f"    delivered {deliver(p, cfg, p.name)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep")
    p.add_argument("video")
    p.add_argument("--name")
    p.add_argument("--only", default="")
    p = sub.add_parser("repick")
    p.add_argument("name")
    p.add_argument("--only", required=True)
    p = sub.add_parser("map")
    p.add_argument("name")
    p.add_argument("file")
    p.add_argument("text")
    p = sub.add_parser("status")
    p.add_argument("name")
    p = sub.add_parser("render")
    p.add_argument("name")
    p.add_argument("--cover-line", default="")
    p.add_argument("--cover", default="1", help="1, 2, 3 (picked frames) or t=SECONDS")
    p.add_argument("--text", default="")
    p.add_argument("--text-start", type=float, default=0.0)
    p.add_argument("--text-secs", type=float, default=3.0)
    p.add_argument("--emoji", default="")
    p.add_argument("--no-deliver", action="store_true")
    a = ap.parse_args()
    cfg = config()
    {"prep": cmd_prep, "repick": cmd_repick, "map": cmd_map, "status": cmd_status, "render": cmd_render}[a.cmd](a, cfg)


if __name__ == "__main__":
    main()
