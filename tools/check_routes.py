"""Checks each map definition's area order against the order the bosses are met in.

    python tools/check_routes.py [slug ...]

For every sheet it lists the bosses in the game's own encounter order with the
number of the area each one stands on (areas are numbered in the order the
definition lists them). On a one-road dungeon ("path") those numbers should
never go down; where they do, the areas are not listed in walking order.
Areas no boss stands on are listed too, since nothing here can order them.
"""
import sys
import make_maps as m
from make_abilities import table as forever_table, FOREVER


def main():
    want = sys.argv[1:]
    blank, _ = m.blank_parchment()
    order = {}
    for r in forever_table("DungeonEncounter", FOREVER):
        order.setdefault((int(r["MapID"]), r["Name_lang"]), int(r["OrderIndex"] or 0))
    for d in m.definitions():
        if want and d["slug"] not in want:
            continue
        splits = [m.split(floor, blank) for floor in d["floors"]]
        bosses = m.boss_points(d, splits)
        print(f"{d['slug']}  path={d.get('path', False)}")
        for f, floor in enumerate(d["floors"]):
            names = list(floor["areas"])
            row, used = [], set()
            for name, x, y in sorted(bosses[f], key=lambda b: order.get((d["instance"], b[0]), 0)):
                at = max(((float(a[y - 3:y + 4, x - 3:x + 4].mean()), n) for n, a in splits[f][1]
                          if n not in ("decor",)), default=(0, None))
                room = at[1] if at[0] > 0.3 else None
                n = "start" if room == "start" else (names.index(room) + 1 if room in names else "?")
                used.add(room)
                guess = "*" if (f, name) in d.get("_guessed", ()) else ""
                row.append(f"{name}{guess}={n}")
            nums = [int(p.rsplit("=", 1)[1]) for p in row if p.rsplit("=", 1)[1].isdigit()]
            bad = "  <-- out of order" if nums != sorted(nums) else ""
            empty = [f"{i + 1}:{n}" for i, n in enumerate(names) if n not in used]
            print(f"  sheet {f + 1}: " + ", ".join(row) + bad)
            if empty:
                print("      no boss on: " + ", ".join(empty))


if __name__ == "__main__":
    main()
