"""Checks the boss marks in FieldNotes/Maps.lua against the skulls painted on
the game's own map sheets (refs/<sheet>.png, see tools/fetch_maps.py).

    python tools/check_skulls.py [slug ...]        # problems only; exit 1 if any
    python tools/check_skulls.py -v [slug ...]     # every boss and skull

A boss within NEAR px of a painted skull but not on it (more than ON px away)
is most likely a little beside where the sheet shows it: pin it on the skull in
its definition ("bosses": {name: (sheet, x, y)}). Before pinning, check that
the boss's spawn (the classic data) is in the same room as the skull: the
sheets come from a later client and some skulls are for bosses that stand
elsewhere in the old world (see the exceptions below). A boss that should stay
where it is goes in KNOWN with the reason.

Skulls are found by matching the skulls of Razorfen Kraul's sheet against each
sheet (normalized cross-correlation); painted sheets of our own (tools/art)
have none and are skipped. Needs numpy and Pillow.
"""
import os
import sys

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from PIL import Image

import make_maps as m
from map_editor import shipped_bosses

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = 9          # half size of a skull template
SCORE = 0.8    # a match at least this good is a skull
ON = 10        # a mark this close to a skull is on it (Jargba, 6 px off, looks right in game)
NEAR = 40      # a mark further than this from every skull has none of its own
TEMPLATES = ("razorfen-kraul-1", [(807, 346), (79, 455), (218, 206), (574, 207), (875, 277)])

# Bosses near a skull that stay off it, with why.
KNOWN = {
    "Ring of Law": "an event in the arena, not one boss",
    "Houndmaster Grebmar": "where the classic data puts him, by the Ring of Law's skull",
    "Ribbly Screwspigot": "where the classic data puts him; the Grim Guzzler's skull is Plugger's",
    "Phalanx": "where the classic data puts him, on the road outside the Grim Guzzler",
    "Princess Moira Bronzebeard": "stands beside the Emperor, whose skull it is",
    "The Vault": "the vault behind Warder Stilgiss, whose skull it is",
    "Gizrul the Slavener": "shares Halycon's room; the skull is Halycon's",
    "Cho'Rush the Observer": "stands beside King Gordok",
    "King Gordok": "beside the skull, in the throne room; the classic spawn is on it",
    "Hydromancer Velratha": "at the pool, where the classic data puts her; the skull is Gahz'rilla's altar",
    "Gahz'rilla": "summoned from the pool, beside the altar",
    "High Priest Venoxis": "the classic spawn is on the road outside the temple the skull marks",
}


def gray(path):
    return np.asarray(Image.open(path).convert("L"), dtype=np.float32)


def templates():
    img = gray(os.path.join(ROOT, "refs", TEMPLATES[0] + ".png"))
    out = []
    for x, y in TEMPLATES[1]:
        t = img[y - R:y + R + 1, x - R:x + R + 1]
        out.append((t - t.mean()) / (t.std() + 1e-6))
    return out


def skulls(img, temps):
    """[(x, y, score)] of the skulls on a sheet, best first."""
    side = 2 * R + 1
    best = np.full((img.shape[0] - 2 * R, img.shape[1] - 2 * R), -1, np.float32)
    for y0 in range(0, best.shape[0], 64):
        w = sliding_window_view(img[y0:y0 + 64 + 2 * R], (side, side))
        z = (w - w.mean(axis=(2, 3), keepdims=True)) / (w.std(axis=(2, 3), keepdims=True) + 1e-6)
        for t in temps:
            c = (z * t).sum(axis=(2, 3)) / side ** 2
            best[y0:y0 + c.shape[0]] = np.maximum(best[y0:y0 + c.shape[0]], c)
    out = []
    while True:
        y, x = divmod(int(np.argmax(best)), best.shape[1])
        if best[y, x] < SCORE:
            return out
        out.append((x + R, y + R, float(best[y, x])))
        best[max(0, y - 12):y + 13, max(0, x - 12):x + 13] = -1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    verbose = "-v" in sys.argv
    temps = templates()
    problems = 0
    for d in m.definitions():
        if args and d["slug"] not in args:
            continue
        marks = shipped_bosses(d["instance"])
        for f, floor in enumerate(d["floors"], 1):
            path = floor.get("ref") and os.path.join(ROOT, "refs", floor["ref"] + ".png")
            if not path or not os.path.exists(path):
                continue
            found = skulls(gray(path), temps)
            if verbose:
                print("%s: skulls at %s" % (floor["ref"], ", ".join("(%d, %d)" % s[:2] for s in found) or "none"))
            for name, x, y in marks.get(f, []):
                dist, sx, sy = min(((((x - a) ** 2 + (y - b) ** 2) ** .5, a, b) for a, b, _ in found),
                                   default=(None, 0, 0))
                bad = dist is not None and ON < dist <= NEAR and KNOWN.get(name) is None
                if bad:
                    problems += 1
                if bad or verbose:
                    print("%s%s: %s at (%d, %d), %s" % (
                        "  " if verbose else "", floor["ref"], name, x, y,
                        "no skull near" if dist is None or dist > NEAR else
                        "on the skull" if dist <= ON else
                        "%d px from the skull at (%d, %d)%s" % (dist, sx, sy,
                                                                "" if bad else " (known: %s)" % KNOWN[name])))
    if problems:
        print("%d boss(es) beside a painted skull" % problems)
        sys.exit(1)
    print("every boss near a painted skull is on it, or known not to be")


if __name__ == "__main__":
    main()
