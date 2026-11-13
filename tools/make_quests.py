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
JUNK = re.compile(r"UNUSED|DEPRECATED|<NYI>|<TXT>|\bTEST\b|^zz|REUSE|\bOLD\b")  # in capitals: not "Old Gods"
TAB = chr(9)
# What the database cannot say about a quest, by quest id.
NOTES = {
    6922: "Baron Aquanis rises when the Fathom Core is taken from the Fathom Stone.",
    6921: "Taking the Fathom Core from the Fathom Stone calls up Baron Aquanis.",
}

# Who to look for, where the database cannot tell (summoned, or handled by a
# script), by quest id.
WHO = {
    4024: ["Bael'Gar"],                                     # A Taste of Flame
    5214: ["Fras Siabi"],                                   # The Great Fras Siabi
    5282: ["Ghostly Citizen", "Spectral Citizen"],          # The Restless Souls
    8945: ["Baron Rivendare"],                              # Dead Man's Plea
    8966: ["Mor Grayhoof"], 8989: ["Mor Grayhoof"],         # Lord Valthalak's Amulet, left and right
    8967: ["Isalien"], 8990: ["Isalien"],
    8968: ["Jarien", "Sothos"], 8991: ["Jarien", "Sothos"],
    5384: ["Kirtonos the Herald"],                          # Kirtonos the Herald
}


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

    tables = read_tables(("quest_template", "creature_loot_template", "gameobject_template", "gameobject",
                          "gameobject_loot_template", "creature_questrelation", "gameobject_questrelation",
                          "item_template", "creature_template", "creature_involvedrelation",
                          "gameobject_involvedrelation"))
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

    # ...and the things it is found in: chests and the like (objects), by what
    # they hold, and objects the quest has you use
    gcols, gdata = tables["gameobject_template"]
    objects = {}
    for r in gdata:
        objects[x.num(r[gcols.index("entry")])] = {"name": r[gcols.index("name")], "type": x.num(r[gcols.index("type")]),
                                                   "loot": x.num(r[gcols.index("data1")]), "spawns": []}
    scols, sdata = tables["gameobject"]
    for r in sdata:
        o = objects.get(x.num(r[scols.index("id")]))
        if o:
            o["spawns"].append([x.num(r[scols.index("map")]), round(float(r[scols.index("position_x")]), 1),
                                round(float(r[scols.index("position_y")]), 1), round(float(r[scols.index("position_z")]), 1)])
    ocols, oloot = tables["gameobject_loot_template"]
    holds = {}
    for r in oloot:
        holds.setdefault(x.num(r[ocols.index("item")]), set()).add(x.num(r[ocols.index("entry")]))
    chests = {}
    for entry, o in objects.items():
        if o["type"] == 3 and o["loot"]:
            chests.setdefault(o["loot"], []).append(entry)
    creature_names = {c["name"] for c in creatures.values()}
    # who hands each quest out (and whether they stand inside an instance),
    # the item that begins it, and the quest it follows
    tcols, tdata = tables["creature_template"]
    names_of = {x.num(r[tcols.index("Entry")]): r[tcols.index("Name")] for r in tdata}
    givers = {}
    rcols, rdata = tables["creature_questrelation"]
    for r in rdata:
        who = x.num(r[rcols.index("id")])
        if names_of.get(who):
            spawns = creatures.get(who, {}).get("spawns", [])
            givers.setdefault(x.num(r[rcols.index("quest")]),
                              (names_of[who], {sp[0] for sp in spawns}, [sp[1:] for sp in spawns]))
    rcols, rdata = tables["gameobject_questrelation"]
    for r in rdata:
        o = objects.get(x.num(r[rcols.index("id")]))
        if o and o["name"]:
            givers.setdefault(x.num(r[rcols.index("quest")]),
                              (o["name"], {sp[0] for sp in o["spawns"]}, [sp[1:] for sp in o["spawns"]]))
    takers = {}  # who each quest is handed in to
    rcols, rdata = tables["creature_involvedrelation"]
    for r in rdata:
        who = x.num(r[rcols.index("id")])
        if names_of.get(who):
            spawns = creatures.get(who, {}).get("spawns", [])
            takers.setdefault(x.num(r[rcols.index("quest")]),
                              (names_of[who], {sp[0] for sp in spawns}, [sp[1:] for sp in spawns]))
    rcols, rdata = tables["gameobject_involvedrelation"]
    for r in rdata:
        o = objects.get(x.num(r[rcols.index("id")]))
        if o and o["name"]:
            takers.setdefault(x.num(r[rcols.index("quest")]),
                              (o["name"], {sp[0] for sp in o["spawns"]}, [sp[1:] for sp in o["spawns"]]))
    icols, idata = tables["item_template"]
    starts, start_item = {}, {}
    for r in idata:
        begins = x.num(r[icols.index("startquest")])
        if begins:
            starts.setdefault(begins, plain(r[icols.index("name")]))
            start_item.setdefault(begins, x.num(r[icols.index("entry")]))
    # the game's list of boss fights: which instance each boss belongs to
    fights = {}
    for e in m.table("DungeonEncounter", m.FOREVER):
        if int(e["MapID"]) in instance:
            fights.setdefault(norm(e["Name_lang"]), int(e["MapID"]))
    titles = {x.num(r[col("entry")]): plain(r[col("Title")]) for r in data}
    spots = {}  # {map: {name: [[x, y, z], ...]}}: where each thing named stands, for the map marks

    def wants(r):
        """-> [[creature or object, ...], ...]: for each thing a quest asks for,
        the creatures and objects that are it or hold it."""
        groups = []
        for i in (1, 2, 3, 4):
            who = x.num(r[col("ReqCreatureOrGOId%d" % i)])
            if who > 0 and who in creatures:
                groups.append([creatures[who]])
            elif who < 0 and -who in objects:
                groups.append([objects[-who]])
            item = x.num(r[col("ReqItemId%d" % i)])
            if not item:
                continue
            found = []
            has = carriers.get(item, [])
            if len(has) <= 12:  # more than that is a drop of the whole place, or the whole world
                found += [creatures[c] for c in has if c in creatures]
            for lootid in holds.get(item, ()):
                found += [objects[e] for e in chests.get(lootid, [])]
            groups.append(found)
        # ...and whoever drops the item that begins it
        begun_by = start_item.get(x.num(r[col("entry")]))
        if begun_by:
            groups.append([creatures[c] for c in carriers.get(begun_by, [])[:12] if c in creatures])
        return groups

    def sources(r):
        """-> [(name, spawns)] of the creatures and objects a quest sends you to."""
        out = []
        for c in (c for group in wants(r) for c in group):
            if not c["name"]:
                continue
            spawns = c["spawns"]
            # a boss that is summoned stands nowhere in the database: the
            # game's own list of fights says which dungeon it belongs to
            if not spawns and norm(c["name"]) in fights:
                spawns = [[fights[norm(c["name"])]]]
            out.append((c["name"], spawns))
        return out

    def targets(r, mp):
        names = []
        for name, spawns in sources(r):
            here = [sp[1:] for sp in spawns if sp[0] == mp]
            if here and name not in names:
                names.append(name)
                spots.setdefault(mp, {}).setdefault(name, []).extend(p for p in here if len(p) == 3)
        return names[:4]

    def home(r):
        """The one instance a quest filed elsewhere really sends you into, if any."""
        found = set()
        for name, spawns in sources(r):
            maps_of = {sp[0] for sp in spawns}
            # creatures only: a chest of the same name stands in many places
            if maps_of and maps_of <= instance and name in creature_names:
                found |= maps_of
        return found.pop() if len(found) == 1 else None

    def homes(r):
        """The instances a quest filed elsewhere really sends you into: the
        one, or each of a few where every piece it asks for comes from one
        instance alone (The Test of Righteousness: the lumber from the
        Deadmines, the hammer from Shadowfang Keep)."""
        found = set()
        for group in wants(r):
            inside = {sp[0] for c in group for sp in c["spawns"]} & instance
            if len(inside) > 1:  # a piece found in several: no telling which
                found = set()
                break
            found |= inside  # (it may also be had outside, like the Kor Gem)
        if 2 <= len(found) <= 3:
            return sorted(found)
        one = home(r)
        return [one] if one else []

    def places(r):
        zone = x.num(r[col("ZoneOrSort")])
        mp = area_map.get(zone) if zone > 0 else None
        if mp in instance:
            return [mp]
        return homes(r)  # filed under the quest giver's zone, but its quarry lives in a dungeon

    by_map = {}
    def named(mp):
        name = maps[mp]["MapName_lang"]
        return ("the " + name) if name in ("Deadmines",) else name

    for r, mp, every in ((r, mp, every) for r in data for every in [places(r)] for mp in every):
        title = r[col("Title")]
        if not title or JUNK.search(title):
            continue
        # not the class sets, profession recipes and turn-ins done over and over
        if x.num(r[col("RequiredSkill")]) or x.num(r[col("SpecialFlags")]) & 1:
            continue
        # a class's own quests are kept for that class (not the raid armour
        # sets: those are handed in over and over)
        classes = x.num(r[col("RequiredClasses")])
        if classes and maps[mp].get("InstanceType") == "2":
            continue
        races = x.num(r[col("RequiredRaces")])
        side = "A" if races and not races & HORDE else "H" if races and not races & ALLIANCE else None
        by_map.setdefault(mp, []).append({
            "id": x.num(r[col("entry")]), "title": plain(title), "level": x.num(r[col("QuestLevel")]),
            "min": x.num(r[col("MinLevel")]), "side": side, "text": plain(r[col("Objectives")]),
            "who": targets(r, mp)})
        q = by_map[mp][-1]
        if classes:
            q["class"] = classes
        if not q["who"] and q["id"] in WHO:
            q["who"] = WHO[q["id"]]
            for name in q["who"]:  # where they stand, for the map
                for c in list(creatures.values()) + list(objects.values()):
                    if c["name"] == name:
                        spots.setdefault(mp, {}).setdefault(name, []).extend(
                            sp[1:] for sp in c["spawns"] if sp[0] == mp and len(sp) == 4)
        if q["id"] in NOTES:
            q["note"] = NOTES[q["id"]]
        elif len(every) > 1:
            rest = [named(m) for m in every if m != mp]
            q["note"] = "The rest of what it asks for is found in %s." % " and ".join(rest)
        giver = givers.get(q["id"])
        if q["id"] in starts:
            q["item"] = starts[q["id"]]
        elif giver:
            q["from"], q["inside"] = plain(giver[0]), mp in giver[1]
            if q["inside"]:  # where they stand, for the map
                spots.setdefault(mp, {}).setdefault(giver[0], []).extend(giver[2])
        taker = takers.get(q["id"])
        if taker and mp in taker[1]:  # handed in inside the dungeon itself: worth knowing, and marking
            q["to"] = plain(taker[0])
            spots.setdefault(mp, {}).setdefault(taker[0], []).extend(taker[2])
        # what it pays: the items you choose one of, and those you get regardless
        q["pick"] = [i for i in (x.num(r[col("RewChoiceItemId%d" % n)]) for n in range(1, 7)) if i]
        q["get"] = [i for i in (x.num(r[col("RewItemId%d" % n)]) for n in range(1, 5)) if i]
        before = titles.get(x.num(r[col("PrevQuestId")]))
        if before and before != q["title"] and not JUNK.search(before):
            q["after"] = before
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
        "--   who: the creatures and objects to look for (to kill, or that hold what is asked for)",
        "--   from: who hands the quest out (inside = true: they stand in the dungeon itself);",
        "--   item: the item that begins it instead; after: the quest it follows",
        "--   to: who it is handed in to, where they stand inside the dungeon",
        "--   note: something worth knowing that the rest does not say",
        "--   class: a mask of the classes it is offered to (bit = class id - 1), where not all",
        "--   pick: item ids of the rewards you choose one of; get: those you are given regardless",
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
            if not who and any(q.get(k) for k in ("from", "item", "after", "to", "note")):
                who = ", nil"
            for k in ("from", "item", "after", "to", "note"):
                if q.get(k):
                    who += ", %s = %s" % (k, lua_string(q[k]))
            if q.get("inside"):
                who += ", inside = true"
            if q.get("class"):
                who = (who or ", nil") + ", class = %d" % q["class"]
            for k in ("pick", "get"):
                if q.get(k):
                    if not who:
                        who = ", nil"
                    who += ", %s = { %s }" % (k, ", ".join(map(str, q[k])))
            out.append(TAB + "{ %d, %s, %d, %d, %s, %s%s }," % (
                q["id"], lua_string(q["title"]), q.get("level") or 0, q.get("min") or 0,
                ('"%s"' % q["side"]) if q.get("side") else "nil", lua_string(q.get("text") or ""), who))
        out.append("}")
    with open(LUA, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    with open(os.path.join(m.ROOT, "refs", "classicdb", "quest_spots.json"), "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in spots.items()}, f)
    print(total, "quests in", len(by_map), "instances; wrote", LUA)
    print("  " + ", ".join("%s %d" % (maps[mp]["MapName_lang"], len(by_map[mp])) for mp in sorted(by_map)))


if __name__ == "__main__":
    main()
