-- The journal window: a contents list on the left, the selected page on the
-- right, and a box for your own notes under it. Built on first open.
local _, ns = ...

local WIDTH, HEIGHT = 800, 560
local INDEX_W, PAGE_W = 172, 512  -- text widths inside the two panes
local NOTES_H = 86
local MAP_W = PAGE_W
local MAP_H = math.floor(PAGE_W * 668 / 1002 + 0.5)

local INK = { 0.20, 0.12, 0.05 }
local FADED = { 0.45, 0.34, 0.20 }
local FADED_HEX = "|cff735733"
local QUESTION = "Interface\\Icons\\INV_Misc_QuestionMark"
local DONE = "|TInterface\\RaidFrame\\ReadyCheck-Ready:12|t "
local OPEN = "|TInterface\\RaidFrame\\ReadyCheck-Waiting:12|t "

local frame, index, page, notes
local canvas          -- the map sheet, a child of the page's scroll area
local sel = {}         -- inst (instanceID), kind ("overview" | "boss" | "map" | "bestiary" | "spoils"), key
local shownKey         -- the page last drawn, to reset scrolling when it changes
local Refresh

local function Font(name)
	return _G[name] or GameFontNormal
end

---------------------------------------------------------------------------
-- A scrolling list of lines. list:Set({ line, ... }); a line is a table:
--   text, font, color, indent, gap (space above), rule (underline),
--   icon, iconSize, selected, click = fn, link = item link,
--   spell = spell ID (tooltip), tip = tooltip text,
--   space = extra empty height below the text (the map sheet sits there)
---------------------------------------------------------------------------
local function RowEnter(self)
	local l = self.line
	if not (l.link or l.spell or l.tip) then return end
	GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
	local ok
	if l.link then
		ok = pcall(GameTooltip.SetHyperlink, GameTooltip, l.link)
	elseif type(l.spell) == "number" and GameTooltip.SetSpellByID then
		ok = pcall(GameTooltip.SetSpellByID, GameTooltip, l.spell)
	end
	if not ok or GameTooltip:NumLines() == 0 then
		GameTooltip:ClearLines()
		GameTooltip:AddLine(l.tip or l.name or "")
	end
	GameTooltip:Show()
end

local function RowLeave()
	GameTooltip:Hide()
end

local function RowClick(self)
	local l = self.line
	if l.link and IsModifiedClick and IsModifiedClick("CHATLINK") then
		local insert = (ChatFrameUtil and ChatFrameUtil.InsertLink) or ChatEdit_InsertLink
		if insert then insert(l.link) end
	elseif l.click then
		l.click()
	end
end

local function NewRow(list)
	local row = CreateFrame("Button", nil, list.child)
	row.mark = row:CreateTexture(nil, "BACKGROUND")
	row.mark:SetAllPoints()
	row.mark:SetColorTexture(0.35, 0.22, 0.08, 0.20)
	row.icon = row:CreateTexture(nil, "ARTWORK")
	row.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	row.text = row:CreateFontString(nil, "ARTWORK", "GameFontNormal")
	row.text:SetJustifyH("LEFT")
	row.text:SetJustifyV("TOP")
	row.text:SetWordWrap(true)
	row.rule = row:CreateTexture(nil, "ARTWORK")
	row.rule:SetColorTexture(0.35, 0.24, 0.12, 0.55)
	row.rule:SetHeight(1)
	row.rule:SetPoint("BOTTOMLEFT")
	row.rule:SetPoint("BOTTOMRIGHT")
	local hl = row:CreateTexture(nil, "HIGHLIGHT")
	hl:SetAllPoints()
	hl:SetColorTexture(0.35, 0.22, 0.08, 0.12)
	row:SetScript("OnEnter", RowEnter)
	row:SetScript("OnLeave", RowLeave)
	row:SetScript("OnClick", RowClick)
	return row
end

local function ListSet(list, lines)
	local y = 0
	for i, line in ipairs(lines) do
		local row = list.rows[i]
		if not row then
			row = NewRow(list)
			list.rows[i] = row
		end
		row.line = line
		y = y + (line.gap or 0)
		local indent = line.indent or 0
		local size = line.icon and (line.iconSize or 18) or 0
		if line.icon then
			row.icon:SetTexture(line.icon)
			row.icon:SetSize(size, size)
			row.icon:ClearAllPoints()
			row.icon:SetPoint("TOPLEFT", indent, -2)
			row.icon:Show()
		else
			row.icon:Hide()
		end
		local tx = indent + (size > 0 and size + 6 or 0)
		local c = line.color or INK
		row.text:SetFontObject(Font(line.font or "QuestFont"))
		row.text:SetTextColor(c[1], c[2], c[3])
		row.text:ClearAllPoints()
		row.text:SetPoint("TOPLEFT", tx, -2)
		row.text:SetWidth(list.width - tx)
		row.text:SetText(line.text or "")
		local h = math.max(row.text:GetStringHeight() or 0, size) + 4 + (line.rule and 3 or 0) + (line.space or 0)
		row:ClearAllPoints()
		row:SetPoint("TOPLEFT", 0, -y)
		row:SetSize(list.width, h)
		if line.rule then row.rule:Show() else row.rule:Hide() end
		if line.selected then row.mark:Show() else row.mark:Hide() end
		row:EnableMouse((line.click or line.link or line.spell or line.tip) and true or false)
		row:Show()
		y = y + h
	end
	for i = #lines + 1, #list.rows do list.rows[i]:Hide() end
	list.child:SetHeight(math.max(y, 1))
end

local function Paper(parent, shade)
	local t = parent:CreateTexture(nil, "BACKGROUND")
	t:SetAllPoints()
	t:SetColorTexture(0.90 * shade, 0.83 * shade, 0.68 * shade, 1)
end

-- A parchment pane with a scrolling list inside it.
local function CreateList(name, width)
	local pane = CreateFrame("Frame", nil, frame)
	local sf = CreateFrame("ScrollFrame", name, pane, "UIPanelScrollFrameTemplate")
	sf:SetPoint("TOPLEFT", 10, -8)
	sf:SetPoint("BOTTOMRIGHT", -28, 8) -- the template's scroll bar sits outside, to the right
	local child = CreateFrame("Frame", nil, sf)
	child:SetSize(width, 1)
	sf:SetScrollChild(child)
	return { pane = pane, sf = sf, child = child, rows = {}, width = width, Set = ListSet }
end

---------------------------------------------------------------------------
-- Page text
---------------------------------------------------------------------------
local SCHOOL = { [1] = "physical", [2] = "holy", [4] = "fire", [8] = "nature", [16] = "frost", [32] = "shadow", [64] = "arcane" }
local RANK = { elite = "Elite", rareelite = "Rare elite", rare = "Rare", worldboss = "Boss" }

local function H1(lines, text)
	lines[#lines + 1] = { text = text, font = "QuestTitleFont" }
end

local function H2(lines, text)
	lines[#lines + 1] = { text = text, font = "GameFontNormalLarge", rule = true, gap = 14 }
end

local function Body(lines, text, indent)
	lines[#lines + 1] = { text = text, indent = indent }
end

local function Faded(lines, text, indent)
	lines[#lines + 1] = { text = text, color = FADED, font = "GameFontNormalSmall", indent = indent }
end

local function Plural(n, one, many)
	return n .. " " .. (n == 1 and one or many)
end

local function SpellIcon(id)
	local tex
	if type(id) == "number" then
		if C_Spell and C_Spell.GetSpellTexture then tex = C_Spell.GetSpellTexture(id) end
		if not tex and GetSpellTexture then tex = GetSpellTexture(id) end
	end
	return tex or QUESTION
end

local function SpellName(id)
	local name = C_Spell and C_Spell.GetSpellName and C_Spell.GetSpellName(id)
	if not name and GetSpellInfo then name = GetSpellInfo(id) end
	if name and name ~= "" then return name end
end

-- The spell's own description, shortened; nil until the client has it loaded.
local function SpellText(id)
	local text = C_Spell and C_Spell.GetSpellDescription and C_Spell.GetSpellDescription(id)
	if not text and GetSpellDescription then text = GetSpellDescription(id) end
	if not text or text == "" then return end
	text = text:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("%s+", " ")
	if #text > 170 then text = text:sub(1, 167):gsub("%s+%S*$", "") .. "..." end
	return text
end

local function ItemIcon(id)
	local tex
	if C_Item and C_Item.GetItemIconByID then tex = C_Item.GetItemIconByID(id) end
	if not tex and GetItemIcon then tex = GetItemIcon(id) end
	return tex or QUESTION
end

-- What has been observed about a spell, as a sentence.
local function Remark(s)
	local t = {}
	if s.cast then t[#t + 1] = "has a cast time" end
	if s.channel then t[#t + 1] = "is channelled" end
	if s.dmg then
		local school = SCHOOL[s.school or 0]
		t[#t + 1] = ("struck for up to %d%s"):format(s.dmg, school and (" " .. school) or "")
	end
	if s.tick then t[#t + 1] = ("burns for up to %d a tick"):format(s.tick) end
	if s.debuff then t[#t + 1] = "leaves an affliction" end
	if s.buff then t[#t + 1] = "empowers the enemy" end
	if s.heal then t[#t + 1] = "heals" end
	if s.summon then t[#t + 1] = "summons " .. s.summon end
	if s.kick then t[#t + 1] = "can be interrupted" end
	if #t == 0 then return "Seen used." end
	local text = table.concat(t, ", ")
	return text:sub(1, 1):upper() .. text:sub(2) .. "."
end

local function MobTag(m)
	local t = {}
	local rank = RANK[m.cls]
	if rank and m.type then
		t[#t + 1] = rank .. " " .. m.type:lower()
	elseif rank or m.type then
		t[#t + 1] = rank or m.type
	end
	if m.skull then
		t[#t + 1] = "level ??"
	elseif m.lo then
		t[#t + 1] = m.lo == m.hi and ("level " .. m.lo) or ("level " .. m.lo .. "-" .. m.hi)
	end
	if m.kills then t[#t + 1] = "slain " .. m.kills end
	return table.concat(t, ", ")
end

local function MobLines(lines, m, showName)
	if showName then
		lines[#lines + 1] = { text = m.name, font = "GameFontNormal", gap = 10 }
	end
	local tag = MobTag(m)
	if tag ~= "" then Faded(lines, tag) end
	if not m.fought then
		Faded(lines, "Seen, but not yet fought.")
		return
	end
	if m.melee then Body(lines, ("Its blows land for up to %d."):format(m.melee), 8) end
	for _, key in ipairs(m.order) do
		local s = m.spells[key]
		lines[#lines + 1] = {
			text = s.name .. "\n" .. FADED_HEX .. Remark(s) .. "|r",
			icon = SpellIcon(key), iconSize = 26, indent = 8, gap = 4,
			spell = key, name = s.name,
		}
	end
	if #m.order == 0 and not m.melee then Faded(lines, "Fought, but nothing of note observed.") end
end

local function LootLines(lines, inst, filter)
	local any
	for _, id in ipairs(inst.lootOrder) do
		local it = inst.loot[id]
		if not filter or filter(it) then
			any = true
			local from
			if not filter then
				local m = it.npc and inst.mobs[it.npc]
				local b = (m and m.enc and inst.bosses[m.enc]) or (it.enc and inst.bosses[it.enc])
				from = (b and b.name) or (m and m.name)
			end
			local sub = (from and ("From " .. from .. ", ") or "") .. "found " .. (it.n == 1 and "once" or (it.n .. " times")) .. "."
			if from then sub = sub:sub(1, 1):upper() .. sub:sub(2) else sub = "F" .. sub:sub(2) end
			lines[#lines + 1] = {
				text = it.link .. "\n" .. FADED_HEX .. sub .. "|r",
				icon = ItemIcon(id), iconSize = 26, indent = 8, gap = 4, link = it.link,
			}
		end
	end
	return any
end

local function Select(inst, kind, key)
	sel.inst, sel.kind, sel.key = inst, kind, key
	Refresh()
end

local function BlankPage(lines)
	H1(lines, "Field Notes")
	Body(lines, "\nThese pages are blank.\n\nNothing is written here until you have seen it yourself. Step into a dungeon or raid and the journal fills in as you go: the halls you walk, the creatures you meet, what they do to you, who leads them, and what they carry.")
end

local function OverviewPage(lines, id, inst)
	H1(lines, inst.name)
	Faded(lines, ("%s. First entered %s, %s."):format(inst.kind == "raid" and "Raid" or "Dungeon",
		ns:Day(inst.first), Plural(inst.visits, "visit", "visits")))

	H2(lines, "Halls and chambers")
	if #inst.areas == 0 then Faded(lines, "Nothing noted yet.") end
	for _, a in ipairs(inst.areas) do Body(lines, a.name, 8) end

	H2(lines, "Adversaries")
	if #inst.bossOrder == 0 then Faded(lines, "No one of note encountered yet.") end
	for _, eid in ipairs(inst.bossOrder) do
		local b = inst.bosses[eid]
		lines[#lines + 1] = {
			text = (b.kills > 0 and DONE or OPEN) .. b.name .. FADED_HEX ..
				(b.kills > 0 and ("  defeated " .. (b.kills == 1 and "once" or (b.kills .. " times"))) or "  not yet defeated") .. "|r",
			indent = 8, click = function() Select(id, "boss", eid) end,
		}
	end

	H2(lines, "Diary")
	local day
	local log = inst.log
	for i = #log, math.max(1, #log - 59), -1 do
		local t, text = log[i][1], log[i][2]
		local d = ns:Day(t)
		if d ~= day then
			day = d
			lines[#lines + 1] = { text = d, font = "GameFontNormalSmall", color = FADED, gap = 6 }
		end
		Body(lines, FADED_HEX .. date("%H:%M", t) .. "|r  " .. text, 8)
	end

	lines[#lines + 1] = {
		text = "Tear these pages out", font = "GameFontNormalSmall", color = FADED, gap = 24,
		tip = "Erase everything noted about " .. inst.name .. ".",
		click = function() StaticPopup_Show("FIELDNOTES_TEAR", inst.name, nil, id) end,
	}
end

local function BossPage(lines, inst, eid)
	local b = inst.bosses[eid]
	H1(lines, b.name)
	local t = { "First faced " .. ns:Day(b.first), Plural(b.pulls, "attempt", "attempts") }
	if b.kills > 0 then t[#t + 1] = Plural(b.kills, "victory", "victories") end
	if b.wipes > 0 then t[#t + 1] = Plural(b.wipes, "defeat", "defeats") end
	if b.best then t[#t + 1] = "swiftest victory " .. ns:Clock(b.best) end
	Faded(lines, table.concat(t, ", ") .. ".")
	if b.kills == 0 then Body(lines, "Not yet defeated.") end

	-- everything fought in this encounter, the boss itself first
	local mobs = {}
	for _, npc in ipairs(inst.mobOrder) do
		local m = inst.mobs[npc]
		if m.enc == eid then
			if m.name == b.name then table.insert(mobs, 1, m) else mobs[#mobs + 1] = m end
		end
	end
	H2(lines, "Observed in battle")
	if #mobs == 0 then Faded(lines, "Nothing observed yet.") end
	for i, m in ipairs(mobs) do
		MobLines(lines, m, #mobs > 1 or m.name ~= b.name)
	end

	-- What is known of the boss from elsewhere (Abilities.lua), written in once
	-- it is defeated: the game hides most of a fight from addons.
	local known = ns.Abilities[eid] or ns.AbilitiesByName[ns:AreaKey(b.name)]
	if known then
		H2(lines, "Known abilities")
		if b.kills == 0 then
			Faded(lines, "To be written down once it is defeated.")
		else
			local observed = {}
			for _, m in ipairs(mobs) do
				for id in pairs(m.spells) do observed[id] = true end
			end
			local any
			for _, id in ipairs(known) do
				local name = not observed[id] and SpellName(id)
				if name then
					any = true
					local text = SpellText(id)
					lines[#lines + 1] = {
						text = name .. (text and ("\n" .. FADED_HEX .. text .. "|r") or ""),
						icon = SpellIcon(id), iconSize = 26, indent = 8, gap = 4,
						spell = id, name = name,
					}
				end
			end
			if not any then Faded(lines, "Nothing beyond what was observed.") end
		end
	end

	H2(lines, "Spoils")
	local any = LootLines(lines, inst, function(it)
		local m = it.npc and inst.mobs[it.npc]
		return it.enc == eid or (m and m.enc == eid)
	end)
	if not any then Faded(lines, "Nothing found yet.") end
end

local function BestiaryPage(lines, inst)
	H1(lines, "Bestiary")
	Faded(lines, "The creatures of " .. inst.name .. ".")
	local any
	for _, npc in ipairs(inst.mobOrder) do
		local m = inst.mobs[npc]
		if not m.enc then
			any = true
			MobLines(lines, m, true)
		end
	end
	if not any then Body(lines, "\nNo creatures noted yet.") end
end

---------------------------------------------------------------------------
-- The map: blank parchment, with each recorded area's part of the game's own
-- map tiles shown through that area's mask. Once every area of a sheet is
-- found, the plain tiles show instead.
---------------------------------------------------------------------------
local function CreateCanvas()
	canvas = CreateFrame("Frame", nil, page.child)
	canvas:SetSize(MAP_W, MAP_H)
	local blank = canvas:CreateTexture(nil, "BACKGROUND")
	blank:SetAllPoints()
	blank:SetTexture(ns.MAP_BLANK)
	canvas.cache = {}  -- [piece or floor] = { texture, ... }, made on first use
	canvas.shown = {}
end

-- One texture per map tile that overlaps the box (in sheet pixels), cropped to it.
local function TileTextures(floor, x, y, w, h, mask)
	local list = {}
	local T = floor.tile or ns.MAP_TILE
	local sx, sy = MAP_W / ns.MAP_REF_W, MAP_H / ns.MAP_REF_H
	local rows = math.ceil(#floor.tiles / floor.cols)
	for row = 0, rows - 1 do
		for col = 0, floor.cols - 1 do
			local l, t = math.max(x, col * T), math.max(y, row * T)
			local r = math.min(x + w, (col + 1) * T, ns.MAP_REF_W)
			local b = math.min(y + h, (row + 1) * T, ns.MAP_REF_H)
			if r > l and b > t then
				local tex = canvas:CreateTexture(nil, "ARTWORK")
				tex:SetTexture(floor.tiles[row * floor.cols + col + 1])
				tex:SetTexCoord((l - col * T) / T, (r - col * T) / T, (t - row * T) / T, (b - row * T) / T)
				tex:SetPoint("TOPLEFT", canvas, "TOPLEFT", l * sx, -t * sy)
				tex:SetSize((r - l) * sx, (b - t) * sy)
				if mask then tex:AddMaskTexture(mask) end
				tex:Hide()
				list[#list + 1] = tex
			end
		end
	end
	return list
end

local function PieceTextures(floor, piece)
	local list = canvas.cache[piece]
	if not list then
		local mask
		-- without mask textures the area shows as a plain rectangle
		if canvas.CreateMaskTexture then
			local sx, sy = MAP_W / ns.MAP_REF_W, MAP_H / ns.MAP_REF_H
			mask = canvas:CreateMaskTexture()
			mask:SetTexture(piece.mask, "CLAMPTOBLACKADDITIVE", "CLAMPTOBLACKADDITIVE")
			mask:SetPoint("TOPLEFT", canvas, "TOPLEFT", piece.x * sx, -piece.y * sy)
			mask:SetSize(piece.w * sx, piece.h * sy)
		end
		list = TileTextures(floor, piece.x, piece.y, piece.w, piece.h, mask)
		canvas.cache[piece] = list
	end
	return list
end

local function DrawMap(sheet)
	for _, tex in ipairs(canvas.shown) do tex:Hide() end
	local shown = {}
	local function Show(list)
		for _, tex in ipairs(list) do
			tex:Show()
			shown[#shown + 1] = tex
		end
	end
	local floor = sheet.floor
	if sheet.complete then
		if not canvas.cache[floor] then
			canvas.cache[floor] = TileTextures(floor, 0, 0, ns.MAP_REF_W, ns.MAP_REF_H)
		end
		Show(canvas.cache[floor])
	else
		for _, piece in ipairs(sheet.pieces) do Show(PieceTextures(floor, piece)) end
	end
	canvas.shown = shown
end

local SHEET = { "First sheet", "Second sheet", "Third sheet", "Fourth sheet", "Fifth sheet", "Sixth sheet" }

local function MapPage(lines, id, inst)
	H1(lines, "Map")
	Faded(lines, "What you have charted of " .. inst.name .. ".")

	-- the pieces found on each floor, and areas the map has no place for
	-- a piece is found by walking into its area, or by fighting someone who lives there
	local floors = ns.Maps[id]
	local known = {}
	for _, a in ipairs(inst.areas) do known[#known + 1] = a.name end
	for _, b in pairs(inst.bosses) do known[#known + 1] = b.name end
	for _, m in pairs(inst.mobs) do
		if m.fought then known[#known + 1] = m.name end
	end
	local sheets, placed = {}, {}
	for f, floor in ipairs(floors) do
		local pieces, seen, found = {}, {}, 0
		if floor.decor then pieces[#pieces + 1] = floor.decor end
		if floor.start then pieces[#pieces + 1] = floor.start end
		for _, name in ipairs(known) do
			local piece = floor.areas[ns:AreaKey(name)]
			if piece then
				placed[name] = true
				if not seen[piece] then
					seen[piece] = true
					found = found + 1
					pieces[#pieces + 1] = piece
				end
			end
		end
		if floor.start or found > 0 then
			sheets[#sheets + 1] = { f = f, floor = floor, pieces = pieces, found = found, complete = found >= floor.count }
		end
	end
	-- An instance with several entrances has an entrance on several sheets.
	-- Once something is found, keep only the sheets you have been on.
	local explored = {}
	for _, sh in ipairs(sheets) do
		if sh.found > 0 then explored[#explored + 1] = sh end
	end
	if #explored > 0 then sheets = explored end

	local shown
	for _, sh in ipairs(sheets) do
		if sh.f == sel.key then shown = sh end
	end
	shown = shown or sheets[1]
	if not shown then
		Body(lines, "\nNothing charted yet.")
		return
	end
	sel.key = shown.f
	if #sheets > 1 then
		for _, sh in ipairs(sheets) do
			lines[#lines + 1] = {
				text = SHEET[sh.f] or ("Sheet " .. sh.f), font = "GameFontNormalSmall",
				selected = sh == shown, gap = sh == sheets[1] and 6 or 0,
				click = function() Select(id, "map", sh.f) end,
			}
		end
	end
	lines[#lines + 1] = { text = "", gap = 6, space = MAP_H, map = shown }

	local loose = {}
	for _, a in ipairs(inst.areas) do
		if not placed[a.name] then loose[#loose + 1] = a.name end
	end
	if #loose > 0 then
		Faded(lines, "Visited, but not yet placed on the map: " .. table.concat(loose, ", ") .. ".")
	end
end

local function SpoilsPage(lines, inst)
	H1(lines, "Spoils")
	Faded(lines, "What has been found in " .. inst.name .. ". Shift-click to link an item.")
	if not LootLines(lines, inst) then Body(lines, "\nNothing found yet.") end
end

---------------------------------------------------------------------------
-- Contents list
---------------------------------------------------------------------------
local function Count(t, skip)
	local n = 0
	for _, v in pairs(t) do
		if not (skip and skip(v)) then n = n + 1 end
	end
	return n
end

local function IndexLines()
	local lines = {}
	local ids = {}
	for id in pairs(ns.db.instances) do ids[#ids + 1] = id end
	table.sort(ids, function(a, b)
		local ia, ib = ns.db.instances[a], ns.db.instances[b]
		if (ia.last or 0) ~= (ib.last or 0) then return (ia.last or 0) > (ib.last or 0) end
		return tostring(a) < tostring(b)
	end)
	if #ids == 0 then
		lines[1] = { text = "No pages yet.", color = FADED, font = "GameFontNormalSmall" }
		return lines
	end
	for _, id in ipairs(ids) do
		local inst = ns.db.instances[id]
		local open = sel.inst == id
		lines[#lines + 1] = {
			text = inst.name, font = "GameFontNormal", gap = 4,
			selected = open and sel.kind == "overview",
			click = function() Select(id, "overview") end,
		}
		if open then
			for _, eid in ipairs(inst.bossOrder) do
				local b = inst.bosses[eid]
				lines[#lines + 1] = {
					text = (b.kills > 0 and DONE or OPEN) .. b.name, font = "GameFontNormalSmall", indent = 10,
					selected = sel.kind == "boss" and sel.key == eid,
					click = function() Select(id, "boss", eid) end,
				}
			end
			if ns.Maps[id] then
				lines[#lines + 1] = {
					text = "Map", font = "GameFontNormalSmall", indent = 10, selected = sel.kind == "map",
					click = function() Select(id, "map") end,
				}
			end
			lines[#lines + 1] = {
				text = ("Bestiary (%d)"):format(Count(inst.mobs, function(m) return m.enc end)),
				font = "GameFontNormalSmall", indent = 10, selected = sel.kind == "bestiary",
				click = function() Select(id, "bestiary") end,
			}
			lines[#lines + 1] = {
				text = ("Spoils (%d)"):format(#inst.lootOrder),
				font = "GameFontNormalSmall", indent = 10, selected = sel.kind == "spoils",
				click = function() Select(id, "spoils") end,
			}
		end
	end
	return lines
end

---------------------------------------------------------------------------
-- Your own notes: on the boss when a boss page is open, else on the instance.
---------------------------------------------------------------------------
local function NotesTarget(inst)
	if not inst then return end
	local b = sel.kind == "boss" and inst.bosses[sel.key]
	if b then return b, b.name end
	return inst, inst.name
end

local function CreateNotes(parent)
	local box = CreateFrame("Frame", nil, parent)
	box:SetHeight(NOTES_H)
	local line = box:CreateTexture(nil, "ARTWORK")
	line:SetColorTexture(0.35, 0.24, 0.12, 0.55)
	line:SetHeight(1)
	line:SetPoint("TOPLEFT")
	line:SetPoint("TOPRIGHT")
	box.label = box:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
	box.label:SetPoint("TOPLEFT", 0, -5)
	box.label:SetTextColor(FADED[1], FADED[2], FADED[3])

	local sf = CreateFrame("ScrollFrame", nil, box)
	sf:SetPoint("TOPLEFT", 0, -20)
	sf:SetPoint("BOTTOMRIGHT", 0, 2)
	local edit = CreateFrame("EditBox", nil, sf)
	edit:SetMultiLine(true)
	edit:SetAutoFocus(false)
	edit:SetMaxLetters(1000)
	edit:SetFontObject(Font("QuestFont"))
	edit:SetTextColor(INK[1], INK[2], INK[3])
	edit:SetWidth(PAGE_W)
	edit:SetHeight(NOTES_H - 22)
	sf:SetScrollChild(edit)
	edit:SetScript("OnEscapePressed", edit.ClearFocus)
	edit:SetScript("OnTextChanged", function(self, user)
		if user and box.target then
			local text = self:GetText()
			box.target.note = text ~= "" and text or nil
		end
	end)
	-- keep the cursor line in view
	edit:SetScript("OnCursorChanged", function(_, _, y, _, h)
		local top, view = sf:GetVerticalScroll(), sf:GetHeight()
		if -y < top then
			sf:SetVerticalScroll(-y)
		elseif -y + h > top + view then
			sf:SetVerticalScroll(-y + h - view)
		end
	end)
	sf:EnableMouse(true)
	sf:SetScript("OnMouseDown", function() edit:SetFocus() end)
	box.edit = edit
	return box
end

---------------------------------------------------------------------------
-- Window
---------------------------------------------------------------------------
StaticPopupDialogs["FIELDNOTES_TEAR"] = {
	text = "Tear the pages on %s out of your journal? Everything noted there is lost.",
	button1 = YES,
	button2 = NO,
	OnAccept = function(_, id) ns:Forget(id) end,
	timeout = 0,
	whileDead = true,
	hideOnEscape = true,
}

Refresh = function()
	if not (frame and frame:IsShown()) then return end
	local inst = sel.inst and ns.db.instances[sel.inst]
	if not inst then
		sel.inst, sel.kind, sel.key = nil, nil, nil
	elseif sel.kind == "boss" and not inst.bosses[sel.key] then
		sel.kind, sel.key = "overview", nil
	elseif sel.kind == "map" and not ns.Maps[sel.inst] then
		sel.kind, sel.key = "overview", nil
	end

	index:Set(IndexLines())

	local lines = {}
	if not inst then
		BlankPage(lines)
	elseif sel.kind == "boss" then
		BossPage(lines, inst, sel.key)
	elseif sel.kind == "map" then
		MapPage(lines, sel.inst, inst)
	elseif sel.kind == "bestiary" then
		BestiaryPage(lines, inst)
	elseif sel.kind == "spoils" then
		SpoilsPage(lines, inst)
	else
		OverviewPage(lines, sel.inst, inst)
	end
	page:Set(lines)

	-- the map sheet sits in the space its line reserved
	local sheet
	for i, line in ipairs(lines) do
		if line.map then
			sheet = line.map
			if not canvas then CreateCanvas() end
			canvas:ClearAllPoints()
			canvas:SetPoint("TOPLEFT", page.rows[i], "TOPLEFT", 0, -4)
			DrawMap(sheet)
			canvas:Show()
		end
	end
	if canvas and not sheet then canvas:Hide() end

	local key = tostring(sel.inst) .. ":" .. tostring(sel.kind) .. ":" .. tostring(sel.key)
	if key ~= shownKey then
		shownKey = key
		page.sf:SetVerticalScroll(0)
	end

	-- only touch the notes box when its subject changes, never while typing
	local target, name = NotesTarget(inst)
	if target ~= notes.target then
		notes.edit:ClearFocus()
		notes.target = target
		notes.edit:SetText(target and target.note or "")
		notes.label:SetText(target and ("My notes on " .. name) or "")
	end
	if target then notes:Show() else notes:Hide() end
end

local function CreateJournal()
	frame = CreateFrame("Frame", "FieldNotesJournal", UIParent, "BasicFrameTemplateWithInset")
	frame:SetSize(WIDTH, HEIGHT)
	frame:SetPoint("CENTER")
	frame:SetFrameStrata("HIGH")
	frame:SetToplevel(true)
	frame:SetClampedToScreen(true)
	frame:SetMovable(true)
	frame:EnableMouse(true)
	frame:RegisterForDrag("LeftButton")
	frame:SetScript("OnDragStart", frame.StartMoving)
	frame:SetScript("OnDragStop", frame.StopMovingOrSizing)
	frame:Hide()
	tinsert(UISpecialFrames, "FieldNotesJournal") -- Esc closes it

	local title = frame.TitleText or frame:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
	if not frame.TitleText then title:SetPoint("TOP", 0, -5) end
	title:SetText("Field Notes")

	index = CreateList("FieldNotesJournalIndex", INDEX_W)
	index.pane:SetPoint("TOPLEFT", 10, -28)
	index.pane:SetPoint("BOTTOMLEFT", 10, 10)
	index.pane:SetWidth(INDEX_W + 38)
	Paper(index.pane, 0.93)

	page = CreateList("FieldNotesJournalPage", PAGE_W)
	page.pane:SetPoint("TOPLEFT", index.pane, "TOPRIGHT", 6, 0)
	page.pane:SetPoint("BOTTOMRIGHT", -10, 10)
	Paper(page.pane, 1)
	page.sf:SetPoint("BOTTOMRIGHT", -28, NOTES_H + 14)

	notes = CreateNotes(page.pane)
	notes:SetPoint("BOTTOMLEFT", 10, 6)
	notes:SetPoint("BOTTOMRIGHT", -28, 6)

	frame:SetScript("OnShow", Refresh)
end

function ns:ToggleJournal()
	if not frame then CreateJournal() end
	if frame:IsShown() then
		frame:Hide()
		return
	end
	-- open on the dungeon you are standing in
	if self.currentID and (not sel.inst or sel.inst ~= self.currentID) then
		sel.inst, sel.kind, sel.key = self.currentID, "overview", nil
	end
	frame:Show()
end

ns:On("FN_DATA", function() Refresh() end)

---------------------------------------------------------------------------
-- /fn maptest: look at a shipped map without visiting the dungeon. Makes a
-- throwaway "Map test" page and uncovers three more areas each time it is
-- run; "/fn maptest off" (or tearing the page out) removes it.
---------------------------------------------------------------------------
local TEST = "maptest"

function ns:MapTest(arg)
	local id = tonumber(arg) or 230
	local inst = self.db.instances[TEST]
	if arg == "off" or not self.Maps[id] then
		self.Maps[TEST] = nil
		self:Forget(TEST)
		if arg ~= "off" then self:Print("no map for instance %d.", id) end
		return
	end
	if not inst or inst.testOf ~= id then
		inst = {
			name = "Map test", kind = "party", first = time(), last = time(), visits = 1, testOf = id,
			areas = {}, bosses = {}, bossOrder = {}, mobs = {}, mobOrder = {}, loot = {}, lootOrder = {}, log = {},
		}
		self.db.instances[TEST] = inst
	else
		-- every area name on every floor, in a stable order; add the next three
		local names, have = {}, {}
		for _, floor in ipairs(self.Maps[id]) do
			for key in pairs(floor.areas) do names[#names + 1] = key end
		end
		table.sort(names)
		for _, a in ipairs(inst.areas) do have[a.name] = true end
		local added = 0
		for _, name in ipairs(names) do
			if not have[name] and added < 3 then
				inst.areas[#inst.areas + 1] = { name = name, t = time() }
				added = added + 1
			end
		end
	end
	self.Maps[TEST] = self.Maps[id]
	if not frame then CreateJournal() end
	sel.inst, sel.kind = TEST, "map"
	frame:Show()
	Refresh()
end

-- the test page never outlives the session
ns:On("PLAYER_LOGOUT", function()
	if ns.db then ns.db.instances[TEST] = nil end
end)
