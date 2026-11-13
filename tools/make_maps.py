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
  art      instead of ref and uimap, for a sheet the game does not have: the
           name of a drawn sheet in tools/art/ (without .png, 1002x668, drawn
           on the same parchment). Its art is shipped with the addon.
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
import glob, importlib.util, json, os, re, sys

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
ART_TILE = 512       # shipped sheets are cut into tiles of this many sheet px...
ART_SCALE = 0.5      # ...stored at this fraction of that size


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


def load_art(name, blank):
    """A drawn sheet, with everything but its drawing replaced by the real
    blank parchment so it sits on exactly the same page as the game's sheets."""
    art = np.asarray(Image.open(os.path.join(ROOT, "tools", "art", name + ".png")).convert("RGB")).astype(np.int16)
    m = (np.abs(art - blank).max(axis=2) > 45).astype(np.float32)
    m = m * (blur(m, 4) > 0.3)
    m = blur(grow(m, 8), 4)[..., None]
    return (blank * (1 - m) + art * m).astype(np.int16)


def art_tiles(img, base, write):
    """Cut a shipped sheet into square tiles. -> (texture names, columns)."""
    cols, rows = -(-W // ART_TILE), -(-H // ART_TILE)
    sheet = Image.new("RGB", (cols * ART_TILE, rows * ART_TILE))
    sheet.paste(Image.fromarray(img.astype(np.uint8)), (0, 0))
    size = round(ART_TILE * ART_SCALE)
    names = []
    for r in range(rows):
        for c in range(cols):
            name = f"{base}-t{r * cols + c + 1}"
            names.append(name)
            if write:
                tile = sheet.crop((c * ART_TILE, r * ART_TILE, (c + 1) * ART_TILE, (r + 1) * ART_TILE))
                tile.resize((size, size), Image.LANCZOS).convert("RGBA").save(os.path.join(OUT, name + ".tga"))
    return names, cols


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
    img = load_art(floor["art"], blank) if "art" in floor else load(floor["ref"])
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


def area_key(name):
    """Same normalisation as ns:AreaKey in the addon."""
    return re.sub(r"[^a-z0-9]", "", re.sub(r"^the ", "", name.lower()))


_boss_data = None


def boss_points(dungeon, splits):
    """Where each boss stands on the dungeon's sheets -> [[(name, x, y), ...] per floor].

    The Forever client's encounter list names the bosses. A boss is placed from
    its spawn point in the classic database (refs/classicdb/creatures.json, see
    tools/extract_classicdb.py), turned into sheet px with the retail map's
    world bounds (UiMapAssignment). Sheets of one instance overlap (they are
    levels of one building), so which sheet a boss goes on is decided by, in
    order: retail's dungeon journal, which pins a boss to a sheet and a spot;
    an area on a sheet named after the boss; the level whose journal-pinned
    bosses stand at the nearest height; the sheet with a room drawn at that
    spot (splits: each floor's (image, pieces)). A boss with no usable spawn
    sits on the middle seed of the area named after it.

    MAP["bosses"] in a definition overrules all of that, per boss:
    (sheet, x, y) pins it, "Other Boss" puts it where that boss is, None
    leaves it off the map."""
    global _boss_data
    if _boss_data is None:
        from make_abilities import ALIASES, table as forever_table, FOREVER
        spawns = {}
        path = os.path.join(REFS, "classicdb", "creatures.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for c in json.load(f).values():
                    for m, x, y, z in c["spawns"]:
                        spawns.setdefault((area_key(c["name"]), m), (x, y, z))
        bounds = {}
        for r in table("UiMapAssignment"):
            lo_x, lo_y, hi_x, hi_y = (float(r[k]) for k in ("Region_0", "Region_1", "Region_3", "Region_4"))
            if hi_x - lo_x < 20000:  # not the catch-all row
                bounds.setdefault((int(r["UiMapID"]), int(r["MapID"])), (lo_x, lo_y, hi_x, hi_y))
        names = {}
        for r in forever_table("DungeonEncounter", FOREVER):
            names.setdefault(int(r["MapID"]), [])
            if r["Name_lang"] not in names[int(r["MapID"])]:
                names[int(r["MapID"])].append(r["Name_lang"])
        # retail's dungeon journal pins many of the same bosses to a sheet and a spot on it
        journal = {}
        pins = {r["JournalEncounterID"]: r for r in table("JournalEncounterXMapLoc")}
        for r in table("JournalEncounter"):
            pin = pins.get(r["ID"], r)
            if pin["UiMapID"] not in ("", "0"):
                journal.setdefault(area_key(r["Name_lang"]), []).append(
                    (int(pin["UiMapID"]), float(pin["Map_0"]), float(pin["Map_1"])))
        _boss_data = (ALIASES, spawns, bounds, names, journal)
    aliases, spawns, bounds, names, journal = _boss_data
    inst, floors = dungeon["instance"], dungeon["floors"]
    out = [[] for _ in floors]
    sheet_of = {floor.get("uimap"): f for f, floor in enumerate(floors) if floor.get("uimap")}
    todo, heights = [], {}  # heights: [floor] = heights of the bosses the journal pins there
    fixed = dungeon.get("bosses", {})
    guessed = dungeon.setdefault("_guessed", set())  # (floor index, boss): placed from its area, not from data

    def on_drawing(f, x, y):
        return max((float(alpha[y - 4:y + 5, x - 4:x + 5].mean()) for n, alpha in splits[f][1]
                    if n != "decor"), default=0) > 0.3

    def middle(seeds):
        cx, cy = sum(x for x, _ in seeds) / len(seeds), sum(y for _, y in seeds) / len(seeds)
        return min(seeds, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)

    for name in names.get(inst, []):
        if name in fixed:
            if isinstance(fixed[name], tuple):
                f, x, y = fixed[name]
                out[f - 1].append((name, x, y))
            continue
        k = area_key(name)
        spot = next((spawns[(area_key(n), inst)] for n in [name] + aliases.get(name, [])
                     if (area_key(n), inst) in spawns), None)
        pin = next((j for j in journal.get(k, []) if j[0] in sheet_of), None)
        # a pin that lands on bare parchment is for some other version of the dungeon
        if pin and not on_drawing(sheet_of[pin[0]], round(pin[1] * W), round(pin[2] * H)):
            pin = None
        if pin:
            f = sheet_of[pin[0]]
            out[f].append((name, round(pin[1] * W), round(pin[2] * H)))
            if spot:
                heights.setdefault(f, []).append(spot[2])
        else:
            todo.append((name, k, spot))
    for name, k, spot in todo:
        # the sheets with an area this boss uncovers, and that area's first seed
        own = {}
        for f, floor in enumerate(floors):
            target = next((t for a, t in floor.get("aliases", {}).items() if area_key(a) == k), None)
            area = next((a for a in floor["areas"] if area_key(a) == k), target)
            if area in floor["areas"]:
                own[f] = middle(floor["areas"][area])
        placed = None
        if spot:
            hits = {}
            for f, floor in enumerate(floors):
                b = bounds.get((floor.get("uimap"), inst))
                if b:
                    x = (b[3] - spot[1]) / (b[3] - b[1]) * W
                    y = (b[2] - spot[0]) / (b[2] - b[0]) * H
                    if 0 < x < W and 0 < y < H:
                        hits[f] = (round(x), round(y))

            def drawn(f):
                x, y = hits[f]
                return max((float(alpha[y - 4:y + 5, x - 4:x + 5].mean()) for n, alpha in splits[f][1]
                            if n != "decor"), default=0)

            f = next((f for f in hits if f in own), None)
            if f is None and not own and hits:
                level = [f for f in hits if f in heights and drawn(f) > 0.3]
                if level:
                    f = min(level, key=lambda f: min(abs(spot[2] - z) for z in heights[f]))
                else:
                    best = max(hits, key=drawn)
                    if drawn(best) > 0.3:
                        f = best
            if f is not None:
                placed = (f, hits[f])
        if not placed and own:
            f = next(iter(own))
            placed = (f, own[f])
            guessed.add((f, name))
        if placed:
            out[placed[0]].append((name, placed[1][0], placed[1][1]))
    # A hub sheet ("hub": True on the floor) shows the whole instance, so every
    # boss is marked on it as well as on its own sheet: at its spawn point if
    # that falls on the drawing, else on the area named after it.
    for f, floor in enumerate(floors):
        if not floor.get("hub"):
            continue
        b = bounds.get((floor.get("uimap"), inst))
        for name in names.get(inst, []):
            if any(mark[0] == name for mark in out[f]) or fixed.get(name, 0) is None:
                continue
            k = area_key(name)
            spot = next((spawns[(area_key(n), inst)] for n in [name] + aliases.get(name, [])
                         if (area_key(n), inst) in spawns), None)
            if spot and b:
                x = round((b[3] - spot[1]) / (b[3] - b[1]) * W)
                y = round((b[2] - spot[0]) / (b[2] - b[0]) * H)
                if 0 < x < W and 0 < y < H and on_drawing(f, x, y):
                    out[f].append((name, x, y))
                    continue
            area = next((a for a in floor["areas"] if area_key(a) == k),
                        next((t for a, t in floor.get("aliases", {}).items() if area_key(a) == k), None))
            if area in floor["areas"]:
                x, y = middle(floor["areas"][area])
                out[f].append((name, x, y))
                guessed.add((f, name))
    for name, other in fixed.items():
        if isinstance(other, str):
            for f, marks in enumerate(out):
                spot = next((m for m in marks if m[0] == other), None)
                if spot:
                    marks.append((name, spot[1], spot[2]))
                    break
    return out


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
--   tiles  the sheet's map tiles, row by row; cols tiles per row. File IDs of
--          the game's own tiles, or paths of shipped ones for the few sheets
--          the game lacks (then tile = their size in sheet pixels)
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


_creature_spawns = None
ROOM_SHARE = 0.10  # a room counts as a creature's if this share of its spawn points are in it


def creature_rooms(dungeon, splits, per_sheet=False):
    """Where each creature named in a one-road definition really stands, from
    its spawn points in the classic database (boss_points must have run).

    On a one-road map, meeting a creature uncovers its room and every room
    before it, so a creature must be filed under the EARLIEST room it lives in
    or the map is uncovered too soon. Returns {floor index: [(name, n or None)]}:
    the room number the name should point at on that floor, None to take the
    name off that floor. Names the database knows nothing of are left alone.

    per_sheet: for dungeons whose sheets are roads of their own ("path":
    "sheets" with "creatures": "auto"): the earliest room on each sheet the
    creature stands on.
    """
    global _creature_spawns
    inst, floors = dungeon["instance"], dungeon["floors"]
    if _creature_spawns is None:
        path = os.path.join(ROOT, "refs", "classicdb", "creatures.json")
        _creature_spawns = {}
        if os.path.exists(path):
            for c in json.load(open(path, encoding="utf-8")).values():
                for sp in c.get("spawns", []):
                    _creature_spawns.setdefault((area_key(c["name"]), sp[0]), []).append(sp)
    aliases, _, bounds, names, _ = _boss_data
    bosses = {area_key(n) for n in names.get(inst, [])}
    for n in names.get(inst, []):
        bosses.update(area_key(a) for a in aliases.get(n, []))
    order = [list(f["areas"]) for f in floors]

    def rooms(pts):
        hits = {}
        for _, wx, wy, _z in pts:
            for f, floor in enumerate(floors):
                b = bounds.get((floor.get("uimap"), inst))
                if not b:
                    continue
                x = round((b[3] - wy) / (b[3] - b[1]) * W)
                y = round((b[2] - wx) / (b[2] - b[0]) * H)
                if not (3 < x < W - 3 and 3 < y < H - 3):
                    continue
                best = max(((float(a[y - 3:y + 4, x - 3:x + 4].mean()), n) for n, a in splits[f][1]
                            if n in floor["areas"]), default=(0, None))
                if best[0] > 0.3:
                    k = (f, order[f].index(best[1]) + 1)
                    hits[k] = hits.get(k, 0) + 1
        return hits

    out = {f: [] for f in range(len(floors))}
    done = set()
    for f, floor in enumerate(floors):
        for name in list(floor["areas"]) + list(floor.get("aliases", {})):
            k = area_key(name)
            pts = _creature_spawns.get((k, inst))
            if k in done or k in bosses or not pts:
                continue
            done.add(k)
            hits = rooms(pts)
            total = sum(hits.values())
            real = sorted(r for r, v in hits.items() if v >= max(1, ROOM_SHARE * total))
            if not real:
                continue
            first = real[0]
            want = {first[0]: first[1]}
            if per_sheet:
                want = {}
                for g in range(len(floors)):
                    here = sum(v for r, v in hits.items() if r[0] == g)
                    mine = sorted(r[1] for r, v in hits.items() if r[0] == g and v >= max(1, ROOM_SHARE * here))
                    if mine:
                        want[g] = mine[0]
            # A later sheet too, only when the earlier one ends in the same room
            # (the room drawn on both): otherwise finding it "on the later
            # sheet" would wrongly complete the earlier one.
            elif all(r[1] == len(order[r[0]]) for r in real if r[0] == first[0]):
                for r in real:
                    want.setdefault(r[0], r[1])
            for g, other in enumerate(floors):
                keyed = next((a for a in other["areas"] if area_key(a) == k),
                             next((t for a, t in other.get("aliases", {}).items() if area_key(a) == k), None))
                now = order[g].index(keyed) + 1 if keyed in other["areas"] else None
                if want.get(g) != now:
                    out[g].append((name, want.get(g)))
    return out


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
        splits = [split(floor, blank) for floor in dungeon["floors"]]
        bosses = boss_points(dungeon, splits)
        moved = {}
        if dungeon.get("path") is True:
            moved = creature_rooms(dungeon, splits)
        elif dungeon.get("creatures") == "auto":
            moved = creature_rooms(dungeon, splits, per_sheet=True)
        for f, floor in enumerate(dungeon["floors"], 1):
            floor["bosses"] = bosses[f - 1]
            img, pieces = splits[f - 1]
            base = f"{slug}-{f}"
            out.append("do")
            if "art" in floor:
                ids, cols = art_tiles(img, base, write)
                out.append("\tlocal floor = { cols = %d, tile = %d, tiles = { %s }, areas = {}, count = 0 }"
                           % (cols, ART_TILE, ", ".join('DIR .. "%s"' % n for n in ids)))
            else:
                ids, cols = tiles(floor["uimap"])
                out.append("\tlocal floor = { cols = %d, tiles = { %s }, areas = {}, count = 0 }"
                           % (cols, ", ".join(map(str, ids))))
            n, seen, numbers = 0, [], {}
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
                out.append("\tfloor.areas[key(%s)].n = %d" % (lua_str(name), n))
                # also under its number, so it stays reachable if its name is given to another piece
                out.append("\tfloor.areas[\"#%d\"] = floor.areas[key(%s)]" % (n, lua_str(name)))
                numbers[name] = n
                road = next((i for i, r in enumerate(floor.get("roads", []), 1) if name in r), 1)
                if road > 1:
                    out.append("\tfloor.areas[key(%s)].g = %d" % (lua_str(name), road))
                out.append("\tfloor.count = floor.count + 1")
                for alias, target in floor.get("aliases", {}).items():
                    if target == name:
                        out.append("\tfloor.areas[key(%s)] = floor.areas[key(%s)]" % (lua_str(alias), lua_str(name)))
            for alias, target in floor.get("aliases", {}).items():
                if target not in floor["areas"]:
                    print(f"  !! alias {alias!r} points at unknown area {target!r}")
            # One-road dungeons: creatures are filed under the earliest room they
            # really stand in (see creature_rooms), whatever the definition says.
            for name, room in moved.get(f - 1, ()):
                if room and room in numbers.values():
                    out.append("	floor.areas[key(%s)] = floor.areas[\"#%d\"]" % (lua_str(name), room))
                    print(f"  {name}: filed under room {room}")
                else:
                    out.append("	floor.areas[key(%s)] = nil" % lua_str(name))
                    print(f"  {name}: taken off sheet {f}")
            # A boss uncovers the room it stands in, whatever the definition
            # guessed: where a boss is known from data, its name is pointed at
            # the piece under its mark.
            keys = {area_key(a): a for a in floor["areas"]}
            keys.update({area_key(a): t for a, t in floor.get("aliases", {}).items()})
            for name, x, y in floor["bosses"]:
                if (f - 1, name) in dungeon.get("_guessed", ()):
                    continue
                at = max(((float(alpha[y - 3:y + 4, x - 3:x + 4].mean()), n) for n, alpha in pieces
                          if n not in ("decor", "start")), default=(0, None))
                room = at[1] if at[0] > 0.3 else None
                if room and keys.get(area_key(name)) != room:
                    was = keys.get(area_key(name))
                    print(f"  {name}: uncovers {room!r}" + (f" (definition said {was!r})" if was else ""))
                    out.append("\tfloor.areas[key(%s)] = floor.areas[\"#%d\"]" % (lua_str(name), numbers[room]))
            if floor["bosses"]:
                out.append("\tfloor.bosses = { %s }" % ", ".join(
                    "{ name = %s, x = %d, y = %d }" % (lua_str(n), x, y) for n, x, y in floor["bosses"]))
            if dungeon.get("path"):
                out.append("\tfloor.path = true")
                if dungeon["path"] == "sheets":
                    out.append("\tfloor.alone = true")
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
    for name, x, y in floor.get("bosses", []):
        d.line((x - 7, y - 7, x + 7, y + 7), fill=(255, 0, 0), width=3)
        d.line((x - 7, y + 7, x + 7, y - 7), fill=(255, 0, 0), width=3)
        d.text((x + 9, y - 6), name, fill=(255, 60, 60), stroke_width=2, stroke_fill=(0, 0, 0))
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
