"""Builds the journal's map masks and FieldNotes/Maps.lua from the retail
reference maps in refs/ and the area definitions in tools/defs/.

    python tools/make_maps.py                    # masks + Maps.lua
    python tools/make_maps.py --preview          # also refs/preview/<floor>.png
    python tools/make_maps.py --only <slug>      # previews for one dungeon only;
                                                 # writes nothing into the addon

A definition is tools/defs/<name>.py holding MAP = { "instance": the dungeon's
instance map ID (8th return of GetInstanceInfo), "slug": file name stem,
"floors": [floor, ...] }. All coordinates are pixels of the 1002x668 reference
image in refs/ (tools/grid.py draws one with a coordinate grid). A floor has:
  ref      the reference image name in refs/ (without .png)
  uimap    the floor's retail uiMapID, to look up its map tile file IDs
  decor    boxes (left, top, right, bottom) of page decoration that is always
           shown: the title banner and the illustration
  start    seed points of the part visible on arrival (the entrance)
  areas    { "Name": [seed points] }
  aliases  { "Other name": "Name" }
A name is anything the journal records in the dungeon: a sub-zone, a boss or
a creature fought. Meeting any of an area's names uncovers it. Every drawn
pixel outside the decor boxes belongs to the area with the nearest seed, so
seeds go on the area's rooms and on its label; add seeds to pull a corridor
or label towards the right area.

The addon ships no map art: it draws the game's own map tiles (by file ID)
and only needs to know which part of the sheet each area covers. That part
is a small alpha mask per area, made like this:
  1. The blank parchment is the per-pixel median of every reference map: the
     drawings sit in different places, so the median has none of them.
  2. Whatever differs from the blank on one map is that map's drawing.
  3. Drawing pixels inside a floor's decor boxes, or far from every seed, are
     decoration; the rest go to the area with the nearest seed point.
  4. Each area's share of the drawing is saved as a mask. In game the map
     tiles are shown through it, over the blank parchment.
"""
import glob, importlib.util, os, sys

import numpy as np
from PIL import Image, ImageFilter

from fetch_maps import table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "refs")
OUT = os.path.join(ROOT, "FieldNotes", "Maps")
LUA = os.path.join(ROOT, "FieldNotes", "Maps.lua")
W, H = 1002, 668
BLANK = (512, 256)   # the parchment texture, squeezed to a power of two
MASK_SCALE = 0.125   # masks are stored at this fraction of the reference size
THRESHOLD = 26       # colour difference from the blank that counts as drawing
GROW = 9             # px the drawing mask is grown, to keep soft shadows
OVERLAP = 5          # px a piece reaches into its neighbours, so no seam shows
FEATHER = 3          # px blur on piece edges
REACH = 150          # px: drawing further than this from every seed is decoration


def definitions():
    maps = []
    for path in sorted(glob.glob(os.path.join(ROOT, "tools", "defs", "*.py"))):
        spec = importlib.util.spec_from_file_location("mapdef", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        maps.append(module.MAP)
    return maps


def load(name):
    return np.asarray(Image.open(os.path.join(REFS, name + ".png")).convert("RGB")).astype(np.int16)


def blank_parchment():
    paths = sorted(glob.glob(os.path.join(REFS, "*-[0-9].png")))
    stack = np.stack([np.asarray(Image.open(p).convert("RGB")) for p in paths])
    return np.median(stack, axis=0).astype(np.int16), len(paths)


def grow(mask, px):
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


def tiles(ui_map):
    """The floor's map tile file IDs, row by row, and the number of columns."""
    art = next(r["UiMapArtID"] for r in table("UiMapXMapArt") if r["UiMapID"] == str(ui_map))
    rows = [r for r in table("UiMapArtTile") if r["UiMapArtID"] == art and r["LayerIndex"] == "0"]
    rows.sort(key=lambda r: (int(r["RowIndex"]), int(r["ColIndex"])))
    cols = 1 + max(int(r["ColIndex"]) for r in rows)
    return [int(r["FileDataID"]) for r in rows], cols


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


def save_mask(alpha, path):
    """Save the piece's alpha, stretched onto a small power-of-two texture.
    -> ((x, y, w, h) on the sheet, the alpha as the game will see it) or None."""
    rows, cols = np.where(alpha > 0.01)
    if len(rows) == 0:
        return None
    x0, x1 = max(cols.min() - 4, 0), min(cols.max() + 5, W)
    y0, y1 = max(rows.min() - 4, 0), min(rows.max() + 5, H)
    w, h = x1 - x0, y1 - y0
    size = (pow2(round(w * MASK_SCALE)), pow2(round(h * MASK_SCALE)))
    small = Image.fromarray((alpha[y0:y1, x0:x1] * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    if path:
        rgba = Image.new("RGBA", size, (255, 255, 255, 0))
        rgba.putalpha(small)
        rgba.save(path)
    seen = np.zeros((H, W), np.float32)
    seen[y0:y1, x0:x1] = np.asarray(small.resize((w, h), Image.BILINEAR)).astype(np.float32) / 255
    return (x0, y0, w, h), seen


def lua_piece(tex, box):
    return '{ mask = DIR .. "%s", x = %d, y = %d, w = %d, h = %d }' % ((tex,) + box)


def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


HEADER = """-- Dungeon maps. GENERATED by tools/make_maps.py from tools/map_defs.py: edit those.
--
-- The addon ships no map art. It draws the game's own map tiles (the client
-- has them, though it shows no map inside dungeons) through a small mask per
-- area, over blank parchment, so each area's part of the drawing appears when
-- the journal records that area (see CheckArea in Record.lua).
--
-- ns.Maps[instanceID] = { floor, ... }, a floor being
--   tiles  the sheet's map tile file IDs, row by row; cols tiles per row
--   decor  the title banner and illustration, always shown
--   start  the part visible on arrival (the entrance), if on this floor
--   areas  { [ns:AreaKey(name)] = piece }
--   count  how many different area pieces the floor has
-- A piece is { mask, x, y, w, h }: a mask texture and its place on the
-- %dx%d sheet.
local _, ns = ...

local DIR = "Interface\\\\AddOns\\\\FieldNotes\\\\Maps\\\\"
ns.MAP_REF_W, ns.MAP_REF_H, ns.MAP_TILE = %d, %d, 256
ns.MAP_BLANK = DIR .. "parchment"

-- Area names are matched ignoring case, punctuation and a leading "The".
function ns:AreaKey(name)
	return (name:lower():gsub("^the ", ""):gsub("[^%%w]", ""))
end

local function key(name) return ns:AreaKey(name) end

ns.Maps = {}
""" % (W, H, W, H)


def main():
    preview = "--preview" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    write = not only
    blank, count = blank_parchment()
    if write:
        os.makedirs(OUT, exist_ok=True)
        for old in glob.glob(os.path.join(OUT, "*.tga")):
            os.remove(old)
        Image.fromarray(blank.astype(np.uint8)).resize(BLANK, Image.LANCZOS).save(os.path.join(OUT, "parchment.tga"))
        print(f"parchment.tga from {count} reference maps")

    out = [HEADER]
    for dungeon in definitions():
        slug = dungeon["slug"]
        if only and slug != only:
            continue
        out.append("-- " + slug)
        out.append("ns.Maps[%d] = {}" % dungeon["instance"])
        for f, floor in enumerate(dungeon["floors"], 1):
            img, pieces = split(floor, blank)
            base = f"{slug}-{f}"
            ids, cols = tiles(floor["uimap"])
            out.append("do")
            out.append("\tlocal floor = { cols = %d, tiles = { %s }, areas = {}, count = 0 }"
                       % (cols, ", ".join(map(str, ids))))
            n, seen = 0, []
            for name, alpha in pieces:
                special = name in ("decor", "start")
                if not special:
                    n += 1
                tex = f"{base}-{name}" if special else f"{base}-{n:02d}"
                saved = save_mask(alpha, os.path.join(OUT, tex + ".tga") if write else None)
                if not saved:
                    if not special:
                        print("  !! no drawing found for", name)
                    continue
                box, as_seen = saved
                seen.append((name, as_seen))
                if special:
                    out.append("\tfloor.%s = %s" % (name, lua_piece(tex, box)))
                    continue
                out.append("\tfloor.areas[key(%s)] = %s" % (lua_str(name), lua_piece(tex, box)))
                out.append("\tfloor.count = floor.count + 1")
                for alias, target in floor.get("aliases", {}).items():
                    if target == name:
                        out.append("\tfloor.areas[key(%s)] = floor.areas[key(%s)]" % (lua_str(alias), lua_str(name)))
            for alias, target in floor.get("aliases", {}).items():
                if target not in floor["areas"]:
                    print(f"  !! alias {alias!r} points at unknown area {target!r}")
            out.append("\tns.Maps[%d][%d] = floor" % (dungeon["instance"], f))
            out.append("end")
            print(f"{base}: {n} areas, {len(ids)} tiles")
            if preview or only:
                write_preview(base, img, blank, seen)
                write_cells(base, img, floor, seen)
    if not write:
        return
    with open(LUA, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    files = glob.glob(os.path.join(OUT, "*.tga"))
    print(f"wrote Maps.lua and {len(files)} textures, {sum(map(os.path.getsize, files)) / 1e6:.2f} MB")


def write_cells(base, img, floor, pieces):
    """refs/preview/<base>-cells.png: the reference with every piece tinted its
    own colour and each seed marked with its area's number (listed top left)."""
    from PIL import ImageDraw
    rng = np.random.default_rng(7)
    canvas = img.astype(np.float32)
    names = [n for n, _ in pieces]
    colours = {n: rng.integers(40, 256, 3) for n in names}
    colours["decor"] = np.array([90, 90, 90])
    for name, alpha in pieces:
        a = alpha[..., None] * 0.55
        canvas = canvas * (1 - a) + colours[name] * a
    im = Image.fromarray(canvas.astype(np.uint8))
    d = ImageDraw.Draw(im)
    order = [n for n in names if n != "decor"]
    seeds = [("start", floor.get("start", []))] + list(floor["areas"].items())
    for name, pts in seeds:
        if name not in order:
            continue
        num = str(order.index(name))
        for x, y in pts:
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 255, 255), outline=(0, 0, 0))
            d.text((x + 5, y - 6), num, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    for i, name in enumerate(order):
        d.text((8, 6 + i * 13), f"{i} {name}", fill=tuple(int(c) for c in colours[name]),
               stroke_width=2, stroke_fill=(0, 0, 0))
    os.makedirs(os.path.join(REFS, "preview"), exist_ok=True)
    im.save(os.path.join(REFS, "preview", base + "-cells.png"))


def compose(img, blank, pieces, shown):
    canvas = blank.astype(np.float32)
    for name, alpha in pieces:
        if name in shown:
            a = alpha[..., None]
            canvas = canvas * (1 - a) + img.astype(np.float32) * a
    return Image.fromarray(canvas.astype(np.uint8))


def write_preview(base, img, blank, pieces):
    """Three stages side by side: arrival, half explored, every area found
    (still drawn through the masks; in game the last stage shows the plain tiles)."""
    names = [n for n, _ in pieces if n not in ("decor", "start")]
    stages = [{"decor", "start"}, {"decor", "start", *names[: (len(names) + 1) // 2]}, {"decor", "start", *names}]
    sheet = Image.new("RGB", (W * 3 + 24, H), "white")
    for i, shown in enumerate(stages):
        sheet.paste(compose(img, blank, pieces, shown), (i * (W + 12), 0))
    os.makedirs(os.path.join(REFS, "preview"), exist_ok=True)
    sheet.save(os.path.join(REFS, "preview", base + ".png"))


if __name__ == "__main__":
    main()
