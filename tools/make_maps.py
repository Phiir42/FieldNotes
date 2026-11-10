"""Builds the journal's map textures and FieldNotes/Maps.lua from the retail
reference maps in refs/ and the area definitions in map_defs.py.

    python tools/make_maps.py            # textures + Maps.lua
    python tools/make_maps.py --preview  # also refs/preview/<floor>.png

How a map is split up:
  1. The blank parchment is the per-pixel median of every reference map: the
     drawings sit in different places, so the median has none of them.
  2. Whatever differs from the blank on one map is that map's drawing.
  3. Drawing pixels inside a floor's decor boxes, or far from every seed, are
     decoration; the rest go to the area with the nearest seed point.
  4. Each area becomes one texture: the original pixels, transparent outside
     the area, to be laid over the blank parchment when the area is found.
"""
import glob, os, sys

import numpy as np
from PIL import Image, ImageFilter

from map_defs import MAPS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "refs")
OUT = os.path.join(ROOT, "FieldNotes", "Maps")
LUA = os.path.join(ROOT, "FieldNotes", "Maps.lua")
W, H = 1002, 668
SCALE = 0.5          # textures are stored at this fraction of the reference size
FULL = (512, 256)    # whole-sheet textures are squeezed to a power of two
REACH = 150          # px: drawing further than this from every seed is decoration
THRESHOLD = 26       # colour difference from the blank that counts as drawing
GROW = 9             # px the drawing mask is grown, to keep soft shadows
OVERLAP = 5          # px a piece reaches into its neighbours, so no seam shows
FEATHER = 3          # px blur on piece edges


def load(name):
    return np.asarray(Image.open(os.path.join(REFS, name + ".png")).convert("RGB")).astype(np.int16)


def blank_parchment():
    paths = sorted(glob.glob(os.path.join(REFS, "*-[0-9].png")))
    stack = np.stack([np.asarray(Image.open(p).convert("RGB")) for p in paths])
    return np.median(stack, axis=0).astype(np.int16), len(paths)


def grow(mask, px):
    """mask: float array 0..1 -> grown by px, as float 0..1."""
    im = Image.fromarray((mask * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * px + 1))).astype(np.float32) / 255


def blur(mask, px):
    im = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(px))).astype(np.float32) / 255


def pow2(n):
    p = 16
    while p < n:
        p *= 2
    return p


def split(floor, blank):
    """-> (original RGB, [(key, alpha array)]) with keys 'decor', 'start' or an area name."""
    img = load(floor["ref"])
    drawing = (np.abs(img - blank).max(axis=2) > THRESHOLD).astype(np.float32)
    drawing = drawing * (blur(drawing, 4) > 0.18)  # drop stray specks of noise
    drawing = blur(grow(drawing, GROW), FEATHER)

    decor = np.zeros((H, W), bool)
    for l, t, r, b in floor.get("decor", []):
        decor[t:b, l:r] = True

    names, seeds = [], []
    for name, pts in [("start", floor.get("start", []))] + list(floor["areas"].items()):
        for p in pts:
            names.append(name)
            seeds.append(p)
    ys, xs = np.mgrid[0:H, 0:W]
    best = np.full((H, W), np.inf, np.float32)
    owner = np.zeros((H, W), np.int32)
    for i, (sx, sy) in enumerate(seeds):
        d = (xs - sx) ** 2 + (ys - sy) ** 2
        closer = d < best
        best[closer] = d[closer]
        owner[closer] = i
    owner_name = np.array(names)[owner]
    decor |= best > REACH * REACH

    pieces = [("decor", drawing * decor)]
    for name in dict.fromkeys(names):
        cell = ((owner_name == name) & ~decor).astype(np.float32)
        pieces.append((name, drawing * blur(grow(cell, OVERLAP), FEATHER)))
    return img.astype(np.uint8), pieces


def save_piece(img, alpha, path):
    """Crop to the piece, scale, pad to power-of-two, save. -> (x, y, w, h, u, v) or None."""
    rows, cols = np.where(alpha > 0.01)
    if len(rows) == 0:
        return None
    x0, x1 = max(cols.min() - 2, 0), min(cols.max() + 3, W)
    y0, y1 = max(rows.min() - 2, 0), min(rows.max() + 3, H)
    crop = np.dstack([img[y0:y1, x0:x1], (alpha[y0:y1, x0:x1] * 255).astype(np.uint8)])
    w, h = max(1, round((x1 - x0) * SCALE)), max(1, round((y1 - y0) * SCALE))
    crop = np.asarray(Image.fromarray(crop).resize((w, h), Image.LANCZOS))
    tw, th = pow2(w), pow2(h)
    rgba = np.zeros((th, tw, 4), np.uint8)
    rgba[:h, :w] = crop
    # repeat edge colours into the padding so filtering never pulls in black
    rgba[:h, w:, :3] = rgba[:h, w - 1:w, :3]
    rgba[h:, :, :3] = rgba[h - 1:h, :, :3]
    Image.fromarray(rgba).save(path)
    return x0, y0, x1 - x0, y1 - y0, w / tw, h / th


def lua_piece(tex, box):
    return '{ tex = DIR .. "%s", x = %d, y = %d, w = %d, h = %d, u = %.5f, v = %.5f }' % ((tex,) + box)


def main():
    preview = "--preview" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    for old in glob.glob(os.path.join(OUT, "*.tga")):
        os.remove(old)
    blank, count = blank_parchment()
    Image.fromarray(blank.astype(np.uint8)).resize(FULL, Image.LANCZOS).save(os.path.join(OUT, "parchment.tga"))
    print(f"parchment.tga from {count} reference maps")

    out = [
        "-- Dungeon maps. GENERATED by tools/make_maps.py from tools/map_defs.py: edit those.",
        "--",
        "-- Unlike everything else in the journal the maps ship with the addon, because",
        "-- the game gives addons no position inside instances to draw from. A map still",
        "-- starts as blank parchment: each area's piece of the drawing is laid on it",
        "-- when the journal records that area (see CheckArea in Record.lua).",
        "--",
        "-- ns.Maps[instanceID] = { floor, ... }, a floor being",
        "--   full   the complete sheet, shown once every area is found",
        "--   decor  the title banner and illustration, always shown",
        "--   start  the part visible on arrival (the entrance), if on this floor",
        "--   areas  { [ns:AreaKey(name)] = piece }",
        "--   count  how many different area pieces the floor has",
        "-- A piece is { tex, x, y, w, h, u, v }: its place on the %dx%d sheet and" % (W, H),
        "-- how much of its (power-of-two) texture is used.",
        "local _, ns = ...",
        "",
        'local DIR = "Interface\\\\AddOns\\\\FieldNotes\\\\Maps\\\\"',
        "ns.MAP_REF_W, ns.MAP_REF_H = %d, %d" % (W, H),
        'ns.MAP_BLANK = DIR .. "parchment"',
        "",
        "-- Area names are matched ignoring case, punctuation and a leading \"The\".",
        "function ns:AreaKey(name)",
        '\treturn (name:lower():gsub("^the ", ""):gsub("[^%w]", ""))',
        "end",
        "",
        "local function key(name) return ns:AreaKey(name) end",
        "",
        "ns.Maps = {}",
    ]
    for dungeon in MAPS:
        slug = dungeon["slug"]
        out.append("")
        out.append("-- " + slug)
        out.append("ns.Maps[%d] = {}" % dungeon["instance"])
        for f, floor in enumerate(dungeon["floors"], 1):
            img, pieces = split(floor, blank)
            base = f"{slug}-{f}"
            Image.fromarray(img).resize(FULL, Image.LANCZOS).save(os.path.join(OUT, base + ".tga"))
            out.append("do")
            out.append('\tlocal floor = { full = DIR .. "%s", areas = {}, count = 0 }' % base)
            n = 0
            for name, alpha in pieces:
                if name in ("decor", "start"):
                    tex = f"{base}-{name}"
                    box = save_piece(img, alpha, os.path.join(OUT, tex + ".tga"))
                    if box:
                        out.append("\tfloor.%s = %s" % (name, lua_piece(tex, box)))
                    continue
                n += 1
                tex = f"{base}-{n:02d}"
                box = save_piece(img, alpha, os.path.join(OUT, tex + ".tga"))
                if not box:
                    print("  !! no drawing found for", name)
                    continue
                out.append("\tfloor.areas[key(%s)] = %s" % (lua_str(name), lua_piece(tex, box)))
                out.append("\tfloor.count = floor.count + 1")
                for alias, target in floor.get("aliases", {}).items():
                    if target == name:
                        out.append("\tfloor.areas[key(%s)] = floor.areas[key(%s)]" % (lua_str(alias), lua_str(name)))
            out.append("\tns.Maps[%d][%d] = floor" % (dungeon["instance"], f))
            out.append("end")
            print(f"{base}: {n} areas")
            if preview:
                write_preview(base, img, blank, pieces)
    with open(LUA, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    size = sum(os.path.getsize(p) for p in glob.glob(os.path.join(OUT, "*.tga")))
    print(f"wrote Maps.lua and {len(glob.glob(os.path.join(OUT, '*.tga')))} textures, {size / 1e6:.1f} MB")


def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def compose(img, blank, pieces, shown):
    canvas = blank.astype(np.float32)
    for name, alpha in pieces:
        if name in shown:
            a = alpha[..., None]
            canvas = canvas * (1 - a) + img.astype(np.float32) * a
    return Image.fromarray(canvas.astype(np.uint8))


def write_preview(base, img, blank, pieces):
    """Three stages side by side: arrival, half explored, everything found."""
    names = [n for n, _ in pieces if n not in ("decor", "start")]
    stages = [{"decor", "start"}, {"decor", "start", *names[: (len(names) + 1) // 2]}, {"decor", "start", *names}]
    sheet = Image.new("RGB", (W * 3 + 24, H), "white")
    for i, shown in enumerate(stages):
        sheet.paste(compose(img, blank, pieces, shown), (i * (W + 12), 0))
    os.makedirs(os.path.join(REFS, "preview"), exist_ok=True)
    sheet.save(os.path.join(REFS, "preview", base + ".png"))


if __name__ == "__main__":
    main()
