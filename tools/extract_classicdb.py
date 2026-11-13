"""Extracts what the journal tools need from the cmangos classic database dump
(https://github.com/cmangos/classic-db, GPL-3.0; download
Full_DB/ClassicDB_1_12_1_z*.sql.gz to refs/classicdb/ClassicDB.sql.gz).

    python tools/extract_classicdb.py

Writes refs/classicdb/creatures.json:
  { "<creature entry>": { "name", "rank", "lo", "hi", "type", "spells": [spell IDs],
                          "spawns": [[map, x, y, z], ...], "summoned": true } }
Spells come from the creature's spell list, its template spells and the
casts in its AI scripts. Only creatures that spawn in an instance map, are
called up by one that does, or have spells are kept.

"summoned": the creature has no place of its own in an instance but is called
up there: by a summoning spell or AI script of a creature that lives there,
or by an instance's own script in the cmangos core (refs/cmangos, see
make_abilities.py), whose NPC_ constants name every creature it handles.
"""
import csv, glob, gzip, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(ROOT, "refs", "classicdb", "ClassicDB.sql.gz")
OUT = os.path.join(ROOT, "refs", "classicdb", "creatures.json")
TABLES = ("creature_template", "creature_template_spells", "creature_spell_list", "creature", "creature_ai_scripts")
ACTION_CAST = 11  # EventAI ACTION_T_CAST: param1 is the spell
ACTION_SUMMON = 12  # EventAI ACTION_T_SUMMON: param1 is the creature
ACTION_SUMMON_ID = 32  # EventAI ACTION_T_SUMMON_ID: param1 is the creature
SPELL_EFFECTS = os.path.join(ROOT, "refs", "tables", "wowf", "SpellEffect.csv")
SUMMON_EFFECTS = {28, 41, 42, 56, 112}  # summon, wild, guardian, pet, demon
SCRIPTS = os.path.join(ROOT, "refs", "cmangos", "mangos-classic", "src", "game", "AI", "ScriptDevAI", "scripts")


def summoning_spells():
    """{spell ID: [creature entry]} for every spell that calls up a creature."""
    out = {}
    if os.path.exists(SPELL_EFFECTS):
        with open(SPELL_EFFECTS, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if num(r["Effect"]) in SUMMON_EFFECTS and num(r["EffectMiscValue_0"]) > 0:
                    out.setdefault(num(r["SpellID"]), []).append(num(r["EffectMiscValue_0"]))
    return out


def scripted_creatures():
    """Creature entries the core's instance scripts name (one folder each)."""
    out = set()
    for path in glob.glob(os.path.join(SCRIPTS, "*", "*", "*.[ch]*")):
        with open(path, encoding="utf-8", errors="replace") as f:
            out.update(int(v) for v in re.findall(r"\bNPC_\w+\s*=\s*(\d+)", f.read()))
    return out


def rows(values):
    """Split the body of INSERT ... VALUES (..),(..); into lists of fields."""
    row, field, quoted, in_row, i, n = [], [], False, False, 0, len(values)
    while i < n:
        c = values[i]
        if quoted:
            if c == "\\" and i + 1 < n:
                field.append(values[i + 1])
                i += 2
                continue
            if c == "'":
                quoted = False
            else:
                field.append(c)
        elif c == "'":
            quoted = True
        elif c == "(" and not in_row:
            in_row, row, field = True, [], []
        elif c == "," and in_row:
            row.append("".join(field))
            field = []
        elif c == ")" and in_row:
            row.append("".join(field))
            yield row
            in_row = False
        elif in_row:
            field.append(c)
        i += 1


def num(v):
    try:
        return int(float(v))
    except ValueError:
        return 0


def main():
    cols, data = {}, {t: [] for t in TABLES}
    current = None
    with gzip.open(DUMP, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r"CREATE TABLE `([^`]+)`", line)
            if m:
                current = m.group(1) if m.group(1) in TABLES else None
                if current:
                    cols[current] = []
                continue
            if current:
                c = re.match(r"\s*`([^`]+)`", line)
                if c:
                    cols[current].append(c.group(1))
                elif line.startswith(")"):
                    current = None
                continue
            m = re.match(r"INSERT INTO `([^`]+)`(?: \([^)]*\))? VALUES\s*(.*)", line, re.S)
            if m and m.group(1) in TABLES:
                data[m.group(1)].extend(rows(m.group(2)))

    def col(table, name):
        return cols[table].index(name)

    creatures = {}
    t = "creature_template"
    e, nm, rk = col(t, "Entry"), col(t, "Name"), col(t, "Rank")
    sl = col(t, "SpellList") if "SpellList" in cols[t] else None
    spell_list_of = {}
    for r in data[t]:
        creatures[num(r[e])] = {"name": r[nm], "rank": num(r[rk]), "lo": num(r[col(t, "MinLevel")]),
                                "hi": num(r[col(t, "MaxLevel")]), "type": num(r[col(t, "CreatureType")]),
                                "spells": [], "spawns": [],
                                # gossip, quest giver, vendor...: someone to talk to, not to fight
                                "npc": num(r[col(t, "NpcFlags")]) if "NpcFlags" in cols[t] else 0,
                                # what it looks like: a creature display id the client can draw
                                "model": next((num(r[col(t, c)]) for c in ("ModelId1", "ModelId2", "ModelId3", "ModelId4")
                                               if c in cols[t] and num(r[col(t, c)])), 0)}
        if sl is not None and num(r[sl]):
            spell_list_of[num(r[e])] = num(r[sl])

    lists = {}
    t = "creature_spell_list"
    for r in data[t]:
        lists.setdefault(num(r[col(t, "Id")]), []).append(num(r[col(t, "SpellId")]))
    for entry, list_id in spell_list_of.items():
        creatures[entry]["spells"] += lists.get(list_id, [])

    t = "creature_template_spells"
    for r in data[t]:
        c = creatures.get(num(r[col(t, "entry")]))
        if c:
            c["spells"] += [num(v) for v in r[2:] if num(v)]

    t = "creature_ai_scripts"
    cid = col(t, "creature_id")
    calls = {}  # creature entry: the creatures it calls up
    for r in data[t]:
        c = creatures.get(num(r[cid]))
        if not c:
            continue
        for a in (1, 2, 3):
            kind, param = num(r[col(t, f"action{a}_type")]), num(r[col(t, f"action{a}_param1")])
            if kind == ACTION_CAST and param:
                c["spells"].append(param)
            elif kind in (ACTION_SUMMON, ACTION_SUMMON_ID) and param:
                calls.setdefault(num(r[cid]), []).append(param)

    t = "creature"
    for r in data[t]:
        c = creatures.get(num(r[col(t, "id")]))
        m = num(r[col(t, "map")])
        if c and m > 1:  # instances only; 0 and 1 are the two continents
            c["spawns"].append([m, round(float(r[col(t, "position_x")]), 1), round(float(r[col(t, "position_y")]), 1),
                                round(float(r[col(t, "position_z")]), 1)])

    # what is called up in an instance, and what that calls up in turn
    spells = summoning_spells()
    summoned = {e for e in scripted_creatures() if e in creatures and not creatures[e]["spawns"]}
    todo = [e for e, c in creatures.items() if c["spawns"]] + sorted(summoned)
    summoners = {}  # creature entry: who calls it up
    while todo:
        e = todo.pop()
        for s in creatures[e]["spells"]:
            calls.setdefault(e, []).extend(spells.get(s, []))
        for other in calls.get(e, []):
            if other in creatures and not creatures[other]["spawns"]:
                summoners.setdefault(other, set()).add(e)
                if other not in summoned:
                    summoned.add(other)
                    todo.append(other)
    for e in summoned:
        # a pet or guardian takes its level from whoever calls it up, not from
        # its record (Voidwalker Minion: 47 on record, 25 in Blackfathom Deeps)
        c, near = creatures[e], [creatures[s] for s in summoners.get(e, ()) if creatures[s]["lo"]]
        if near and not any(n["lo"] - 5 <= c["hi"] and c["lo"] <= n["hi"] + 5 for n in near):
            c["lo"] = c["hi"] = 0
        # not the unseen helpers scripts call up (spawn points, kill credit...)
        if not re.search(r"\(DND\)|Trigger|Kill Credit|Spawner|Spawn Point|GM can see", creatures[e]["name"]):
            creatures[e]["summoned"] = True

    kept = {}
    for entry, c in creatures.items():
        c["spells"] = list(dict.fromkeys(c["spells"]))
        # elites and bosses are kept even with neither: a scripted boss is
        # summoned and casts from code, but its picture is still wanted
        if c["spells"] or c["spawns"] or c.get("summoned") or (c["rank"] and c["model"]):
            kept[entry] = c
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(kept, f)
    with_spells = sum(1 for c in kept.values() if c["spells"])
    print({k: len(v) for k, v in data.items()})
    print(f"{len(kept)} creatures kept, {with_spells} with spells, {len(summoned)} summoned -> {OUT}")


if __name__ == "__main__":
    main()
