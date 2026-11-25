"""The names the Forever client can report, for the checks that need them.

    python tools/game_names.py      # refresh tools/data/game_names.json

Two checks ask what the game itself knows: check_boss_marks (every boss fight
of each dungeon) and check_map_names (every sub-zone, boss fight and creature
name the journal could ever record). The answers come from the client's
tables and the classic database under refs/, which is not in the repository.
So that the checks also run where refs/ is missing (the tests on GitHub), the
names are kept in tools/data/game_names.json: with refs/ at hand they are
read fresh and the file is rewritten when it no longer agrees (commit it);
without, the file is what is read.
"""
import json
import os

import make_abilities as m

ROOT = m.ROOT
SNAPSHOT = os.path.join(ROOT, "tools", "data", "game_names.json")
CREATURES = os.path.join(ROOT, "refs", "classicdb", "creatures.json")
EXTRA = ("forever_creatures.json", "forever_npcs.json")  # Forever's own, in the repository


def fresh():
    """The names as refs/ has them."""
    encounters = {}
    for r in m.table("DungeonEncounter", m.FOREVER):
        encounters.setdefault(r["MapID"], set()).add(r["Name_lang"])
    names = {m.key(r["AreaName_lang"]) for r in m.table("AreaTable", m.FOREVER)}
    names |= {m.key(r["AreaName_lang"]) for r in m.table("WMOAreaTable", m.FOREVER) if r.get("AreaName_lang")}
    names |= {m.key(n) for found in encounters.values() for n in found}
    with open(CREATURES, encoding="utf-8") as f:
        names |= {m.key(c["name"]) for c in json.load(f).values() if c["name"]}
    names.discard("")
    return {"build": m.FOREVER,
            "encounters": {k: sorted(v) for k, v in sorted(encounters.items(), key=lambda e: int(e[0]))},
            "reportable": sorted(names)}


def load():
    old = None
    if os.path.exists(SNAPSHOT):
        with open(SNAPSHOT, encoding="utf-8") as f:
            old = json.load(f)
    if not os.path.exists(CREATURES):
        if old is None:
            raise SystemExit("neither refs/ nor tools/data/game_names.json: nothing to check against")
        return old
    new = fresh()
    if new != old:
        with open(SNAPSHOT, "w", encoding="utf-8", newline="\n") as f:
            json.dump(new, f, indent=0, ensure_ascii=False)
            f.write("\n")
        print("tools/data/game_names.json rewritten from refs/: commit it")
    return new


def encounters():
    """{instance map ID: {boss fight names}}"""
    return {int(k): set(v) for k, v in load()["encounters"].items()}


def reportable():
    """Keys (as ns:AreaKey makes them) of every name the journal could record."""
    names = set(load()["reportable"])
    for extra in EXTRA:
        path = os.path.join(ROOT, "tools", "data", extra)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                names |= {m.key(n) for n in json.load(f)}
    return names


if __name__ == "__main__":
    data = load()
    print("%d dungeons' boss fights, %d names (build %s)" % (
        len(data["encounters"]), len(data["reportable"]), data["build"]))
