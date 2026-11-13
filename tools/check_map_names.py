"""Checks the map definitions (tools/defs) for areas nothing in the game can
uncover: an area opens when the journal records one of its names, and the
journal only ever records a sub-zone the client names (AreaTable or, indoors,
WMOAreaTable), a boss fight (DungeonEncounter) or a creature it has met.

    python tools/check_map_names.py              # areas with no such name
    python tools/check_map_names.py --aliases    # also every alias no one can report

An alias no one reports is harmless (see tools/defs/BRIEF.md); an area with
none stays blank unless it is the entrance or a one-road dungeon reaches past
it.
"""
import glob
import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_abilities as m  # noqa: E402

ROOT = m.ROOT


def reportable():
    names = {m.key(r["AreaName_lang"]) for r in m.table("AreaTable", m.FOREVER)}
    names |= {m.key(r["AreaName_lang"]) for r in m.table("WMOAreaTable", m.FOREVER) if r.get("AreaName_lang")}
    names |= {m.key(e["Name_lang"]) for e in m.table("DungeonEncounter", m.FOREVER)}
    with open(os.path.join(ROOT, "refs", "classicdb", "creatures.json"), encoding="utf-8") as f:
        names |= {m.key(c["name"]) for c in json.load(f).values() if c["name"]}
    for extra in ("forever_creatures.json", "forever_npcs.json"):
        path = os.path.join(ROOT, "tools", "data", extra)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                names |= {m.key(n) for n in json.load(f)}
    return names


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
                    bad += 1
                    print("%s: %r has no name the game reports" % (sheet, area))
            if "--aliases" in sys.argv:
                for a in aliases:
                    if m.key(a) not in known:
                        print("%s: alias %r is never reported" % (sheet, a))
    print(bad, "areas nothing uncovers")


if __name__ == "__main__":
    main()
