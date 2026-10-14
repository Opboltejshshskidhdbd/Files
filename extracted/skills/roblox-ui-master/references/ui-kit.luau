-- ROBLOX UI KIT (copy this block to the top of every generated UI LocalScript, then adapt THEME / METRICS)
-- Requires: local TweenService = game:GetService("TweenService"), a THEME table (Color3 values incl. panel, panelLight, stroke, text, muted, dark)
-- and a FONT table (title/bold/body). All helpers set Parent LAST and keep text >= 12px.
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

