-- A small stand-in for the WoW client, enough to load Field Notes and walk
-- it through a dungeon run outside the game (see tools/test_addon.py).
-- It models what the Forever client does to addons: hostile units' ids, names
-- and casts are "secret" values that raise an error when used as strings.
local M = { frames = {}, timers = {}, chat = {}, missing = {}, now = 1000, clock = 1794000000 }

---------------------------------------------------------------------------
-- Secret values
---------------------------------------------------------------------------
local secret_mt = {
	__tostring = function() error("attempt to perform string conversion on a secret value", 2) end,
	__concat = function() error("attempt to concatenate a secret value", 2) end,
	__index = function() error("attempt to index a secret value", 2) end,
	__eq = function() error("attempt to compare a secret value", 2) end,
	__lt = function() error("attempt to compare a secret value", 2) end,
}
local function Secret() return setmetatable({}, secret_mt) end
M.Secret = Secret
function issecretvalue(v) return type(v) == "table" and getmetatable(v) == secret_mt end

---------------------------------------------------------------------------
-- Frames and regions
---------------------------------------------------------------------------
local NOOP = { "Set", "Clear", "Register", "Unregister", "Enable", "Disable", "Add", "Raise", "Lower", "Start",
	"Stop", "Remove", "Lock", "Unlock", "Insert", "Highlight", "Apply", "Update" }
local Object = {}
local object_mt

local function New(kind, parent, name)
	local o = setmetatable({ __kind = kind, __parent = parent, __shown = kind ~= "GameTooltip", __scripts = {},
		__events = {}, __w = 100, __h = 20, __text = "", __name = name }, object_mt)
	M.frames[#M.frames + 1] = o
	return o
end

function Object:SetScript(what, fn) self.__scripts[what] = fn end
function Object:GetScript(what) return self.__scripts[what] end
function Object:HookScript(what, fn)
	local old = self.__scripts[what]
	self.__scripts[what] = function(...) if old then old(...) end return fn(...) end
end
function Object:RegisterEvent(event)
	if event == "COMBAT_LOG_EVENT_UNFILTERED" then
		error("ADDON_ACTION_FORBIDDEN: Frame:RegisterEvent()", 2)
	end
	self.__events[event] = true
end
function Object:UnregisterEvent(event) self.__events[event] = nil end
function Object:Show()
	if not self.__shown then
		self.__shown = true
		if self.__scripts.OnShow then self.__scripts.OnShow(self) end
	end
end
function Object:Hide()
	if self.__shown then
		self.__shown = false
		if self.__scripts.OnHide then self.__scripts.OnHide(self) end
	end
end
function Object:SetShown(on) if on then self:Show() else self:Hide() end end
function Object:IsShown() return self.__shown end
function Object:IsVisible() return self.__shown end
function Object:GetParent() return self.__parent end
function Object:GetName() return self.__name end
function Object:GetObjectType() return self.__kind end
function Object:CreateTexture() return New("Texture", self) end
function Object:CreateMaskTexture() return New("MaskTexture", self) end
function Object:CreateFontString() return New("FontString", self) end
function Object:SetText(text)
	if issecretvalue(text) then return end
	self.__text = text == nil and "" or tostring(text)
end
function Object:GetText() return self.__text end
function Object:SetSize(w, h) self.__w, self.__h = w, h end
function Object:SetWidth(w) self.__w = w end
function Object:SetHeight(h) self.__h = h end
function Object:GetWidth() return self.__w end
function Object:GetHeight() return self.__h end
function Object:GetSize() return self.__w, self.__h end
function Object:GetStringHeight()
	local _, lines = self.__text:gsub("\n", "\n")
	return 14 * (lines + 1)
end
function Object:GetStringWidth() return 6 * #self.__text end
function Object:GetCenter() return 500, 400 end
function Object:GetLeft() return 400 end
function Object:GetRight() return 600 end
function Object:GetTop() return 500 end
function Object:GetBottom() return 300 end
function Object:GetEffectiveScale() return 1 end
function Object:GetScale() return 1 end
function Object:GetFrameLevel() return 1 end
function Object:GetVerticalScroll() return 0 end
function Object:GetVerticalScrollRange() return 0 end
function Object:GetScrollChild() return self.__child end
function Object:SetScrollChild(child) self.__child = child end
function Object:NumLines() return 1 end
function Object:IsMouseOver() return false end
function Object:GetAlpha() return 1 end
function Object:GetPoint() return "TOPLEFT", UIParent, "TOPLEFT", 40, -60 end
function Object:IsProtected() return false end
function Object:HasFocus() return false end
function Object:AddMessage(text) M.chat[#M.chat + 1] = tostring(text) end
-- an item link shown on a tooltip: addons are told of it (see TooltipDataProcessor)
function Object:SetHyperlink(link)
	self.__lines = {}
	local id = type(link) == "string" and tonumber(link:match("item:(%d+)"))
	if id then
		for _, fn in ipairs(M.tooltipCalls[0] or {}) do fn(self, { id = id }) end
	end
end
-- tooltips keep their lines, so a test can read them
function Object:AddLine(text) self.__lines = self.__lines or {}; self.__lines[#self.__lines + 1] = tostring(text) end
function Object:ClearLines() self.__lines = {} end
function Object:Click() if self.__scripts.OnClick then self.__scripts.OnClick(self, "LeftButton") end end

object_mt = {
	__index = function(t, k)
		if Object[k] then return Object[k] end
		if type(k) ~= "string" or k:sub(1, 2) == "__" then return nil end
		for _, prefix in ipairs(NOOP) do
			if k:sub(1, #prefix) == prefix then return function() end end
		end
		if k:match("^Get") or k:match("^Is") or k:match("^Has") or k:match("^Num") or k:match("^Can") then
			error("the mock has no method " .. k, 2)
		end
		-- a child region of a template (TitleText, CloseButton, Inset, ...)
		if k:match("^%u") then
			local child = New("Region", t)
			rawset(t, k, child)
			return child
		end
	end,
}

function CreateFrame(kind, name, parent)
	local f = New(kind or "Frame", parent, name)
	if name then _G[name] = f end
	return f
end

UIParent = New("Frame"); UIParent.__w, UIParent.__h = 1366, 768
Minimap = New("Minimap")
WorldMapFrame = New("Frame"); WorldMapFrame.__shown = false
GameTooltip = New("GameTooltip")
GameTooltipTextLeft1 = New("FontString")
DEFAULT_CHAT_FRAME = New("ScrollingMessageFrame")
function print(...)
	local t = {}
	for i = 1, select("#", ...) do t[i] = tostring((select(i, ...))) end
	M.chat[#M.chat + 1] = table.concat(t, " ")
end

---------------------------------------------------------------------------
-- Globals
---------------------------------------------------------------------------
UNKNOWN, UNKNOWNOBJECT = "Unknown", "Unknown Entity"
COMBATLOG_XPGAIN_FIRSTPERSON = "%s dies, you gain %d experience."
LOOT_ITEM_SELF, LOOT_ITEM_SELF_MULTIPLE = "You receive loot: %s.", "You receive loot: %sx%d."
LOOT_ITEM, LOOT_ITEM_MULTIPLE = "%s receives loot: %s.", "%s receives loot: %sx%d."
StaticPopupDialogs, SlashCmdList, UISpecialFrames = {}, {}, {}
function StaticPopup_Show(which, text, _, data)
	local d = StaticPopupDialogs[which]
	M.popup = { which = which, data = data }
	if M.accept_popups and d and d.OnAccept then d.OnAccept({ data = data }, data) end
end
function time() return M.clock end
function GetTime() return M.now end
date = os.date
format = string.format
strlower, strupper, strfind, strmatch, strsub, strlen, gsub, strrep = string.lower, string.upper, string.find,
	string.match, string.sub, string.len, string.gsub, string.rep
tinsert, tremove, floor, ceil, min, max, abs = table.insert, table.remove, math.floor, math.ceil, math.min,
	math.max, math.abs
function strtrim(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end
function strsplit(sep, s)
	local out = {}
	for part in (s .. sep):gmatch("(.-)%" .. sep) do out[#out + 1] = part end
	return unpack(out)
end
function wipe(t) for k in pairs(t) do t[k] = nil end return t end
function hooksecurefunc(name, fn)
	local old = _G[name]
	_G[name] = function(...) local r = { old(...) } fn(...) return unpack(r) end
end
C_Timer = { After = function(sec, fn) M.timers[#M.timers + 1] = { at = M.now + sec, fn = fn } end }
function InCombatLockdown() return M.combat end
function IsModifiedClick() return false end
function GetCursorPosition() return 500, 400 end
function PlaySound() end
function GetLocale() return "enUS" end
function ChatEdit_InsertLink() return true end
function HideUIPanel(f) f:Hide() end
function ShowUIPanel(f) f:Show() end
function ToggleWorldMap() if WorldMapFrame:IsShown() then WorldMapFrame:Hide() else WorldMapFrame:Show() end end

-- where the character is
M.instance = nil    -- { name, kind, id }
M.subzone = ""
function GetInstanceInfo()
	local i = M.instance
	if i then return i.name, i.kind, 1, "Normal", 5, 0, false, i.id end
	return "Kalimdor", "none", 0, "", 0, 0, false, 1
end
function IsInInstance() return M.instance ~= nil, M.instance and M.instance.kind or "none" end
function GetSubZoneText() return M.subzone end
function GetMinimapZoneText() return M.subzone end

-- units: hostile creatures are secret, like the Forever client
M.units = {}   -- [token] = { name, guid, level, dead, player }
local function U(token) return M.units[token] end
function UnitExists(t) return U(t) ~= nil end
function UnitGUID(t) local u = U(t) if not u then return end return u.player and u.guid or Secret() end
function UnitName(t) local u = U(t) if not u then return end return u.player and u.name or Secret() end
function UnitIsPlayer(t) local u = U(t) return u and u.player or false end
function UnitPlayerControlled(t) local u = U(t) return u and u.player or false end
function UnitCanAttack(_, t) local u = U(t) return u and not u.player or false end
M.group, M.raid = 0, false   -- how many are in the group (the character too), and whether it is a raid
function GetNumGroupMembers() return M.group end
function IsInRaid() return M.raid end
M.questsDone, M.questsOn, M.questLog, M.questGoals = {}, {}, {}, {}
C_QuestLog = {
	IsQuestFlaggedCompleted = function(id) return M.questsDone[id] or false end,
	IsOnQuest = function(id) return M.questsOn[id] or false end,
	GetNumQuestLogEntries = function() return #M.questLog end,
	GetInfo = function(i) return M.questLog[i] end,
	GetQuestObjectives = function(id) return M.questGoals[id] end,
}
function UnitFactionGroup() return "Alliance", "Alliance" end
function UnitClass() return "Warrior", "WARRIOR", 1 end
function UnitLevel(t) local u = U(t) return u and u.level or 0 end
function UnitClassification() return "elite" end
function UnitCreatureType() return "Humanoid" end
function UnitIsDead(t) local u = U(t) return u and u.dead or false end
function UnitAffectingCombat() return M.combat end

-- lockouts: { { name, reset (s left), total, done, mapID }, ... }
M.saved = {}
function GetNumSavedInstances() return #M.saved end
function GetSavedInstanceInfo(i)
	local l = M.saved[i]
	return l.name, 1, l.reset, 1, true, false, 0, true, 40, "Normal", l.total, l.done, false, l.mapID
end
function RequestRaidInfo() M.fire("UPDATE_INSTANCE_INFO") end

-- loot
M.loot = {}    -- { { link, guid }, ... }
function GetNumLootItems() return #M.loot end
function GetLootSlotLink(i) return M.loot[i].link end
function GetLootSourceInfo(i) return M.loot[i].guid, 1 end

-- items and spells
C_Item = {
	GetItemQualityByID = function() return 2 end,
	GetItemInfo = function(id) return "Item " .. tostring(id), nil, 2 end,
	GetItemIconByID = function() return 134400 end,
	-- 10978 is an enchanting material (Small Glimmering Shard)
	GetItemInfoInstant = function(id)
		if id == 10978 then return id, "Tradeskill", "Enchanting", "", 134400, 7, 12 end
		return id, "Armor", "Cloth", "", 134400, 4, 1
	end,
}
function GetItemInfo(id) return "Item " .. tostring(id), nil, 2 end
function GetItemIcon() return 134400 end
C_Spell = {
	GetSpellName = function(id) return "Spell " .. id end,
	GetSpellDescription = function(id) return "What spell " .. id .. " does." end,
	GetSpellTexture = function() return 136243 end,
}
C_AddOns = { GetAddOnMetadata = function(_, field) return field == 'Version' and 'test' or nil end }
C_TooltipInfo = { GetHyperlink = function() return nil end }
-- addons are told of each item tooltip after the game has filled it in
Enum = { TooltipDataType = { Item = 0, Unit = 2 } }
M.tooltipCalls = {}
TooltipDataProcessor = {
	AddTooltipPostCall = function(kind, fn)
		M.tooltipCalls[kind] = M.tooltipCalls[kind] or {}
		table.insert(M.tooltipCalls[kind], fn)
	end,
}
-- show an item's tooltip as the game would: its own lines, then the addons'
function M.itemTooltip(id, tip)
	tip = tip or GameTooltip
	tip:ClearLines()
	tip:AddLine("Item " .. id)
	for _, fn in ipairs(M.tooltipCalls[Enum.TooltipDataType.Item] or {}) do fn(tip, { id = id, type = 0 }) end
	return table.concat(tip.__lines, "\n")
end

-- anything else the addon reaches for is noted, so the test can report it
setmetatable(_G, { __index = function(_, k) M.missing[k] = true end })

---------------------------------------------------------------------------
-- Driving it
---------------------------------------------------------------------------
function M.fire(event, ...)
	for _, f in ipairs(M.frames) do
		if f.__events[event] and f.__scripts.OnEvent then f.__scripts.OnEvent(f, event, ...) end
	end
end

-- let seconds pass, running the timers that fall due
function M.wait(sec)
	local target = M.now + sec
	while true do
		local best
		for i, t in ipairs(M.timers) do
			if t.at <= target and (not best or t.at < M.timers[best].at) then best = i end
		end
		if not best then break end
		local t = table.remove(M.timers, best)
		M.now = math.max(M.now, t.at)
		t.fn()
	end
	M.clock = M.clock + sec
	M.now = target
end

function M.slash(text)
	SlashCmdList["FIELDNOTES"](text)
end

return M
