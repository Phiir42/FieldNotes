"""Checks that every quest's targets can be marked on its dungeon's map.

    python tools/check_quest_marks.py

The map marks where a quest leads (Journal.lua, QuestMarks): for each creature
or object a quest names (and, once it is done, who it is handed in to), a spot
from the sheet's places, a boss's mark, or the middle of a room filed under that
name. A name with none of these on any sheet of its dungeon gets no mark; this
lists them. The fix is usually a place (tools/make_maps.py reads spawns and
objects from the classic data) or an alias in the dungeon's definition.

Dungeons without a map are skipped. Needs lupa (pip install lupa).
"""
import io
import os
import sys

from lupa import lua51 as lupa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LUA = r'''
local ns = ...
local out = {}
for id, quests in pairs(ns.Quests) do
	local floors = ns.Maps[id]
	if floors then
		local function known(name)
			local k = ns:AreaKey(name)
			for _, floor in ipairs(floors) do
				if (floor.places and floor.places[k]) or floor.areas[k] then return true end
				for _, b in ipairs(floor.bosses or {}) do
					if ns:AreaKey(b.name) == k then return true end
				end
			end
		end
		for _, q in ipairs(quests) do
			for _, who in ipairs(q[7] or {}) do
				if not known(who) then out[#out + 1] = id .. "\t" .. q[2] .. "\tlook for\t" .. who end
			end
			if q.to and not known(q.to) then out[#out + 1] = id .. "\t" .. q[2] .. "\thand in to\t" .. q.to end
		end
	end
end
table.sort(out)
return out
'''


def main():
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    load = lua.eval("function(src, name) local f, err = loadstring(src, name) if not f then error(err) end return f end")
    ns = lua.table()
    for name in ("Maps.lua", "Quests.lua"):
        load(io.open(os.path.join(ROOT, "FieldNotes", name), encoding="utf-8").read(), "@" + name)("FieldNotes", ns)
    rows = list(load(LUA, "@check")(ns).values())
    # Forever's own dungeons (map IDs past classic's, above 1000) have no classic
    # data behind them: their creatures are placed from real runs only.
    forever = set(range(1001, 100000))
    waiting = [r for r in rows if int(r.split("\t")[0]) in forever]
    rows = [r for r in rows if r not in waiting]
    for row in rows:
        print("  ".join(row.split("\t")))
    if "-v" in sys.argv:
        for row in waiting:
            print("  (waits on a run)  " + "  ".join(row.split("\t")))
    print("%d quest target(s) with no spot on the map, and %d in Forever's own dungeons that wait on a"
          " real run (-v lists them)" % (len(rows), len(waiting)))
    sys.exit(1 if rows else 0)


if __name__ == "__main__":
    main()
