-- A dungeon run played against the mock client (tools/wowmock.lua).
-- Run with: python tools/test_addon.py
local M, ns = ...
local fails, checks = {}, 0

local function check(what, ok)
	checks = checks + 1
	if not ok then fails[#fails + 1] = what end
end

local function step(what, fn, ...)
	local ok, err = xpcall(fn, debug.traceback, ...)
	checks = checks + 1
	if not ok then fails[#fails + 1] = what .. ": " .. tostring(err) end
end

-- the text of the journal page currently shown
local function pageText()
	local t = {}
	for _, f in ipairs(M.frames) do
		if f.__kind == "FontString" and f.__text ~= "" then
			local row = f.__parent
			if row and row.__shown then t[#t + 1] = f.__text end
		end
	end
	return table.concat(t, "\n")
end

local function open(kind, key)
	-- click the matching line of the contents list, as a player would
	for _, f in ipairs(M.frames) do
		if f.__kind == "Button" and f.__shown and rawget(f, "line") and f.line.click then
			local text = f.line.text or ""
			if text:find(kind, 1, true) then f.line.click() return true end
		end
	end
	return false
end

local CREATURE = "Creature-0-4444-36-111-%d-%010X"
local function item(id, name) return ("|cff1eff00|Hitem:%d::::::::20:::::|h[%s]|h|r"):format(id, name) end

---------------------------------------------------------------------------
step("load", function()
	M.fire("ADDON_LOADED", "SomeOtherAddon")
	M.fire("ADDON_LOADED", "FieldNotes")
	check("saved variables made", type(FieldNotesDB) == "table" and ns.db == FieldNotesDB)
	check("minimap button made", FieldNotesMinimapButton ~= nil)
	M.fire("PLAYER_ENTERING_WORLD")
	M.wait(3)
	check("nothing recorded outside a dungeon", next(ns.db.instances) == nil)
end)

step("blank journal", function()
	M.slash("")
	check("journal shows", FieldNotesJournal:IsShown())
	check("blank page text", pageText():find("These pages are blank", 1, true))
	M.slash("")
	check("journal hides", not FieldNotesJournal:IsShown())
end)

step("slash commands", function()
	for _, cmd in ipairs({ "help", "announce", "announce", "button", "button", "quality 3", "quality 2",
		"quality x", "mapkey", "mapkey", "debug", "nonsense", "version", "reset" }) do
		M.slash(cmd)
	end
end)

step("events outside a dungeon are ignored", function()
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Kobold Vermin dies, you gain 12 experience.")
	M.fire("CHAT_MSG_MONSTER_YELL", "For the Alliance!", "Some Guard")
	M.fire("ENCOUNTER_START", 1, "Nobody", 1, 5)
	M.fire("ENCOUNTER_END", 1, "Nobody", 1, 5, 1)
	M.loot = { { link = item(1, "A"), guid = CREATURE:format(1, 1) } }
	M.fire("LOOT_OPENED")
	M.fire("CHAT_MSG_LOOT", "You receive loot: " .. item(2, "B") .. ".")
	M.fire("UPDATE_MOUSEOVER_UNIT")
	M.fire("UNIT_SPELLCAST_START", "target", "x", 5)
	check("still nothing recorded", next(ns.db.instances) == nil)
end)

local inst
step("enter the Deadmines", function()
	M.instance = { name = "The Deadmines", kind = "party", id = 36 }
	M.subzone = ""
	M.fire("PLAYER_ENTERING_WORLD")
	M.wait(3)
	inst = ns.db.instances[36]
	check("instance page made", inst and inst.name == "The Deadmines" and inst.visits == 1)
	M.subzone = "The Deadmines"
	M.fire("ZONE_CHANGED")
	check("the instance's own name is not an area", #inst.areas == 0)
	M.subzone = "Goblin Foundry"
	M.fire("ZONE_CHANGED_INDOORS")
	M.fire("ZONE_CHANGED_INDOORS")
	check("area noted once", #inst.areas == 1 and inst.areas[1].name == "Goblin Foundry")
end)

step("creatures: everything on the unit is secret", function()
	M.units.mouseover = { name = "Defias Miner", guid = CREATURE:format(598, 1), level = 18 }
	M.units.target = M.units.mouseover
	M.units.nameplate1 = M.units.mouseover
	GameTooltipTextLeft1:SetText("")
	M.fire("UPDATE_MOUSEOVER_UNIT")
	M.fire("PLAYER_TARGET_CHANGED")
	M.fire("NAME_PLATE_UNIT_ADDED", "nameplate1")
	M.fire("UNIT_THREAT_LIST_UPDATE", "nameplate1")
	M.fire("UNIT_SPELLCAST_START", "target", M.Secret(), M.Secret())
	M.fire("UNIT_SPELLCAST_SUCCEEDED", "nameplate1", "cast-1", 6016)
	check("no creature from secret units", #inst.mobOrder == 0)
	check("hidden ids were counted", (ns.db.debug["unit id hidden at rest"] or 0) > 0)
	-- friendly players are never written down
	M.units.target = { name = "Friend", guid = "Player-1-0001", level = 20, player = true }
	M.fire("PLAYER_TARGET_CHANGED")
	check("no entry for a player", #inst.mobOrder == 0)
	M.units = {}
end)

step("creatures: experience, speech, corpses", function()
	M.fire("CHAT_MSG_MONSTER_YELL", "Intruders!", "Defias Overseer")
	check("speech out of combat is not a meeting", #inst.mobOrder == 0)
	M.combat = true
	M.fire("CHAT_MSG_MONSTER_EMOTE", "%s attempts to run away in fear!", "Defias Miner")
	M.fire("CHAT_MSG_MONSTER_SAY", M.Secret(), M.Secret())
	M.combat = false
	check("speech in combat names a creature", inst.mobs["n:Defias Miner"] ~= nil)
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Defias Miner dies, you gain 85 experience.")
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Goblin Craftsman dies, you gain 90 experience.")
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "You gain 300 experience.")
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", M.Secret())
	check("kill counted from experience", inst.mobs["n:Defias Miner"].kills == 1)
	check("second creature", inst.mobs["n:Goblin Craftsman"] ~= nil)
	-- looting the corpse gives the id: the entry moves under it, kills stay 1
	M.loot = { { link = item(1930, "Stonemason Cloak"), guid = CREATURE:format(1731, 7) },
		{ link = nil, guid = CREATURE:format(1731, 7) } }
	M.fire("LOOT_OPENED")
	check("entry re-filed under the npc id", inst.mobs[1731] and not inst.mobs["n:Goblin Craftsman"])
	check("kill not double counted", inst.mobs[1731].kills == 1)
	check("loot noted against the creature", inst.loot[1930] and inst.loot[1930].npc == 1731 and inst.loot[1930].n == 1)
	M.fire("LOOT_OPENED")
	check("same corpse opened twice counts once", inst.loot[1930].n == 1)
	M.fire("CHAT_MSG_LOOT", "You receive loot: " .. item(1930, "Stonemason Cloak") .. ".")
	check("chat line for the same item counts once", inst.loot[1930].n == 1)
	-- a corpse of something never named before: the shipped name table fills it in
	M.loot = { { link = nil, guid = CREATURE:format(622, 9) } }
	M.fire("LOOT_OPENED")
	check("corpse alone starts an entry", inst.mobs[622] and inst.mobs[622].name == ns.CreatureNames[622])
	-- a secret corpse id
	M.loot = { { link = item(2000, "Thing"), guid = M.Secret() } }
	M.fire("LOOT_OPENED")
	check("loot from a hidden corpse still noted", inst.loot[2000] ~= nil)
	M.loot = {}
end)

step("a boss: wipe, then kill", function()
	M.combat = true
	M.fire("ENCOUNTER_START", 2741, "Rhahk'Zor", 1, 5)
	M.fire("CHAT_MSG_MONSTER_YELL", "VanCleef pay big for your heads!", "Rhahk'Zor")
	M.wait(20)
	M.fire("ENCOUNTER_END", 2741, "Rhahk'Zor", 1, 5, 0)
	M.combat = false
	local b = inst.bosses[2741]
	check("boss page made", b and b.pulls == 1 and b.wipes == 1 and b.kills == 0)
	M.combat = true
	M.fire("ENCOUNTER_START", 2741, "Rhahk'Zor", 1, 5)
	M.wait(42)
	M.fire("ENCOUNTER_END", 2741, "Rhahk'Zor", 1, 5, 1)
	M.combat = false
	check("kill recorded with a time", b.kills == 1 and b.best and math.abs(b.best - 42) < 0.01)
	-- the experience line for the boss arrives after the fight is over
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Rhahk'Zor dies, you gain 300 experience.")
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Someone New dies, you gain 300 experience.")
	-- someone else loots: only the chat line is seen
	M.wait(5)
	M.fire("CHAT_MSG_LOOT", "Friend receives loot: " .. item(872, "Rockslicer") .. ".")
	check("chat loot just after the kill is the boss's", inst.loot[872] and inst.loot[872].enc == 2741)
	-- trash loot long after is not
	M.wait(60)
	M.fire("CHAT_MSG_LOOT", "Friend receives loot: " .. item(4000, "Trash Blade") .. ".")
	check("later chat loot is not the boss's", inst.loot[4000] and not inst.loot[4000].enc)
	-- the boss's own corpse
	M.loot = { { link = item(5187, "Rhahk'Zor's Hammer"), guid = CREATURE:format(644, 3) } }
	M.fire("LOOT_OPENED")
	check("loot on the boss's corpse is the boss's", inst.loot[5187] and inst.loot[5187].enc == 2741)
	M.loot = {}
	-- an encounter the addon has no data for
	M.fire("ENCOUNTER_START", 99999, "Someone New", 1, 5)
	M.fire("ENCOUNTER_END", 99999, "Someone New", 1, 5, 1)
	M.fire("ENCOUNTER_END", 88888, nil, 1, 5, 1)
	M.wait(1)
end)

step("every page of the journal", function()
	M.slash("")
	check("opens on the dungeon", pageText():find("The Deadmines", 1, true))
	check("diary has entries", pageText():find("Came upon Goblin Foundry", 1, true))
	check("boss page opens", open("Rhahk'Zor"))
	check("boss page text", pageText():find("swiftest victory 0:42", 1, true))
	check("boss page lists its loot", pageText():find("Rockslicer", 1, true))
	check("boss page leaves trash out", not pageText():find("Trash Blade", 1, true))
	check("known abilities shown after the kill", pageText():find("Known abilities", 1, true))
	check("unknown boss page opens", open("Someone New"))
	check("bestiary opens", open("Bestiary"))
	check("bosses are left out of the bestiary", pageText():find("Bestiary (3)", 1, true))
	check("bestiary lists the craftsman", pageText():find("Goblin Craftsman", 1, true))
	check("bestiary shows shipped level", pageText():find("level 18-19", 1, true))
	check("spoils opens", open("Spoils"))
	check("spoils lists loot", pageText():find("Stonemason Cloak", 1, true))
	check("map opens", open("Map"))
	check("map page text", pageText():find("What you have charted", 1, true))
	-- a boss marker for the boss that was faced, and it leads to its page
	local marks = 0
	for _, f in ipairs(M.frames) do
		if f.__kind == "Button" and f.__shown and rawget(f, "go") then
			marks = marks + 1
			if f.__scripts.OnEnter then f.__scripts.OnEnter(f) end
			if f.__scripts.OnLeave then f.__scripts.OnLeave(f) end
		end
	end
	check("one boss marker on the map (found " .. marks .. ")", marks == 1)
	-- the parts shown for the first time are being sketched in
	local function drawing()
		local n = 0
		for _, f in ipairs(M.frames) do
			if f.__scripts.OnUpdate and f ~= FieldNotesMinimapButton then n = n + 1 end
		end
		return n
	end
	local function run(sec)
		for _ = 1, sec * 20 do
			M.wait(0.05)
			for _, f in ipairs(M.frames) do
				if f.__scripts.OnUpdate and f ~= FieldNotesMinimapButton then f.__scripts.OnUpdate(f, 0.05) end
			end
		end
	end
	check("the map is being sketched in", drawing() == 1)
	run(0.5)
	check("still drawing after half a second", drawing() == 1)
	M.fire("ZONE_CHANGED")
	M.wait(0.5)   -- a redraw in the middle of it
	run(8)
	check("the sketch finishes", drawing() == 0)
	check("what was drawn is remembered", inst.charted and inst.charted["boss:rhahkzor"] and next(inst.charted))
	open("Spoils"); open("Map")
	check("nothing is drawn twice", drawing() == 0)
	-- a new area: only it is sketched; leaving the page mid-sketch ends it
	M.subzone = "Mast Room"
	M.fire("ZONE_CHANGED")
	M.wait(1)
	check("the second sheet opens", open("Second sheet"))
	check("a newly found area is sketched", drawing() == 1)
	run(8)
	check("and that sketch finishes too", drawing() == 0)
	M.subzone = "Ironclad Cove"
	M.fire("ZONE_CHANGED")
	M.wait(1)
	check("the next area is sketched", drawing() == 1)
	open("Spoils")
	check("leaving the page ends the sketch", drawing() == 0)
	open("Map")
	M.slash("sketch")
	M.fire("ENCOUNTER_START", 2745, "Edwin VanCleef", 1, 5)
	M.fire("ENCOUNTER_END", 2745, "Edwin VanCleef", 1, 5, 0)
	M.wait(1)
	check("with sketching off, areas simply appear", drawing() == 0)
	M.slash("sketch")
	-- hover and click every visible row
	for _, kind in ipairs({ "The Deadmines", "Rhahk'Zor", "Bestiary", "Spoils", "Map" }) do
		open(kind)
		for _, f in ipairs(M.frames) do
			if f.__kind == "Button" and f.__shown and rawget(f, "line") then
				f.__scripts.OnEnter(f)
				f.__scripts.OnLeave(f)
			end
		end
	end
	M.wait(1)
	M.slash("")
end)

step("the map key", function()
	check("journal closed", not FieldNotesJournal:IsShown())
	ToggleWorldMap()
	check("map key opens the journal", FieldNotesJournal:IsShown())
	check("the game's map is put away", not WorldMapFrame:IsShown())
	check("on the map page", pageText():find("What you have charted", 1, true))
	ToggleWorldMap()
	check("map key closes the journal", not FieldNotesJournal:IsShown())
	M.slash("mapkey")
	ToggleWorldMap()
	check("with mapkey off the game's map opens", WorldMapFrame:IsShown() and not FieldNotesJournal:IsShown())
	ToggleWorldMap()
	M.slash("mapkey")
end)

step("minimap button and compartment", function()
	local b = FieldNotesMinimapButton
	b.__scripts.OnEnter(b)
	b.__scripts.OnLeave(b)
	b.__scripts.OnDragStart(b)
	if b.__scripts.OnUpdate then b.__scripts.OnUpdate(b, 0.1) end
	b.__scripts.OnDragStop(b)
	b:Click()
	b:Click()
	FieldNotes_OnCompartmentEnter("FieldNotes", b)
	FieldNotes_OnCompartmentLeave()
	FieldNotes_OnCompartmentClick()
	FieldNotes_OnCompartmentClick()
end)

step("leave and return", function()
	M.instance = nil
	M.fire("ZONE_CHANGED_NEW_AREA")
	M.wait(3)
	check("no current instance outside", ns.currentID == nil)
	M.slash("")
	check("journal still shows the dungeon", pageText():find("The Deadmines", 1, true))
	M.slash("")
	M.wait(4000)
	M.instance = { name = "The Deadmines", kind = "party", id = 36 }
	M.fire("PLAYER_ENTERING_WORLD")
	M.wait(3)
	check("second visit counted", inst.visits == 2)
end)

step("every shipped map draws, area by area", function()
	local ids = {}
	for id in pairs(ns.Maps) do if type(id) == "number" then ids[#ids + 1] = id end end
	table.sort(ids)
	check("maps shipped", #ids >= 27)
	for _, id in ipairs(ids) do
		local n = 0
		for _, floor in ipairs(ns.Maps[id]) do
			for _ in pairs(floor.areas) do n = n + 1 end
			check("map " .. id .. " floor has tiles", #floor.tiles > 0 and floor.cols > 0)
			for _, spot in ipairs(floor.bosses or {}) do
				check("map " .. id .. " boss " .. spot.name .. " on the sheet",
					spot.x > 0 and spot.x < 1002 and spot.y > 0 and spot.y < 668)
			end
		end
		for _ = 1, math.ceil(n / 3) + 2 do
			ns:MapTest(tostring(id))
			-- look at every sheet
			for _, f in ipairs(M.frames) do
				if f.__kind == "Button" and f.__shown and rawget(f, "line") and f.line.click
					and (f.line.text or ""):find("heet") then
					f.line.click()
				end
			end
		end
	end
	ns:MapTest("off")
	check("test page removed", ns.db.instances.maptest == nil)
	ns:MapTest("123456")
end)

step("a full run of every dungeon with a map", function()
	-- walk in, face each marked boss, look at the map: no errors, markers match
	for id, floors in pairs(ns.Maps) do
		if type(id) == "number" and id ~= 36 then
			M.instance = { name = "Dungeon " .. id, kind = "party", id = id }
			M.fire("PLAYER_ENTERING_WORLD")
			M.wait(3)
			local eid = 500000 + id * 100
			local want = 0
			for _, floor in ipairs(floors) do
				for _, spot in ipairs(floor.bosses or {}) do
					eid = eid + 1
					M.fire("ENCOUNTER_START", eid, spot.name, 1, 5)
					M.wait(10)
					M.fire("ENCOUNTER_END", eid, spot.name, 1, 5, 1)
					want = want + 1
				end
			end
			M.wait(1)
			if not FieldNotesJournal:IsShown() then ns:ToggleJournal("map") end
			open("Map")
			for _, f in ipairs(M.frames) do
				if f.__kind == "Button" and f.__shown and rawget(f, "line") and f.line.click
					and (f.line.text or ""):find("heet") then
					f.line.click()
				end
			end
			open("Dungeon " .. id)
			M.slash("")
		end
	end
end)

step("a dungeon the addon has no map or lore for", function()
	M.instance = { name = "Blackmaw Hold", kind = "raid", id = 77777 }
	M.subzone = "The Maw"
	M.fire("PLAYER_ENTERING_WORLD")
	M.wait(3)
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Maw Lurker dies, you gain 85 experience.")
	M.fire("ENCOUNTER_START", 31337, "The Mawlord", 1, 5)
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Maw Spawn dies, you gain 5 experience.")
	M.fire("ENCOUNTER_END", 31337, "The Mawlord", 1, 5, 1)
	M.wait(1)
	ToggleWorldMap()
	check("map key opens the overview where there is no map", pageText():find("First entered", 1, true))
	check("no map line in the contents", not open("Map"))
	open("The Mawlord")
	check("adds are on the boss's page", pageText():find("Maw Spawn", 1, true))
	open("Bestiary")
	check("trash is in the bestiary, adds are not", pageText():find("Maw Lurker", 1, true)
		and not pageText():find("Maw Spawn", 1, true))
	open("Spoils")
	M.slash("")
end)

step("mistakes are caught and kept for reporting", function()
	check("no errors during the run: " .. tostring(ns.db.errors and ns.db.errors[1].msg), ns.db.errors == nil)
	ns:On("FN_TEST", function() error("deliberate") end)
	local reached
	ns:On("FN_TEST", function() reached = true end)
	ns:Fire("FN_TEST")
	ns:Fire("FN_TEST")
	check("later handlers still run", reached)
	check("error kept once, counted twice", #ns.db.errors == 1 and ns.db.errors[1].n == 2)
	M.slash("errors")
	M.slash("errors clear")
	M.slash("errors")
	check("error list cleared", ns.db.errors == nil)
end)

step("tearing pages out", function()
	M.instance = { name = "The Deadmines", kind = "party", id = 36 }
	M.fire("PLAYER_ENTERING_WORLD")
	M.wait(3)
	M.accept_popups = true
	ns:Forget(36)
	check("a fresh page starts when still inside", ns.db.instances[36] and #ns.db.instances[36].mobOrder == 0)
	M.instance = nil
	M.fire("PLAYER_ENTERING_WORLD")
	M.wait(3)
	ns:Forget(36)
	check("gone when outside", ns.db.instances[36] == nil)
	M.fire("PLAYER_LOGOUT")
end)

local missing = {}
for k in pairs(M.missing) do missing[#missing + 1] = k end
table.sort(missing)
return checks, fails, missing, M.chat
