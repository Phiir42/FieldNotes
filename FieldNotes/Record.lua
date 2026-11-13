-- Recording: everything the journal knows is written here, from what the
-- character witnesses inside a dungeon or raid.
--   areas      sub-zone changes
--   creatures  anything hostile you mouse over, target or see a nameplate of
--   abilities  spells those creatures are seen casting
--   bosses     ENCOUNTER_START / ENCOUNTER_END
--   loot       corpses you open, and loot messages from your group
--
-- The Forever client restricts combat data like Retail does: addons may not
-- register COMBAT_LOG_EVENT_UNFILTERED, and during instance combat a unit's
-- GUID, name and spells can be "secret" values that error when used. So
-- nothing here reads the combat log, every value from a unit is checked with
-- issecretvalue before use, and whatever is secret is simply not recorded;
-- most of a creature's entry is written when it is seen out of combat.
local _, ns = ...

local issecret = issecretvalue or function() return false end

local BOSS_LOOT_WINDOW = 30 -- s after a boss dies in which loot seen only in chat counts as its
local LOOT_REPEAT = 300    -- s: one item is counted once per this window from chat messages
local VISIT_GAP = 1800     -- s away before coming back counts as a new visit

local cur        -- the instance record being written to, nil outside dungeons
local encounter  -- { id = encounterID, t = GetTime() } while a boss fight runs
local lastKill   -- { id = encounterID, t = GetTime() }
local lootSeen = {}  -- [corpseGUID .. itemID] = true: counted this session
local lootTime = {}  -- [itemID] = GetTime() it was last counted
local slain = {}     -- [corpseGUID] = true: kill counted this session

local function NpcID(guid)
	if issecret(guid) or not guid then return end
	local kind, _, _, _, _, id = strsplit("-", guid)
	if kind == "Creature" or kind == "Vehicle" then return tonumber(id) end
end

-- Counts of what the game let the journal read and what it hid, kept in the
-- saved data (FieldNotesDB.debug) so a run can be looked at afterwards.
local function Tally(what)
	local d = ns.db.debug
	if not d then d = {}; ns.db.debug = d end
	d[what] = (d[what] or 0) + 1
end

-- The visit under way (inst.runs, newest last): when it began and was last
-- seen to go on, who went, and what came of it. what: "kills", "deaths" or
-- "finds", counted one more.
local RUNS_MAX = 20
local function Visit(what)
	local runs = cur and cur.runs
	local r = runs and runs[#runs]
	if not r then return end
	r.last = time()
	if what then r[what] = (r[what] or 0) + 1 end
end

local function NewVisit(inst)
	inst.runs = inst.runs or {}
	local level = UnitLevel and UnitLevel("player")
	local who = UnitName and UnitName("player")
	if issecret(level) or type(level) ~= "number" or level < 1 then level = nil end
	if issecret(who) or type(who) ~= "string" or who == "" then who = nil end
	inst.runs[#inst.runs + 1] = { t = time(), last = time(), level = level, who = who }
	if #inst.runs > RUNS_MAX then table.remove(inst.runs, 1) end
end

-- Who else went on the visit under way: the names of the group, as they join.
local WITH_MAX = 40
local function Company()
	local runs = cur and cur.runs
	local r = runs and runs[#runs]
	if not r or not GetNumGroupMembers then return end
	local n = GetNumGroupMembers()
	if issecret(n) or type(n) ~= "number" or n < 2 then return end
	local raid = IsInRaid and IsInRaid()
	local me = UnitName("player")
	if issecret(me) then me = nil end
	for i = 1, raid and n or (n - 1) do
		local name = UnitName((raid and "raid" or "party") .. i)
		Tally(issecret(name) and "group member's name hidden" or "group member's name shown")
		if not issecret(name) and type(name) == "string" and name ~= "" and name ~= me
			and name ~= UNKNOWNOBJECT then
			r.with = r.with or {}
			local known
			for _, w in ipairs(r.with) do known = known or w == name end
			if not known and #r.with < WITH_MAX then
				r.with[#r.with + 1] = name
				ns:Changed()
			end
		end
	end
end

---------------------------------------------------------------------------
-- Creatures and their abilities
---------------------------------------------------------------------------
-- A creature is filed under its NPC id. When the game hides the id but shows
-- the name, it is filed under "n:<name>" until the id turns up (on its corpse).
local function Mob(id, name)
	local m = cur.mobs[id]
	if not m and name then
		local other = type(id) == "number" and ("n:" .. name) or nil
		if other and cur.mobs[other] then
			-- met by name before: move that entry under the id
			m = cur.mobs[other]
			cur.mobs[other], cur.mobs[id] = nil, m
			for i, key in ipairs(cur.mobOrder) do
				if key == other then cur.mobOrder[i] = id end
			end
			for _, it in pairs(cur.loot) do
				if it.npc == other then it.npc = id end
			end
			ns:Changed()
			return m
		elseif not other then
			-- no id this time: the same creature may already be filed under one
			for _, known in pairs(cur.mobs) do
				if known.name == name then return known end
			end
		end
	end
	if not m then
		if not name or name == "" or name == UNKNOWN or name == UNKNOWNOBJECT then return end
		m = { name = name, first = time(), spells = {}, order = {} }
		cur.mobs[id] = m
		cur.mobOrder[#cur.mobOrder + 1] = id
		ns:Changed()
	end
	return m
end

local function Fought(m)
	if m.fought then return end
	m.fought = time()
	if encounter then m.enc = encounter.id end
	ns:Changed()
end

local function Spell(m, id, name)
	local s = m.spells[id]
	if not s then
		s = { name = name, first = time() }
		m.spells[id] = s
		m.order[#m.order + 1] = id
		ns:Changed()
	end
	return s
end

-- A creature's name from its GUID alone, as the game's tooltip gives it.
local function NameOf(guid)
	if not (C_TooltipInfo and C_TooltipInfo.GetHyperlink) then return end
	local ok, data = pcall(C_TooltipInfo.GetHyperlink, "unit:" .. guid)
	local line = ok and type(data) == "table" and data.lines and data.lines[1]
	local text = line and line.leftText
	if type(text) == "string" and not issecret(text) and text ~= "" then return text end
end

-- A corpse seen or looted: count the kill once. A corpse is often the first
-- time the game shows who a creature was, so this can also start its entry.
local function Slain(guid)
	if issecret(guid) or not guid or slain[guid] then return end
	local id = NpcID(guid)
	local m = id and (cur.mobs[id] or Mob(id, NameOf(guid) or ns.CreatureNames[id]))
	if not m then return end
	slain[guid] = true
	Fought(m)
	-- kills are counted from experience messages when those name the creature
	if not m.xp then m.kills = (m.kills or 0) + 1 end
	ns:Changed()
end

-- true / false, or nil when the game hides the answer
local function Plain(v)
	if issecret(v) then return nil end
	return v
end

-- The journal entry for a hostile creature behind a unit token, with what the
-- token shows about it. nil for anything else, or while its identity is secret.
local function Creature(unit)
	if not cur or not Plain(UnitExists(unit)) then return end
	local guid, name = UnitGUID(unit), UnitName(unit)
	local when = InCombatLockdown() and " in combat" or " at rest"
	if issecret(guid) then Tally("unit id hidden" .. when); guid = nil else Tally("unit id shown" .. when) end
	if issecret(name) then Tally("unit name hidden" .. when); name = nil else Tally("unit name shown" .. when) end
	if not name and unit == "mouseover" and GameTooltipTextLeft1 then
		-- the tooltip under the cursor names it too
		local text = GameTooltipTextLeft1:GetText()
		if issecret(text) then
			Tally("tooltip name hidden" .. when)
		elseif type(text) == "string" and text ~= "" then
			Tally("tooltip name shown" .. when)
			name = text:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
		end
	end
	if not guid and not name then return end
	if Plain(UnitIsPlayer(unit)) ~= false or Plain(UnitPlayerControlled(unit)) ~= false then return end
	if not Plain(UnitCanAttack("player", unit)) then return end
	local id = NpcID(guid) or (not guid and name and ("n:" .. name))
	local m = id and Mob(id, name)
	if not m then return end

	local changed
	local level = Plain(UnitLevel(unit))
	if type(level) == "number" then
		if level > 0 then
			if not m.lo or level < m.lo then m.lo = level; changed = true end
			if not m.hi or level > m.hi then m.hi = level; changed = true end
		elseif level == -1 and not m.skull then
			m.skull = true
			changed = true
		end
	end
	local cls = Plain(UnitClassification(unit))
	if cls and cls ~= m.cls then m.cls = cls; changed = true end
	local kind = Plain(UnitCreatureType(unit))
	if kind and kind ~= m.type then m.type = kind; changed = true end
	if changed then ns:Changed() end

	if Plain(UnitIsDead(unit)) then
		if guid then Slain(guid) else Fought(m) end
	elseif Plain(UnitAffectingCombat(unit)) then
		Fought(m)
	end
	return m
end

-- pcall: should the game hide something this code does not expect, skip the
-- sighting instead of raising an error in the middle of a fight
local function See(unit)
	if cur and type(unit) == "string" then pcall(Creature, unit) end
end

-- Creatures name themselves when they shout, speak or emote ("... attempts to
-- run away in fear!"). Only while fighting: a boss calling out across the room
-- has not been met yet. Bosses get their own pages, not a bestiary entry.
local function Heard(_, sender)
	if not cur then return end
	if issecret(sender) then Tally("speaker name hidden") return end
	if type(sender) ~= "string" or sender == "" then return end
	Tally("speaker name shown")
	if not (encounter or InCombatLockdown()) then return end
	local key = ns:AreaKey(sender)
	if ns.AbilitiesByName[key] then return end
	-- Friends speak in a fight too (escorts, captives). In the old dungeons
	-- only the creatures known to live there are taken for enemies; in new
	-- ones nothing is known, so every speaker is.
	local lore = ns.Creatures[key]
	if lore and lore.friend then return end -- someone you talk to, not fight
	local known = lore or type(ns.currentID) ~= "number" or ns.currentID > 1000
	local m = known and Mob("n:" .. sender, sender)
	if not known then
		for _, old in pairs(cur.mobs) do
			if old.name == sender then m = old end
		end
	end
	if m then Fought(m) end
end
ns:On("CHAT_MSG_MONSTER_EMOTE", Heard)

-- "Goblin Craftsman dies, you gain 85 experience." names what was just slain:
-- the one dependable account of a kill the game gives an addon in a dungeon.
local xpPattern
ns:On("CHAT_MSG_COMBAT_XP_GAIN", function(msg)
	if not cur then return end
	if issecret(msg) then Tally("experience message hidden") return end
	if type(msg) ~= "string" then return end
	if not xpPattern then
		-- the client's own wording, up to the amount: "%s dies, you gain "
		local fmt = (COMBATLOG_XPGAIN_FIRSTPERSON or "%s dies, you gain %d experience."):gsub("%%1%$s", "%%s")
		local head = fmt:match("^(.-)%%%d?%$?d") or fmt
		xpPattern = "^" .. head:gsub("([%(%)%.%+%-%*%?%[%]%^%$])", "%%%1"):gsub("%%s", "(.-)")
	end
	local name = msg:match(xpPattern)
	if not name or name == "" then Tally("experience message without a name") return end
	Tally("experience message names the kill")
	local m = Mob("n:" .. name, name)
	if not m then return end
	Fought(m)
	-- filed with a boss because it was first met in that fight, but here it is
	-- killed on its own: it is one of the place's creatures after all
	if m.enc and not encounter then m.enc = nil end
	m.xp = true
	m.kills = (m.kills or 0) + 1
	Visit()
	if not encounter then ns:NamedBoss(cur, m, true) end
	ns:Changed()
end)
ns:On("CHAT_MSG_MONSTER_YELL", Heard)
ns:On("CHAT_MSG_MONSTER_SAY", Heard)

ns:On("UPDATE_MOUSEOVER_UNIT", function() See("mouseover") end)
ns:On("PLAYER_TARGET_CHANGED", function() See("target") end)
ns:On("NAME_PLATE_UNIT_ADDED", See)
ns:On("UNIT_THREAT_LIST_UPDATE", See)

-- A spell a creature is seen casting. how: "cast", "channel" or nil (instant).
local function Cast(how, unit, _, spellID)
	if not cur or type(unit) ~= "string" then return end
	if issecret(spellID) then Tally("cast spell hidden") return end
	if type(spellID) ~= "number" then return end
	if not (unit == "target" or unit == "focus" or unit == "mouseover"
		or unit:find("^nameplate") or unit:find("^boss")) then return end
	local m = Creature(unit)
	if not m then return end
	Tally("cast spell shown")
	local name = C_Spell and C_Spell.GetSpellName and C_Spell.GetSpellName(spellID)
	if not name and GetSpellInfo then name = GetSpellInfo(spellID) end
	if issecret(name) or not name or name == "" then return end
	Fought(m)
	local s = Spell(m, spellID, name)
	if how and not s[how] then
		s[how] = true
		ns:Changed()
	end
end

ns:On("UNIT_SPELLCAST_START", function(...) pcall(Cast, "cast", ...) end)
ns:On("UNIT_SPELLCAST_CHANNEL_START", function(...) pcall(Cast, "channel", ...) end)
ns:On("UNIT_SPELLCAST_SUCCEEDED", function(...) pcall(Cast, nil, ...) end)

---------------------------------------------------------------------------
-- Bosses
---------------------------------------------------------------------------
local function Boss(id, name)
	local b = cur.bosses[id]
	-- a name the game hid when the fight began, given at its end
	if b and name and b.name == UNKNOWN then
		b.name = name
		-- and the diary's line on meeting it
		local met = ("Faced %s for the first time."):format(UNKNOWN)
		for i = #cur.log, math.max(1, #cur.log - 30), -1 do
			if cur.log[i][2] == met then
				cur.log[i][2] = ("Faced %s for the first time."):format(ns:The(name))
				break
			end
		end
		ns:Changed()
	end
	if not b then
		b = { name = name or UNKNOWN, first = time(), pulls = 0, kills = 0, wipes = 0 }
		cur.bosses[id] = b
		cur.bossOrder[#cur.bossOrder + 1] = id
		ns:Log(cur, ("Faced %s for the first time."):format(ns:The(b.name)))
	end
	return b
end

-- A boss the game announces no fight for: one the addon knows by name (it has
-- a list of abilities), killed like any creature. It is given a boss's place
-- all the same, filed under its name instead of an encounter's number.
-- live: a kill just now (else: making good what older notes hold).
function ns:NamedBoss(inst, m, live)
	if not (m.kills and m.kills > 0 and ns.AbilitiesByName) then return end
	local key = ns:AreaKey(m.name)
	if not ns.AbilitiesByName[key] then return end
	local id = "n:" .. key
	local b = inst.bosses[id]
	if b then
		m.enc = id
		if live then
			b.kills, b.pulls, b.lastKill = b.kills + 1, b.pulls + 1, time()
			lastKill = { id = id, t = GetTime() }
			Visit("kills")
		end
		return
	end
	-- not one the game did announce: by its name, or (where the fight goes by
	-- another name than the creature) by having died as that fight ended
	-- (Gelihast, whose fight the game calls "Geilhast"): it is that boss, and
	-- what it carried is that boss's
	-- By name first; else the fight that ended nearest the kill (not one never
	-- won, nor any for notes too old to say when the creature was fought).
	local at = live and time() or m.fought or 0
	local near, gap
	for oid, other in pairs(inst.bosses) do
		if ns:AreaKey(other.name) == key then
			m.enc = m.enc or oid
			return
		end
		local d = other.lastKill and at > 0 and math.abs(other.lastKill - at)
		if d and d < 60 and (not gap or d < gap) then near, gap = oid, d end
	end
	if near then
		m.enc = m.enc or near
		return
	end
	inst.bosses[id] = {
		name = m.name, first = m.first or at, pulls = m.kills, kills = m.kills, wipes = 0, lastKill = at,
	}
	inst.bossOrder[#inst.bossOrder + 1] = id
	m.enc = id
	if live then
		-- loot seen only in chat just after is this boss's, as for any other
		lastKill = { id = id, t = GetTime() }
		Visit("kills")
		ns:Log(inst, ("Defeated %s."):format(ns:The(m.name)))
	end
end

ns:On("ENCOUNTER_START", function(id, name)
	if not cur or issecret(id) or not id or type(id) == "boolean" or type(id) == "table" then return end
	if issecret(name) or type(name) ~= "string" or name == "" then name = nil end
	local b = Boss(id, name)
	b.pulls = b.pulls + 1
	encounter = { id = id, t = GetTime() }
	-- Creatures first fought during the fight are filed with it (see Fought).
	-- Not those met just before: a kill is only heard of once the creature is
	-- dead, so anything already known is the trash on the way in.
	local now = time()
	for _, m in pairs(cur.mobs) do
		if m.name == b.name then m.enc = id end
	end
	cur.last = now
	ns:Changed()
end)

ns:On("ENCOUNTER_END", function(id, name, _, _, success)
	if not cur or issecret(id) or not id or type(id) == "boolean" or type(id) == "table" then return end
	if issecret(name) or type(name) ~= "string" or name == "" then name = nil end
	if issecret(success) then success = nil end
	local b = Boss(id, name)
	local started = encounter and encounter.id == id and encounter.t
	encounter = nil
	if success == 1 or success == true then
		b.kills = b.kills + 1
		b.lastKill = time()
		lastKill = { id = id, t = GetTime() }
		Visit("kills")
		if started then
			local took = GetTime() - started
			if not b.best or took < b.best then b.best = took end
			ns:Log(cur, ("Defeated %s in %s."):format(ns:The(b.name), ns:Clock(took)))
		else
			ns:Log(cur, ("Defeated %s."):format(ns:The(b.name)))
		end
	else
		b.wipes = b.wipes + 1
		ns:Log(cur, ("Driven back by %s."):format(ns:The(b.name)))
	end
	cur.last = time()
end)

-- Your own death is part of the story.
ns:On("PLAYER_DEAD", function()
	if not cur then return end
	cur.deaths = (cur.deaths or 0) + 1
	Visit("deaths")
	local b = encounter and cur.bosses[encounter.id]
	local area = cur.areas[#cur.areas]
	if b then
		b.deaths = (b.deaths or 0) + 1
		ns:Log(cur, ("Fell in battle against %s."):format(ns:The(b.name)))
	elseif area then
		ns:Log(cur, ("Fell in battle in %s."):format(ns:The(area.name)))
	else
		ns:Log(cur, "Fell in battle.")
	end
end)

---------------------------------------------------------------------------
-- Loot
---------------------------------------------------------------------------
local function Quality(link, id)
	local q
	if C_Item and C_Item.GetItemQualityByID then q = C_Item.GetItemQualityByID(link) end
	if not q and GetItemInfo then q = select(3, GetItemInfo(link)) end
	if not q and C_Item and C_Item.GetItemInfo then q = select(3, C_Item.GetItemInfo(id)) end
	return q
end

-- Dusts, essences and shards come from disenchanting what was found, not from
-- the dungeon: the chat line for them reads like any other loot.
local function Disenchanted(id)
	local instant = (C_Item and C_Item.GetItemInfoInstant) or GetItemInfoInstant
	if not instant then return false end
	local ok, _, _, _, _, _, class, subclass = pcall(instant, id)
	return ok and class == 7 and subclass == 12 -- trade goods: enchanting
end

-- guid: the corpse it lay on, when known (nil for loot seen only in chat).
local function AddLoot(link, guid)
	local id = tonumber(link:match("item:(%d+)"))
	if not id or Disenchanted(id) then return end
	local q = Quality(link, id)
	if not q or q < ns.db.settings.minQuality then return end

	local now = GetTime()
	if issecret(guid) then guid = nil end
	if guid then
		local key = guid .. id
		if lootSeen[key] then return end
		lootSeen[key] = true
	elseif now - (lootTime[id] or -LOOT_REPEAT) < LOOT_REPEAT then
		return -- already counted from the corpse or an earlier message
	end
	lootTime[id] = now

	local it = cur.loot[id]
	if not it then
		it = { link = link, first = time(), n = 0 }
		cur.loot[id] = it
		cur.lootOrder[#cur.lootOrder + 1] = id
		ns:Log(cur, ("Found %s."):format(link))
	end
	it.n = it.n + 1
	Visit("finds")
	local npc = NpcID(guid)
	if npc then
		-- An opened corpse says exactly whose the item was, and overrules any
		-- earlier guess: a boss's if the corpse is a boss (by name) or was part
		-- of its fight, otherwise that creature's.
		local m = cur.mobs[npc]
		local name = (m and m.name) or ns.CreatureNames[npc]
		local boss = m and m.enc
		if name then
			local key = ns:AreaKey(name)
			for id, b in pairs(cur.bosses) do
				if ns:AreaKey(b.name) == key then boss = id end
			end
		end
		if boss then
			it.enc, it.npc = boss, nil
		else
			it.enc, it.npc = nil, m and npc or nil
		end
	elseif not it.npc and not it.enc and lastKill and now - lastKill.t < BOSS_LOOT_WINDOW then
		-- seen only in chat (someone else looted it), just after a boss fell
		it.enc = lastKill.id
	end
	ns:Changed()
end

ns:On("LOOT_OPENED", function()
	if not cur then return end
	for slot = 1, GetNumLootItems() do
		local link = GetLootSlotLink(slot)
		-- a secret value may not even be tested for truth: ask issecret first
		local guid
		if GetLootSourceInfo then guid = GetLootSourceInfo(slot) end
		if issecret(guid) then
			Tally("corpse id hidden")
			guid = nil
		elseif guid then
			Tally("corpse id shown")
		end
		if issecret(link) then link = nil end
		Slain(guid) -- an opened corpse is a kill, whether or not it held anything of note
		if link then AddLoot(link, guid) end
	end
end)

-- Only lines saying someone received loot count: not rolls, not things made
-- or handed over. The client's own wordings are turned into patterns, so this
-- works in any language; the item itself is read from its link.
local lootPatterns
local function IsLootLine(msg)
	if not lootPatterns then
		lootPatterns = {}
		for _, fmt in ipairs({ LOOT_ITEM_SELF, LOOT_ITEM_SELF_MULTIPLE, LOOT_ITEM, LOOT_ITEM_MULTIPLE }) do
			if type(fmt) == "string" then
				local pat = fmt:gsub("([%(%)%.%+%-%*%?%[%]%^%$])", "%%%1")
					:gsub("%%%d?%$?s", ".+"):gsub("%%%d?%$?d", "%%d+")
				lootPatterns[#lootPatterns + 1] = "^" .. pat .. "$"
			end
		end
	end
	if #lootPatterns == 0 then return true end -- wordings unknown: take every line
	for _, pat in ipairs(lootPatterns) do
		if msg:find(pat) then return true end
	end
	return false
end

ns:On("CHAT_MSG_LOOT", function(msg)
	if not cur then return end
	if issecret(msg) then Tally("loot message hidden") return end
	if type(msg) ~= "string" or not IsLootLine(msg) then return end
	local link = msg:match("|c[^|]*|Hitem:.-|h.-|h|r")
	if link then AddLoot(link) end
end)

---------------------------------------------------------------------------
-- Areas and the instance itself
---------------------------------------------------------------------------
local function CheckArea()
	if not cur then return end
	Visit()
	local name = GetSubZoneText()
	if issecret(name) then return end
	if not name or name == "" then name = GetMinimapZoneText() end
	if issecret(name) then return end
	if not name or name == "" or ns:AreaKey(name) == ns:AreaKey(cur.name) then return end
	for _, a in ipairs(cur.areas) do
		if a.name == name then return end
	end
	cur.areas[#cur.areas + 1] = { name = name, t = time() }
	cur.last = time()
	ns:Log(cur, ("Came upon %s."):format(ns:The(name)))
end

local function CheckInstance()
	if not ns.db then return end
	local name, kind, _, _, _, _, _, id = GetInstanceInfo()
	if (kind == "party" or kind == "raid") and id and name and name ~= "" then
		local inst = ns.db.instances[id]
		if not inst then
			inst = {
				name = name, kind = kind, first = time(), visits = 0,
				areas = {}, bosses = {}, bossOrder = {}, mobs = {}, mobOrder = {},
				loot = {}, lootOrder = {}, log = {},
			}
			ns.db.instances[id] = inst
		end
		if cur ~= inst then
			cur, ns.current, ns.currentID = inst, inst, id
			encounter, lastKill = nil, nil
			local now = time()
			if now - (inst.last or 0) > VISIT_GAP then
				inst.visits = inst.visits + 1
				NewVisit(inst)
				ns:Log(inst, inst.visits == 1 and ("Set foot in %s for the first time."):format(ns:The(name))
					or ("Returned to %s."):format(ns:The(name)))
			else
				-- the same visit goes on, unless it was begun before visits were
				-- kept, or by another character
				local last = inst.runs and inst.runs[#inst.runs]
				local who = UnitName and UnitName("player")
				if issecret(who) then who = nil end
				if not last or (who and last.who and who ~= last.who) then NewVisit(inst) end
			end
			inst.last = now
			Visit()
			Company()
			ns:Changed()
		end
		CheckArea()
	elseif cur then
		Visit()
		cur.last = time()
		cur, ns.current, ns.currentID = nil, nil, nil
		encounter = nil
		ns:Changed()
	end
end

-- Take out what earlier versions noted by mistake.
local function Tidy()
	if not ns.db then return end
	local changed
	for _, inst in pairs(ns.db.instances) do
		for i = #inst.lootOrder, 1, -1 do
			local id = inst.lootOrder[i]
			if type(id) == "number" and Disenchanted(id) then
				inst.loot[id] = nil
				table.remove(inst.lootOrder, i)
				changed = true
			end
		end
		-- bosses killed without the game announcing the fight, noted by older
		-- versions as creatures that then showed nowhere
		for _, m in pairs(inst.mobs) do
			if not m.enc then ns:NamedBoss(inst, m) end
		end
		-- falls to a boss were counted from 0.2.0-beta.10 on: before, only the
		-- diary says so
		for _, b in pairs(inst.bosses) do
			if b.deaths == nil then
				-- (written "the Butcher" mid-sentence since; "The Butcher" before)
				local line, old, n = ("Fell in battle against %s."):format(ns:The(b.name)),
					("Fell in battle against %s."):format(b.name), 0
				for _, e in ipairs(inst.log) do
					if e[2] == line or e[2] == old then n = n + 1 end
				end
				b.deaths = n
			end
		end
		-- visits were kept from 0.2.0-beta.10 on: the earlier ones, from the
		-- diary (each begins where it says you set foot in or returned), as
		-- far as the first one kept
		local first = inst.runs and inst.runs[1] and inst.runs[1].t
		if #inst.log > 0 and (inst.runs == nil or (first and type(inst.log[1][1]) == "number" and inst.log[1][1] < first)) then
			local runs = {}
			for _, e in ipairs(inst.log) do
				local t, text = e[1], e[2]
				if type(t) == "number" and type(text) == "string" and not (first and t >= first) then
					if text:find("^Set foot in ") or text:find("^Returned to ") then
						runs[#runs + 1] = { t = t, last = t }
					elseif runs[#runs] then
						local r = runs[#runs]
						-- a find counts while it is still in the journal (not a shard)
						local item = text:find("^Found ") and tonumber(text:match("item:(%d+)"))
						local what = (text:find("^Defeated ") and "kills") or (text:find("^Fell in battle") and "deaths")
							or (item and inst.loot[item] and "finds")
						-- (a quest taken up elsewhere is no part of a visit)
						if what or item or text:find("^Faced ") or text:find("^Came upon ") or text:find("^Driven back by ") then
							r.last = t
							if what then r[what] = (r[what] or 0) + 1 end
						end
					end
				end
			end
			if inst.runs == nil then
				inst.runs, changed = runs, true
			elseif #runs > 0 then
				for i = #runs, 1, -1 do table.insert(inst.runs, 1, runs[i]) end
				changed = true
			end
			while #inst.runs > RUNS_MAX do table.remove(inst.runs, 1) end
		end
	end
	if changed then ns:Changed() end -- (item tooltips are written from the loot)
end

-- Instance info can lag a moment behind the loading screen.
local function CheckSoon()
	Tidy()
	CheckInstance()
	C_Timer.After(2, CheckInstance)
end

ns:On("PLAYER_ENTERING_WORLD", CheckSoon)
ns:On("ZONE_CHANGED_NEW_AREA", CheckSoon)
ns:On("ZONE_CHANGED", CheckArea)
ns:On("ZONE_CHANGED_INDOORS", CheckArea)
ns:On("GROUP_ROSTER_UPDATE", function() Company() end)

-- /fn debug: what the game has shown and hidden so far.
function ns:DebugReport()
	local d, keys = self.db.debug or {}, {}
	for k in pairs(d) do keys[#keys + 1] = k end
	table.sort(keys)
	self:Print("what the game has shown and hidden (%s):", cur and ("in " .. cur.name) or "not in a dungeon")
	if #keys == 0 then print("  nothing counted yet") end
	for _, k in ipairs(keys) do print(("  %s: %d"):format(k, d[k])) end
end

-- Tear an instance's pages out of the journal.
function ns:Forget(id)
	if not self.db.instances[id] then return end
	self.db.instances[id] = nil
	if self.currentID == id then
		cur, self.current, self.currentID = nil, nil, nil
		CheckInstance() -- still standing in it: start a fresh page
	end
	self:Changed()
end
