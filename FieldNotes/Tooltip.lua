-- Item tooltips: an item the journal has noted says, wherever it is shown (in
-- your bags, a chat link, a roll), where it was found and who carried it.
-- Preferences → "Finds on item tooltips" turns this off.
local _, ns = ...

local issecret = issecretvalue or function() return false end
local PLACES_MAX = 3

-- [item id] = { { inst = the instance's record, it = its loot entry }, ... },
-- made on first use and again whenever the journal changes
local found

local function Index()
	if found then return found end
	found = {}
	for id, inst in pairs(ns.db.instances) do
		if id ~= "maptest" then
			for item, it in pairs(inst.loot or {}) do
				local list = found[item]
				if not list then
					list = {}
					found[item] = list
				end
				list[#list + 1] = { inst = inst, it = it }
			end
		end
	end
	-- the place it was found in most often first
	for _, list in pairs(found) do
		table.sort(list, function(a, b)
			if a.it.n ~= b.it.n then return a.it.n > b.it.n end
			return a.inst.name < b.inst.name
		end)
	end
	return found
end

ns:On("FN_DATA", function() found = nil end)

-- Who carried it: the boss it is credited to, else the creature.
local function Source(inst, it)
	local m = it.npc and inst.mobs[it.npc]
	local eid = (m and m.enc) or it.enc
	local b = eid and inst.bosses[eid]
	if b then return b.name end
	return m and m.name
end

-- The lines for an item, as the tooltip shows them; nil if it was never noted.
function ns:FoundLines(item)
	if not (self.db and type(item) == "number") then return end
	local list = Index()[item]
	if not list then return end
	local out = {}
	for i, f in ipairs(list) do
		if i > PLACES_MAX then
			local more = #list - PLACES_MAX
			out[#out + 1] = ("and in %d other %s."):format(more, more == 1 and "place" or "places")
			break
		end
		local from = Source(f.inst, f.it)
		out[#out + 1] = "found in " .. f.inst.name .. (from and (", from " .. from) or "")
			.. (f.it.n > 1 and (", " .. f.it.n .. " times") or "") .. "."
	end
	return out
end

local function Add(tooltip, item)
	if not (ns.db and ns.db.settings.itemTips) or ns.ownTip then return end
	if issecret(item) or type(item) ~= "number" or type(tooltip) ~= "table" or not tooltip.AddLine then return end
	local lines = ns:FoundLines(item)
	if not lines then return end
	for i, text in ipairs(lines) do
		tooltip:AddLine((i == 1 and "|cffc8a878Field Notes:|r " or "") .. text, 0.86, 0.78, 0.62, true)
	end
end

-- The game tells addons of every item tooltip one of two ways, by client.
if TooltipDataProcessor and TooltipDataProcessor.AddTooltipPostCall and Enum and Enum.TooltipDataType
	and Enum.TooltipDataType.Item then
	TooltipDataProcessor.AddTooltipPostCall(Enum.TooltipDataType.Item, function(tooltip, data)
		pcall(Add, tooltip, type(data) == "table" and data.id or nil)
	end)
else
	local function Hook(tooltip)
		if not (tooltip and tooltip.HookScript and tooltip.GetItem) then return end
		pcall(tooltip.HookScript, tooltip, "OnTooltipSetItem", function(self)
			pcall(function()
				local _, link = self:GetItem()
				if issecret(link) or type(link) ~= "string" then return end
				Add(self, tonumber(link:match("item:(%d+)")))
			end)
		end)
	end
	Hook(GameTooltip)
	Hook(ItemRefTooltip)
end
