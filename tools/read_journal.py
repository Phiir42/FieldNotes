"""Read a saved journal (WTF/Account/<name>/SavedVariables/FieldNotes.lua) and
print what a run recorded, in the order it happened: the evidence for
correcting a dungeon's map definition.

    python tools/read_journal.py <FieldNotes.lua> [instance id ...]

Needs lupa (pip install lupa).
"""
import sys
import time

from lupa import lua51 as lupa


def load(path):
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(open(path, encoding="utf-8", errors="replace").read())
    return lua.globals().FieldNotesDB


def clock(t):
    return time.strftime("%d %b %H:%M:%S", time.localtime(t)) if t else "?"


def main():
    db = load(sys.argv[1])
    want = set(sys.argv[2:])
    if db.errors:
        print("ERRORS")
        for e in db.errors.values():
            print("  x%d [%s] %s (version %s)" % (e.n, e.event, e.msg, e.version))
    if db.debug:
        print("SHOWN AND HIDDEN")
        for k, v in sorted(db.debug.items()):
            print("  %s: %d" % (k, v))
    for iid, inst in db.instances.items():
        if want and str(iid) not in want:
            continue
        print("\n%s (%s): %d visits, %s deaths" % (inst.name, iid, inst.visits or 0, inst.deaths or 0))
        events = []
        for a in (inst.areas or {}).values():
            events.append((a.t or 0, "area   " + a.name))
        for eid, b in (inst.bosses or {}).items():
            events.append((b.first or 0, "BOSS   %s (encounter %s, %d kills, %d wipes)" % (b.name, eid, b.kills, b.wipes)))
        for key, m in (inst.mobs or {}).items():
            where = " [boss fight %s]" % m.enc if m.enc else ""
            events.append((m.fought or m.first or 0, "mob    %s (%s, slain %s)%s" % (m.name, key, m.kills or 0, where)))
        for t, text in sorted(events):
            print("  %s  %s" % (clock(t), text))
        loot = list((inst.loot or {}).items())
        print("  loot: %d items; unplaced areas and notes are in the file" % len(loot))


if __name__ == "__main__":
    main()
