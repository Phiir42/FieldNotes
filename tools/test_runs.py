"""Replays real dungeon runs against the shipped maps and checks that each
sheet still uncovers when it did when the run was last looked at.

    python tools/test_runs.py            # check
    python tools/test_runs.py --update   # accept the maps as they now are

tools/data/runs.json holds, per instance, the order things were met in on a
real run (from a tester's saved journal: sub-zones, bosses and creatures by
name only) and, for each step, what the map showed: "s1:1,2  s2:1" is pieces
1 and 2 of the first sheet and piece 1 of the second. A change to a map
definition that makes a sheet open earlier or later than before fails here;
if the new order is right (replay the run with tools/replay_journal.py and
compare with when the run really got there), accept it with --update.

To add a run: python tools/test_runs.py --add <FieldNotes.lua> <instance id>

Needs lupa (pip install lupa).
"""
import io
import json
import os
import sys

from lupa import lua51 as lupa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, "tools", "data", "runs.json")

# The same rules as MapPage in Journal.lua: what each sheet shows, given the
# names met so far.
LUA = r'''
local ns, id, events = ...
local floors = ns.Maps[id]
local function shown(known)
	local seenOn = {}
	for f, floor in ipairs(floors) do
		local seen = {}
		seenOn[f] = seen
		for _, name in ipairs(known) do
			local piece = floor.areas[ns:AreaKey(name)]
			if piece then seen[piece] = true end
		end
	end
	local beyond
	for f = #floors, 1, -1 do
		local floor, seen = floors[f], seenOn[f]
		if floor.path then
			local all = beyond and not floor.alone
			local reach = {}
			for piece in pairs(seen) do
				local g = piece.g or 1
				if piece.n > (reach[g] or 0) then reach[g] = piece.n end
			end
			for _, piece in pairs(floor.areas) do
				if all or piece.n <= (reach[piece.g or 1] or 0) then seen[piece] = true end
			end
		end
		if next(seen) then beyond = true end
	end
	local parts = {}
	for f in ipairs(floors) do
		local n = {}
		for piece in pairs(seenOn[f]) do n[#n + 1] = piece.n end
		table.sort(n)
		if #n > 0 then parts[#parts + 1] = "s" .. f .. ":" .. table.concat(n, ",") end
	end
	return table.concat(parts, "  ")
end
local out, known = {}, {}
for i = 1, #events do
	known[#known + 1] = events[i]
	out[i] = shown(known)
end
return out
'''


def addon():
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    ns = lua.table()
    load = lua.eval("function(src, name) return assert(loadstring(src, name)) end")
    load(io.open(os.path.join(ROOT, "FieldNotes", "Maps.lua"), encoding="utf-8").read(), "@Maps.lua")("FieldNotes", ns)
    return lua, ns, load(LUA, "@replay")


def replay(lua, ns, fn, iid, names):
    return list(fn(ns, iid, lua.table_from(names)).values())


def add(path, iid):
    """The order a saved journal met things in, for one instance."""
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(io.open(path, encoding="utf-8", errors="replace").read())
    inst = lua.globals().FieldNotesDB.instances[iid]
    events = []
    for a in (inst.areas or {}).values():
        events.append((a.t or 0, 0, a.name))
    for b in (inst.bosses or {}).values():
        events.append((b.first or 0, 1, b.name))
    for m in (inst.mobs or {}).values():
        if m.fought:
            events.append((m.fought, 2, m.name))
    events.sort()
    return [name for _, _, name in events]


def main():
    runs = json.load(open(RUNS, encoding="utf-8")) if os.path.exists(RUNS) else {}
    if "--add" in sys.argv:
        i = sys.argv.index("--add")
        path, iid = sys.argv[i + 1], int(sys.argv[i + 2])
        runs[str(iid)] = {"met": add(path, iid), "shows": []}
    lua, ns, fn = addon()
    update = "--update" in sys.argv or "--add" in sys.argv
    bad = 0
    for iid, run in sorted(runs.items()):
        now = replay(lua, ns, fn, int(iid), run["met"])
        if update:
            if now != run["shows"]:
                print("%s: accepted the map as it now is" % iid)
            run["shows"] = now
            continue
        for step, (name, was, got) in enumerate(zip(run["met"], run["shows"], now), 1):
            if was != got:
                bad += 1
                print("%s, step %d (%s): the map showed %r, now %r" % (iid, step, name, was, got))
    if update:
        with open(RUNS, "w", encoding="utf-8", newline="\n") as f:
            json.dump(runs, f, indent=1, ensure_ascii=False)
            f.write("\n")
    print("%d runs, %d steps changed" % (len(runs), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
