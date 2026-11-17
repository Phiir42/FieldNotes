"""Checks each map definition's area order against the order the bosses are met in.

    python tools/check_routes.py [slug ...]

For every sheet it lists the bosses in the game's own encounter order (or the
order a real run met them in, where tools/data/runs.json has one) with the
number of the area each one stands on (areas are numbered in the order the
definition lists them). On a one-road dungeon ("path") those numbers should
never go down along a road; where they do, the areas are not listed in
walking order. Where a real run is on record its replay (tools/test_runs.py)
is the judge, and the line only points there.
Areas no boss stands on are listed too, since nothing here can order them.
"""
import json
import os
import sys
import make_maps as m
from make_abilities import table as forever_table, FOREVER


def main():
    want = sys.argv[1:]
    blank, _ = m.blank_parchment()
    order = {}
    for r in forever_table("DungeonEncounter", FOREVER):
        order.setdefault((int(r["MapID"]), r["Name_lang"]), int(r["OrderIndex"] or 0))
    # Where a real run is on record (tools/data/runs.json), the bosses are put
    # in the order it met them: the game's order is not the walking order
    # where a boss is optional or the dungeon is walked another way.
    runs = json.load(open(os.path.join(m.ROOT, "tools", "data", "runs.json"), encoding="utf-8"))
    for d in m.definitions():
        if want and d["slug"] not in want:
            continue
        splits = [m.split(floor, blank) for floor in d["floors"]]
        bosses = m.boss_points(d, splits)
        met = runs.get(str(d["instance"]), {}).get("met", [])

        def when(name):
            if name in met:
                return (0, met.index(name))
            return (1 if met else 0, order.get((d["instance"], name), 0))
        print(f"{d['slug']}  path={d.get('path', False)}" + ("  (in the order of a real run)" if met else ""))
        for f, floor in enumerate(d["floors"]):
            names = list(floor["areas"])
            row, used = [], set()
            for name, x, y in sorted(bosses[f], key=lambda b: when(b[0])):
                at = max(((float(a[y - 3:y + 4, x - 3:x + 4].mean()), n) for n, a in splits[f][1]
                          if n not in ("decor",)), default=(0, None))
                room = at[1] if at[0] > 0.3 else None
                n = "start" if room == "start" else (names.index(room) + 1 if room in names else "?")
                used.add(room)
                guess = "*" if (f, name) in d.get("_guessed", ()) else ""
                row.append(f"{name}{guess}={n}")
            # Order matters only where reaching an area uncovers those before it
            # (a "path"), and only among the areas of one road: areas in no road
            # of the floor's "roads" are on the first.
            roads = floor.get("roads", [])
            listed = {a for r in roads for a in r}

            def road(area):
                return next((i + 1 for i, r in enumerate(roads) if area in r), 0)
            by_road = {}
            for p in row:
                n = p.rsplit("=", 1)[1]
                if n.isdigit():
                    area = names[int(n) - 1]
                    by_road.setdefault(road(area) if area in listed else 0, []).append(int(n))
            bad = ""
            if d.get("path") and any(nums != sorted(nums) for nums in by_road.values()):
                # With a real run on record, what opens when is checked against
                # it by tools/test_runs.py: walking back to a boss in an area
                # already open (Kraul's Aggem) is not a fault.
                bad = "  (not in order: see the replay, tools/test_runs.py)" if met else "  <-- out of order"
            empty = [f"{i + 1}:{n}" for i, n in enumerate(names) if n not in used]
            print(f"  sheet {f + 1}: " + ", ".join(row) + bad)
            if empty:
                print("      no boss on: " + ", ".join(empty))


if __name__ == "__main__":
    main()
