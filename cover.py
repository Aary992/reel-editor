"""Cover image: a chosen frame plus Aarit's cover line, in the same Instagram-text look as his on-screen
text, kept inside the 3:4 area the profile grid shows."""
import argparse, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FONT = str(Path(__file__).parent / "fonts" / "figtree-700" / "figtree-700.ttf")   # same family as the captions
GRID_TOP = (H - W * 4 // 3) // 2      # the grid crops covers to the middle 3:4: y 240..1680


def wrap(text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and font.getlength(trial) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--t", type=float, required=True, help="frame time in seconds")
    ap.add_argument("--line", required=True, help="cover line, exactly as Aarit wrote it")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ffmpeg", default="ffmpeg")
    ap.add_argument("--px", type=int, default=86)
    ap.add_argument("--y", type=float, default=0.22, help="centre of the text block, fraction of height")
    a = ap.parse_args()

    frame = Path(a.out).with_suffix(".frame.png")
    subprocess.run([a.ffmpeg, "-v", "error", "-y", "-ss", f"{a.t}", "-i", a.video, "-frames:v", "1",
                    "-vf", f"scale={W}:{H}:flags=lanczos,setsar=1", str(frame)], check=True)
    base = Image.open(frame).convert("RGBA")
    font = ImageFont.truetype(FONT, a.px)
    lines = wrap(a.line, font, W * 0.8)
    line_h = round(a.px * 1.2)
    top = max(GRID_TOP + 40, round(H * a.y - line_h * len(lines) / 2))
    text, shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0)), Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td, sd = ImageDraw.Draw(text), ImageDraw.Draw(shadow)
    for i, ln in enumerate(lines):
        x = (W - font.getlength(ln)) / 2
        y = top + i * line_h
        sd.text((x, y + 4), ln, font=font, fill=(0, 0, 0, 170), stroke_width=4, stroke_fill=(0, 0, 0, 170))
        td.text((x, y), ln, font=font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 100))
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7)))
    base.alpha_composite(text)
    base.convert("RGB").save(a.out, quality=95)
    frame.unlink()
    print(f"wrote {a.out}: {len(lines)} lines {lines}")


if __name__ == "__main__":
    main()
