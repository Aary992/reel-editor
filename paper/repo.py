"""The repo look (10-30): a copy of a creator's "someone made a Claude repo" reel (Downloads/Video-16746.mp4).
Whole reel split: light grey panel on top with one animated UI card per beat (GitHub repo card, Claude Code
terminal, checklist doc, impressions counter, comment box), his talking head below. Blue two-line hook title on
the seam for the first sentence, then UPPERCASE pixel captions, lime on a blue box, on the seam.

  py -3.14 paper\repo.py prep NAME [VIDEO]       reels/NAME (after `reel.py cut`), or an edited VIDEO
  py -3.14 paper\repo.py still NAME 150 400 ...    frames as PNGs in reels/NAME/repo stills
  py -3.14 paper\repo.py render NAME             render, voice to -14 LUFS, no music, "NAME final.mp4"

Between prep and render Claude writes paper/src/repo/beats.tsx for this reel. Shares the paper project's
node_modules; its media goes in paper/public/repo/."""
import json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paper  # noqa: E402  (probe, source_video, face, talk_reel, reel helpers)

SRC = HERE / "src" / "repo"
PUBLIC = HERE / "public" / "repo"
BEATS = SRC / "beats.tsx"
ENTRY = "src/repo/index.ts"


def beats_reel():
    m = re.search(r'THIS REEL: "([^"]+)"', BEATS.read_text(encoding="utf-8")) if BEATS.exists() else None
    return m.group(1) if m else None


def cmd_prep(name, cfg, video_arg=None):
    if video_arg:
        (paper.REELS / name).mkdir(parents=True, exist_ok=True)
        (paper.REELS / name / "source.json").write_text(json.dumps({"video": str(Path(video_arg).resolve())}), encoding="utf-8")
    reel = paper.reel_dir(name)
    video = paper.source_video(reel)
    fps, dur, frames = paper.probe(cfg, video)
    if not (reel / "words.json").exists():
        subprocess.run([cfg["whisper_python"], "-W", "ignore", str(HERE.parent / "transcribe.py"), str(video),
                        str(reel / "words.json")], check=True)
    words = json.loads((reel / "words.json").read_text(encoding="utf-8"))["words"]
    cut = reel / "cut.json"
    if cut.exists():
        clips = [{"t0": s["t0"], **{k: s["face"][k] for k in ("hair", "chin", "cx")}}
                 for s in json.loads(cut.read_text(encoding="utf-8"))["segments"]]
    else:
        f = paper.face.measure(cfg["ffmpeg"], video, [(0, dur)], fps)[0] or {"hair": 0.36, "chin": 0.73, "cx": 0.5}
        clips = [{"t0": 0.0, **{k: f[k] for k in ("hair", "chin", "cx")}}]
    data = {"name": name, "fps": fps, "duration": round(dur, 4), "frames": frames, "clips": clips,
            "words": [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in words]}
    SRC.mkdir(exist_ok=True)
    (SRC / "reel.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    PUBLIC.mkdir(parents=True, exist_ok=True)
    shutil.copy2(video, PUBLIC / "cut.mp4")
    shutil.rmtree(PUBLIC / "sfx", ignore_errors=True)
    shutil.copytree(HERE.parent / "sfx", PUBLIC / "sfx", ignore=shutil.ignore_patterns("*.txt"))
    shutil.rmtree(PUBLIC / "assets", ignore_errors=True)
    if (reel / "repo").exists():
        shutil.copytree(reel / "repo", PUBLIC / "assets")
    if not (HERE / "node_modules").exists():
        subprocess.run([paper.NPM, "ci", "--no-audit", "--no-fund"], cwd=HERE, check=True)
    print(f"  {name}: {dur:.2f}s, {frames} frames at {fps:g} fps, {len(clips)} clips, {len(words)} words")
    if beats_reel() != name:
        print(f"  repo/beats.tsx is for {beats_reel()!r}: write this reel's beats first")


def check_beats(name):
    if beats_reel() != name:
        sys.exit(f'repo/beats.tsx is for {beats_reel()!r}, not {name!r}: write its beats first (THIS REEL: "{name}")')
    data = json.loads((SRC / "reel.json").read_text(encoding="utf-8"))
    if data["name"] != name:
        sys.exit(f"the repo project holds {data['name']!r}: run `repo.py prep {name}` first")
    return data


def cmd_still(name, frames):
    check_beats(name)
    out = paper.reel_dir(name) / "repo stills"
    out.mkdir(exist_ok=True)
    for f in frames:
        subprocess.run([paper.NPX, "remotion", "still", ENTRY, "Repo", str(out / f"f{int(f):04d}.png"),
                        f"--frame={int(f)}", "--scale=0.5", "--log=error"], cwd=HERE, check=True)
    print(f"  {len(frames)} stills in {out}")


def cmd_render(name, cfg):
    data = check_beats(name)
    reel = paper.reel_dir(name)
    raw = reel / "repo render.mp4"
    subprocess.run([paper.NPX, "remotion", "render", ENTRY, "Repo", str(raw), "--codec=h264", "--crf=17",
                    "--log=error"], cwd=HERE, check=True)
    final = reel / f"{name} final.mp4"
    af = f"{paper.talk_reel.loudnorm_filter(cfg['ffmpeg'], str(raw))},{paper.talk_reel.LIMITER}"   # no music
    subprocess.run([cfg["ffmpeg"], "-v", "error", "-y", "-i", str(raw), "-af", af, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-movflags", "+faststart", str(final)], check=True)
    _, _, frames = paper.probe(cfg, final)
    if frames != data["frames"]:
        print(f"  WARNING: {frames} frames, the source has {data['frames']}")
    r = subprocess.run([cfg["ffmpeg"], "-hide_banner", "-nostats", "-i", str(final), "-vn", "-af",
                        f"loudnorm={paper.talk_reel.LOUDNESS}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"): r.stderr.rindex("}") + 1])
    shutil.copy2(final, Path(cfg["deliver_dir"]) / final.name)
    print(f"  {final.name}: {frames} frames, {m['input_i']} LUFS, true peak {m['input_tp']} dBTP, in {cfg['deliver_dir']}")


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("prep", "still", "render"):
        sys.exit(__doc__)
    cfg = paper.config()
    cmd, name = sys.argv[1], sys.argv[2]
    if cmd == "prep":
        cmd_prep(name, cfg, sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "still":
        cmd_still(name, sys.argv[3:] or ["30"])
    else:
        cmd_render(name, cfg)
