"""Lift a painted sheet's dungeon off its own parchment and set it on the
journal's blank parchment, so that only the dungeon differs from the blank
sheet and uncovering an area never shows a patch of off-colour paper.

    python tools/settle_sheet.py <slug> [...]     (rewrites tools/art/<slug>.png)

The painting (from tools/codex_sheet.py) comes on parchment of its own tone.
The paper's tone is estimated across the page; whatever stands out from it is
the dungeon (pale floors count as paper, which is how the game's own sheets
look). The painting's colours are shifted so its paper matches the blank
sheet's, and the dungeon is laid over the blank sheet with a soft edge. The untouched painting
is kept as tools/art/raw/<slug>.png.
"""
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import make_maps as m

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "tools", "art")
ROUGH = 45     # colour distance from the page-edge paper that is surely dungeon
NEAR, FAR = 9, 24  # distance from the paper around: below NEAR is paper, above FAR is drawing
FEATHER = 1.5  # px of soft edge


def settle(slug, blank):
    path = os.path.join(ART, slug + ".png")
    raw = os.path.join(ART, "raw", slug + ".png")
    os.makedirs(os.path.dirname(raw), exist_ok=True)
    if not os.path.exists(raw):
        shutil.copyfile(path, raw)
    P = np.asarray(Image.open(raw).convert("RGB").resize((m.W, m.H), Image.LANCZOS)).astype(np.float32)
    B = blank.astype(np.float32)

    def gauss(a, r):
        if a.ndim == 2:
            # PIL blurs 8-bit images only: values here are 0..255 or 0..1
            k = 255.0 if a.max() <= 1.0 else 1.0
            im = Image.fromarray(np.clip(a * k, 0, 255).astype(np.uint8))
            return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / k
        return np.dstack([gauss(a[..., c], r) for c in range(a.shape[2])])

    def dist(a, b):
        return np.sqrt(((a - b) ** 2).sum(axis=2))

    # A first rough idea of where the dungeon is: far from the colour of a
    # ring just inside the page edge, with room to spare around it.
    ring = np.zeros((m.H, m.W), bool)
    e = int(m.H * 0.07)
    ring[:e], ring[-e:], ring[:, :e], ring[:, -e:] = True, True, True, True
    paper = np.median(P[ring], axis=0)
    soft = gauss(P, 3)
    rough = (dist(soft, paper) > ROUGH).astype(np.float32)
    rough = np.asarray(Image.fromarray((rough * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(31))) / 255.0
    # The paper's own tone drifts across the page: estimate it everywhere from
    # the paper around (a blur that ignores the dungeon).
    free = (1 - rough)[..., None]
    # (deep inside the dungeon there is no paper near: lean on the page-edge colour)
    weight = gauss(free[..., 0], 60)[..., None]
    local = (gauss(P * free, 60) + 0.08 * paper) / (weight + 0.08)
    # the dungeon: whatever stands out from the paper around it
    d = dist(soft, local)
    mask = np.clip((d - NEAR) / (FAR - NEAR), 0, 1)
    mask = gauss(np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) / 255.0,
                 FEATHER)[..., None]
    mask = np.clip(mask * 1.5, 0, 1)
    dungeon = (mask[..., 0] > 0.5) * 255
    # carry the painting from its paper's tone to the blank sheet's
    shifted = np.clip(P + (gauss(B, 60) - local), 0, 255)
    out = B * (1 - mask) + shifted * mask
    Image.fromarray(out.astype(np.uint8)).save(path)
    # where the dungeon is, for make_maps: the solid parts, closed up so that
    # pale floors between walls belong to it, without the faint drift around
    solid = Image.fromarray(((d > FAR) * 255).astype(np.uint8))
    solid = solid.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(2))
    solid.save(os.path.join(ART, slug + "-mask.png"))
    print("%s: dungeon covers %.0f%% of the sheet" % (slug, 100 * (dungeon > 0).mean()))


if __name__ == "__main__":
    blank, _ = m.blank_parchment()
    for slug in sys.argv[1:]:
        settle(slug, blank)
