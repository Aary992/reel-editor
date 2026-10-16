"""Find hard cuts in an edited Reel and check whether the edit already has a whoosh on them."""
import argparse, json, re, subprocess
import numpy as np

SR = 16000


def find_cuts(ffmpeg, video, threshold=0.3, min_gap=0.5):
    r = subprocess.run([ffmpeg, "-hide_banner", "-i", video, "-vf",
                        f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    times = [float(t) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]
    cuts = []
    for t in times:
        if not cuts or t - cuts[-1] >= min_gap:
            cuts.append(round(t, 2))
    return cuts


def hiss_energy(ffmpeg, video):
    """Per-10ms energy above 5 kHz: voice has little up there, whooshes have a lot."""
    raw = subprocess.run([ffmpeg, "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", str(SR),
                          "-af", "highpass=f=5000,highpass=f=5000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop = SR // 100
    n = len(x) // hop
    return np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ffmpeg", default="ffmpeg")
    a = ap.parse_args()

    cuts = find_cuts(a.ffmpeg, a.video)
    e = hiss_energy(a.ffmpeg, a.video)
    base = float(np.median(e))
    # speech sibilants also live above 5 kHz, so compare against ordinary 0.6 s windows of this clip
    normal = np.array([e[i:i + 60].max() / base for i in range(0, len(e) - 60, 30)])
    limit = float(np.percentile(normal, 99))
    report = []
    for c in cuts:
        i = int(c * 100)
        win = e[max(0, i - 30): i + 30]                      # +-0.3 s around the cut
        ratio = float(win.max() / base) if len(win) else 0.0
        report.append({"t": c, "hiss_ratio": round(ratio, 1), "has_sfx": ratio > limit})
        print(f"  cut at {c:6.2f}s  hiss x{ratio:5.1f} (speech p99 x{limit:.1f})  {'existing SFX?' if ratio > limit else ''}")
    json.dump({"cuts": report}, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
