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
Only spells that exist in the Forever client (refs/tables/wowf/SpellName.csv)
are kept, and only encounters the Forever client has (DungeonEncounter.csv).
"""
import csv, glob, os, re, urllib.request

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


def main():
    names = {int(r["ID"]): r["Name_lang"] for r in table("SpellName", FOREVER)}
    mod_id, mod_name = boss_mod_spells()
    jrn_id, jrn_name = journal_spells()
    maps = {r["ID"]: r["MapName_lang"] for r in table("Map", FOREVER)}

    out, total, with_data = [], 0, 0
    encounters = sorted(table("DungeonEncounter", FOREVER), key=lambda r: (int(r["MapID"]), int(r["OrderIndex"] or 0)))
    seen_keys = set()
    last_map = None
    for e in encounters:
        eid, name = int(e["ID"]), e["Name_lang"]
        total += 1
        k = key(name)
        raw = mod_id.get(eid, []) + mod_name.get(k, []) + jrn_id.get(eid, []) + jrn_name.get(k, [])
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
        "local _, ns = ...",
        "",
        "local A, N = {}, {}",
        "ns.Abilities, ns.AbilitiesByName = A, N",
    ]
    with open(LUA, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(header + out) + "\n")
    print(f"{with_data} of {total} Forever encounters have abilities; wrote {LUA}")


if __name__ == "__main__":
    main()
