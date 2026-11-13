-- The minimap button, the addon compartment entry and slash commands.
local _, ns = ...

local ICON = "Interface\\Icons\\INV_Misc_Book_09"

local function Tooltip(owner, extra)
	GameTooltip:SetOwner(owner, "ANCHOR_LEFT")
	GameTooltip:AddLine("Field Notes")
	local n = 0
	for _ in pairs(ns.db.instances) do n = n + 1 end
	GameTooltip:AddLine(n == 0 and "The pages are blank" or (n == 1 and "1 place written about" or (n .. " places written about")), 1, 1, 1)
	GameTooltip:AddLine("Click: open the journal", 0.7, 0.7, 0.7)
	if extra then GameTooltip:AddLine(extra, 0.7, 0.7, 0.7) end
	GameTooltip:Show()
end

---------------------------------------------------------------------------
-- Minimap button: a named Button parented to Minimap, so minimap button
-- collectors pick it up. Once a collector re-parents it, its position is
-- left alone.
---------------------------------------------------------------------------
local button

local function OwnedByMinimap()
	return button:GetParent() == Minimap
end

local function Place()
	if not OwnedByMinimap() then return end
	local a = math.rad(ns.db.settings.buttonAngle)
	local r = Minimap:GetWidth() / 2 + 5
	button:ClearAllPoints()
	button:SetPoint("CENTER", Minimap, "CENTER", math.cos(a) * r, math.sin(a) * r)
end

local function DragUpdate()
	local mx, my = Minimap:GetCenter()
	local cx, cy = GetCursorPosition()
	local sc = Minimap:GetEffectiveScale()
	ns.db.settings.buttonAngle = math.deg(math.atan2(cy / sc - my, cx / sc - mx))
	Place()
end

local function CreateButton()
	local b = CreateFrame("Button", "FieldNotesMinimapButton", Minimap)
	button = b
	b:SetSize(31, 31)
	b:SetFrameStrata("MEDIUM")
	b:SetFrameLevel(8)
	b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
	b:RegisterForDrag("LeftButton")
	b:SetHighlightTexture("Interface\\Minimap\\UI-Minimap-ZoomButton-Highlight")
	local bg = b:CreateTexture(nil, "BACKGROUND")
	bg:SetTexture("Interface\\Minimap\\UI-Minimap-Background")
	bg:SetSize(20, 20)
	bg:SetPoint("CENTER")
	local icon = b:CreateTexture(nil, "ARTWORK")
	icon:SetTexture(ICON)
	icon:SetSize(18, 18)
	icon:SetPoint("CENTER")
	icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	local border = b:CreateTexture(nil, "OVERLAY")
	border:SetTexture("Interface\\Minimap\\MiniMap-TrackingBorder")
	border:SetSize(53, 53)
	border:SetPoint("TOPLEFT")
	b:SetScript("OnClick", function() ns:ToggleJournal() end)
	b:SetScript("OnEnter", function(self) Tooltip(self, OwnedByMinimap() and "Drag: move" or nil) end)
	b:SetScript("OnLeave", function() GameTooltip:Hide() end)
	b:SetScript("OnDragStart", function(self)
		if OwnedByMinimap() then self:SetScript("OnUpdate", DragUpdate) end
	end)
	b:SetScript("OnDragStop", function(self) self:SetScript("OnUpdate", nil) end)
	Place()
end

function ns:UpdateMinimapButton()
	if self.db.settings.button then
		if not button then CreateButton() end
		if not button:IsShown() then button:Show() end
	elseif button and button:IsShown() then
		button:Hide()
	end
end

ns:On("FN_LOADED", function() ns:UpdateMinimapButton() end)

---------------------------------------------------------------------------
-- Addon compartment (globals named in the TOC). The first argument is the
-- addon name or the menu entry frame depending on the caller.
---------------------------------------------------------------------------
function FieldNotes_OnCompartmentClick()
	ns:ToggleJournal()
end

function FieldNotes_OnCompartmentEnter(addonOrFrame, frame)
	local owner = type(addonOrFrame) == "table" and addonOrFrame or frame
	if type(owner) == "table" then Tooltip(owner) end
end

function FieldNotes_OnCompartmentLeave()
	GameTooltip:Hide()
end

---------------------------------------------------------------------------
-- /fn
---------------------------------------------------------------------------
BINDING_HEADER_FIELDNOTES = "Field Notes"
BINDING_NAME_FIELDNOTES_TOGGLE = "Open or close the journal"

SLASH_FIELDNOTES1 = "/fn"
SLASH_FIELDNOTES2 = "/fieldnotes"
SlashCmdList["FIELDNOTES"] = function(msg)
	local cmd, arg = (msg or ""):lower():match("^%s*(%S*)%s*(.-)%s*$")
	local s = ns.db.settings
	if cmd == "" then
		ns:ToggleJournal()
	elseif cmd == "announce" then
		s.announce = not s.announce
		ns:Print("chat lines for new entries %s.", s.announce and "on" or "off")
	elseif cmd == "button" then
		s.button = not s.button
		ns:UpdateMinimapButton()
		ns:Print("minimap button %s.", s.button and "shown" or "hidden")
	elseif cmd == "debug" then
		ns:DebugReport()
	elseif cmd == "errors" then
		local list = ns.db.errors or {}
		if arg == "clear" then
			ns.db.errors = nil
			ns:Print("error list cleared.")
		elseif #list == 0 then
			ns:Print("no errors noted.")
		else
			ns:Print("%d %s noted (version %s). \"/fn errors clear\" empties the list.", #list,
				#list == 1 and "error" or "errors", ns.VERSION)
			for _, e in ipairs(list) do
				print(("  %s  x%d  [%s]  %s"):format(date("%d %b %H:%M", e.t), e.n, tostring(e.event), e.msg))
			end
		end
	elseif cmd == "version" then
		ns:Print("version %s.", ns.VERSION)
	elseif cmd == "mapkey" then
		s.mapKey = not s.mapKey
		ns:Print("the map key %s inside dungeons.", s.mapKey and "opens the journal" or "opens the game's map")
	elseif cmd == "notices" and (arg == "move" or arg == "reset") then
		ns:PlaceNotice(arg == "reset")
	elseif cmd == "notices" then
		s.notices = not s.notices
		ns:Print("on-screen notes for new entries %s.", s.notices and "on" or "off")
	elseif cmd == "sound" then
		s.sound = not s.sound
		ns:Print("journal sounds %s.", s.sound and "on" or "off")
	elseif cmd == "sketch" then
		s.sketch = not s.sketch
		ns:Print("newly charted parts of a map %s.", s.sketch and "are sketched in" or "simply appear")
	elseif cmd == "maptest" then
		ns:MapTest(arg ~= "" and arg or nil)
	elseif cmd == "quality" and tonumber(arg) then
		s.minQuality = math.max(0, math.min(5, math.floor(tonumber(arg))))
		ns:Print("noting items of quality %d and better (1 common, 2 uncommon, 3 rare, 4 epic).", s.minQuality)
	else
		ns:Print("version %s. Commands:", ns.VERSION)
		print("  /fn  -  open or close the journal")
		print("  /fn announce  -  chat lines when something new is written down")
		print("  /fn quality <0-5>  -  lowest item quality worth noting")
		print("  /fn button  -  show or hide the minimap button")
		print("  /fn debug  -  what the game has let the journal read, and what it hid")
		print("  /fn mapkey  -  whether the map key opens the journal inside dungeons")
		print("  /fn notices [move | reset]  -  a slip of parchment on screen when something new is written down; drag it to move it")
		print("  /fn sound  -  the journal's sounds")
		print("  /fn sketch  -  whether new parts of a map are sketched in or simply appear")
		print("  /fn maptest [instance id | off]  -  preview a map, three more areas each time")
		print("  /fn errors  -  anything that went wrong, for reporting")
	end
end
