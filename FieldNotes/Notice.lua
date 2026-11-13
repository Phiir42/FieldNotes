-- Notices: when something new is written in the journal, a slip of parchment
-- shows near the top of the screen for a few seconds with what was written.
-- Click it to open the journal. "/fn notices" turns them off (chat lines are
-- separate: "/fn announce"). Also the journal's few sounds ("/fn sound").
local _, ns = ...

local WIDTH, HEIGHT = 300, 36
local FADE_IN, HOLD, FADE_OUT = 0.35, 3.2, 1.0
local QUEUE_MAX = 6      -- older notes are dropped when more than this wait
local ICON = "Interface\\Icons\\INV_Misc_Book_09"

local slip
local queue = {}
local showing    -- { t0 = GetTime() it appeared, hold = seconds to stay }

local function Create()
	slip = CreateFrame("Button", "FieldNotesNotice", UIParent)
	slip:SetSize(WIDTH, HEIGHT)
	slip:SetPoint("TOP", UIParent, "TOP", 0, -150)
	slip:SetFrameStrata("MEDIUM")
	local edge = slip:CreateTexture(nil, "BACKGROUND")
	edge:SetAllPoints()
	edge:SetColorTexture(0.25, 0.16, 0.07, 0.9)
	local paper = slip:CreateTexture(nil, "BORDER")
	paper:SetPoint("TOPLEFT", 1, -1)
	paper:SetPoint("BOTTOMRIGHT", -1, 1)
	paper:SetColorTexture(0.90, 0.83, 0.68, 0.96)
	local icon = slip:CreateTexture(nil, "ARTWORK")
	icon:SetTexture(ICON)
	icon:SetSize(22, 22)
	icon:SetPoint("LEFT", 8, 0)
	icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	slip.text = slip:CreateFontString(nil, "ARTWORK", "GameFontNormal")
	slip.text:SetFontObject(_G.QuestFont or GameFontNormal)
	slip.text:SetTextColor(0.20, 0.12, 0.05)
	slip.text:SetPoint("LEFT", icon, "RIGHT", 8, 0)
	slip.text:SetPoint("RIGHT", -8, 0)
	slip.text:SetJustifyH("LEFT")
	slip.text:SetWordWrap(false)
	slip:SetScript("OnClick", function()
		slip:Hide()
		if not (FieldNotesJournal and FieldNotesJournal:IsShown()) then ns:ToggleJournal() end
	end)
	slip:SetScript("OnHide", function()
		showing = nil
		slip:SetScript("OnUpdate", nil)
		for i = #queue, 1, -1 do queue[i] = nil end
	end)
	slip:Hide()
end

local Next

local function Tick()
	local t = GetTime() - showing.t0
	local hold = showing.hold
	if t < FADE_IN then
		slip:SetAlpha(t / FADE_IN)
	elseif t < FADE_IN + hold then
		slip:SetAlpha(1)
	elseif t < FADE_IN + hold + FADE_OUT then
		slip:SetAlpha(1 - (t - FADE_IN - hold) / FADE_OUT)
	elseif #queue > 0 then
		Next()
	else
		slip:Hide()
	end
end

Next = function()
	local text = table.remove(queue, 1)
	-- with more waiting, each stays a shorter while
	showing = { t0 = GetTime(), hold = #queue > 0 and HOLD / 2 or HOLD }
	slip.text:SetText(text)
	slip:SetAlpha(0)
	slip:Show()
	slip:SetScript("OnUpdate", Tick)
end

function ns:Notice(text)
	if not (self.db and self.db.settings.notices) then return end
	if not slip then Create() end
	queue[#queue + 1] = text
	while #queue > QUEUE_MAX do table.remove(queue, 1) end
	if not showing then Next() end
end

---------------------------------------------------------------------------
-- Sounds: the book opening and closing, a page turning.
---------------------------------------------------------------------------
local SOUNDS = {
	open = { "IG_QUEST_LOG_OPEN", 844 },
	close = { "IG_QUEST_LOG_CLOSE", 845 },
	page = { "IG_ABILITY_PAGE_TURN", 836 },
}

function ns:Sound(which)
	if not (self.db and self.db.settings.sound) then return end
	local s = SOUNDS[which]
	local id = s and ((SOUNDKIT and SOUNDKIT[s[1]]) or s[2])
	if id and PlaySound then pcall(PlaySound, id) end
end
