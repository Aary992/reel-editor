"""Where his face is in a frame, without a model: skin-tone pixels, the biggest blob in the upper part of the
frame, his chin where that blob narrows into the neck, and the top of his hair above it.

The story look uses it to keep app UI above his head (never on his face), to keep captions off his mouth
and to anchor the jump-cut punch-ins on his face. All values are fractions of the frame (0..1)."""
from collections import deque
import numpy as np
from PIL import Image, ImageFilter

SW, SH = 135, 240        # analysis size: 1/8 of 1080x1920, square pixels


def skin_mask(rgb):
    """Skin in YCrCb (the classic box, a little wider on Cr for warm room light)."""
    a = rgb.astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cr = (r - y) * 0.713 + 128
    cb = (b - y) * 0.564 + 128
    return (cr >= 136) & (cr <= 178) & (cb >= 80) & (cb <= 128) & (y > 45) & (y < 245)


def blobs(mask):
    """Connected regions of a boolean mask (4-neighbour), biggest first, as lists of (row, col)."""
    seen = np.zeros_like(mask, bool)
    h, w = mask.shape
    out = []
    for r0, c0 in zip(*np.nonzero(mask)):
        if seen[r0, c0]:
            continue
        q, pix = deque([(r0, c0)]), []
        seen[r0, c0] = True
        while q:
            r, c = q.popleft()
            pix.append((r, c))
            for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= rr < h and 0 <= cc < w and mask[rr, cc] and not seen[rr, cc]:
                    seen[rr, cc] = True
                    q.append((rr, cc))
        out.append(pix)
    return sorted(out, key=len, reverse=True)


def locate(img):
    """Face of one frame (a PIL image of any size): {hair, top, eyes, chin, cx, cy, w} as fractions, or None."""
    small = img.convert("RGB").resize((SW, SH), Image.BILINEAR)
    m = skin_mask(np.asarray(small))
    # tidy the mask: close pinholes (eyes, mouth), drop specks
    mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    m = np.asarray(mi) > 127
    best, best_score = None, 0.0
    for pix in blobs(m)[:6]:
        if len(pix) < 0.012 * SW * SH:
            break
        rows = np.array([p[0] for p in pix])
        cols = np.array([p[1] for p in pix])
        cy, cx = rows.mean() / SH, cols.mean() / SW
        # a face sits in the upper two thirds and near the middle; hands and arms sit lower or at the sides
        score = len(pix) * (1.0 if cy < 0.62 else 0.35) * (1.0 - min(abs(cx - 0.5), 0.5))
        if score > best_score:
            best, best_score = (rows, cols), score
    if best is None:
        return None
    rows, cols = best
    blob = np.zeros((SH, SW), bool)
    blob[rows, cols] = True
    widths = blob.sum(axis=1)
    r_top = int(rows.min())
    # the cheeks: widest row in the upper part of the blob (the neck and shoulders can be wider lower down)
    span = int(rows.max()) - r_top + 1
    upper = range(r_top, r_top + max(3, int(span * 0.55)))
    r_wide = max(upper, key=lambda r: widths[r])
    w_max = max(1, int(widths[r_wide]))
    top = next((r for r in range(r_top, r_wide + 1) if widths[r] >= 0.3 * w_max), r_top)
    # chin: going down from the cheeks, the first row where the blob narrows into the neck
    chin = None
    for r in range(r_wide + 1, min(SH, r_wide + int(w_max * 1.6))):
        if widths[r] < 0.62 * w_max:
            chin = r
            break
    if chin is None or chin - top < 0.8 * w_max:
        chin = int(top + 1.3 * w_max)
    c_in = np.nonzero(blob[r_wide])[0]
    c0, c1 = int(c_in.min()), int(c_in.max())
    # hair: dark pixels above the face, in the face's columns, connected upward from the forehead
    lum = np.asarray(small.convert("L"), np.float32)
    hair = top
    for r in range(top - 1, max(-1, top - int(0.45 * w_max) - 1), -1):   # hair is never taller than ~half the face is wide
        dark = (lum[r, c0:c1 + 1] < 70).mean()
        if dark < 0.18:
            # allow a one-row gap (a highlight on the hair)
            if r > 0 and (lum[r - 1, c0:c1 + 1] < 70).mean() >= 0.18:
                continue
            break
        hair = r
    return {"hair": round(hair / SH, 4), "top": round(top / SH, 4), "chin": round(min(chin, SH - 1) / SH, 4),
            "eyes": round((top + 0.33 * (chin - top)) / SH, 4), "cx": round((c0 + c1) / 2 / SW, 4),
            "cy": round((top + chin) / 2 / SH, 4), "w": round((c1 - c0 + 1) / SW, 4)}


def summarise(faces):
    """One face for a shot from several frames: medians (a hand on the mic can merge into the chin on one
    frame), with the most cautious hair line (the highest)."""
    faces = [f for f in faces if f]
    if not faces:
        return None
    out = {k: round(float(np.median([f[k] for f in faces])), 4) for k in faces[0]}
    out["hair"] = round(min(f["hair"] for f in faces), 4)
    return out


def measure(ffmpeg, video, spans, fps, picks=(0.2, 0.5, 0.8)):
    """His face in each (start, end) span of a video, from a few frames per span, in one decode."""
    import subprocess
    want = {}
    for k, (a, b) in enumerate(spans):
        for p in picks:
            want.setdefault(int((a + (b - a) * p) * fps), []).append(k)
    proc = subprocess.Popen([ffmpeg, "-v", "error", "-i", str(video), "-vf", f"scale={SW}:{SH}:flags=area",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    got = [[] for _ in spans]
    n, size = 0, SW * SH * 3
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        if n in want:
            f = locate(Image.frombuffer("RGB", (SW, SH), buf, "raw", "RGB", 0, 1))
            for k in want[n]:
                got[k].append(f)
        n += 1
    proc.wait()
    return [summarise(g) for g in got]
