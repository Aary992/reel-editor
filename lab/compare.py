"""Side-by-side of the style options: a labelled 3x2 grid video, a stills sheet, and copies in Downloads.

  py -3.14 render.py --reel "reels/<name>" --look glass --out "reels/<name>/lab/glass.mp4"   (one per look)
  py -3.14 lab/compare.py --reel "reels/<name>"
"""
import argparse, json, shutil, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OPTIONS = [("0 current", None), ("1 glass", "glass"), ("2 spotlight", "spotlight"),
           ("3 cinematic", "cinematic"), ("4 keynote", "keynote"), ("5 kinetic", "kinetic")]
STILLS = [1.2, 3.9, 14.6, 41.6, 48.6, 51.5]
TW, TH = 360, 640


def label_png(text, path):
    im = Image.new("RGBA", (TW, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, 10 + 22 * len(text) + 24, 54), radius=16, fill=(0, 0, 0, 170))
    d.text((22, 32), text.upper(), font=ImageFont.truetype("C:/Windows/Fonts/seguisb.ttf", 26),
           fill=(255, 255, 255, 255), anchor="lm")
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reel", required=True)
    a = ap.parse_args()
    reel = ROOT / a.reel
    lab = reel / "lab"
    ff = json.loads((ROOT / "config.json").read_text())["ffmpeg"]
    deliver = Path(json.loads((ROOT / "config.json").read_text())["deliver_dir"]) / f"{reel.name} style options"
    deliver.mkdir(parents=True, exist_ok=True)
    files = []
    for name, look in OPTIONS:
        src = reel / f"{reel.name} preview.mp4" if look is None else lab / f"{look}.mp4"
        files.append((name, src))
        shutil.copy2(src, deliver / f"{reel.name} {name}.mp4")
    # grid video, audio from the current version
    inputs, fc = [], ""
    for i, (name, src) in enumerate(files):
        lp = lab / f"label_{i}.png"
        label_png(name, lp)
        inputs += ["-i", str(src), "-i", str(lp)]
        fc += f"[{2 * i}:v]scale={TW}:{TH},setsar=1[v{i}];[v{i}][{2 * i + 1}:v]overlay=0:0[l{i}];"
    fc += "".join(f"[l{i}]" for i in range(6)) + "xstack=inputs=6:layout=0_0|w0_0|w0+w1_0|0_h0|w0_h0|w0+w1_h0[g]"
    grid = deliver / f"{reel.name} all 6 side by side.mp4"
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[g]",
                    "-map", "0:a", "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(grid)], check=True)
    # stills sheet: one row per option, one column per moment
    sw, sh = 240, 427
    sheet = Image.new("RGB", (sw * len(STILLS), sh * len(files)), (0, 0, 0))
    for r, (name, src) in enumerate(files):
        for c, t in enumerate(STILLS):
            raw = subprocess.run([ff, "-v", "error", "-ss", str(t), "-i", str(src), "-frames:v", "1",
                                  "-vf", f"scale={sw}:{sh},setsar=1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                 capture_output=True, check=True).stdout
            sheet.paste(Image.frombytes("RGB", (sw, sh), raw), (c * sw, r * sh))
        lab_img = Image.open(lab / f"label_{r}.png")
        sheet.paste(lab_img, (0, r * sh), lab_img)
    sheet.save(deliver / f"{reel.name} stills sheet.jpg", quality=90)
    print(f"delivered to {deliver}")


if __name__ == "__main__":
    main()
