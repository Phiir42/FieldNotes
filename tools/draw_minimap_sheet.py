"""Draws map sheets for dungeons the game has no sheet for, from their
minimaps: the minimap is washed in parchment tones and laid on the real blank
parchment, cut to the dungeon's extent with a soft edge.

    python tools/draw_minimap_sheet.py [slug ...]

Reads refs/minimap/<slug>.png (see tools/fetch_minimap.py) and writes
tools/art/<slug>.png (1002x668). Per dungeon, SHEETS gives:
  crop  the part of the minimap shown, in minimap px (3:2; may overhang)
  mask  what part of that is the dungeon:
          "grey" / "dark"  everything but the minimap's flat grey / black surround
          [(x, y), ...]    a polygon, in sheet px
          None             everything the minimap has
(Alcaz Prison's plan of rooms is drawn by tools/draw_alcaz_prison.py instead.)
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_maps import blank_parchment, ROOT, W, H

SHEETS = {
    "blackmaw-hold": {"crop": (14, 156, 1835, 1371), "mask": "grey"},
    "the-drowned-city": {"crop": (710, 546, 2177, 1526), "mask": "dark"},
    "the-hall-of-thanes": {"crop": (1987, 2959, 3139, 3727), "mask": "grey"},
    "city-of-dalaran": {"crop": (745, 976, 1729, 1630),
                        "mask": [(501, 30), (640, 60), (740, 160), (790, 300), (770, 450), (700, 570), (600, 640),
                                 (480, 650), (380, 620), (290, 540), (240, 420), (235, 280), (280, 150), (380, 60)]},
    "ruins-of-lordaeron": {"crop": (367, 743, 1212, 1306),
                           "mask": [(225, 35), (480, 35), (490, 0), (540, 0), (545, 35), (785, 35), (790, 420),
                                    (710, 545), (520, 650), (330, 575), (225, 440)]},
    "kroldok-stronghold": {"crop": (307, 296, 1809, 1297),
                           "mask": [(610, 0), (750, 25), (800, 250), (720, 370), (600, 420), (570, 590), (420, 668),
                                    (205, 660), (195, 530), (225, 310), (390, 235), (510, 140)]},
    "the-shapers-terrace": {"crop": (-128, 512, 2176, 2048), "mask": None},
    # without the stray tiles top left and the snow (Dun Morogh, outside) bottom left
    "excavation-site-wetlands": {"crop": (486, 510, 3544, 2548),
                                 "mask": [(190, 20), (1002, 20), (1002, 668), (440, 668), (440, 485), (0, 485),
                                          (0, 185), (190, 185)]},
}
MARGIN = 34  # the parchment's own border: nothing is drawn on it


def f(img):
    return np.asarray(img).astype(np.float32) / 255


def largest(mask):
    """Tidy a boolean mask of 'not surround': close gaps, drop specks, and keep
    anything the surround does not reach from the sheet's edge (holes are inside)."""
    img = Image.fromarray((mask * 255).astype(np.uint8))
    img = img.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))      # close gaps
    img = img.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))      # drop specks
    framed = Image.new("L", (W + 2, H + 2), 0)
    framed.paste(img, (1, 1))
    ImageDraw.floodfill(framed, (0, 0), 128)                                         # the surround
    return np.asarray(framed)[1:-1, 1:-1] != 128


def draw(slug):
    spec = SHEETS[slug]
    src = Image.open(os.path.join(ROOT, "refs", "minimap", slug + ".png")).convert("RGBA")
    img = src.crop(spec["crop"]).resize((W, H), Image.LANCZOS)
    rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    alpha = f(img.getchannel("A"))
    lum = rgb.mean(axis=2)
    sat = rgb.max(axis=2) - rgb.min(axis=2)

    how = spec["mask"]
    if how == "grey":
        inside = largest((sat > 22) | (lum > 150) | (lum < 75))
    elif how == "dark":
        inside = largest(np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))) > 42)
    elif how:
        poly = Image.new("L", (W, H), 0)
        ImageDraw.Draw(poly).polygon(how, fill=255)
        inside = np.asarray(poly) > 127
    else:
        inside = np.ones((H, W), bool)
    inside = inside & (alpha > 0.5)
    inside[:MARGIN] = inside[-MARGIN:] = False
    inside[:, :MARGIN] = inside[:, -MARGIN:] = False
    hard = Image.fromarray((inside * 255).astype(np.uint8))
    feather = 3 if how in ("grey", "dark") else 14
    a = f(hard.filter(ImageFilter.MinFilter(2 * feather + 1)).filter(ImageFilter.GaussianBlur(feather)))
    if how in ("grey", "dark"):
        a = f(hard.filter(ImageFilter.GaussianBlur(1.5)))

    blank, _ = blank_parchment()
    page = blank.astype(np.float32)
    grain = page / page.mean(axis=(0, 1))

    # ink wash: mostly the minimap's light and dark in parchment browns, with a little of its colour
    lo, hi = np.percentile(lum[inside], [2, 98]) if inside.any() else (0, 255)
    t = np.clip((lum - lo) / max(hi - lo, 1), 0, 1)[..., None]
    ink, paper = np.array([62, 52, 42], np.float32), np.array([230, 216, 188], np.float32)  # greyer than the page, so all of it reads as drawing
    wash = ink * (1 - t) + paper * t
    colour = rgb * 0.75 + 45
    toned = (wash * 0.68 + colour * 0.32) * (0.7 + 0.3 * grain)

    shadow = f(hard.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(5)))
    out = page * (1 - 0.3 * (shadow * (1 - a))[..., None])
    out = out * (1 - a[..., None]) + toned * a[..., None]
    if how in ("grey", "dark"):
        edge = np.clip(f(hard.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(0.8))) - a, 0, 1)[..., None]
        out = out * (1 - 0.8 * edge) + ink * 0.8 * edge

    path = os.path.join(ROOT, "tools", "art", slug + ".png")
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path)
    print("wrote", path)


if __name__ == "__main__":
    for slug in sys.argv[1:] or SHEETS:
        draw(slug)
