"""Checks the map definitions (tools/defs) for areas nothing in the game can
uncover: an area opens when the journal records one of its names, and the
journal only ever records a sub-zone the client names (AreaTable or, indoors,
WMOAreaTable), a boss fight (DungeonEncounter) or a creature it has met.

    python tools/check_map_names.py              # areas with no such name
    python tools/check_map_names.py --aliases    # also every alias no one can report

An alias no one reports is harmless (see tools/defs/BRIEF.md); an area with
none stays blank unless it is the entrance or a one-road dungeon reaches past
it.

Runs without refs/ too (see tools/game_names.py).
"""
import glob
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_abilities as m  # noqa: E402
from game_names import reportable  # noqa: E402  (the client's tables, or their copy in tools/data)

ROOT = m.ROOT


# Areas that stay blank on purpose, with why.
BLANK = {
    "Lower Observatory": "Shadowfang Keep's retail sheet: no classic boss stands there, and the old keep has no such hall",
    "Upper Observatory": "as the Lower Observatory",
}


def main():
    known = reportable()
    bad = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "tools", "defs", "*.py"))):
        spec = importlib.util.spec_from_file_location("mapdef", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for floor in mod.MAP["floors"]:
            sheet = floor.get("ref") or floor.get("art")
            aliases = floor.get("aliases", {})
            for area in floor.get("areas", {}):
                names = [area] + [a for a, to in aliases.items() if to == area]
                if not any(m.key(n) in known for n in names):
                    if area in BLANK:
                        if "-v" in sys.argv:
                            print("%s: %r is blank on purpose: %s" % (sheet, area, BLANK[area]))
                        continue
                    bad += 1
                    print("%s: %r has no name the game reports" % (sheet, area))
            if "--aliases" in sys.argv:
                for a in aliases:
                    if m.key(a) not in known:
                        print("%s: alias %r is never reported" % (sheet, a))
    print(bad, "areas nothing uncovers (and %d blank on purpose: -v lists them)" % len(BLANK))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
