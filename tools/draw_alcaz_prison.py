"""Draws tools/art/alcaz-prison.png: a map sheet for Alcaz Prison, which the
game has no sheet for, in the style of the game's own dungeon sheets (flat
pale floors with a dark painted outline, on the real blank parchment).

    python tools/draw_alcaz_prison.py

The floor plan is traced from the instance's minimap
(refs/minimap/alcaz-prison.png, see tools/fetch_minimap.py). Coordinates
below are in a 1002x668 crop of that minimap (minimap px 120..450, 170..390);
place() moves them onto the sheet.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_maps import blank_parchment, ROOT, W, H

SS = 3                      # supersampling
SCALE, CX, CY = 0.84, 505, 330   # shrink the traced plan about its centre...
TO = (501, 342)             # ...and put that centre here on the sheet

RECTS = [
    (392, 25, 440, 105), (402, 105, 430, 240),      # north cell and its passage
    (522, 25, 570, 105), (530, 105, 558, 470),      # north cell and the long spine south
    (352, 140, 595, 168),                           # upper cross passage
    (292, 118, 340, 205),                           # north-west cell
    (185, 228, 270, 276),                           # west hall
    (365, 235, 612, 300),                           # main hall
    (408, 300, 424, 315), (470, 300, 486, 315),     # its two alcoves
    (612, 238, 725, 266), (722, 222, 825, 288),     # passage east and the gatehouse
    (297, 310, 338, 360), (218, 358, 415, 406),     # south of the west chamber: cross hall
    (305, 406, 330, 440),
    (446, 325, 642, 372), (446, 390, 642, 436),     # the two cell blocks
    (422, 488, 500, 536), (592, 488, 668, 536),     # wings of the south chamber
    (522, 558, 570, 632),
]
CIRCLES = [
    (643, 153, 48),                                 # round room, north-east
    (316, 520, 72), (316, 458, 40), (316, 592, 40), (248, 522, 34), (382, 522, 32),  # clover chamber
]
OCTAGONS = [(318, 258, 56), (545, 512, 52)]         # west and south chambers
TINTS = [  # (x, y, radius, colour): the boss chambers, washed with colour as the game's sheets do
    (316, 520, 100, (150, 70, 60)),
]


def place(x, y):
    return ((x - CX) * SCALE + TO[0]) * SS, ((y - CY) * SCALE + TO[1]) * SS


def main():
    mask = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(mask)
    for x0, y0, x1, y1 in RECTS:
        d.rectangle([place(x0, y0), place(x1, y1)], fill=255)
    for x, y, r in CIRCLES:
        d.ellipse([place(x - r, y - r), place(x + r, y + r)], fill=255)
    for x, y, r in OCTAGONS:
        k = r * 0.414
        pts = [(x - k, y - r), (x + k, y - r), (x + r, y - k), (x + r, y + k),
               (x + k, y + r), (x - k, y + r), (x - r, y + k), (x - r, y - k)]
        d.polygon([place(*p) for p in pts], fill=255)
    mask = mask.resize((W, H), Image.LANCZOS)

    def f(img):
        return np.asarray(img).astype(np.float32) / 255

    floor = f(mask)
    wall = np.clip(f(mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(0.8))) - floor, 0, 1)
    shadow = f(mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(5)))
    inner = 1 - f(mask.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(2.5)))  # near a wall, inside

    blank, _ = blank_parchment()
    page = blank.astype(np.float32)
    grain = page / page.mean(axis=(0, 1))                      # the parchment's own mottling
    rng = np.random.default_rng(7)
    noise = np.asarray(Image.fromarray((rng.random((H, W)) * 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255 - 0.5

    stone = np.array([203, 183, 138], np.float32) * (0.55 + 0.45 * grain) * (1 + 0.10 * noise[..., None])
    yy, xx = np.mgrid[0:H, 0:W]
    for x, y, r, colour in TINTS:
        px, py = place(x, y)
        near = np.clip(1.15 - np.hypot(xx - px / SS, yy - py / SS) / (r * SCALE), 0, 1)[..., None]
        stone = stone * (1 - 0.45 * np.minimum(near * 3, 1)) + np.array(colour, np.float32) * 1.25 * 0.45 * np.minimum(near * 3, 1)
    stone = stone * (1 - 0.22 * (inner * floor)[..., None])     # floors darken toward the walls

    out = page * (1 - 0.35 * (shadow * (1 - floor))[..., None])  # soft shadow on the page
    out = out * (1 - floor[..., None]) + stone * floor[..., None]
    line = np.array([88, 62, 34], np.float32) * (0.8 + 0.2 * grain)
    out = out * (1 - 0.9 * wall[..., None]) + line * 0.9 * wall[..., None]

    path = os.path.join(ROOT, "tools", "art", "alcaz-prison.png")
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
