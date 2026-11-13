"""Builds FieldNotes/Abilities.lua: the spells each boss is known to use.

    python tools/make_abilities.py

The Forever client hides most combat data from addons, so the journal cannot
note a boss's abilities by watching the fight. Instead it ships a list of
spell IDs per boss and writes them onto the boss's page once the boss is
defeated; the game supplies each spell's name, icon and description.

Sources, merged per encounter:
  1. The BigWigs / LittleWigs classic boss modules installed in the retail
     client's AddOns folder (the spells each module tracks).
  2. Retail's dungeon journal tables from wago.tools (cached in refs/tables).
  3. The cmangos classic database (see tools/extract_classicdb.py): the
     spells each creature of the boss's name casts.
  4. The cmangos boss scripts (see script_spells): the spells of fights that
     are written in code rather than in the database.
Only spells that exist in the Forever client (refs/tables/wowf/SpellName.csv)
are kept, and only encounters the Forever client has (DungeonEncounter.csv).
"""
import csv, glob, json, os, re, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = os.path.join(ROOT, "refs", "tables")
ADDONS = r"C:\Program Files (x86)\World of Warcraft\_retail_\Interface\AddOns"
LUA = os.path.join(ROOT, "FieldNotes", "Abilities.lua")
FOREVER = "1.60.1.70862"
MAX_SPELLS = 14


def table(name, build=None):
    path = os.path.join(TABLES, "wowf" if build else "", name + ".csv")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        url = f"https://wago.tools/db2/{name}/csv" + (f"?build={build}" if build else "")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
            f.write(r.read())
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def key(name):
    """Same normalisation as ns:AreaKey in the addon."""
    return re.sub(r"[^a-z0-9]", "", re.sub(r"^the ", "", name.lower()))


def boss_mod_spells():
    """-> ({encounterID: [spellID]}, {name key: [spellID]}) from the installed boss modules."""
    by_id, by_name = {}, {}
    files = glob.glob(os.path.join(ADDONS, "BigWigs_Classic", "*", "*.lua")) + \
        glob.glob(os.path.join(ADDONS, "LittleWigs_Classic", "*", "*.lua"))
    for path in files:
        src = open(path, encoding="utf-8", errors="replace").read()
        boss = re.search(r'NewBoss\("([^"]+)"', src)
        options = re.search(r"function mod:GetOptions\(\)(.*?)\nend", src, re.S)
        if not boss or not options:
            continue
        body = options.group(1).split("},nil", 1)[0].split("}, nil", 1)[0]
        spells = [int(n) for n in re.findall(r"^\s*\{?\s*(\d{3,7})\s*[,}]", body, re.M)]
        if not spells:
            continue
        by_name.setdefault(key(boss.group(1)), []).extend(spells)
        enc = re.search(r"SetEncounterID\(([^)]*)\)", src)
        for n in re.findall(r"\d+", enc.group(1)) if enc else []:
            by_id.setdefault(int(n), []).extend(spells)
    return by_id, by_name


def journal_spells():
    """-> ({encounterID: [spellID]}, {name key: [spellID]}) from retail's dungeon journal."""
    by_id, by_name = {}, {}
    sections = {}
    for s in table("JournalEncounterSection"):
        if s["SpellID"] not in ("", "0"):
            sections.setdefault(s["JournalEncounterID"], []).append((int(s["OrderIndex"] or 0), int(s["SpellID"])))
    for e in table("JournalEncounter"):
        spells = [sp for _, sp in sorted(sections.get(e["ID"], []))]
        if not spells:
            continue
        by_name.setdefault(key(e["Name_lang"]), []).extend(spells)
        if e["DungeonEncounterID"] not in ("", "0"):
            by_id.setdefault(int(e["DungeonEncounterID"]), []).extend(spells)
    return by_id, by_name


# Encounters whose name is not the name of the creature(s) fought.
ALIASES = {
    "Geilhast": ["Gelihast"],
    "The Lost Dwarves": ["Baelog", 'Eric "The Swift"', "Olaf"],
    "Ring of Law": ["Gorosh the Dervish", "Grizzle", "Eviscerator", "Ok'thor the Breaker", "Anub'shiah", "Hedrum the Creeper"],
    "The Vault": ["Warder Stilgiss", "Verek"],
    "The Seven": ["Doom'rel", "Seeth'rel", "Gloom'rel", "Dope'rel", "Hate'rel", "Vile'rel", "Anger'rel"],
    "Kirtonos": ["Kirtonos the Herald"],
    "Ras Frostwhisperer": ["Ras Frostwhisper"],
}


def classicdb_spells():
    """-> {name key: [spellID]} from the cmangos classic database
    (refs/classicdb/creatures.json, written by tools/extract_classicdb.py)."""
    path = os.path.join(ROOT, "refs", "classicdb", "creatures.json")
    by_name = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for c in json.load(f).values():
                if c["spells"]:
                    by_name.setdefault(key(c["name"]), []).extend(c["spells"])
    return by_name


SCRIPTS = os.path.join(ROOT, "refs", "cmangos", "mangos-classic", "src", "game", "AI", "ScriptDevAI", "scripts")


def script_spells():
    """-> {script name key: ([spellID], is a boss script)} from the cmangos
    boss scripts. Bosses whose fights are written in code rather than in the
    database (Arugal's curse and teleports, say) have their spells there:
    SPELL_* constants, used inside a "struct boss_<name>AI". Get the sources with
      git clone --depth 1 --filter=blob:none --sparse https://github.com/cmangos/mangos-classic refs/cmangos/mangos-classic
      git -C refs/cmangos/mangos-classic sparse-checkout set src/game/AI/ScriptDevAI/scripts
    """
    out = {}
    for path in glob.glob(os.path.join(SCRIPTS, "**", "*.cpp"), recursive=True):
        text = open(path, encoding="utf-8", errors="replace").read()
        consts = {m.group(1): int(m.group(2)) for m in re.finditer(r"(SPELL_\w+)\s*=\s*(\d+)", text)}
        if not consts:
            continue
        structs = list(re.finditer(r"struct\s+((?:boss|npc|mob)_\w+?)AI", text))
        for i, m in enumerate(structs):
            body = text[m.start():structs[i + 1].start() if i + 1 < len(structs) else len(text)]
            ids = [consts[c] for c in dict.fromkeys(re.findall(r"SPELL_\w+", body)) if c in consts]
            kind, _, name = m.group(1).partition("_")
            if ids:
                got = out.setdefault(key(name.replace("_", " ")), ([], kind == "boss"))
                got[0].extend(ids)
        # a file for one boss whose script uses no struct of that name
        base = os.path.basename(path)[:-4]
        if base.startswith("boss_") and not structs:
            out.setdefault(key(base[5:].replace("_", " ")), ([], True))[0].extend(consts.values())
    return out


MACHINERY = re.compile(r"Self|Hover|Submerge|Emerge|Visual|Effect|Passive|Trigger|Dummy|Speed Burst|Double Attack|"
                       r"Dual Wield|Invisib|Transform|Spawn|Root|Despawn|Kill Credit|Teleport Self|Cosmetic|Test|Fade")


def script_for(k, scripts):
    """The scripted spells for a boss name key: a script named exactly so, or
    whose name is part of the boss's ("arugal" for Archmage Arugal), or a boss
    script whose name contains the boss's."""
    ids = []
    for sk, (spells, boss) in scripts.items():
        if sk == k or (len(sk) >= 5 and sk in k) or (boss and len(k) >= 5 and k in sk):
            ids += spells
    return ids


RANKS = {1: "elite", 2: "rareelite", 3: "worldboss", 4: "rare"}
TYPES = {1: "Beast", 2: "Dragonkin", 3: "Demon", 4: "Elemental", 5: "Giant", 6: "Undead", 7: "Humanoid",
         8: "Critter", 9: "Mechanical"}
MAX_CREATURE_SPELLS = 6


def creature_lines(names, boss_keys):
    """Lua lines for ns.Creatures: level, rank, kind and spells of every creature
    that lives in an instance, from the classic database. Bosses' spells are
    left to the boss lists."""
    path = os.path.join(ROOT, "refs", "classicdb", "creatures.json")
    if not os.path.exists(path):
        return []
    merged, ids = {}, []
    with open(path, encoding="utf-8") as f:
        for entry, c in json.load(f).items():
            if not c["spawns"] or not c["name"]:
                continue
            ids.append((int(entry), c["name"]))
            m = merged.setdefault(key(c["name"]), {"name": c["name"], "lo": c["lo"], "hi": c["hi"],
                                                    "rank": 0, "type": c["type"], "spells": []})
            m["lo"], m["hi"] = min(m["lo"], c["lo"]), max(m["hi"], c["hi"])
            m["rank"] = max(m["rank"], c["rank"] if c["rank"] in RANKS else 0)
            m["spells"] += c["spells"]
    out = []
    for k in sorted(merged):
        m = merged[k]
        spells, used = [], set()
        for sp in ([] if k in boss_keys else m["spells"]):
            label = names.get(sp)
            if label and label not in used and "(OLD)" not in label and "DND" not in label:
                used.add(label)
                spells.append(sp)
        fields = []
        if m["lo"] > 0:
            fields.append("lo = %d, hi = %d" % (m["lo"], m["hi"]))
        if m["rank"]:
            fields.append('cls = "%s"' % RANKS[m["rank"]])
        if m["type"] in TYPES:
            fields.append('type = "%s"' % TYPES[m["type"]])
        fields.append("spells = { %s }" % ", ".join(map(str, spells[:MAX_CREATURE_SPELLS])))
        out.append('C["%s"] = { %s } -- %s' % (k, ", ".join(fields), m["name"]))
    out += ["", "-- Creature names by NPC id: a looted corpse shows its id but not its name"]
    out += ['I[%d] = "%s"' % (entry, name.replace("\\", "").replace('"', '\\"')) for entry, name in sorted(ids)]
    return out


def main():
    names = {int(r["ID"]): r["Name_lang"] for r in table("SpellName", FOREVER)}
    mod_id, mod_name = boss_mod_spells()
    jrn_id, jrn_name = journal_spells()
    cdb_name = classicdb_spells()
    scripts = script_spells()
    print(len(scripts), "boss and creature scripts read")
    maps = {r["ID"]: r["MapName_lang"] for r in table("Map", FOREVER)}

    out, total, with_data = [], 0, 0
    encounters = sorted(table("DungeonEncounter", FOREVER), key=lambda r: (int(r["MapID"]), int(r["OrderIndex"] or 0)))
    seen_keys = set()
    last_map = None
    for e in encounters:
        eid, name = int(e["ID"]), e["Name_lang"]
        total += 1
        k = key(name)
        raw = mod_id.get(eid, []) + mod_name.get(k, []) + jrn_id.get(eid, []) + jrn_name.get(k, []) + cdb_name.get(k, [])
        scripted = script_for(k, scripts)
        for alias in ALIASES.get(name, []):
            raw += cdb_name.get(key(alias), [])
            scripted += script_for(key(alias), scripts)
        # scripts also name the fight's stage machinery: leave that out
        raw += [sp for sp in scripted if not MACHINERY.search(names.get(sp, ""))]
        spells, used = [], set()
        for sp in raw:
            label = names.get(sp)
            # one entry per spell name: seasonal copies of a spell share the name
            if label and label not in used and "(OLD)" not in label and "DND" not in label:
                used.add(label)
                spells.append((sp, label))
        spells = spells[:MAX_SPELLS]
        if not spells:
            continue
        with_data += 1
        if e["MapID"] != last_map:
            last_map = e["MapID"]
            out.append("\n-- " + maps.get(e["MapID"], "map " + e["MapID"]))
        ids = ", ".join(str(sp) for sp, _ in spells)
        comment = ", ".join(label for _, label in spells)
        out.append("A[%d] = { %s } -- %s: %s" % (eid, ids, name, comment))
        if k not in seen_keys:
            seen_keys.add(k)
            out.append('N["%s"] = A[%d]' % (k, eid))

    header = [
        "-- Boss abilities. GENERATED by tools/make_abilities.py: do not edit.",
        "--",
        "-- The client hides most combat data from addons, so these lists ship with",
        "-- the addon and are written onto a boss's page once the boss is defeated.",
        "-- Only spell IDs are stored; the game supplies names, icons and descriptions.",
        "--   ns.Abilities[encounterID] = { spellID, ... }",
        "--   ns.AbilitiesByName[ns:AreaKey(boss name)] = the same list",
        "--   ns.Creatures[ns:AreaKey(creature name)] = { lo, hi, cls, type, spells }: what is",
        "--     known of the creatures that live in instances, shown on their bestiary entries",
        "local _, ns = ...",
        "",
        "local A, N, C, I = {}, {}, {}, {}",
        "ns.Abilities, ns.AbilitiesByName, ns.Creatures, ns.CreatureNames = A, N, C, I",
    ]
    with open(LUA, "w", encoding="utf-8", newline="\n") as f:
        creatures = creature_lines(names, seen_keys)
        f.write("\n".join(header + out + ["", "-- Creatures"] + creatures) + "\n")
    print(len(creatures), "creatures")
    print(f"{with_data} of {total} Forever encounters have abilities; wrote {LUA}")
    missing = {}
    for e in encounters:
        if ("A[%d] = " % int(e["ID"])) not in "\n".join(out):
            missing.setdefault(maps.get(e["MapID"], e["MapID"]), []).append(e["Name_lang"])
    for m, bosses in missing.items():
        print(f"  {m}: {', '.join(bosses)}")


if __name__ == "__main__":
    main()
