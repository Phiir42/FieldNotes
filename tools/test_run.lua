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
	for _, cmd in ipairs({ "help", "notices", "notices", "sound", "sound", "announce", "announce", "sketch", "sketch", "button", "button", "quality 3", "quality 2",
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
	M.fire("CHAT_MSG_LOOT", "You create: " .. item(3000, "Made Thing") .. ".")
	M.fire("CHAT_MSG_LOOT", "Friend has selected Need for: " .. item(3001, "Rolled Thing"))
	check("made and rolled-for items are not loot", not inst.loot[3000] and not inst.loot[3001])
	M.fire("CHAT_MSG_LOOT", "Friend receives loot: " .. item(10978, "Small Glimmering Shard") .. ".")
	check("disenchanting results are not loot", not inst.loot[10978])
	-- one noted by an earlier version is taken out on the next loading screen
	inst.loot[10978] = { link = item(10978, "Small Glimmering Shard"), first = 1, n = 1 }
	inst.lootOrder[#inst.lootOrder + 1] = 10978
	M.fire("PLAYER_ENTERING_WORLD")
	M.wait(3)
	check("old disenchanting entries are removed", not inst.loot[10978] and inst.lootOrder[#inst.lootOrder] ~= 10978)
	M.fire("CHAT_MSG_LOOT", "Friend receives loot: " .. item(3002, "Stacked Thing") .. "x3.")
	check("a stack someone received is loot", inst.loot[3002] ~= nil)
	-- a captive calling out in a fight is not a creature fought
	M.combat = true
	M.fire("CHAT_MSG_MONSTER_SAY", "Help me!", "Some Captive")
	M.combat = false
	check("an unknown speaker is not put in the bestiary", inst.mobs["n:Some Captive"] == nil)
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
	-- one whose name the game hides as it begins, and gives at its end;
	-- falling in it counts against it
	local deaths = inst.deaths or 0
	M.fire("ENCOUNTER_START", 77001, M.Secret(), 1, 5)
	check("a hidden name is written as unknown", inst.bosses[77001] and inst.bosses[77001].name == UNKNOWN)
	M.fire("PLAYER_DEAD")
	M.fire("ENCOUNTER_END", 77001, "Late Name", 1, 5, 0)
	check("and filled in once the game gives it", inst.bosses[77001].name == "Late Name")
	check("a death in a boss fight counts against the boss", inst.bosses[77001].deaths == 1 and inst.deaths == deaths + 1)
	M.wait(1)
end)

step("notices and deaths", function()
	local slip = FieldNotesNotice
	check("a notice was shown for what was written", slip ~= nil and slip:IsShown())
	local deaths = inst.deaths or 0
	M.fire("PLAYER_DEAD")
	check("death written in the diary", inst.deaths == deaths + 1 and inst.log[#inst.log][2]:find("Fell in battle", 1, true))
	for _ = 1, 600 do
		M.wait(0.05)
		if slip.__scripts.OnUpdate then slip.__scripts.OnUpdate(slip, 0.05) end
	end
	check("notices fade away when all are shown", not slip:IsShown() and not slip.__scripts.OnUpdate)
	M.slash("notices")
	M.fire("PLAYER_DEAD")
	check("no notice when turned off", not slip:IsShown() and inst.deaths == deaths + 2)
	M.slash("notices")
	M.subzone = "Somewhere Unmapped"
	M.fire("ZONE_CHANGED")
	check("a notice shows again", slip:IsShown())
	slip:Click()
	check("clicking a notice opens the journal", FieldNotesJournal:IsShown() and not slip:IsShown())
	M.slash("")
	-- moving it
	M.slash("notices move")
	check("a sample is held on screen", slip:IsShown())
	for _ = 1, 400 do M.wait(0.05) slip.__scripts.OnUpdate(slip, 0.05) end
	check("the sample does not fade", slip:IsShown())
	slip.__scripts.OnDragStart(slip)
	slip.__scripts.OnDragStop(slip)
	check("where it was dropped is remembered", ns.db.noticePos and ns.db.noticePos[3] == 40 and ns.db.noticePos[4] == -60)
	slip:Click()
	check("clicking the sample only puts it away", not slip:IsShown() and not FieldNotesJournal:IsShown())
	M.slash("notices reset")
	check("reset forgets the place", ns.db.noticePos == nil)
end)

step("preferences page", function()
	M.slash("settings")
	check("preferences page opens", FieldNotesJournal:IsShown() and pageText():find("Click a line to change it", 1, true))
	check("sound toggles by clicking", open("Sounds") and ns.db.settings.sound == false)
	check("and back", open("Sounds") and ns.db.settings.sound == true)
	check("item tooltips toggle by clicking", open("Finds on item tooltips") and ns.db.settings.itemTips == false)
	open("Finds on item tooltips")
	check("minimap button hides by clicking", open("Minimap button") and not FieldNotesMinimapButton:IsShown())
	open("Minimap button")
	check("pictures in colour by clicking", open("In true colour") and ns.db.settings.pictures == "colour")
	check("still pictures by clicking", open("Still") and ns.db.settings.picturesMove == false)
	open("Animated")
	open("As sketches")
	check("quality by clicking", open("Rare and better") and ns.db.settings.minQuality == 3)
	open("Uncommon and better")
	check("size by clicking", open("Larger") and ns.db.settings.scale == 1.1)
	open("Usual")
	check("writing size by clicking", open("Larger text") and ns.db.settings.textScale == 1.3)
	check("paper by clicking", open("Pale paper") and ns.db.settings.paper == 0.66)
	check("window opacity by clicking", open("See-through") and ns.db.settings.alpha < 1)
	open("Solid")
	open("Usual text")
	check("map mark size by clicking", open("Large marks") and ns.db.settings.markSize == 24)
	open("Usual marks")
	check("the sample note shows from the page", open("Move the note") and FieldNotesNotice:IsShown())
	FieldNotesNotice:Click()
	FieldNotesJournal.__scripts.OnDragStop(FieldNotesJournal)
	check("the journal's place is remembered", ns.db.journalPos ~= nil)
	-- filling the screen, by the page, the title button and the command
	check("fill the screen by clicking", open("Fill the screen") and ns.db.settings.full == true)
	FieldNotesJournal.full:Click()
	check("the title button puts it back", ns.db.settings.full == false)
	M.slash("full")
	check("/fn full fills the screen", ns.db.settings.full == true)
	FieldNotesJournal.__scripts.OnDragStop(FieldNotesJournal)
	M.slash("full")
	-- dragging the corner grip
	local grip = FieldNotesJournal.grip
	grip.__scripts.OnEnter(grip); grip.__scripts.OnLeave(grip)
	grip.__scripts.OnMouseDown(grip)
	grip.__scripts.OnUpdate(grip, 0.1)
	grip.__scripts.OnMouseUp(grip)
	check("dragging the grip sets a size within bounds", ns.db.settings.scale >= 0.6 and ns.db.settings.scale <= 1.4
		and ns.db.journalPos[1] == "TOPLEFT")
	open("Usual")
	check("back to the dungeon from the contents", open("The Deadmines") and pageText():find("First entered", 1, true))
	M.slash("")
	FieldNotesMinimapButton.__scripts.OnClick(FieldNotesMinimapButton, "RightButton")
	check("right-click opens preferences", pageText():find("Click a line to change it", 1, true))
	M.slash("")
end)

step("every page of the journal", function()
	M.slash("")
	check("opens on the dungeon", pageText():find("The Deadmines", 1, true))
	check("diary has entries", pageText():find("Came upon Goblin Foundry", 1, true))
	check("boss page opens", open("Rhahk'Zor"))
	check("boss page text", pageText():find("swiftest victory 0:42", 1, true))
	local function portraits()
		local t = {}
		for _, f in ipairs(M.frames) do
			if rawget(f, "tint") and rawget(f, "row") then t[#t + 1] = f.key end
		end
		return t
	end
	check("the boss has a portrait from its display id", portraits()[1] and portraits()[1]:find("^d14403sketch"))
	check("boss page lists its loot", pageText():find("Rockslicer", 1, true))
	check("boss page leaves trash out", not pageText():find("Trash Blade", 1, true))
	check("known abilities shown after the kill", pageText():find("Known abilities", 1, true))
	check("unknown boss page opens", open("Someone New"))
	check("bestiary opens", open("Bestiary"))
	check("bosses are left out of the bestiary", pageText():find("Bestiary (3)", 1, true))
	-- a note of your own on one creature
	check("clicking a creature turns the notes box to it", open("Goblin Craftsman") and pageText():find("My notes on Goblin Craftsman", 1, true))
	inst.mobs[1731].note = "Hits hard."
	open("Bestiary")
	check("the note shows under the creature", pageText():find("My note:|r Hits hard.", 1, true))
	check("bestiary entries have portraits", #portraits() >= 2)
	ns.db.settings.pictures = "off"
	open("Bestiary")
	check("no portraits when turned off", #portraits() == 0 and pageText():find("level 18-19", 1, true))
	ns.db.settings.pictures = "sketch"
	open("Bestiary")
	check("bestiary lists the craftsman", pageText():find("Goblin Craftsman", 1, true))
	check("bestiary shows shipped level", pageText():find("level 18-19", 1, true))
	-- quests of the dungeon
	check("quests page opens", open("Quests (7)"))
	check("quests are listed with where they lead", pageText():find("The Defias Brotherhood", 1, true)
		and pageText():find("Look for Edwin VanCleef.", 1, true))
	M.questsOn[166], M.questsOn[2040], M.questsDone[214] = true, true, true
	-- the quest log: progress, and a quest the addon had not heard of
	M.questGoals[166] = { { text = "0/1 Head of VanCleef", finished = false } }
	M.questLog = {
		{ title = "Westfall", isHeader = true },
		{ title = "Elsewhere", questID = 99000, level = 12 },
		{ title = "The Deadmines", isHeader = true },
		{ title = "A New Errand", questID = 99001, level = 19 },
	}
	M.questsOn[99001] = true
	open("The Deadmines") open("Quests (8)")
	do -- a class's own quests are for that class only
		local paladin, shown = 0, 0
		for _, q in ipairs(ns.Quests[48]) do if q.class == 2 then paladin = paladin + 1 end end
		check("class quests are in the data", paladin >= 1)
	end
	check("quests show what they pay", pageText():find("Reward, one of:", 1, true) and pageText():find("Item 6087", 1, true))
	check("quests say who gives them", pageText():find("Given by Wilder Thistlenettle", 1, true))
	check("but not for one you hold", not pageText():find("Given by Gryan Stoutmantle", 1, true))
	check("a quest in the log shows how far along it is", pageText():find("So far: 0/1 Head of VanCleef.", 1, true))
	check("a quest the log files under the dungeon is written down", pageText():find("A New Errand", 1, true)
		and not pageText():find("Elsewhere", 1, true) and inst.quests[99001].title == "A New Errand")
	M.questLog = {}
	open("The Deadmines") open("Quests (8)")
	check("and stays written down once it has left the log", pageText():find("A New Errand", 1, true))
	-- a quest filed elsewhere that moves along in here is this dungeon's too
	M.questLog = { { title = "Westfall", isHeader = true }, { title = "Stepping Stones", questID = 99002, level = 20 } }
	M.questsOn[99002] = true
	M.questGoals[99002] = { { text = "0/3 Stones", finished = false } }
	M.fire("QUEST_LOG_UPDATE")
	check("a quest filed elsewhere is not this dungeon's yet", not inst.quests[99002])
	M.questGoals[99002] = { { text = "1/3 Stones", finished = false } }
	M.fire("QUEST_LOG_UPDATE") M.wait(1)
	check("until it moves along while you are inside", inst.quests[99002] and inst.quests[99002].title == "Stepping Stones")
	M.questLog = {}
	check("quests show whether you carry or finished them", pageText():find("level 22, in your quest log", 1, true)
		and pageText():find("level 17, done", 1, true))
	check("the other side's quests are left out", #ns.Quests[43] > 0 and not pageText():find("Hamuul Runetotem", 1, true))
	do -- grouped: those you carry, those to take up, those done
		M.units.player = { name = "Me", guid = "Player-1-0002", level = 15, player = true }
		open("The Deadmines") open("Quests (")
		local text = pageText()
		local a, b, c = text:find("In your quest log", 1, true), text:find("To be taken up", 1, true), text:find("\nDone", 1, true)
		check("quests are grouped by how you stand with them", a and b and c and a < b and b < c)
		check("a quest you are too young for says so", text:find("Can be taken up from level 16.", 1, true)
			and not text:find("Can be taken up from level 15.", 1, true))
		M.units.player = nil
	end
	check("spoils opens", open("Spoils"))
	check("spoils lists loot", pageText():find("Stonemason Cloak", 1, true))
	check("the notes box went back to the dungeon on turning the page", pageText():find("My notes on The Deadmines", 1, true))
	check("clicking an item turns the notes box to it", open("Stonemason Cloak") and pageText():find("My notes on Stonemason Cloak", 1, true))
	check("spoils are grouped under the boss and the halls", pageText():find("From the halls", 1, true)
		and pageText():find("From Goblin Craftsman", 1, true))
	-- an item's tooltip anywhere says where it was found
	do
		local tip = M.itemTooltip(1930)
		check("an item's tooltip says where it was found", tip:find("Field Notes:", 1, true)
			and tip:find("found in The Deadmines, from Goblin Craftsman.", 1, true))
		check("and a boss's find names the boss", M.itemTooltip(872):find("from Rhahk'Zor", 1, true))
		check("an item never found says nothing", not M.itemTooltip(123456):find("Field Notes", 1, true))
		local hovered = 0
		for _, f in ipairs(M.frames) do
			if f.__kind == "Button" and f.__shown and rawget(f, "line") and f.line.link == inst.loot[1930].link then
				M.itemTooltip(1930) -- the tooltip holds the line from before
				f.__scripts.OnEnter(f)
				hovered = hovered + 1
			end
		end
		check("the spoils page's own tooltips do not repeat it", hovered == 1
			and not table.concat(GameTooltip.__lines or {}, "\n"):find("Field Notes", 1, true))
		ns.db.settings.itemTips = false
		check("turned off, tooltips say nothing", not M.itemTooltip(1930):find("Field Notes", 1, true))
		ns.db.settings.itemTips = true
	end
	check("map opens", open("Map"))
	check("map page text", pageText():find("What you have charted", 1, true))
	-- a boss marker for the boss that was faced, and it leads to its page
	local marks, quests, lit = 0, 0, 0
	for _, f in ipairs(M.frames) do
		if f.__kind == "Button" and f.__shown and rawget(f, "go") then
			if rawget(f, "name"):find("here", 1, true) then
				quests = quests + 1
				if not rawget(f, "note"):find("Not in your log", 1, true) then lit = lit + 1 end
			else
				marks = marks + 1
			end
			if f.__scripts.OnEnter then f.__scripts.OnEnter(f) end
			if f.__scripts.OnLeave then f.__scripts.OnLeave(f) end
		end
	end
	check("one boss marker on the map (found " .. marks .. ")", marks == 1)
	check("the map marks where quests lead (found " .. quests .. ")", quests >= 1)
	check("a quest you carry is marked as such", lit >= 1)
	-- once its objectives are met, a quest no longer marks the map
	do
		local function questMarks()
			local n = 0
			for _, f in ipairs(M.frames) do
				if f.__kind == "Button" and f.__shown and rawget(f, "go") and rawget(f, "name"):find("here", 1, true) then n = n + 1 end
			end
			return n
		end
		local before = questMarks()
		M.questGoals[166] = { { text = "1/1 Head of VanCleef", finished = true } }
		M.questGoals[2040] = { { text = "1/1 Gnoam Sprecklesprocket", finished = true } }
		M.fire("QUEST_LOG_UPDATE") M.wait(1)
		check("quests ready to hand in leave the map (" .. before .. " to " .. questMarks() .. ")", questMarks() < before)
		M.questGoals[166] = { { text = "0/1 Head of VanCleef", finished = false } }
		M.questGoals[2040] = nil
		M.fire("QUEST_LOG_UPDATE") M.wait(1)
	end
	-- the parts shown for the first time are being sketched in
	local function drawing()
		local n = 0
		for _, f in ipairs(M.frames) do
			if f.__scripts.OnUpdate and rawget(f, "anim") then n = n + 1 end
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
	local function inking()
		local n = 0
		for _, f in ipairs(M.frames) do
			if f.__scripts.OnUpdate and rawget(f, "list") then n = n + 1 end
		end
		return n
	end
	check("new entries on the pages are being inked in", inking() == 1)
	check("the map is being sketched in", drawing() == 1)
	run(0.5)
	check("still drawing after half a second", drawing() == 1)
	M.fire("ZONE_CHANGED")
	M.wait(0.5)   -- a redraw in the middle of it
	run(8)
	check("the sketch finishes", drawing() == 0)
	check("the inking finishes", inking() == 0)
	open("Spoils"); open("Bestiary"); open("The Deadmines")
	check("pages read before are not inked again", inking() == 0)
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Defias Taskmaster dies, you gain 90 experience.")
	M.wait(1)
	open("Bestiary")
	check("a new bestiary entry is inked in", inking() == 1)
	run(3)
	check("and finishes", inking() == 0)
	open("Map")
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
	-- a boss with no place of its own, and who it fights beside
	M.fire("ENCOUNTER_START", 2742, "Sneed", 1, 5)
	M.fire("ENCOUNTER_END", 2742, "Sneed", 1, 5, 1)
	M.wait(1)
	open("The Deadmines")
	check("Sneed has a page", open("Sneed"))
	check("a boss's page names the quests that send you after it, or its company",
		pageText():find("Underground Assault|cff5c3b14  in your quest log", 1, true))
	do
		local keys = table.concat(portraits(), " ")
		check("a summoned boss has a portrait", keys:find("d7125", 1, true))
		check("and his shredder beside him", keys:find("d1269", 1, true) and pageText():find("Sneed's Shredder", 1, true))
		check("with what it is", pageText():find("mechanical, level 20", 1, true))
	end
	check("group fights name their members", #ns.Company.twinemperors == 2 and ns.Pictures.nefarian)
	check("new bosses are drawn by NPC id", ns.BossNpc.withermaw == 247195 and ns.BossNpc.infurnus == ns.BossNpc.magmatus)
	-- a boss the game announces no fight for: killed like any creature, kept as a boss
	M.wait(90) -- well after the last announced fight ended
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Cookie dies, you gain 120 experience.")
	M.wait(1)
	check("a known boss killed without an encounter becomes a boss", inst.bosses["n:cookie"]
		and inst.bosses["n:cookie"].kills == 1 and inst.mobs["n:Cookie"].enc == "n:cookie")
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Cookie dies, you gain 120 experience.")
	check("and its later kills are counted", inst.bosses["n:cookie"].kills == 2 and inst.mobs["n:Cookie"].enc == "n:cookie")
	M.fire("CHAT_MSG_LOOT", "Friend receives loot: " .. item(5197, "Cookie's Tenderizer") .. ".")
	check("loot seen in chat just after it falls is its", inst.loot[5197] and inst.loot[5197].enc == "n:cookie")
	M.wait(1)
	open("The Deadmines")
	check("it has a page of its own", open("Cookie") and pageText():find("2 victories", 1, true))
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
	-- the last thing met was on the second sheet: the map opens there, with its boss marked
	check("the map opens on the sheet last visited", pageText():find("Second sheet", 1, true)
		and ns.db.instances[36].charted["boss:edwinvancleef"])
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
	GameTooltip:ClearLines()
	b.__scripts.OnEnter(b)
	check("the button's tooltip tells of the place you are in", table.concat(GameTooltip.__lines, "\n"):find("The Deadmines: %d+ of %d+ foes faced defeated"))
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
	-- a dungeon's quest handed in away from it goes in its diary, quietly
	do
		local said, log = #M.chat, #inst.log
		M.fire("QUEST_TURNED_IN", 166, 1000, 500)
		check("a quest handed in is in its dungeon's diary", #inst.log == log + 1
			and inst.log[#inst.log][2] == "Handed in \"The Defias Brotherhood\".")
		check("away from the dungeon, without a chat line", #M.chat == said)
		M.fire("QUEST_ACCEPTED", 3, 168) -- clients that give the log index first
		check("a quest taken up is too", inst.log[#inst.log][2] == "Took up the quest \"Collecting Memories\".")
		M.fire("QUEST_ACCEPTED", 999999)
		M.fire("QUEST_TURNED_IN", M.Secret())
		check("quests the journal does not know of are not written", #inst.log == log + 2)
	end
	M.slash("")
	check("journal still shows the dungeon", pageText():find("The Deadmines", 1, true))
	check("the contents page lists every place", open("Contents") and pageText():find("1 place written about", 1, true)
		and pageText():find("foes of note", 1, true) and not pageText():find("These pages are blank", 1, true))
	check("a place opens from the contents page", open("kinds of creature") and pageText():find("First entered", 1, true))
	M.slash("")
	M.wait(4000)
	M.instance = { name = "The Deadmines", kind = "party", id = 36 }
	M.fire("PLAYER_ENTERING_WORLD")
	M.wait(3)
	check("second visit counted", inst.visits == 2)
	check("each visit is kept with what came of it", inst.runs and #inst.runs == 2 and inst.runs[1].kills >= 2
		and (inst.runs[1].finds or 0) >= 3 and (inst.runs[1].deaths or 0) >= 1 and inst.runs[1].last > inst.runs[1].t
		and (inst.runs[2].kills or 0) == 0)
	M.slash("")
	check("the dungeon's page lists its visits", pageText():find("Visits", 1, true)
		and pageText():find("foes of note defeated", 1, true))
	M.slash("")
	local said = #M.chat
	M.fire("QUEST_ACCEPTED", 2040)
	check("inside the dungeon a quest taken up is announced", #M.chat == said + 1
		and inst.log[#inst.log][2]:find("Underground Assault", 1, true))
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
	check("not saved, nothing said of it", not pageText():find("Saved to it", 1, true))
	M.slash("")
	M.saved = { { name = "Blackmaw Hold", reset = 3 * 86400, total = 6, done = 1 } }
	M.slash("")
	check("a lockout is shown, from the game's raid information", pageText():find("Saved to it until", 1, true)
		and pageText():find("(1 of 6 foes defeated)", 1, true))
	M.saved = {}
	M.slash("") M.slash("")
	check("no map line in the contents", not open("Map"))
	open("The Mawlord")
	check("adds are on the boss's page", pageText():find("Maw Spawn", 1, true))
	open("Bestiary")
	check("trash is in the bestiary, adds are not", pageText():find("Maw Lurker", 1, true)
		and not pageText():find("Maw Spawn", 1, true))
	open("Spoils")
	M.slash("")
end)

step("creatures a quest wants", function()
	M.instance = { name = "Wailing Caverns", kind = "party", id = 43 }
	M.fire("PLAYER_ENTERING_WORLD")
	M.wait(3)
	M.questsOn[1487] = true
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Deviate Ravager dies, you gain 85 experience.")
	M.fire("CHAT_MSG_COMBAT_XP_GAIN", "Deviate Crocolisk dies, you gain 85 experience.")
	M.wait(1)
	M.slash("")
	open("Bestiary")
	check("a creature says which quests want it", pageText():find("Wanted for Deviate Eradication (in your quest log).", 1, true)
		and pageText():find("Wanted for Crocolisk Hunting.", 1, true))
	M.questsDone[385] = true
	open("Spoils") open("Bestiary")
	check("but not for quests done", not pageText():find("Wanted for Crocolisk Hunting", 1, true))
	M.questsOn[1487], M.questsDone[385] = nil, nil
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
	-- a page that fails to draw is kept the same way, not thrown at the player
	local quests = ns.Quests[36]
	ns.Quests[36] = { { 1 } } -- a quest with nothing but its id
	if not FieldNotesJournal:IsShown() then M.slash("") end
	open("The Deadmines")
	local ok = pcall(open, "Quests (")
	check("a page that fails to draw is caught", ok and ns.db.errors and ns.db.errors[1].event == "drawing a page")
	ns.Quests[36] = quests
	ns.db.errors = nil
	M.slash("")
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
