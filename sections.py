import subprocess, sys, json
import numpy as np
ff, src, out = sys.argv[1:4]
W, H, FPS = 54, 96, 10
raw = subprocess.run([ff, "-v", "error", "-i", src, "-vf", f"fps={FPS},scale={W}:{H},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(float)
rows = []
for i, f in enumerate(fr):
    top, bot = f[: H * 4 // 10].mean(), f[H * 5 // 10:].mean()
    # row-wise jump to find a horizontal seam (split screen edge)
    prof = f.mean(axis=1)
    jumps = np.abs(np.diff(prof))
    seam = int(jumps[20:80].argmax() + 20)
    rows.append((i / FPS, round(f.mean()), round(top), round(bot), seam, round(float(jumps[seam]))))
kind = []
for t, m, top, bot, seam, j in rows:
    if m < 12: k = "black"
    elif m > 185 and f is not None and bot > 180: k = "card"
    elif j > 25 and bot < 60 and top > 60: k = "split"
    else: k = "face"
    kind.append(k)
# collapse into sections
sec = []
for (t, *_), k in zip(rows, kind):
    if sec and sec[-1]["kind"] == k: sec[-1]["end"] = round(t + 1 / FPS, 2)
    else: sec.append({"kind": k, "start": round(t, 2), "end": round(t + 1 / FPS, 2)})
seams = [r[4] for r, k in zip(rows, kind) if k == "split"]
json.dump({"sections": sec, "split_seam_frac": (np.median(seams) / H) if seams else None}, open(out, "w"), indent=1)
for s in sec: print(f'{s["kind"]:6} {s["start"]:6.2f} -> {s["end"]:6.2f}')
print("split seam at", round(np.median(seams) / H, 3) if seams else None, "of height")
