"""Subtle keyframed face zoom and Flow B-roll slots for talking-head Reels.

Zoom is applied in Python with sub-pixel crop boxes (ffmpeg's zoompan snaps to whole pixels,
which shows up as shake on slow zooms), eased with smootherstep so it reads like keyframes."""
import re, subprocess
from pathlib import Path
import numpy as np
from PIL import Image

ZOOM_IN = 1.06      # gentle: the most it ever gets is 6% bigger
ZOOM_Y = 0.66       # zoom around mouth height so the face stays put and captions below stay clear
MAX_EASE = 3.0      # an ease takes the whole sentence, capped at 3 s, then holds


def smootherstep(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * u * (u * (6 * u - 15) + 10)


def plan_zoom(sections, scene_cuts, words):
    """Keyframes per face shot: each sentence eases between 1.00 and ZOOM_IN. Cards and split screens stay 1.0."""
    shots = []
    for s in sections:
        if s["kind"] != "face":
            continue
        edges = [s["start"]] + [c for c in scene_cuts if s["start"] + 0.3 < c < s["end"] - 0.3] + [s["end"]]
        shots += list(zip(edges, edges[1:]))
    keys = []   # (start, end, from, to)
    for a, b in shots:
        ws = [w for w in words if a - 0.05 <= w["s"] < b]
        starts = [a] + [w2["s"] for w1, w2 in zip(ws, ws[1:]) if w1["t"][-1:] in ".,!?" and w2["s"] < b - 0.5]
        level = 1.0
        for i, s0 in enumerate(starts):
            s1 = starts[i + 1] if i + 1 < len(starts) else b
            target = ZOOM_IN if level < (1 + ZOOM_IN) / 2 else 1.0
            keys.append((s0, s1, level, target))
            level = target
    return keys


def zoom_at(t, keys):
    for s0, s1, z0, z1 in keys:
        if s0 <= t < s1:
            dur = min(s1 - s0, MAX_EASE)
            return z0 + (z1 - z0) * smootherstep((t - s0) / dur)
    return 1.0


def edit_filters(edits, w, h, fps_str, first_input=1):
    """Lay his Flow-edited segments over the source, each squeezed or stretched to its exact slot.

    Omni can hand back a clip a few frames longer or at another frame rate; fitting it to the slot
    keeps his lips on his original audio. Returns (input args, filter text, output label)."""
    args = ["-i", None]                      # placeholder for the source, filled by the caller
    fc = f"[0:v]scale={w}:{h}:flags=lanczos,setsar=1,format=yuv420p[e0]"
    last = "e0"
    for k, e in enumerate(edits, 1):
        stretch = e["dur"] / e["clip_dur"]
        args += ["-i", str(e["path"])]
        fc += (f";[{first_input + k - 1}:v]setpts=(PTS-STARTPTS)*{stretch:.5f}+{e['t']}/TB,fps={fps_str},"
               f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h},setsar=1,"
               f"format=yuv420p[c{k}];[{last}][c{k}]overlay=0:0:eof_action=pass:"
               f"enable='gte(t,{e['t']})*lt(t,{e['end']})'[e{k}]")
        last = f"e{k}"
    return args, fc, last


def pipe_zoom(ffmpeg, video, w, h, fps, keys, sink, edits=(), fps_str=None):
    """Decode at w x h (with any edited segments laid in), zoom each frame, write raw yuv420p to sink.

    Works on the Y, U and V planes directly: going through RGB and back shifted his skin tones
    about 4 levels darker, while staying in YUV leaves colour exactly as the source has it."""
    if edits:
        args, fc, last = edit_filters(edits, w, h, fps_str or str(fps))
        args[1] = video
        cmd = [ffmpeg, "-v", "error", *args, "-filter_complex", fc, "-map", f"[{last}]"]
    else:
        cmd = [ffmpeg, "-v", "error", "-i", video, "-vf", f"scale={w}:{h}:flags=lanczos,setsar=1"]
    src = subprocess.Popen(cmd + ["-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE)
    ysz, csz = w * h, (w // 2) * (h // 2)
    n = 0
    while True:
        buf = src.stdout.read(ysz + 2 * csz)
        if len(buf) < ysz + 2 * csz:
            break
        z = zoom_at(n / fps, keys)
        if z > 1.0005:
            bw, bh = w / z, h / z
            x0, y0 = (w - bw) * 0.5, (h - bh) * ZOOM_Y
            planes = [(buf[:ysz], w, h, 1), (buf[ysz:ysz + csz], w // 2, h // 2, 2),
                      (buf[ysz + csz:], w // 2, h // 2, 2)]
            out = []
            for data, pw, ph, k in planes:
                im = Image.frombuffer("L", (pw, ph), data, "raw", "L", 0, 1)
                box = (x0 / k, y0 / k, (x0 + bw) / k, (y0 + bh) / k)
                out.append(im.resize((pw, ph), Image.BICUBIC, box=box).tobytes())
            buf = b"".join(out)
        sink.write(buf)
        n += 1
    src.wait()
    return n


LAND_AT = 0.85   # the cut's animation should finish 85% of the way through the spoken words, then hold
CUT_FADE_IN, CUT_FADE_OUT = 0.1, 0.07   # seconds: soft dissolve into and out of a text cut


def src_fps(ffmpeg, path):
    probe = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"(\d+(?:\.\d+)?) fps", probe)
    return float(m.group(1)) if m else 24.0


def motion_span(ffmpeg, path, rel=0.04):
    """When does a Flow text clip actually animate? Returns (start, settle, duration) in clip seconds,
    from per-frame differences: dead frames before the motion and the long still hold after it are found."""
    rate = src_fps(ffmpeg, path)
    raw = subprocess.run([ffmpeg, "-v", "error", "-i", str(path), "-vf", "scale=96:170,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 170, 96).astype(np.float32)
    if len(fr) < 3:
        return 0.0, 0.0, len(fr) / rate
    diff = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    # relative to the clip's own biggest move, so the slow tail of an ease-out still counts as motion
    on = diff > max(0.05, rel * diff.max())
    # only sustained runs count: Flow clips have lone one-frame blips (compression keyframes) long after
    # the text has settled, and trusting those made the animation look 2.5x longer than it is
    runs, i = [], 0
    while i < len(on):
        if on[i]:
            j = i
            while j + 1 < len(on) and on[j + 1]:
                j += 1
            if j - i + 1 >= 3:
                runs.append((i, j))
            i = j + 1
        else:
            i += 1
    if not runs:
        return 0.0, 0.0, len(fr) / rate
    return runs[0][0] / rate, (runs[-1][1] + 1) / rate, len(fr) / rate


def auto_time(ffmpeg, cut):
    """Fill in from/speed so the clip's animation lands just as he finishes saying the words."""
    start, settle, dur = motion_span(ffmpeg, cut["path"])
    cut = {**cut, "src_fps": src_fps(ffmpeg, cut["path"])}
    window = cut["end"] - cut["t"]
    anim = settle - start
    if anim <= 0.05:
        return {**cut, "from": 0.0, "speed": 1.0}
    # speed up a slow animation to fit; never slow one down (slow-mo text reads as sluggish), it just holds
    speed = min(max(anim / (LAND_AT * window), 1.0), 3.0)
    return {**cut, "from": round(max(0.0, start - 1 / 30), 3), "speed": round(speed, 3),
            "anim": (round(start, 2), round(settle, 2))}


def cut_filters(cuts, first_input, fps, w, h, last):
    """Hard-cut to each Flow text clip full-screen for its slot (after the zoom, so graphics never zoom).
    `from` skips into the clip, `speed` > 1 plays it faster to squeeze a slow animation into a short slot.
    Returns (input args, filter text, new last label)."""
    args, fc = [], ""
    for k, s in enumerate(cuts):
        idx = first_input + k
        dur, speed = s["end"] - s["t"], s.get("speed", 1.0)
        args += ["-i", str(s["path"])]
        # Smoothness without artefacts: when the clip is sped up enough that every output frame gets a
        # different source frame, just pick the nearest real frame (no repeats, nothing invented).
        # Only if frames would have to repeat, blend neighbours instead. Motion-compensated interpolation
        # (minterpolate mci) tore fast-sliding letters apart, so it is not used.
        num, den = (str(fps).split("/") + ["1"])[:2]
        per_out = speed * s.get("src_fps", 24.0) / (float(num) / float(den))
        retime = f"fps={fps}" if per_out >= 1.0 else f"minterpolate=fps={fps}:mi_mode=blend"
        # iOS-style soft cut: a 3-frame dissolve in and 2-frame dissolve out instead of a hard cut
        fade = (f"format=yuva420p,fade=t=in:st={s['t']}:d={CUT_FADE_IN}:alpha=1,"
                f"fade=t=out:st={max(s['t'], s['end'] - CUT_FADE_OUT):.3f}:d={CUT_FADE_OUT}:alpha=1")
        fc += (f";[{idx}:v]trim=start={s.get('from', 0.0)}:duration={dur * speed + 0.15:.3f},"
               f"setpts=(PTS-STARTPTS)/{speed}+{s['t']}/TB,{retime},"
               f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h},setsar=1,{fade}[ct{k}];"
               f"[{last}][ct{k}]overlay=0:0:eof_action=pass:enable='gte(t,{s['t']})*lt(t,{s['end']})'[cv{k}]")
        last = f"cv{k}"
    return args, fc, last
