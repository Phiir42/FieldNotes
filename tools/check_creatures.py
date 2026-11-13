"""List where the map generator files creatures differently from a definition.

    python tools/check_creatures.py [slug ...]      (default: every one-road dungeon)

On a one-road map, meeting a creature uncovers its room and every room before
it, so a creature filed under a later room than it first appears in uncovers
the map too early. make_maps.py therefore files each creature under the
earliest room its spawn points (classic database) really lie in; this prints
those corrections without building anything. For dungeons that are not
one-road ("path": True) the generator leaves the definition alone, so naming
one here shows what it would change if it were.

Needs refs/ (map tiles, tables, classicdb/creatures.json); see make_maps.py.
"""
import sys

import make_maps as m


def main():
    blank, _ = m.blank_parchment()
    want = sys.argv[1:]
    for d in m.definitions():
        if (want and d["slug"] not in want) or (not want and d.get("path") is not True):
            continue
        splits = [m.split(f, blank) for f in d["floors"]]
        m.boss_points(d, splits)
        moved = m.creature_rooms(d, splits)
        order = [list(f["areas"]) for f in d["floors"]]
        print("%s: %d changes" % (d["slug"], sum(map(len, moved.values()))))
        for f, rows in sorted(moved.items()):
            for name, room in rows:
                print("    sheet %d  %-30s -> %s" % (
                    f + 1, name, "room %d (%s)" % (room, order[f][room - 1]) if room else "not on this sheet"))


if __name__ == "__main__":
    main()
