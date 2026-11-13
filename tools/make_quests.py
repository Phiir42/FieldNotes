"""Builds FieldNotes/Quests.lua: the quests that belong to each dungeon and raid.

    python tools/make_quests.py

Classic dungeons: the cmangos classic database (refs/classicdb/ClassicDB.sql.gz,
see extract_classicdb.py), every quest filed under a dungeon's area. The
dungeons new to Forever: tools/data/forever_quests.json, gathered from
published guides ({ map name: [ { id, title, side, level, min, text, who } ] }).

  ns.Quests[instance map id] = { { id, "Title", level, min level, "A"/"H"/nil, "objective", { who } }, ... }
"""
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_classicdb as x  # noqa: E402
import make_abilities as m  # noqa: E402

LUA = os.path.join(m.ROOT, "FieldNotes", "Quests.lua")
EXTRA = os.path.join(m.ROOT, "tools", "data", "forever_quests.json")
ALLIANCE, HORDE = 77, 178  # race masks
JUNK = re.compile(r"UNUSED|DEPRECATED|<NYI>|<TXT>|\bTEST\b|^zz|REUSE|OLD\b", re.I)
TAB = chr(9)


def read_tables(wanted):
    """-> {table: (columns, rows)} from the database dump."""
    cols, data, current = {t: [] for t in wanted}, {t: [] for t in wanted}, None
    with gzip.open(x.DUMP, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            made = re.match(r"CREATE TABLE `([^`]+)`", line)
            if made:
                current = made.group(1) if made.group(1) in wanted else None
                continue
            if current:
                c = re.match(r"\s*`([^`]+)`", line)
                if c:
                    cols[current].append(c.group(1))
                elif line.startswith(")"):
                    current = None
                continue
            hit = re.match(r"INSERT INTO `([^`]+)`(?: \([^)]*\))? VALUES\s*(.*)", line, re.S)
            if hit and hit.group(1) in wanted:
                data[hit.group(1)].extend(x.rows(hit.group(2)))
    return {t: (cols[t], data[t]) for t in wanted}


def norm(name):
    return re.sub(r"[^a-z]", "", re.sub(r"^the ", "", name.lower()))


def plain(text):
    """Quest text as the journal can show it: no client placeholders."""
    text = re.sub(r"\$[Bb]", " ", text or "")
    text = re.sub(r"\$[Gg]\s*([^:;]*):([^;]*);", r"\1", text)
    text = re.sub(r"\$[NnCc]", "adventurer", text)
    text = re.sub(r"\$[Rr]", "traveller", text)
    text = text.replace(chr(92) + "n", " ").replace(chr(92) + "'", "'").replace(chr(92) + '"', '"')
    return re.sub(r"\s+", " ", text).strip()


def lua_string(s):
    return '"' + s.replace(chr(92), chr(92) * 2).replace('"', chr(92) + '"') + '"'


def main():
    maps = {int(r["ID"]): r for r in m.table("Map", m.FOREVER)}
    instance = {i for i, r in maps.items() if r.get("InstanceType") in ("1", "2")}
    area_map = {int(r["ID"]): int(r["ContinentID"]) for r in m.table("AreaTable", m.FOREVER)}
    # a dungeon's quests are filed under its area, which the area table may
    # place on the continent outside (the entrance): go by its name as well
    by_name = {norm(r["MapName_lang"]): i for i, r in maps.items() if i in instance}
    for a in m.table("AreaTable", m.FOREVER):
        if area_map.get(int(a["ID"])) not in instance and norm(a["AreaName_lang"]) in by_name:
            area_map[int(a["ID"])] = by_name[norm(a["AreaName_lang"])]

    tables = read_tables(("quest_template", "creature_loot_template"))
    cols, data = tables["quest_template"]
    col = cols.index
    # who to look for: the creatures a quest asks you to kill, and those that
    # carry what it asks you to bring; only ones that live in that instance
    with open(os.path.join(m.ROOT, "refs", "classicdb", "creatures.json"), encoding="utf-8") as f:
        creatures = {int(k): v for k, v in json.load(f).items()}
    lcols, loot = tables["creature_loot_template"]
    carriers = {}
    for r in loot:
        carriers.setdefault(x.num(r[lcols.index("item")]), []).append(x.num(r[lcols.index("entry")]))

    def targets(r, mp):
        ids = [x.num(r[col("ReqCreatureOrGOId%d" % i)]) for i in (1, 2, 3, 4)]
        for i in (1, 2, 3, 4):
            ids += carriers.get(x.num(r[col("ReqItemId%d" % i)]), [])
        names = []
        for i in ids:
            c = creatures.get(i)
            if c and c["name"] and any(sp[0] == mp for sp in c["spawns"]) and c["name"] not in names:
                names.append(c["name"])
        return names[:4]

    by_map = {}
    for r in data:
        zone = x.num(r[col("ZoneOrSort")])
        mp = area_map.get(zone) if zone > 0 else None
        title = r[col("Title")]
        if mp not in instance or not title or JUNK.search(title):
            continue
        # not the class sets, profession recipes and turn-ins done over and over
        if x.num(r[col("RequiredClasses")]) or x.num(r[col("RequiredSkill")]) or x.num(r[col("SpecialFlags")]) & 1:
            continue
        races = x.num(r[col("RequiredRaces")])
        side = "A" if races and not races & HORDE else "H" if races and not races & ALLIANCE else None
        by_map.setdefault(mp, []).append({
            "id": x.num(r[col("entry")]), "title": plain(title), "level": x.num(r[col("QuestLevel")]),
            "min": x.num(r[col("MinLevel")]), "side": side, "text": plain(r[col("Objectives")]),
            "who": targets(r, mp)})
    if os.path.exists(EXTRA):
        with open(EXTRA, encoding="utf-8") as f:
            for name, quests in json.load(f).items():
                if norm(name) not in by_name:
                    print("no instance map named", name)
                    continue
                mp = by_name[norm(name)]
                have = {q["id"] for q in by_map.get(mp, [])}
                by_map.setdefault(mp, []).extend(q for q in quests if q["id"] not in have)

    out = [
        "-- Quests of each dungeon and raid. GENERATED by tools/make_quests.py: do not edit.",
        "--   ns.Quests[instance map id] = { { quest id, title, level, min level, side, objective, who }, ... }",
        "--   side: \"A\" or \"H\" where only one faction is offered the quest",
        "--   who: the creatures to look for (those to kill, or that carry what is asked for)",
        "local _, ns = ...",
        "",
        "local Q = {}",
        "ns.Quests = Q",
    ]
    total = 0
    for mp in sorted(by_map):
        quests = sorted(by_map[mp], key=lambda q: (q.get("level") or 99, q["title"], q["id"]))
        out.append("")
        out.append("-- " + maps[mp]["MapName_lang"])
        out.append("Q[%d] = {" % mp)
        for q in quests:
            total += 1
            who = ", { %s }" % ", ".join(lua_string(w) for w in q["who"]) if q.get("who") else ""
            out.append(TAB + "{ %d, %s, %d, %d, %s, %s%s }," % (
                q["id"], lua_string(q["title"]), q.get("level") or 0, q.get("min") or 0,
                ('"%s"' % q["side"]) if q.get("side") else "nil", lua_string(q.get("text") or ""), who))
        out.append("}")
    with open(LUA, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print(total, "quests in", len(by_map), "instances; wrote", LUA)
    print("  " + ", ".join("%s %d" % (maps[mp]["MapName_lang"], len(by_map[mp])) for mp in sorted(by_map)))


if __name__ == "__main__":
    main()
