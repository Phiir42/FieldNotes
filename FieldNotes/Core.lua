-- Field Notes core: saved data, events and small helpers.
--
-- Nothing about any dungeon ships with the addon. Every page is written from
-- what the character witnesses (see Record.lua) and shown by Journal.lua.
--
-- FieldNotesDB.instances[instanceID] = {
--   name, kind ("party" | "raid"), first, last, visits, note,
--   areas     = { { name, t }, ... }                 in discovery order
--   bosses    = { [encounterID] = { name, first, pulls, kills, wipes, best, lastKill, note } }
--   bossOrder = { encounterID, ... }
--   mobs      = { [npcID] = { name, first, cls, type, lo, hi, skull, kills, melee,
--                             fought, enc, spells = { [spellID or name] = spell }, order = { key, ... } } }
--   mobOrder  = { npcID, ... }
--   loot      = { [itemID] = { link, first, n, npc, enc } }
--   lootOrder = { itemID, ... }
--   log       = { { t, text }, ... }                 the diary, oldest first
-- }
local ADDON, ns = ...
FieldNotes = ns

local DB_VERSION = 1
local LOG_MAX = 200

ns.DEFAULTS = {
	announce = true,   -- a chat line when something new is written down
	minQuality = 2,    -- lowest item quality worth noting (2 = uncommon)
	button = true,     -- minimap button
	buttonAngle = 200,
}

---------------------------------------------------------------------------
-- Events: one frame for the whole addon. ns:On("EVENT", fn).
-- Names starting with FN_ are internal messages sent with ns:Fire:
--   FN_LOADED  saved variables are ready
--   FN_DATA    something was written in the journal: redraw it
---------------------------------------------------------------------------
local handlers = {}
local frame = CreateFrame("Frame")
frame:SetScript("OnEvent", function(_, event, ...)
	for _, fn in ipairs(handlers[event]) do fn(...) end
end)

function ns:On(event, fn)
	local list = handlers[event]
	if not list then
		list = {}
		handlers[event] = list
		-- pcall: registering an event this client doesn't have throws
		if event:sub(1, 3) ~= "FN_" then pcall(frame.RegisterEvent, frame, event) end
	end
	list[#list + 1] = fn
end

function ns:Fire(event, ...)
	local list = handlers[event]
	if list then
		for _, fn in ipairs(list) do fn(...) end
	end
end

-- Combat can write many things in one moment; redraw at most a few times a second.
local pending
function ns:Changed()
	if pending then return end
	pending = true
	C_Timer.After(0.3, function()
		pending = false
		ns:Fire("FN_DATA")
	end)
end

ns:On("ADDON_LOADED", function(name)
	if name ~= ADDON then return end
	FieldNotesDB = FieldNotesDB or {}
	local db = FieldNotesDB
	db.instances = db.instances or {}
	db.settings = db.settings or {}
	for k in pairs(db.settings) do
		if ns.DEFAULTS[k] == nil then db.settings[k] = nil end
	end
	for k, v in pairs(ns.DEFAULTS) do
		if db.settings[k] == nil then db.settings[k] = v end
	end
	db.version = DB_VERSION
	ns.db = db
	ns:Fire("FN_LOADED")
end)

---------------------------------------------------------------------------
-- Helpers
---------------------------------------------------------------------------
local PREFIX = "|cffc8a878Field Notes|r: "

function ns:Print(msg, ...)
	DEFAULT_CHAT_FRAME:AddMessage(PREFIX .. (select("#", ...) > 0 and msg:format(...) or msg))
end

-- A line in the instance's diary, and in chat when announcements are on.
function ns:Log(inst, text)
	local log = inst.log
	log[#log + 1] = { time(), text }
	if #log > LOG_MAX then table.remove(log, 1) end
	if self.db.settings.announce then
		DEFAULT_CHAT_FRAME:AddMessage(PREFIX .. text, 0.86, 0.78, 0.62)
	end
	self:Changed()
end

function ns:Clock(sec)
	sec = math.floor(sec + 0.5)
	return ("%d:%02d"):format(sec / 60, sec % 60)
end

function ns:Day(t)
	return date("%d %b %Y", t)
end
