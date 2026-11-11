"""Downloads an instance's minimap tiles from wago.tools and stitches them into
one top-down image under refs/minimap/. For dungeons the game has no map
sheet for, this is the layout reference a drawn sheet is made from.

    python tools/fetch_minimap.py <game build> <map directory> <name>
    python tools/fetch_minimap.py 1.60.1.70862 2970 the-drowned-city

The map directory is the Directory column of the Map table (for new maps it
is the map ID). Prints the stitched size, or says there are no tiles: indoor
dungeons built as one big model have none.
"""
import io, json, os, re, sys, urllib.parse, urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "refs", "minimap")
BASE = "https://wago.tools"
AGENT = {"User-Agent": "Mozilla/5.0"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=60) as r:
        return r.read()


def main():
    build, directory, name = sys.argv[1:4]
    query = urllib.parse.urlencode({"search": f"world/minimaps/{directory}/map", "version": build})
    files = json.loads(get(f"{BASE}/api/files?{query}")) or {}
    tiles = {}
    for fdid, path in files.items():
        m = re.search(rf"minimaps/{re.escape(directory)}/map(\d+)_(\d+)\.blp$", path, re.I)
        if m:
            tiles[(int(m.group(1)), int(m.group(2)))] = fdid
    if not tiles:
        print(f"{name}: no minimap tiles")
        return
    xs, ys = [x for x, _ in tiles], [y for _, y in tiles]
    x0, y0 = min(xs), min(ys)
    first = Image.open(io.BytesIO(get(f"{BASE}/api/casc/{next(iter(tiles.values()))}")))
    size = first.width
    sheet = Image.new("RGBA", ((max(xs) - x0 + 1) * size, (max(ys) - y0 + 1) * size))
    for (x, y), fdid in tiles.items():
        tile = Image.open(io.BytesIO(get(f"{BASE}/api/casc/{fdid}"))).convert("RGBA")
        sheet.paste(tile, ((x - x0) * size, (y - y0) * size))
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    sheet.save(path)
    print(f"{name}: {sheet.width}x{sheet.height} from {len(tiles)} tiles -> {path}")


if __name__ == "__main__":
    main()
