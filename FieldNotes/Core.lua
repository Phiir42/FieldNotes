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

local metadata = (C_AddOns and C_AddOns.GetAddOnMetadata) or GetAddOnMetadata
ns.VERSION = (metadata and metadata(ADDON, "Version")) or "?"
local LOG_MAX = 200

ns.DEFAULTS = {
	announce = true,   -- a chat line when something new is written down
	minQuality = 2,    -- lowest item quality worth noting (2 = uncommon)
	button = true,     -- minimap button
	buttonAngle = 200,
	notices = true,    -- a slip of parchment on screen when something new is written down
	sound = true,      -- the book opening and closing, pages turning
	picturesMove = true, -- portraits are animated (false: held still)
	pictures = "sketch", -- portraits of creatures: "sketch", "colour" or "off"
	textScale = 1,     -- size of the writing, on top of each font's own
	paper = 0.34,      -- how light the page is (0 as dark as the map sheet)
	alpha = 1,         -- how solid the window is
	questMarks = true, -- where quests lead, marked on the map
	itemTips = true,   -- an item's tooltip says where the journal noted it
	markSize = 18,     -- boss marks on the map
	full = false,      -- the journal fills the screen
	scale = 1,         -- size of the journal window
	sketch = true,     -- newly charted parts of a map are sketched in, not just shown
	mapKey = true,     -- inside a dungeon, the map key opens the journal's map
}

---------------------------------------------------------------------------
-- Events: one frame for the whole addon. ns:On("EVENT", fn).
-- Names starting with FN_ are internal messages sent with ns:Fire:
--   FN_LOADED  saved variables are ready
--   FN_DATA    something was written in the journal: redraw it
---------------------------------------------------------------------------
local handlers = {}
local frame = CreateFrame("Frame")

-- A mistake in the journal must never interrupt play. Errors are caught, kept
-- in the saved data (FieldNotesDB.errors, shown by "/fn errors") and mentioned
-- in chat once a session, so they can be reported.
local ERRORS_MAX = 20
local told
local function Failed(event, err)
	err = tostring(err)
	local db = ns.db or FieldNotesDB
	if type(db) == "table" then
		db.errors = db.errors or {}
		local found
		for _, e in ipairs(db.errors) do
			if e.msg == err then e.n, e.t, found = e.n + 1, time(), true end
		end
		if not found then
			db.errors[#db.errors + 1] = { msg = err, event = event, t = time(), n = 1, version = ns.VERSION }
			if #db.errors > ERRORS_MAX then table.remove(db.errors, 1) end
		end
	end
	if not told then
		told = true
		DEFAULT_CHAT_FRAME:AddMessage("|cffc8a878Field Notes|r: something went wrong while taking notes. "
			.. "\"/fn errors\" shows what; please pass it on to the author.")
	end
end

local function Dispatch(event, ...)
	local list = handlers[event]
	if not list then return end
	for _, fn in ipairs(list) do
		local ok, err = pcall(fn, ...)
		if not ok then Failed(event, err) end
	end
end

frame:SetScript("OnEvent", function(_, event, ...) Dispatch(event, ...) end)

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
	Dispatch(event, ...)
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
	if not db.welcomed then
		db.welcomed = true
		ns:Print("a blank journal is in your pack. It fills in as you explore dungeons and raids. "
			.. "\"/fn\" opens it, \"/fn help\" lists what else it can do.")
	end
end)

---------------------------------------------------------------------------
-- Helpers
---------------------------------------------------------------------------
local PREFIX = "|cffc8a878Field Notes|r: "

function ns:Print(msg, ...)
	DEFAULT_CHAT_FRAME:AddMessage(PREFIX .. (select("#", ...) > 0 and msg:format(...) or msg))
end

-- A line in the instance's diary, and in chat when announcements are on.
-- quiet: in the diary only (something that happened away from the place).
function ns:Log(inst, text, quiet)
	local log = inst.log
	log[#log + 1] = { time(), text }
	if #log > LOG_MAX then table.remove(log, 1) end
	if not quiet then
		if self.db.settings.announce then
			DEFAULT_CHAT_FRAME:AddMessage(PREFIX .. text, 0.86, 0.78, 0.62)
		end
		if self.Notice then self:Notice(text) end
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
