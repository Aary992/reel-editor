"""Pick cover-frame candidates: sharp, steady frames from face shots (not cards or split screens)."""
import argparse, json, subprocess
from pathlib import Path
import numpy as np
from talk_reel import load_sections, W, H

SW, SH, FPS = 270, 480, 4


def frames(ffmpeg, video):
    raw = subprocess.run([ffmpeg, "-v", "error", "-i", video, "-vf",
                          f"fps={FPS},scale={SW}:{SH},setsar=1,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, SH, SW).astype(np.float32)


def sharpness(f):
    c = f[SH // 5: SH * 7 // 10, SW // 5: SW * 4 // 5]          # where the face sits
    lap = -4 * c[1:-1, 1:-1] + c[:-2, 1:-1] + c[2:, 1:-1] + c[1:-1, :-2] + c[1:-1, 2:]
    return float(lap.var())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--sections", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--ffmpeg", default="ffmpeg")
    ap.add_argument("--n", type=int, default=3)
    a = ap.parse_args()

    faces = [s for s in load_sections(a.sections) if s["kind"] == "face"]
    fr = frames(a.ffmpeg, a.video)
    sharp = np.array([sharpness(f) for f in fr])
    motion = np.array([0.0] + [float(np.abs(fr[i] - fr[i - 1]).mean()) for i in range(1, len(fr))])
    z = lambda v: (v - v.mean()) / (v.std() + 1e-6)
    score = z(sharp) - z(motion)

    ok = [i for i in range(len(fr)) if any(s["start"] + 0.3 <= i / FPS <= s["end"] - 0.3 for s in faces)]
    picks = []
    for i in sorted(ok, key=lambda i: -score[i]):
        if all(abs(i - p) / FPS >= 2.0 for p in picks):    # spread the options out
            picks.append(i)
        if len(picks) == a.n:
            break

    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    times = []
    for rank, i in enumerate(picks, 1):
        t = i / FPS
        dst = out / f"cover_{rank}.png"
        subprocess.run([a.ffmpeg, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", a.video, "-frames:v", "1",
                        "-vf", f"scale={W}:{H}:flags=lanczos,setsar=1", str(dst)], check=True)
        times.append(round(t, 2))
        print(f"  cover_{rank}: t={t:.2f}s  sharp={sharp[i]:.0f}  motion={motion[i]:.2f}  score={score[i]:.2f}")
    (out / "covers.json").write_text(json.dumps(times))


if __name__ == "__main__":
    main()
