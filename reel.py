"""Aarit's Reel engine: one video in, his locked look out (STYLE.md). The whole process is in README.md.

  1. ASK HIM FIRST: "Do you want motion graphic text in this video?"
  2. py -3.14 reel.py prep "<video>" --text-cuts yes|no [--name NAME]
        transcribe, exact shot cuts, money-burn line, motion text picks (if yes), 3 cover frames, and the
        Flow folder in Downloads ("NAME Flow") when there is anything to make in Flow.
     py -3.14 reel.py repick NAME --only "₹1 CRORE|DAY 2"      Claude's override of the motion text picks
     py -3.14 reel.py visual NAME START END "what changes"     add an in-scene Flow visual on that shot
     py -3.14 reel.py visual NAME --drop V1                    take one out again
  3. He makes the clips in Flow and saves them into the Flow folder.
     py -3.14 reel.py status NAME                              collects his clips, says what is missing
     py -3.14 reel.py map NAME "<flow file>.mp4" T2            a clip with Flow's own name goes to its slot
  4. py -3.14 reel.py render NAME --cover-line "his words" [--cover t=43] [--text "..." --text-start S]
        final Reel + cover into Downloads, checked for frame count and loudness.
     py -3.14 reel.py preview NAME                             same render, kept in reels/NAME (no delivery)
     py -3.14 reel.py split NAME                               redo the 9 s parts in the Flow folder

No B-roll, ever. Paths live in config.json. A Reel's working files live in reels/NAME (never committed)."""
import argparse, glob, json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REELS = ROOT / "reels"
FLOW_MAX = 9.0           # Google Flow only edits clips of 10 s or less; 9 s leaves a margin
PARTS_DIR = "whole reel in 9s parts"

# the money-burn edit he approved, word for word (option 4 on hedge 1, made with Omni edit mode)
MONEY_BURN_PROMPT = (
    "Edit the provided video. Make glowing cash banknotes drift slowly upward in the air around the young man "
    "like floating embers, and as they rise past his head they burn away into small red sparks and ash that fade "
    "near the top of the frame. A faint red glow pulses on the wall behind him. Keep it subtle and cinematic: the "
    "notes stay around the edges and behind him, never covering his face or the microphone. Keep the person in the "
    "provided video exactly as he is: same face, same lip movements, same expressions, same hands, same microphone, "
    "same clothes. Keep the camera framing and movement unchanged, the same length and timing as the original, "
    "vertical 9:16. No text, letters, numbers, logos or watermarks anywhere.")
# every in-scene visual ends with this, so Flow leaves him and the timing alone
KEEP_PERSON = (
    "Keep it subtle and cinematic. Keep the person in the provided video exactly as he is: same face, same lip "
    "movements, same head and body movements, same expressions, same hands, same clothes. Keep the camera framing "
    "and movement unchanged, the same length and exactly the same timing as the original, frame for frame, "
    "vertical 9:16. No text, letters, numbers, logos or watermarks anywhere.")
LOSS_WORDS = {"lose", "lost", "losing", "lossed", "burned", "burnt", "blew"}


# ---------- config and helpers ----------

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
    # every step prints UTF-8 (a ₹ in motion text crashed moments.py on the Windows console encoding)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env)
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        sys.exit(f"step failed: {' '.join(map(str, cmd[:3]))}...\n{out[-2000:]}")
    if out and not quiet:
        print("\n".join("    " + ln for ln in out.splitlines() if ln.strip()))
    return out


def ffprobe(cfg):
    p = Path(cfg["ffmpeg"])
    return str(p.with_name(p.name.replace("ffmpeg", "ffprobe"))) if p.parent != Path(".") else "ffprobe"


def duration(cfg, path):
    return float(run([ffprobe(cfg), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                     quiet=True).strip())


def load(reel, name, default):
    p = reel / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save(reel, name, data):
    (reel / name).write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def reel_dir(name):
    reel = REELS / name
    if not (reel / "source.json").exists():
        sys.exit(f"no reel called {name!r}; run prep first (reels: {sorted(p.name for p in REELS.iterdir())})")
    return reel


def source(reel):
    return json.loads((reel / "source.json").read_text())["video"]


def flow_dir(cfg, name):
    """The ONE folder he works from in Flow: prompts, upload clips, 9 s parts, and his results."""
    return Path(cfg["deliver_dir"]) / f"{name} Flow"


def words_of(reel):
    sys.path.insert(0, str(ROOT))
    from talk_reel import tidy_words
    return tidy_words(load(reel, "words.json", {"words": []})["words"])


def said(reel, t, end):
    return " ".join(w["t"] for w in words_of(reel) if t - 0.05 <= w["s"] < end).strip()


def export_segment(cfg, src, t, end, out):
    run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-ss", f"{t}", "-to", f"{end}",
         "-vf", "scale=1080:1920:flags=lanczos,setsar=1", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
         "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])


# ---------- prep pieces ----------

def loss_segment(reel):
    """The first clause where he talks about losing money, clipped to one continuous face shot.
    Returns (start, end) or None. This is the only place the money-burn edit goes."""
    sys.path.insert(0, str(ROOT))
    from talk_reel import load_sections
    words = words_of(reel)
    sections = load_sections(reel / "sections.json")
    scene = load(reel, "shots.json", {"cuts": []})["cuts"]
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


def add_upload(cfg, reel, slot, kind, t, end, prompt):
    """An in-scene edit slot: the exact shot is exported for him to upload, and remembered in edits.json."""
    src = source(reel)
    seg = f"{kind} {slot} {t:.2f}-{end:.2f}s.mp4"
    export_segment(cfg, src, t, end, reel / seg)
    edits = [e for e in load(reel, "edits.json", []) if e["file"] != f"{slot}.mp4"]
    edits.append({"file": f"{slot}.mp4", "kind": kind, "segment": seg, "t": t, "end": end,
                  "say": said(reel, t, end), "prompt": prompt})
    save(reel, "edits.json", sorted(edits, key=lambda e: e["t"]))


def upload_name(e):
    return f"upload {Path(e['file']).stem} ({e['t']:.1f}-{e['end']:.1f}s).mp4"


def split_parts(cfg, src, folder):
    """His whole Reel in parts of at most 9 s, so any part of it can go into Flow."""
    dur = duration(cfg, src)
    n = int(-(-dur // FLOW_MAX))
    edges = [min(i * FLOW_MAX, dur) for i in range(n + 1)]
    if n > 1 and edges[-1] - edges[-2] < 3.0:  # no stub of a part: share the length out evenly instead
        edges = [dur * i / n for i in range(n + 1)]
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.mp4"):
        old.unlink()
    for i in range(n):
        t, end = edges[i], edges[i + 1]
        export_segment(cfg, src, round(t, 3), round(end, 3), folder / f"part {i + 1} ({t:.0f}-{end:.0f}s).mp4")
    return n


def write_flow(cfg, reel):
    """Build (or refresh) the Flow folder: prompts in play order, upload clips, 9 s parts.
    The prompts file lives ONLY in this folder. Nothing to make in Flow means no folder."""
    sys.path.insert(0, str(ROOT))
    import moments
    cuts = load(reel, "cuts.json", [])
    edits = load(reel, "edits.json", [])
    folder = flow_dir(cfg, reel.name)
    if not cuts and not edits:
        print("    nothing to make in Flow for this video")
        return None
    folder.mkdir(parents=True, exist_ok=True)
    items = []
    for c in cuts:
        items.append((c["t"], f"MOTION TEXT | save as {c['file']} | at {c['t']:.2f}s while you say \"{c['text']}\"\n"
                              f"(Flow: text to video, no upload)", moments.prompt(c["kind"], c["text"], "red_card")))
    for e in edits:
        label = "MONEY BURN" if e.get("kind") == "money" else "VISUAL"
        prompt = e.get("prompt") or (MONEY_BURN_PROMPT if e.get("kind") == "money" else
                                     "Edit the provided video. " + KEEP_PERSON)
        items.append((e["t"], f"{label} | save as {e['file']} | {e['t']:.2f}-{e['end']:.2f}s while you say "
                              f"\"{e.get('say') or said(reel, e['t'], e['end'])}\"\n"
                              f"(Flow: upload \"{upload_name(e)}\" from this folder as the video, then paste this)",
                      prompt))
        shutil.copy2(reel / e["segment"], folder / upload_name(e))
    wanted = {upload_name(e) for e in edits}
    for old in folder.glob("upload *.mp4"):
        if old.name not in wanted:
            old.unlink()
    head = (f"FLOW PROMPTS FOR \"{reel.name}\"\n\n"
            "1. Make each clip below in Google Flow.\n"
            "   MOTION TEXT: text to video, paste the prompt, no upload.\n"
            "   VISUAL or MONEY BURN: upload the matching \"upload ...\" clip from this folder, then paste the prompt.\n"
            "2. Check the spelling on every motion text clip.\n"
            "3. Save every result back into THIS folder. Name it as shown (T1.mp4, V1.mp4 ...), or keep Flow's own\n"
            "   name: Claude matches clips by what is in them.\n"
            "4. Tell Claude \"Flow clips are in\".\n\n"
            f"The \"{PARTS_DIR}\" folder is your full video in pieces Flow can edit, if you ever need them.\n")
    body = "".join(f"\n\n{h}\n\n{p}\n" for _, h, p in sorted(items, key=lambda i: i[0]))
    (folder / "flow prompts.txt").write_text(head + body, encoding="utf-8")
    if not (folder / PARTS_DIR).exists():
        n = split_parts(cfg, source(reel), folder / PARTS_DIR)
        print(f"    {n} parts of max {FLOW_MAX:.0f} s in \"{PARTS_DIR}\"")
    for stale in (reel / "flow prompts.txt", reel / "text cuts.txt"):
        stale.unlink(missing_ok=True)
    print(f"    Flow folder: {folder} ({len(cuts)} motion text, {len(edits)} upload)")
    return folder


# ---------- commands ----------

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
        wav.unlink(missing_ok=True)
    print("[2/6] shots on the exact frame, his text cards and split screens")
    run([cfg["python"], ROOT / "sections.py", cfg["ffmpeg"], src, reel / "sections.json"])
    sys.path.insert(0, str(ROOT))
    import render as renderer
    save(reel, "shots.json", {"cuts": renderer.exact_cuts(cfg["ffmpeg"], src)})
    print("[3/6] looking for a money-loss line for the money-burn edit")
    edits = [e for e in load(reel, "edits.json", []) if e.get("kind") != "money" and e["file"] != "money.mp4"]
    save(reel, "edits.json", edits)
    seg = loss_segment(reel)
    if seg:
        add_upload(cfg, reel, "M1", "money", seg[0], seg[1], MONEY_BURN_PROMPT)
        print(f"    money burn at {seg[0]:.2f}-{seg[1]:.2f}s")
    else:
        print("    no loss line, no money burn this time")
    # motion graphic text is optional per video: he is asked every time, and the answer is kept with the reel
    save(reel, "options.json", {"text_cuts": a.text_cuts})
    if a.text_cuts == "yes":
        print("[4/6] picking motion graphic text moments")
        cmd = [cfg["python"], ROOT / "moments.py", "--reel", reel]
        if a.only:
            cmd += ["--only", a.only]
        out = run(cmd, quiet=True)
        print("\n".join("    " + ln.strip() for ln in out.splitlines() if "PICK" in ln))
    else:
        save(reel, "cuts.json", [])
        print("[4/6] no motion graphic text in this video (his choice)")
    print("[5/6] picking cover frames")
    run([cfg["python"], ROOT / "cover_pick.py", "--video", src, "--sections", reel / "sections.json",
         "--outdir", reel / "covers", "--ffmpeg", cfg["ffmpeg"]], quiet=True)
    print(f"    {reel / 'covers'} (cover_1..3.png)")
    print("[6/6] Flow folder")
    write_flow(cfg, reel)
    print(f"\nready: {reel}\n  next: Claude reviews the picks and adds any visuals (reel.py visual), then he makes the "
          f"Flow clips; with nothing for Flow, go straight to render")


def cmd_repick(a, cfg):
    reel = reel_dir(a.name)
    if load(reel, "options.json", {}).get("text_cuts") == "no":
        sys.exit("he said no motion graphic text for this video; re-run prep with --text-cuts yes if he changes his mind")
    run([cfg["python"], ROOT / "moments.py", "--reel", reel, "--only", a.only])
    write_flow(cfg, reel)


def cmd_visual(a, cfg):
    reel = reel_dir(a.name)
    if a.drop:
        slot = Path(a.drop).stem.upper()
        edits = load(reel, "edits.json", [])
        save(reel, "edits.json", [e for e in edits if Path(e["file"]).stem.upper() != slot])
        print(f"dropped {slot}")
        write_flow(cfg, reel)
        return
    if a.start is None or a.end is None or not a.change:
        sys.exit('usage: reel.py visual NAME START END "what changes in the shot"')
    src = source(reel)
    dur = duration(cfg, src)
    cuts = [0.0] + load(reel, "shots.json", {"cuts": []})["cuts"] + [dur]
    # a visual covers whole shots: snap to the real cuts around the times given
    t = max(c for c in cuts if c <= a.start + 0.25)
    end = min(c for c in cuts if c >= a.end - 0.25)
    if end - t > FLOW_MAX:
        sys.exit(f"{t:.2f}-{end:.2f}s is {end - t:.1f} s; Flow edits at most 10 s, pick a shorter stretch")
    clash = [c["text"] for c in load(reel, "cuts.json", []) if c["t"] < end and c["end"] > t]
    if clash:
        print(f"    note: motion text {clash} sits inside this shot; it covers the visual while it is up")
    edits = load(reel, "edits.json", [])
    taken = {Path(e["file"]).stem for e in edits}
    slot = next(f"V{k}" for k in range(1, 99) if f"V{k}" not in taken)
    prompt = f"Edit the provided video. {a.change.strip()} {KEEP_PERSON}"
    add_upload(cfg, reel, slot, "visual", round(t, 2), round(end, 2), prompt)
    print(f"{slot}: {t:.2f}-{end:.2f}s (snapped to the shot) while he says \"{said(reel, t, end)}\"")
    write_flow(cfg, reel)


def slots(reel):
    """(slot file, what it is) for every Flow clip this reel uses."""
    out = [(c["file"], f"motion text \"{c['text']}\"") for c in load(reel, "cuts.json", []) if c.get("kind") != "broll"]
    out += [(e["file"], f"{e.get('kind', 'visual')} {e['t']:.2f}-{e['end']:.2f}s") for e in load(reel, "edits.json", [])]
    return out


def cmd_status(a, cfg):
    """Collect his clips from the Flow folder into the reel, then say what is in and what is missing."""
    reel = reel_dir(a.name)
    folder = flow_dir(cfg, a.name)
    wanted = slots(reel)
    names = {f for f, _ in wanted}
    if folder.exists():
        for f in names:
            got = folder / f
            if got.exists() and (not (reel / f).exists() or got.stat().st_mtime > (reel / f).stat().st_mtime):
                shutil.copy2(got, reel / f)
    for f, what in wanted:
        print(f"  {Path(f).stem:4} {what:40} {'in' if (reel / f).exists() else 'missing'}")
    if not wanted:
        print("  no Flow clips needed for this reel")
    if folder.exists():
        mapped = load(reel, "flow_map.json", {})
        loose = [p for p in folder.glob("*.mp4")
                 if p.name not in names and p.name not in mapped and not p.name.startswith("upload ")]
        texts = {c["file"]: c["text"] for c in load(reel, "cuts.json", [])}
        for p in loose:
            low = p.name.lower().replace("%20", " ").replace("_", " ")
            guess = next((Path(f).stem for f in names if f"upload {Path(f).stem.lower()}" in low), None)
            guess = guess or next((Path(f).stem for f, txt in texts.items()
                                   if any(len(w) > 1 and w in low for w in txt.lower().split())), None)
            print(f"  not matched yet: {p.name}" + (f"  (looks like {guess})" if guess else ""))
        if loose:
            print("  check each one's frames, then: reel.py map NAME \"<file>\" <slot>")


def cmd_map(a, cfg):
    reel = reel_dir(a.name)
    slot = Path(a.slot).stem.upper() + ".mp4"
    if slot not in {f for f, _ in slots(reel)}:
        sys.exit(f"no slot {slot}; this reel has {[f for f, _ in slots(reel)]}")
    src = Path(a.file)
    if not src.is_absolute():
        src = next((p for p in (flow_dir(cfg, a.name) / a.file, reel / a.file) if p.exists()), src)
    if not src.exists():
        sys.exit(f"can't find {a.file}")
    shutil.copy2(src, reel / slot)
    mapped = load(reel, "flow_map.json", {})
    mapped[src.name] = slot
    save(reel, "flow_map.json", mapped)
    print(f"{src.name} -> {slot}")


def cmd_split(a, cfg):
    reel = reel_dir(a.name)
    n = split_parts(cfg, source(reel), flow_dir(cfg, a.name) / PARTS_DIR)
    print(f"{n} parts of max {FLOW_MAX:.0f} s in {flow_dir(cfg, a.name) / PARTS_DIR}")


# ---------- render ----------

def render(reel, cfg, out, a=None):
    cmd = [cfg["python"], ROOT / "render.py", "--reel", reel, "--out", out]
    if a is not None and getattr(a, "text", ""):
        cmd += ["--text", a.text, "--text-start", str(a.text_start), "--text-secs", str(a.text_secs)]
        if a.emoji:
            cmd += ["--emoji", a.emoji]
    log = run(cmd, quiet=True)
    print("\n".join("    " + ln.strip() for ln in log.splitlines()
                    if re.search(r"leak|cut:|visual:|accent:|text:|wrote", ln)))


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
    shutil.copy2(path, dst)
    return dst


def cmd_preview(a, cfg):
    reel = reel_dir(a.name)
    cmd_status(a, cfg)
    out = reel / f"{a.name} preview.mp4"
    print("rendering a preview (about 0.5 s per frame)")
    render(reel, cfg, out)
    check(cfg, source(reel), out)


def cmd_render(a, cfg):
    reel = reel_dir(a.name)
    cmd_status(a, cfg)
    final = reel / f"{a.name} final.mp4"
    print("rendering (about 0.5 s per frame)")
    render(reel, cfg, final, a)
    src = source(reel)
    check(cfg, src, final)
    outs = [final]
    if a.cover_line:
        times = load(reel, "covers/covers.json", [])
        t = float(a.cover[2:]) if a.cover.startswith("t=") else times[int(a.cover) - 1]
        cover = reel / f"{a.name} cover.jpg"
        run([cfg["python"], ROOT / "cover.py", "--video", src, "--t", t, "--line", a.cover_line, "--out", cover,
             "--ffmpeg", cfg["ffmpeg"]])
        outs.append(cover)
    if not a.no_deliver:
        for p in outs:
            print(f"    delivered {deliver(p, cfg, p.name)}")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # ₹ in motion text vs the Windows console
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep")
    p.add_argument("video")
    p.add_argument("--text-cuts", required=True, choices=["yes", "no"],
                   help="motion graphic text in this video? ASK HIM every time, never assume")
    p.add_argument("--name")
    p.add_argument("--only", default="")
    p = sub.add_parser("repick")
    p.add_argument("name")
    p.add_argument("--only", required=True)
    p = sub.add_parser("visual")
    p.add_argument("name")
    p.add_argument("start", type=float, nargs="?")
    p.add_argument("end", type=float, nargs="?")
    p.add_argument("change", nargs="?", default="", help="what changes in the shot, e.g. 'the sunny garden turns stormy'")
    p.add_argument("--drop", default="", help="slot to remove, e.g. V1")
    p = sub.add_parser("status")
    p.add_argument("name")
    p = sub.add_parser("map")
    p.add_argument("name")
    p.add_argument("file")
    p.add_argument("slot", help="T1, V2, M1 ...")
    p = sub.add_parser("split")
    p.add_argument("name")
    p = sub.add_parser("preview")
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
    {"prep": cmd_prep, "repick": cmd_repick, "visual": cmd_visual, "status": cmd_status, "map": cmd_map,
     "split": cmd_split, "preview": cmd_preview, "render": cmd_render}[a.cmd](a, cfg)


if __name__ == "__main__":
    main()
