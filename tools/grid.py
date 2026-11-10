"""Draws a coordinate grid over reference maps, for placing seeds by eye.

    python tools/grid.py blackrock-depths-1 [more names...]

Writes refs/grid/<name>.png: lines every 50 px, labelled every 100 px.
"""
import os, sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "refs")


def main():
    os.makedirs(os.path.join(REFS, "grid"), exist_ok=True)
    for name in sys.argv[1:]:
        im = Image.open(os.path.join(REFS, name + ".png")).convert("RGB")
        d = ImageDraw.Draw(im, "RGBA")
        for x in range(0, im.width, 50):
            d.line((x, 0, x, im.height), fill=(255, 255, 255, 150 if x % 100 == 0 else 60))
            if x % 100 == 0:
                d.text((x + 2, 2), str(x), fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
        for y in range(0, im.height, 50):
            d.line((0, y, im.width, y), fill=(255, 255, 255, 150 if y % 100 == 0 else 60))
            if y % 100 == 0:
                d.text((2, y + 2), str(y), fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
        im.save(os.path.join(REFS, "grid", name + ".png"))
        print("refs/grid/" + name + ".png")


if __name__ == "__main__":
    main()
