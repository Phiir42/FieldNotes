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

local ENGAGE_GRACE = 5     -- s: creatures first fought this soon before a boss pull belong to it
local BOSS_LOOT_WINDOW = 180 -- s after a boss dies in which unattributed group loot counts as its
local LOOT_REPEAT = 300    -- s: one item is counted once per this window from chat messages
local VISIT_GAP = 1800     -- s away before coming back counts as a new visit

local cur        -- the instance record being written to, nil outside dungeons
local encounter  -- { id = encounterID, t = GetTime() } while a boss fight runs
local lastKill   -- { id = encounterID, t = GetTime() }
local lootSeen = {}  -- [corpseGUID .. itemID] = true: counted this session
local lootTime = {}  -- [itemID] = GetTime() it was last counted
local slain = {}     -- [corpseGUID] = true: kill counted this session

local function NpcID(guid)
	if not guid or issecret(guid) then return end
	local kind, _, _, _, _, id = strsplit("-", guid)
	if kind == "Creature" or kind == "Vehicle" then return tonumber(id) end
end

---------------------------------------------------------------------------
-- Creatures and their abilities
---------------------------------------------------------------------------
local function Mob(id, name)
	local m = cur.mobs[id]
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

-- A corpse seen or looted: count the kill once.
local function Slain(guid)
	if not guid or issecret(guid) or slain[guid] then return end
	local id = NpcID(guid)
	local m = id and cur.mobs[id]
	if not m then return end
	slain[guid] = true
	Fought(m)
	m.kills = (m.kills or 0) + 1
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
	if issecret(guid) or issecret(name) then return end
	if Plain(UnitIsPlayer(unit)) ~= false or Plain(UnitPlayerControlled(unit)) ~= false then return end
	if not Plain(UnitCanAttack("player", unit)) then return end
	local id = NpcID(guid)
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
		Slain(guid)
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

ns:On("UPDATE_MOUSEOVER_UNIT", function() See("mouseover") end)
ns:On("PLAYER_TARGET_CHANGED", function() See("target") end)
ns:On("NAME_PLATE_UNIT_ADDED", See)
ns:On("UNIT_THREAT_LIST_UPDATE", See)

-- A spell a creature is seen casting. how: "cast", "channel" or nil (instant).
local function Cast(how, unit, _, spellID)
	if not cur or type(unit) ~= "string" or issecret(spellID) or type(spellID) ~= "number" then return end
	if not (unit == "target" or unit == "focus" or unit == "mouseover"
		or unit:find("^nameplate") or unit:find("^boss")) then return end
	local m = Creature(unit)
	if not m then return end
	local name = C_Spell and C_Spell.GetSpellName and C_Spell.GetSpellName(spellID)
	if not name and GetSpellInfo then name = GetSpellInfo(spellID) end
	if not name or issecret(name) or name == "" then return end
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
	if not b then
		b = { name = name or UNKNOWN, first = time(), pulls = 0, kills = 0, wipes = 0 }
		cur.bosses[id] = b
		cur.bossOrder[#cur.bossOrder + 1] = id
		ns:Log(cur, ("Faced %s for the first time."):format(b.name))
	end
	return b
end

ns:On("ENCOUNTER_START", function(id, name)
	if not cur or not id then return end
	local b = Boss(id, name)
	b.pulls = b.pulls + 1
	encounter = { id = id, t = GetTime() }
	-- the pull itself usually lands in the combat log just before this event
	local now = time()
	for _, m in pairs(cur.mobs) do
		if m.name == b.name or (not m.enc and m.fought and now - m.fought <= ENGAGE_GRACE) then
			m.enc = id
		end
	end
	cur.last = now
	ns:Changed()
end)

ns:On("ENCOUNTER_END", function(id, name, _, _, success)
	if not cur or not id then return end
	local b = Boss(id, name)
	local started = encounter and encounter.id == id and encounter.t
	encounter = nil
	if success == 1 or success == true then
		b.kills = b.kills + 1
		b.lastKill = time()
		lastKill = { id = id, t = GetTime() }
		if started then
			local took = GetTime() - started
			if not b.best or took < b.best then b.best = took end
			ns:Log(cur, ("Defeated %s in %s."):format(b.name, ns:Clock(took)))
		else
			ns:Log(cur, ("Defeated %s."):format(b.name))
		end
	else
		b.wipes = b.wipes + 1
		ns:Log(cur, ("Driven back by %s."):format(b.name))
	end
	cur.last = time()
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

-- guid: the corpse it lay on, when known (nil for loot seen only in chat).
local function AddLoot(link, guid)
	local id = tonumber(link:match("item:(%d+)"))
	if not id then return end
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
	if not it.npc and not it.enc then
		local npc = NpcID(guid)
		if npc and cur.mobs[npc] then
			it.npc = npc
		elseif lastKill and now - lastKill.t < BOSS_LOOT_WINDOW then
			it.enc = lastKill.id
		end
	end
	ns:Changed()
end

ns:On("LOOT_OPENED", function()
	if not cur then return end
	for slot = 1, GetNumLootItems() do
		local link = GetLootSlotLink(slot)
		local guid = GetLootSourceInfo and GetLootSourceInfo(slot) or nil
		if link then AddLoot(link, guid) end
		Slain(guid) -- an opened corpse is a kill, whether or not it held anything of note
	end
end)

-- Works in any client language: only the item link is read.
ns:On("CHAT_MSG_LOOT", function(msg)
	if not cur or type(msg) ~= "string" then return end
	local link = msg:match("|c.-|Hitem:.-|h.-|h|r")
	if link then AddLoot(link) end
end)

---------------------------------------------------------------------------
-- Areas and the instance itself
---------------------------------------------------------------------------
local function CheckArea()
	if not cur then return end
	local name = GetSubZoneText()
	if not name or name == "" then name = GetMinimapZoneText() end
	if not name or name == "" or name == cur.name then return end
	for _, a in ipairs(cur.areas) do
		if a.name == name then return end
	end
	cur.areas[#cur.areas + 1] = { name = name, t = time() }
	cur.last = time()
	ns:Log(cur, ("Came upon %s."):format(name))
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
			encounter = nil
			local now = time()
			if now - (inst.last or 0) > VISIT_GAP then
				inst.visits = inst.visits + 1
				ns:Log(inst, inst.visits == 1 and ("Set foot in %s for the first time."):format(name)
					or ("Returned to %s."):format(name))
			end
			inst.last = now
			ns:Changed()
		end
		CheckArea()
	elseif cur then
		cur.last = time()
		cur, ns.current, ns.currentID = nil, nil, nil
		encounter = nil
		ns:Changed()
	end
end

-- Instance info can lag a moment behind the loading screen.
local function CheckSoon()
	CheckInstance()
	C_Timer.After(2, CheckInstance)
end

ns:On("PLAYER_ENTERING_WORLD", CheckSoon)
ns:On("ZONE_CHANGED_NEW_AREA", CheckSoon)
ns:On("ZONE_CHANGED", CheckArea)
ns:On("ZONE_CHANGED_INDOORS", CheckArea)

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
