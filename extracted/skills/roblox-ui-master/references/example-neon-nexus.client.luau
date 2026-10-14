-- NEON NEXUS v3 (responsive, fills the whole safe area)
-- Place as a LocalScript in: StarterPlayer > StarterPlayerScripts   (Instance name: NeonNexus, class: LocalScript)
-- No external assets. Icons are drawn from Frames, so nothing renders as an empty box.
-- Layout rules: every region lives inside a UIListLayout / UIGridLayout / ScrollingFrame, so panels cannot overlap.
-- Safe area: the ScreenGui keeps Roblox's DEFAULT insets (below the top bar). Do NOT set ScreenInsets = TopbarSafeInsets:
--   that confines the ScreenGui to the thin top-bar strip and the whole layout collapses (seen on device).
-- Sizes are computed from the real available area, so the UI uses the full screen on every device.
-- DEMO values below are placeholders - wire them to your own data.

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local GuiService = game:GetService("GuiService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local DEMO = {
	credits = "12,840",
	level = 27,
	xp = 7240,
	xpMax = 10000,
}

local THEME = {
	panel = Color3.fromRGB(16, 18, 38),
	panelLight = Color3.fromRGB(26, 29, 56),
	stroke = Color3.fromRGB(70, 78, 140),
	cyan = Color3.fromRGB(0, 229, 255),
	purple = Color3.fromRGB(139, 92, 246),
	pink = Color3.fromRGB(255, 92, 170),
	green = Color3.fromRGB(70, 230, 140),
	text = Color3.fromRGB(240, 244, 255),
	muted = Color3.fromRGB(160, 168, 205),
	dark = Color3.fromRGB(8, 10, 24),
}
local FONT = {
	title = Enum.Font.GothamBlack,
	bold = Enum.Font.GothamBold,
	body = Enum.Font.Gotham,
}

-- layout metrics per screen class (all sizes in pixels, text never below 12)
local METRICS = {
	full = { pad = 16, gap = 12, header = 64, nav = 64, navBtn = 48, side = 260, hero = 240, card = 110, heroMin = 200, heroMax = 340, cardMin = 100, cardMax = 160, cols = 4, title = 34, h2 = 20, body = 14, orb = 150 },
	compact = { pad = 8, gap = 8, header = 48, nav = 52, navBtn = 40, side = 190, hero = 120, card = 74, heroMin = 110, heroMax = 180, cardMin = 70, cardMax = 110, cols = 4, title = 24, h2 = 16, body = 13, orb = 84 },
	portrait = { pad = 8, gap = 8, header = 48, nav = 48, navBtn = 40, side = 0, hero = 150, card = 72, heroMin = 150, heroMax = 150, cardMin = 72, cardMax = 72, cols = 2, title = 22, h2 = 15, body = 13, orb = 76 },
}

-- available = size of the ScreenGui area (viewport minus the top-bar inset); fluid heights fill the screen
local function layoutFor(available)
	local mode = "full"
	if available.X < 560 or available.X < available.Y then
		mode = "portrait"
	elseif available.X < 1000 or available.Y < 480 then
		mode = "compact"
	end
	local M = table.clone(METRICS[mode])
	if mode == "compact" and available.X < 760 then
		M.side = 0 -- narrow phones: stats move into the scrolling column instead of a side panel
	end
	if mode ~= "portrait" then
		local bodyHeight = available.Y - 2 * M.pad - M.header - M.gap
		M.hero = math.clamp(math.floor(bodyHeight * 0.56) - math.floor(M.gap / 2), M.heroMin, M.heroMax)
		M.card = math.clamp(bodyHeight - M.hero - M.gap, M.cardMin, M.cardMax)
	end
	return mode, M
end

-- ---------- tiny UI kit ----------
local function make(class, props, parent)
	local inst = Instance.new(class)
	for key, value in pairs(props) do
		inst[key] = value
	end
	inst.Parent = parent
	return inst
end

local function round(parent, radius)
	return make("UICorner", { CornerRadius = UDim.new(0, radius) }, parent)
end

local function outline(parent, color, transparency, thickness)
	return make("UIStroke", { Color = color, Transparency = transparency, Thickness = thickness or 1, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, parent)
end

local function pad(parent, left, top, right, bottom)
	return make("UIPadding", {
		PaddingLeft = UDim.new(0, left), PaddingTop = UDim.new(0, top),
		PaddingRight = UDim.new(0, right or left), PaddingBottom = UDim.new(0, bottom or top),
	}, parent)
end

local function column(parent, gapPx)
	return make("UIListLayout", { FillDirection = Enum.FillDirection.Vertical, SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, gapPx) }, parent)
end

local function row(parent, gapPx, align)
	return make("UIListLayout", {
		FillDirection = Enum.FillDirection.Horizontal, SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, gapPx),
		HorizontalAlignment = align or Enum.HorizontalAlignment.Left, VerticalAlignment = Enum.VerticalAlignment.Center,
	}, parent)
end

local function panel(parent, props)
	local frame = make("Frame", {
		BackgroundColor3 = THEME.panel, BackgroundTransparency = 0.12, BorderSizePixel = 0,
		Size = props.Size or UDim2.new(1, 0, 1, 0), LayoutOrder = props.LayoutOrder or 0, Name = props.Name or "Panel",
	}, parent)
	round(frame, 14)
	outline(frame, THEME.stroke, 0.55, 1)
	make("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(255, 255, 255), Color3.fromRGB(190, 195, 230)) }, frame)
	return frame
end

local function label(parent, text, size, font, color, extra)
	local props = {
		Text = text, TextSize = size, Font = font, TextColor3 = color, BackgroundTransparency = 1, BorderSizePixel = 0,
		TextXAlignment = Enum.TextXAlignment.Left, TextTruncate = Enum.TextTruncate.AtEnd,
		Size = UDim2.new(1, 0, 0, math.ceil(size * 1.25)),
	}
	for key, value in pairs(extra or {}) do
		props[key] = value
	end
	return make("TextLabel", props, parent)
end

local function tween(inst, seconds, goal)
	TweenService:Create(inst, TweenInfo.new(seconds, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), goal):Play()
end

local function pressFeedback(button, scaleTarget)
	local uiScale = make("UIScale", { Scale = 1 }, scaleTarget or button)
	button.MouseButton1Down:Connect(function()
		tween(uiScale, 0.08, { Scale = 0.96 })
	end)
	button.MouseButton1Up:Connect(function()
		tween(uiScale, 0.12, { Scale = 1 })
	end)
end

-- icons drawn from Frames (no emoji, no asset ids)
local function box(parent, x, y, w, h, color, radius)
	local part = make("Frame", { Position = UDim2.fromOffset(x, y), Size = UDim2.fromOffset(w, h), BackgroundColor3 = color, BorderSizePixel = 0 }, parent)
	round(part, radius)
	return part
end

local function drawIcon(kind, parent, color)
	local holder = make("Frame", { Name = "Icon", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 0.5, 0), Size = UDim2.fromOffset(20, 20), BackgroundTransparency = 1 }, parent)
	if kind == "hub" then
		box(holder, 1, 1, 8, 8, color, 2)
		box(holder, 11, 1, 8, 8, color, 2)
		box(holder, 1, 11, 8, 8, color, 2)
		box(holder, 11, 11, 8, 8, color, 2)
	elseif kind == "bag" then
		box(holder, 1, 6, 18, 13, color, 4)
		local handle = box(holder, 6, 1, 8, 7, THEME.dark, 3)
		handle.BackgroundTransparency = 1
		outline(handle, color, 0, 2)
	elseif kind == "quest" then
		local diamond = box(holder, 4, 4, 12, 12, color, 2)
		diamond.Rotation = 45
		box(holder, 8, 8, 4, 4, THEME.dark, 2)
	elseif kind == "coin" then
		local ring = box(holder, 1, 1, 18, 18, color, 9)
		ring.BackgroundTransparency = 1
		outline(ring, color, 0, 2)
		box(holder, 7, 7, 6, 6, color, 3)
	else
		box(holder, 1, 3, 18, 2, color, 1)
		box(holder, 1, 9, 18, 2, color, 1)
		box(holder, 1, 15, 18, 2, color, 1)
		box(holder, 4, 1, 5, 6, color, 2)
		box(holder, 11, 7, 5, 6, color, 2)
		box(holder, 6, 13, 5, 6, color, 2)
	end
	return holder
end

-- ---------- state ----------
local gui = nil
local toastHost = nil
local navButtons = {}
local currentKey = nil
local toastCount = 0

local function toast(message)
	if not toastHost then
		return
	end
	local cards = {}
	for _, child in ipairs(toastHost:GetChildren()) do
		if child.Name == "ToastCard" then
			table.insert(cards, child)
		end
	end
	while #cards >= 3 do
		table.remove(cards, 1):Destroy()
	end
	toastCount += 1
	local card = panel(toastHost, { Name = "ToastCard", Size = UDim2.new(1, 0, 0, 44), LayoutOrder = toastCount })
	pad(card, 12, 6, 12, 6)
	local title = label(card, "SYSTEM PULSE", 12, FONT.bold, THEME.cyan, { Size = UDim2.new(1, 0, 0, 14) })
	label(card, message, 13, FONT.body, THEME.text, { Position = UDim2.new(0, 0, 0, 16), Size = UDim2.new(1, 0, 0, 16) })
	title.TextTransparency = 1
	card.BackgroundTransparency = 1
	tween(card, 0.25, { BackgroundTransparency = 0.12 })
	tween(title, 0.25, { TextTransparency = 0 })
	task.delay(3.5, function()
		if card.Parent then
			tween(card, 0.3, { BackgroundTransparency = 1 })
			task.delay(0.35, function()
				card:Destroy()
			end)
		end
	end)
end

local function setActive(index)
	for i, button in ipairs(navButtons) do
		local on = i == index
		tween(button, 0.15, { BackgroundColor3 = on and THEME.purple or THEME.panelLight })
	end
end

local function buildHeader(parent, M, mode)
	local header = panel(parent, { Name = "Header", Size = UDim2.new(1, 0, 0, M.header), LayoutOrder = 1 })
	pad(header, 12, 6, 12, 6)
	local rightWidth = mode == "full" and 300 or (mode == "compact" and 240 or 120)

	local brand = make("Frame", { Name = "Brand", Size = UDim2.new(1, -(rightWidth + 8), 1, 0), BackgroundTransparency = 1 }, header)
	row(brand, 10)
	local mark = box(brand, 0, 0, M.header - 20, M.header - 20, THEME.purple, 10)
	mark.LayoutOrder = 1
	label(mark, "N", M.h2, FONT.title, THEME.text, { Size = UDim2.new(1, 0, 1, 0), TextXAlignment = Enum.TextXAlignment.Center })
	local names = make("Frame", { Name = "Names", Size = UDim2.new(1, -(M.header - 10), 1, 0), BackgroundTransparency = 1, LayoutOrder = 2 }, brand)
	local nameList = column(names, 0)
	nameList.VerticalAlignment = Enum.VerticalAlignment.Center
	label(names, "NEON NEXUS", M.h2 + 2, FONT.title, THEME.text, { LayoutOrder = 1 })
	if mode ~= "portrait" then
		label(names, "COMMAND INTERFACE // ONLINE", 12, FONT.bold, THEME.cyan, { LayoutOrder = 2 })
	end

	local right = make("Frame", { Name = "Right", Size = UDim2.new(0, rightWidth, 1, 0), Position = UDim2.new(1, 0, 0, 0), AnchorPoint = Vector2.new(1, 0), BackgroundTransparency = 1 }, header)
	row(right, 8, Enum.HorizontalAlignment.Right)
	local credits = make("Frame", { Name = "Credits", Size = UDim2.new(0, mode == "full" and 124 or 96, 1, 0), BackgroundColor3 = THEME.panelLight, BorderSizePixel = 0, LayoutOrder = 1 }, right)
	round(credits, 10)
	pad(credits, 10, 2, 10, 2)
	column(credits, 0)
	label(credits, "CREDITS", 12, FONT.bold, THEME.muted, { LayoutOrder = 1 })
	label(credits, DEMO.credits, M.body + 3, FONT.bold, THEME.text, { LayoutOrder = 2 })
	if mode ~= "portrait" then
		local profile = make("Frame", { Name = "Profile", Size = UDim2.new(0, mode == "full" and 160 or 128, 1, 0), BackgroundColor3 = THEME.panelLight, BorderSizePixel = 0, LayoutOrder = 2 }, right)
		round(profile, 10)
		pad(profile, 8, 4, 8, 4)
		row(profile, 8)
		local avatar = box(profile, 0, 0, 28, 28, THEME.purple, 14)
		avatar.LayoutOrder = 1
		label(avatar, string.upper(string.sub(player.DisplayName, 1, 1)), 14, FONT.bold, THEME.text, { Size = UDim2.new(1, 0, 1, 0), TextXAlignment = Enum.TextXAlignment.Center })
		local who = make("Frame", { Name = "Who", Size = UDim2.new(1, -36, 1, 0), BackgroundTransparency = 1, LayoutOrder = 2 }, profile)
		column(who, 0).VerticalAlignment = Enum.VerticalAlignment.Center
		label(who, player.DisplayName, 13, FONT.bold, THEME.text, { LayoutOrder = 1 })
		label(who, "LEVEL " .. DEMO.level, 12, FONT.bold, THEME.green, { LayoutOrder = 2 })
	end
	return header
end

local function buildNav(parent, M)
	local nav = panel(parent, { Name = "Nav", Size = UDim2.new(0, M.nav, 1, 0), LayoutOrder = 1 })
	pad(nav, 4, 4, 4, 4)
	local list = column(nav, 4)
	list.HorizontalAlignment = Enum.HorizontalAlignment.Center
	navButtons = {}
	local kinds = { "hub", "bag", "quest", "coin", "gear" }
	local names = { "Hub", "Inventory", "Quests", "Market", "Settings" }
	for i, kind in ipairs(kinds) do
		local button = make("TextButton", {
			Name = "Nav" .. names[i], Text = "", AutoButtonColor = false, BorderSizePixel = 0, LayoutOrder = i,
			Size = UDim2.fromOffset(M.navBtn, M.navBtn), BackgroundColor3 = THEME.panelLight,
		}, nav)
		round(button, 12)
		drawIcon(kind, button, THEME.text)
		pressFeedback(button)
		button.MouseEnter:Connect(function()
			tween(button, 0.12, { BackgroundTransparency = 0.15 })
		end)
		button.MouseLeave:Connect(function()
			tween(button, 0.12, { BackgroundTransparency = 0 })
		end)
		button.Activated:Connect(function()
			setActive(i)
			toast(names[i] .. " opened")
		end)
		navButtons[i] = button
	end
	setActive(1)
	return nav
end

local function buildHero(parent, M, mode)
	local hero = panel(parent, { Name = "Hero", Size = UDim2.new(1, 0, 0, M.hero), LayoutOrder = 1 })
	pad(hero, 14, 10, 14, 10)

	local left = make("Frame", { Name = "HeroText", Size = UDim2.new(0.62, 0, 1, 0), BackgroundTransparency = 1 }, hero)
	local list = column(left, 6)
	list.VerticalAlignment = Enum.VerticalAlignment.Center
	label(left, "SECTOR 07 / NEXUS CORE", 12, FONT.bold, THEME.cyan, { LayoutOrder = 1 })
	local headline = mode == "full" and "READY TO\nBREAK THE LIMIT." or "BREAK THE LIMIT."
	label(left, headline, M.title, FONT.title, THEME.text, { LayoutOrder = 2, TextWrapped = true, TextTruncate = Enum.TextTruncate.None, AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0) })
	if mode == "full" then
		label(left, "Your command center is synchronized. Choose a module and make something impossible.", M.body, FONT.body, THEME.muted, { LayoutOrder = 3, TextWrapped = true, TextTruncate = Enum.TextTruncate.None, AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0) })
	end
	local cta = make("TextButton", {
		Name = "EnterNexus", Text = "ENTER NEXUS", TextSize = M.body, Font = FONT.bold, TextColor3 = THEME.dark, AutoButtonColor = false,
		BackgroundColor3 = THEME.cyan, BorderSizePixel = 0, Size = UDim2.fromOffset(mode == "full" and 170 or 140, mode == "full" and 44 or 40), LayoutOrder = 4,
	}, left)
	round(cta, 12)
	pressFeedback(cta)
	cta.Activated:Connect(function()
		toast("Entering the Nexus")
	end)

	local orbArea = make("Frame", { Name = "OrbArea", Size = UDim2.new(0.38, 0, 1, 0), Position = UDim2.new(1, 0, 0, 0), AnchorPoint = Vector2.new(1, 0), BackgroundTransparency = 1 }, hero)
	local glow = make("Frame", { Name = "OrbGlow", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 0.5, 0), Size = UDim2.fromOffset(M.orb + 16, M.orb + 16), BackgroundTransparency = 1 }, orbArea)
	round(glow, 999)
	local glowStroke = outline(glow, THEME.cyan, 0.6, 2)
	TweenService:Create(glowStroke, TweenInfo.new(1.6, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { Transparency = 0.9 }):Play()
	local orb = make("Frame", { Name = "Orb", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 0.5, 0), Size = UDim2.fromOffset(M.orb, M.orb), BackgroundColor3 = THEME.purple, BorderSizePixel = 0 }, orbArea)
	round(orb, 999)
	make("UIGradient", { Rotation = 45, Color = ColorSequence.new(THEME.purple, THEME.cyan) }, orb)
	outline(orb, THEME.cyan, 0.3, 2)
	label(orb, "N", math.floor(M.orb * 0.42), FONT.title, THEME.text, { Size = UDim2.new(1, 0, 1, 0), TextXAlignment = Enum.TextXAlignment.Center })
	return hero
end

local function buildModules(parent, M)
	local grid = make("Frame", { Name = "Modules", Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, BackgroundTransparency = 1, LayoutOrder = 2 }, parent)
	make("UIGridLayout", {
		CellSize = UDim2.new(1 / M.cols, -((M.cols - 1) * M.gap) / M.cols, 0, M.card),
		CellPadding = UDim2.fromOffset(M.gap, M.gap), SortOrder = Enum.SortOrder.LayoutOrder,
	}, grid)
	local modules = {
		{ "01", "INVENTORY", "24 items", THEME.cyan },
		{ "02", "QUESTS", "3 active", THEME.purple },
		{ "03", "MARKET", "Live now", THEME.pink },
		{ "04", "EVENT", "Starts soon", THEME.green },
	}
	for i, data in ipairs(modules) do
		local card = make("TextButton", { Name = "Module" .. data[1], Text = "", AutoButtonColor = false, BackgroundColor3 = THEME.panel, BackgroundTransparency = 0.12, BorderSizePixel = 0, LayoutOrder = i }, grid)
		round(card, 14)
		local stroke = outline(card, data[4], 0.6, 1)
		pad(card, 12, 8, 12, 8)
		local list = column(card, 2)
		list.VerticalAlignment = Enum.VerticalAlignment.Center
		label(card, data[1], 12, FONT.bold, data[4], { LayoutOrder = 1 })
		label(card, data[2], M.body + 1, FONT.bold, THEME.text, { LayoutOrder = 2 })
		label(card, data[3], 12, FONT.body, THEME.muted, { LayoutOrder = 3 })
		pressFeedback(card)
		card.MouseEnter:Connect(function()
			tween(stroke, 0.15, { Transparency = 0.1 })
		end)
		card.MouseLeave:Connect(function()
			tween(stroke, 0.15, { Transparency = 0.6 })
		end)
		card.Activated:Connect(function()
			toast(data[2] .. " selected")
		end)
	end
	return grid
end

local function buildStats(parent, M, order)
	local stats = panel(parent, { Name = "Stats", Size = UDim2.new(1, 0, 0, 0), LayoutOrder = order })
	stats.AutomaticSize = Enum.AutomaticSize.Y
	pad(stats, 14, 12, 14, 12)
	column(stats, 6)
	label(stats, "SYNC PROGRESS", 12, FONT.bold, THEME.muted, { LayoutOrder = 1 })
	label(stats, "LEVEL " .. DEMO.level, M.h2 + 4, FONT.title, THEME.text, { LayoutOrder = 2 })
	local track = make("Frame", { Name = "XpTrack", Size = UDim2.new(1, 0, 0, 8), BackgroundColor3 = THEME.dark, BorderSizePixel = 0, LayoutOrder = 3 }, stats)
	round(track, 4)
	local fill = make("Frame", { Name = "XpFill", Size = UDim2.new(DEMO.xp / DEMO.xpMax, 0, 1, 0), BackgroundColor3 = THEME.cyan, BorderSizePixel = 0 }, track)
	round(fill, 4)
	make("UIGradient", { Color = ColorSequence.new(THEME.cyan, THEME.purple) }, fill)
	label(stats, "7,240 / 10,000 XP", 12, FONT.body, THEME.muted, { LayoutOrder = 4 })
	label(stats, "LIVE SYSTEMS", 12, FONT.bold, THEME.muted, { LayoutOrder = 5 })
	local rows = {
		{ "Players", tostring(#Players:GetPlayers()) },
		{ "Session", string.format("%02d:%02d", math.floor(workspace.DistributedGameTime / 60) % 100, math.floor(workspace.DistributedGameTime) % 60) },
		{ "Status", "Stable" },
	}
	for i, data in ipairs(rows) do
		local line = make("Frame", { Name = "Row" .. i, Size = UDim2.new(1, 0, 0, 20), BackgroundTransparency = 1, LayoutOrder = 5 + i }, stats)
		label(line, data[1], 13, FONT.body, THEME.muted, { Size = UDim2.new(0.6, 0, 1, 0) })
		label(line, data[2], 13, FONT.bold, THEME.text, { Size = UDim2.new(0.4, 0, 1, 0), Position = UDim2.new(0.6, 0, 0, 0), TextXAlignment = Enum.TextXAlignment.Right })
	end
	return stats
end

local refresh = nil

local function render(mode, M)
	if gui then
		gui:Destroy()
	end
	gui = make("ScreenGui", {
		Name = "NeonNexus", ResetOnSpawn = false, IgnoreGuiInset = false, DisplayOrder = 20,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
	}, playerGui)
	-- the real ScreenGui size is only known after layout: re-check once it changes (self-correcting)
	gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
		task.defer(refresh)
	end)

	local root = make("Frame", { Name = "Root", Size = UDim2.new(1, 0, 1, 0), BackgroundTransparency = 1 }, gui)
	pad(root, M.pad, M.pad, M.pad, M.pad)
	column(root, M.gap)
	buildHeader(root, M, mode)

	local body = make("Frame", { Name = "Body", Size = UDim2.new(1, 0, 1, -(M.header + M.gap)), BackgroundTransparency = 1, LayoutOrder = 2 }, root)
	row(body, M.gap).VerticalAlignment = Enum.VerticalAlignment.Top
	buildNav(body, M)

	local reserved = M.nav + M.gap + (M.side > 0 and (M.side + M.gap) or 0)
	local main
	if mode == "full" then
		-- plenty of room: no scrolling, content centered vertically
		main = make("Frame", { Name = "Main", Size = UDim2.new(1, -reserved, 1, 0), BackgroundTransparency = 1, LayoutOrder = 2 }, body)
		column(main, M.gap).VerticalAlignment = Enum.VerticalAlignment.Center
	else
		-- small screens: the column scrolls instead of overlapping or getting cut off
		main = make("ScrollingFrame", {
			Name = "Main", Size = UDim2.new(1, -reserved, 1, 0), BackgroundTransparency = 1, BorderSizePixel = 0, LayoutOrder = 2,
			ScrollBarThickness = 4, ScrollBarImageColor3 = THEME.cyan, CanvasSize = UDim2.new(0, 0, 0, 0),
			AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y,
		}, body)
		column(main, M.gap)
	end
	buildHero(main, M, mode)
	buildModules(main, M)

	if M.side > 0 then
		local side = make("Frame", { Name = "Side", Size = UDim2.new(0, M.side, 1, 0), BackgroundTransparency = 1, LayoutOrder = 3 }, body)
		buildStats(side, M, 1)
	else
		buildStats(main, M, 3)
	end

	toastHost = make("Frame", {
		Name = "ToastHost", AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, M.pad + M.header + M.gap),
		Size = UDim2.new(0, 250, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, BackgroundTransparency = 1, ZIndex = 50,
	}, gui)
	column(toastHost, 6)
	return gui
end

local function getCamera()
	local camera = workspace.CurrentCamera
	while not camera do
		task.wait()
		camera = workspace.CurrentCamera
	end
	return camera
end

local camera = getCamera()

refresh = function()
	local available = Vector2.new(camera.ViewportSize.X, camera.ViewportSize.Y - GuiService:GetGuiInset().Y)
	if gui and gui.AbsoluteSize.X > 0 and gui.AbsoluteSize.Y > 0 then
		available = gui.AbsoluteSize
	end
	local mode, M = layoutFor(available)
	local key = mode .. ":" .. M.hero .. ":" .. M.card
	if key ~= currentKey then
		currentKey = key
		render(mode, M)
		toast("Nexus interface synchronized")
	end
end

camera:GetPropertyChangedSignal("ViewportSize"):Connect(refresh)
refresh()
