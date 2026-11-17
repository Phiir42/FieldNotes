"""Checks that every boss fight the Forever client knows of has a mark on its
dungeon's map (FieldNotes/Maps.lua), where the dungeon has a map.

    python tools/check_boss_marks.py          # problems only; exit 1 if any
    python tools/check_boss_marks.py -v       # the known gaps too, with why

A boss with no mark is not drawn on the map once faced (unless the game tells
where you stood as it fell, see BossSpot in Journal.lua). Give it a pin in its
definition ("bosses": {name: (sheet, x, y)}), or, when it should have none,
put it in KNOWN with the reason.
"""
import sys

import make_maps as m
from make_abilities import table as forever_table, FOREVER
from map_editor import shipped_bosses

# Fights with no mark, on purpose.
KNOWN = {
    "Mechanical Menagerie": "Season of Discovery's Gnomeregan raid (difficulty 198): not in Forever's Gnomeregan",
    "The Molten Core": "Season of Discovery's Molten Core: not a classic fight",
    "Ezra Grimm": "not in the classic data: no spot to give him until a real run shows where he stands",
}
# Forever's own dungeons whose bosses are placed from real runs only.
WAITING = {"the-shapers-terrace": "Forever's own; its minimap and a run will place the bosses"}


def main():
    verbose = "-v" in sys.argv
    names = {}
    for r in forever_table("DungeonEncounter", FOREVER):
        names.setdefault(int(r["MapID"]), set()).add(r["Name_lang"])
    bad = 0
    for d in m.definitions():
        marked = {n for floor in shipped_bosses(d["instance"]).values() for n, _, _ in floor}
        pins = d.get("bosses", {})
        for name in sorted(names.get(d["instance"], ())):
            if name in marked or (name in pins and pins[name] is None):
                continue
            why = KNOWN.get(name) or WAITING.get(d["slug"])
            if why:
                if verbose:
                    print("%s: %s has no mark (known: %s)" % (d["slug"], name, why))
                continue
            bad += 1
            print("%s: %s has no mark on the map" % (d["slug"], name))
    print("%d boss(es) with no mark" % bad)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
