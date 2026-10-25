"""The paper look (LOCKED 10-25): a creator tutorial's step-by-step look, built in Remotion (paper/src).

  py -3.14 paper\\paper.py prep NAME [VIDEO]      reels/NAME (after `reel.py cut`), or an edited VIDEO,
                                                  into the Remotion project
  py -3.14 paper\\paper.py still NAME 150 400 ...   frames as PNGs in reels/NAME/paper stills, to check beats
  py -3.14 paper\\paper.py render NAME            render, voice to -14 LUFS, no music, "NAME final.mp4"

Between prep and render Claude writes paper/src/beats.tsx for this reel (see README.md in this folder).
Per-reel pictures and clips the beats use go in reels/NAME/paper/ and are served as assets/<file>."""
import json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import face, talk_reel  # noqa: E402
from reel import REELS, config, reel_dir  # noqa: E402

PUBLIC = HERE / "public"
BEATS = HERE / "src" / "beats.tsx"
NPX = shutil.which("npx.cmd") or shutil.which("npx") or "npx"
NPM = shutil.which("npm.cmd") or shutil.which("npm") or "npm"


def probe(cfg, video):
    ffprobe = str(Path(cfg["ffmpeg"]).with_name("ffprobe.exe"))
    if not Path(ffprobe).exists():
        ffprobe = "ffprobe"
    out = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                          "stream=r_frame_rate,nb_read_packets:format=duration", "-of", "json", str(video)],
                         capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    num, den = d["streams"][0]["r_frame_rate"].split("/")
    return float(num) / float(den), float(d["format"]["duration"]), int(d["streams"][0]["nb_read_packets"])


def source_video(reel):
    cut = reel / "cut.mp4"
    if cut.exists():
        return cut
    src = reel / "source.json"
    if src.exists():
        return Path(json.loads(src.read_text(encoding="utf-8"))["video"])
    sys.exit(f"{reel.name}: no cut.mp4 or source.json; run `reel.py cut` (raw takes) or give paper.py prep the video")


def beats_reel():
    m = re.search(r'THIS REEL: "([^"]+)"', BEATS.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def cmd_prep(name, cfg, video_arg=None):
    if video_arg:
        (REELS / name).mkdir(parents=True, exist_ok=True)
        (REELS / name / "source.json").write_text(json.dumps({"video": str(Path(video_arg).resolve())}), encoding="utf-8")
    reel = reel_dir(name)
    video = source_video(reel)
    fps, dur, frames = probe(cfg, video)
    if not (reel / "words.json").exists():
        subprocess.run([cfg["whisper_python"], "-W", "ignore", str(HERE.parent / "transcribe.py"), str(video),
                        str(reel / "words.json")], check=True)
    words = json.loads((reel / "words.json").read_text(encoding="utf-8"))["words"]
    cut = reel / "cut.json"
    if cut.exists():
        clips = [{"t0": s["t0"], **{k: s["face"][k] for k in ("hair", "chin", "cx")}}
                 for s in json.loads(cut.read_text(encoding="utf-8"))["segments"]]
    else:
        f = face.measure(cfg["ffmpeg"], video, [(0, dur)], fps)[0] or {"hair": 0.36, "chin": 0.73, "cx": 0.5}
        clips = [{"t0": 0.0, **{k: f[k] for k in ("hair", "chin", "cx")}}]
    for c in clips:
        if c["chin"] > 0.9:   # a screen take: no face, keep its captions on screen if a face layout lands there
            print(f"  clip at {c['t0']:.2f}s has no face (chin {c['chin']}): give it a split or full layout")
    data = {"name": name, "fps": fps, "duration": round(dur, 4), "frames": frames, "clips": clips,
            "words": [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in words]}
    (HERE / "src" / "reel.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    PUBLIC.mkdir(exist_ok=True)
    shutil.copy2(video, PUBLIC / "cut.mp4")
    shutil.rmtree(PUBLIC / "sfx", ignore_errors=True)
    shutil.copytree(HERE.parent / "sfx", PUBLIC / "sfx", ignore=shutil.ignore_patterns("*.txt"))
    shutil.rmtree(PUBLIC / "assets", ignore_errors=True)
    if (reel / "paper").exists():
        shutil.copytree(reel / "paper", PUBLIC / "assets")
    if not (HERE / "node_modules").exists():
        subprocess.run([NPM, "ci", "--no-audit", "--no-fund"], cwd=HERE, check=True)
    print(f"  {name}: {dur:.2f}s, {frames} frames at {fps:g} fps, {len(clips)} clips, {len(words)} words")
    if beats_reel() != name:
        print(f"  beats.tsx is still for {beats_reel()!r}: write this reel's beats (keep the old one in paper/examples/)")


def check_beats(name):
    if beats_reel() != name:
        sys.exit(f'beats.tsx is for {beats_reel()!r}, not {name!r}: write its beats first (THIS REEL: "{name}")')
    data = json.loads((HERE / "src" / "reel.json").read_text(encoding="utf-8"))
    if data["name"] != name:
        sys.exit(f"the Remotion project holds {data['name']!r}: run `paper.py prep {name}` first")
    return data


def cmd_still(name, frames, cfg):
    check_beats(name)
    out = reel_dir(name) / "paper stills"
    out.mkdir(exist_ok=True)
    for f in frames:
        subprocess.run([NPX, "remotion", "still", "src/index.ts", "Reel", str(out / f"f{int(f):04d}.png"),
                        f"--frame={int(f)}", "--scale=0.5", "--log=error"], cwd=HERE, check=True)
    print(f"  {len(frames)} stills in {out}")


def cmd_render(name, cfg):
    data = check_beats(name)
    reel = reel_dir(name)
    raw = reel / "paper render.mp4"
    subprocess.run([NPX, "remotion", "render", "src/index.ts", "Reel", str(raw), "--codec=h264", "--crf=17",
                    "--log=error"], cwd=HERE, check=True)
    final = reel / f"{name} final.mp4"
    af = f"{talk_reel.loudnorm_filter(cfg['ffmpeg'], str(raw))},{talk_reel.LIMITER}"   # no music, his call 10-25
    subprocess.run([cfg["ffmpeg"], "-v", "error", "-y", "-i", str(raw), "-af", af, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-movflags", "+faststart", str(final)], check=True)
    _, _, frames = probe(cfg, final)
    if frames != data["frames"]:
        print(f"  WARNING: {frames} frames, the source has {data['frames']}")
    r = subprocess.run([cfg["ffmpeg"], "-hide_banner", "-nostats", "-i", str(final), "-vn", "-af",
                        f"loudnorm={talk_reel.LOUDNESS}:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"): r.stderr.rindex("}") + 1])
    shutil.copy2(final, Path(cfg["deliver_dir"]) / final.name)
    print(f"  {final.name}: {frames} frames, {m['input_i']} LUFS, true peak {m['input_tp']} dBTP, in {cfg['deliver_dir']}")


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("prep", "still", "render"):
        sys.exit(__doc__)
    cfg = config()
    cmd, name = sys.argv[1], sys.argv[2]
    if cmd == "prep":
        cmd_prep(name, cfg, sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "still":
        cmd_still(name, sys.argv[3:] or ["30"], cfg)
    else:
        cmd_render(name, cfg)
