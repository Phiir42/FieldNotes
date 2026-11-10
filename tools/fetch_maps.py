"""Downloads a dungeon's retail map art from wago.tools and stitches each floor
into one reference image under refs/ (not committed: it is Blizzard's art,
used only as a layout reference for the redrawn maps).

    python tools/fetch_maps.py blackrock-depths 242 243

The numbers are uiMapIDs, one per floor (see refs/tables/UiMap.csv).
"""
import csv, io, os, sys, urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "refs")
TABLES = os.path.join(REFS, "tables")
BASE = "https://wago.tools"
AGENT = {"User-Agent": "Mozilla/5.0"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=60) as r:
        return r.read()


def table(name):
    path = os.path.join(TABLES, name + ".csv")
    if not os.path.exists(path):
        os.makedirs(TABLES, exist_ok=True)
        with open(path, "wb") as f:
            f.write(get(f"{BASE}/db2/{name}/csv"))
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def stitch(ui_map):
    art = next(r["UiMapArtID"] for r in table("UiMapXMapArt") if r["UiMapID"] == str(ui_map))
    style = next(r["UiMapArtStyleID"] for r in table("UiMapArt") if r["ID"] == art)
    layer = next(r for r in table("UiMapArtStyleLayer")
                 if r["UiMapArtStyleID"] == style and r["LayerIndex"] == "0")
    width, height = int(layer["LayerWidth"]), int(layer["LayerHeight"])
    tw, th = int(layer["TileWidth"]), int(layer["TileHeight"])
    tiles = [r for r in table("UiMapArtTile") if r["UiMapArtID"] == art and r["LayerIndex"] == "0"]
    image = Image.new("RGBA", (width, height))
    for t in tiles:
        tile = Image.open(io.BytesIO(get(f"{BASE}/api/casc/{t['FileDataID']}"))).convert("RGBA")
        image.paste(tile, (int(t["ColIndex"]) * tw, int(t["RowIndex"]) * th))
    return image, len(tiles)


def main():
    name, ids = sys.argv[1], sys.argv[2:]
    os.makedirs(REFS, exist_ok=True)
    for floor, ui_map in enumerate(ids, 1):
        image, n = stitch(ui_map)
        path = os.path.join(REFS, f"{name}-{floor}.png")
        image.save(path)
        print(f"{path}: {image.width}x{image.height} from {n} tiles")


if __name__ == "__main__":
    main()
