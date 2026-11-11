"""Has Codex paint a map sheet in the style of the game's own dungeon maps,
for a dungeon the game has no sheet for.

    python tools/codex_sheet.py [--dry] [slug ...]      (default: every dungeon below)

For each dungeon it gives Codex the dungeon's minimap (cropped as in
tools/draw_minimap_sheet.py) for the layout and one of the game's sheets for
the style, and saves the painting to tools/art/<slug>.png, replacing the
sheet draw_minimap_sheet.py made. Afterwards check the areas still sit on the
right rooms (python tools/make_maps.py --only <slug>, then look at
refs/preview/<slug>-1-cells.png) and run python tools/make_maps.py.
--dry only writes the layout references (refs/minimap/<slug>-layout.png).
"""
import glob, os, subprocess, sys, time
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_minimap_sheet import SHEETS, ROOT, W, H

CROPS = dict({k: v["crop"] for k, v in SHEETS.items()}, **{"alcaz-prison": (120, 170, 450, 390)})
# (what it is, which of the game's sheets to imitate)
ABOUT = {
    "alcaz-prison": ("a stone prison of corridors, cell blocks and round chambers", "scarlet-monastery-2"),
    "the-hall-of-thanes": ("a dwarven hall of stone chambers below, opening onto snowy mountain ledges above", "scarlet-monastery-2"),
    "the-drowned-city": ("a ruined troll temple city on the sea bed: stone courts around an octagonal pool, with rocky paths", "zul-farrak-1"),
    "blackmaw-hold": ("a furbolg hold: forest clearings and rocky dens under a snowy ridge", "zul-farrak-1"),
    "city-of-dalaran": ("the walled mage city of Dalaran: domed towers around a central plaza", "zul-farrak-1"),
    "ruins-of-lordaeron": ("the ruined walled capital of Lordaeron: streets and courtyards around a domed palace", "zul-farrak-1"),
    "kroldok-stronghold": ("an ogre stronghold of stone towers and walls winding up a hillside", "zul-farrak-1"),
    "the-shapers-terrace": ("a titan garden: plains, tar pits, crystal springs and rocky highlands", "zul-farrak-1"),
    "excavation-site-wetlands": ("a marshy valley dig site among rocky hills", "zul-farrak-1"),
}
PROMPT = """Generate one image with your image generation tool. Do not write code.

Image 1 is a top-down minimap of a World of Warcraft dungeon: {what}. Image 2 is one of the game's official dungeon map sheets, shown only for its art style.

Paint a new dungeon map sheet of the place in image 1, in exactly the style of image 2: an aged tan parchment page filling the whole image, with the dungeon painted on it top-down in the game's hand-painted map style (pale floors and paths, dark outlined walls and cliffs, soft shadows, muted earthy colours), fading into bare parchment around the edges.

Requirements:
- Landscape 3:2 image (1536x1024).
- Keep the layout of image 1: the same rooms, buildings, paths and landmarks, in the same positions and proportions. Do not add, remove, mirror or rearrange anything. Leave out the surroundings that are not part of the dungeon.
- The dungeon sits in the same place on the page as in image 1, with plain parchment everywhere else.
- No text, no labels, no numbers, no legend, no compass, no title banner, no icons.
"""


def layout(slug):
    src = Image.open(os.path.join(ROOT, "refs", "minimap", slug + ".png")).convert("RGBA")
    flat = Image.new("RGBA", src.size, (110, 110, 110, 255))
    flat.alpha_composite(src)
    path = os.path.join(ROOT, "refs", "minimap", slug + "-layout.png")
    flat.crop(CROPS[slug]).resize((W, H), Image.LANCZOS).convert("RGB").save(path)
    return path


def paint(slug):
    what, style = ABOUT[slug]
    ref, started = layout(slug), time.time()
    subprocess.run(["codex", "exec", "--sandbox", "workspace-write", "-i", ref,
                    "-i", os.path.join(ROOT, "refs", style + ".png"), "-"],
                   input=PROMPT.format(what=what), text=True, cwd=ROOT, shell=(os.name == "nt"), check=True)
    made = [p for p in glob.glob(os.path.join(os.path.expanduser("~"), ".codex", "generated_images", "**", "*.png"),
                                 recursive=True) if os.path.getmtime(p) > started]
    if not made:
        print("!!", slug, "Codex made no image")
        return
    out = os.path.join(ROOT, "tools", "art", slug + ".png")
    Image.open(max(made, key=os.path.getmtime)).convert("RGB").resize((W, H), Image.LANCZOS).save(out)
    print("wrote", out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--dry"]
    for slug in args or ABOUT:
        print(layout(slug)) if "--dry" in sys.argv else paint(slug)
