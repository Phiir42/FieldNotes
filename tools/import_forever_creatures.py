"""Creatures new to Forever, which the classic database never heard of, for
their bestiary entries (kind, rank, levels where known, and an NPC id to draw
them by). Wowhead does not know where they stand, so they are taken by name.

1. Open https://www.wowhead.com/forever/npcs/classification:1?filter=37;2;245000
   in a browser (elites with NPC id 245000 or more: the Forever-made ones;
   Wowhead refuses scripted fetches) and run this in its console:

     const d = g_listviews.npcs.data, by = {};
     for (const x of d) {
       const r = x.react || [];
       if (r.includes(1) && !r.includes(-1)) continue;  // friendly
       const loc = (x.location || []).length > 0, prev = by[x.name];
       if (!prev || (!prev.loc && loc)) by[x.name] = {id: x.id, t: x.type || 0, lo: x.minlevel, hi: x.maxlevel, loc};
     }
     copy(Object.keys(by).sort().map(n => { const v = by[n];
       return [v.id, n, v.t, v.lo > 0 && v.lo < 100 ? v.lo + '-' + v.hi : ''].join('|'); }).join('\\n'));

2. Paste into a file and run

     python tools/import_forever_creatures.py <file> [rank]

   rank: 1 elite (the default), 2 rare elite, 4 rare, 0 normal.

Merges into tools/data/forever_creatures.json ({ name: { npc, rank, type, lo,
hi } }, Wowhead's creature type numbers); names already there are kept.
tools/make_abilities.py writes them into ns.Creatures where the classic
database has no creature of the name.
"""
import json
import os
import re
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "forever_creatures.json")
JUNK = re.compile(r"stalker|trigger|dnt|\[|s0\d|bunny|credit|test|dummy|invisible|controller|placeholder|unused"
                  r"|^zz|^\(|vehicle|cosmetic|spawner|portal|target|^npc|vendor|<ph>|ptr"
                  r"|^translocation$|^gear adjustment$|^battery$|^glaive$|^plunder$", re.I)


def main():
    src = sys.argv[1]
    rank = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    data = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            data = json.load(f)
    added = 0
    for line in open(src, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        npc, name, kind, levels = line.split("|")
        if JUNK.search(name) or name in data:
            continue
        c = {"npc": int(npc), "rank": rank, "type": int(kind)}
        if levels:
            lo, hi = levels.split("-")
            c["lo"], c["hi"] = int(lo), int(hi)
        data[name] = c
        added += 1
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print(added, "added,", len(data), "in", OUT)


if __name__ == "__main__":
    main()
