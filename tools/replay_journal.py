"""Replay a saved journal against the shipped maps: after each thing the run
met, in the order it met them, which areas of each sheet the map would show.
The way to see whether a map runs ahead of the player or lags behind.

    python tools/replay_journal.py <FieldNotes.lua> <instance id>

Needs lupa (pip install lupa). Uses FieldNotes/Maps.lua as built.
"""
import io
import os
import sys

from lupa import lua51 as lupa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LUA = r'''
local ns, db, id = ...
local inst = db.instances[id]
local floors = ns.Maps[id]
local events = {}
for _, a in ipairs(inst.areas or {}) do events[#events + 1] = { t = a.t or 0, name = a.name, what = "area" } end
for _, b in pairs(inst.bosses or {}) do events[#events + 1] = { t = b.first or 0, name = b.name, what = "BOSS" } end
for _, m in pairs(inst.mobs or {}) do
	if m.fought then events[#events + 1] = { t = m.fought, name = m.name, what = "mob " } end
end
table.sort(events, function(a, b) return a.t < b.t end)

-- the same rules as MapPage in Journal.lua
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
		local ns_ = {}
		for piece in pairs(seenOn[f]) do ns_[#ns_ + 1] = piece.n end
		table.sort(ns_)
		if #ns_ > 0 then parts[#parts + 1] = "s" .. f .. ":" .. table.concat(ns_, ",") end
	end
	return table.concat(parts, "  ")
end

local out, known, last = {}, {}, nil
for _, e in ipairs(events) do
	known[#known + 1] = e.name
	local now = shown(known)
	local placed = false
	for _, floor in ipairs(floors) do
		if floor.areas[ns:AreaKey(e.name)] then placed = true end
	end
	out[#out + 1] = ("%s %-28s %s%s"):format(e.what, e.name, now ~= last and now or "  (no change)",
		placed and "" or "   [not on the map]")
	last = now
end
local total = {}
for f, floor in ipairs(floors) do total[#total + 1] = "s" .. f .. " has " .. floor.count end
out[#out + 1] = table.concat(total, ", ")
return table.concat(out, "\n")
'''


def main():
    path, iid = sys.argv[1], sys.argv[2]
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(io.open(path, encoding="utf-8", errors="replace").read())
    ns = lua.table()
    load = lua.eval("function(src, name) return assert(loadstring(src, name)) end")
    load(io.open(os.path.join(ROOT, "FieldNotes", "Maps.lua"), encoding="utf-8").read(), "@Maps.lua")("FieldNotes", ns)
    key = int(iid) if iid.isdigit() else iid
    print(load(LUA, "@replay")(ns, lua.globals().FieldNotesDB, key))


if __name__ == "__main__":
    main()
