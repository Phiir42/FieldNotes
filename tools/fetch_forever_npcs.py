"""NPC ids of the bosses of the dungeons new to Forever, by name, from
Wowhead's search suggestions. The classic database knows nothing of these
creatures, so their portraits are drawn from the NPC id instead of a display
id (PlayerModel:SetCreature).

    python tools/fetch_forever_npcs.py

Writes tools/data/forever_npcs.json: { boss name: npc id }. Only exact name
matches of type NPC are kept; names with none are listed and left out.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_abilities as m  # noqa: E402

OUT = os.path.join(m.ROOT, "tools", "data", "forever_npcs.json")
URL = "https://www.wowhead.com/forever/search/suggestions-template?q="
# Names the guides use for bosses the client's encounter list calls otherwise,
# and bosses the list leaves out.
ALSO = ["Arcanic Enigma", "The Baron", "Magmatus", "Deathless Marrow", "Bossman Toof", "War Handler Ashka",
        "Overlord Mugg", "Zarla Ober"]


def main():
    maps = {r["ID"]: r["MapName_lang"] for r in m.table("Map", m.FOREVER)}
    names = [e["Name_lang"] for e in m.table("DungeonEncounter", m.FOREVER) if int(e["MapID"]) > 1000] + ALSO
    found, missing = {}, []
    for name in dict.fromkeys(names):
        req = urllib.request.Request(URL + urllib.parse.quote(name), headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                results = json.load(r).get("results", [])
        except Exception as e:  # noqa: BLE001
            print("failed:", name, e)
            results = []
        ids = [x["id"] for x in results if x.get("type") == 1 and x.get("name", "").lower() == name.lower()]
        # an elite of the name before a common creature of the same name
        elite = [x["id"] for x in results if x.get("type") == 1 and x.get("name", "").lower() == name.lower()
                 and "Elite" in " ".join(x.get("pinBreadcrumb") or [])]
        if elite or ids:
            found[name] = (elite or ids)[0]
        else:
            missing.append(name)
        time.sleep(0.4)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(found, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print(len(found), "found;", len(missing), "not found:", ", ".join(missing))


if __name__ == "__main__":
    main()
