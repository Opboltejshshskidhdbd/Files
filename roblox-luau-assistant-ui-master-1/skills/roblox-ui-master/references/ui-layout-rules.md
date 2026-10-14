# Layout rules and cookbook

## The one rule
Anything that must not overlap shares ONE layout container (UIListLayout, UIGridLayout, ScrollingFrame). Free `Position` is only for a single anchored element.

## Scale vs offset
- Region sizes: scale (+ small negative offset for gaps) or list/grid cells. `Size = UDim2.new(1, -(navW + gap), 1, 0)` is fine because it is computed from known constants.
- Component sizes (buttons, icons, chips): offsets (px) so they stay touch-sized.
- Never combine a scaled panel with a bottom-anchored row of fixed offset (`Position = UDim2.new(0,76,1,-150)`): short screens make them collide. Put both in the same column.

## Safe area
```lua
local gui = Instance.new("ScreenGui")
gui.IgnoreGuiInset = false          -- default insets: UI starts below the Roblox top bar
gui.ResetOnSpawn = false
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
-- do NOT set gui.ScreenInsets = Enum.ScreenInsets.TopbarSafeInsets: it confines the ScreenGui to the top-bar strip
-- (confirmed on device: the whole layout collapsed to a sliver). Leave ScreenInsets alone unless you verified a value in the docs.
```

## Header + body + side (the standard shell)
Root (UIPadding, vertical UIListLayout) -> Header (fixed height) + Body (Size 1,0,1,-(header+gap), horizontal UIListLayout) -> Nav (fixed width) + Main (width = 1,-(nav+side+gaps)) + Side (fixed width). Horizontal list layouts do NOT share leftover space automatically: compute Main's width with a negative offset.

## Responsive, fluid and self-correcting
```lua
local function layoutFor(available) -- available = ScreenGui area (viewport minus top-bar inset)
	local mode = "full"
	if available.X < 560 or available.X < available.Y then mode = "portrait"
	elseif available.X < 1000 or available.Y < 480 then mode = "compact" end
	local M = table.clone(METRICS[mode])
	if mode ~= "portrait" then
		local bodyH = available.Y - 2 * M.pad - M.header - M.gap
		M.hero = math.clamp(math.floor(bodyH * 0.56) - math.floor(M.gap / 2), M.heroMin, M.heroMax)
		M.card = math.clamp(bodyH - M.hero - M.gap, M.cardMin, M.cardMax)   -- fills the screen, clamped on big screens
	end
	return mode, M
end
local function refresh()
	local available = Vector2.new(camera.ViewportSize.X, camera.ViewportSize.Y - GuiService:GetGuiInset().Y)
	if gui and gui.AbsoluteSize.X > 0 and gui.AbsoluteSize.Y > 0 then available = gui.AbsoluteSize end -- real size wins
	local mode, M = layoutFor(available)
	local key = mode .. ":" .. M.hero .. ":" .. M.card
	if key ~= currentKey then currentKey = key; render(mode, M) end   -- render() destroys the old ScreenGui
end
camera:GetPropertyChangedSignal("ViewportSize"):Connect(refresh)
-- inside render(): gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(function() task.defer(refresh) end)
```

## Scrolling column
`ScrollingFrame{ Size=(1,-reserved,1,0), AutomaticCanvasSize=Y, CanvasSize=(0,0,0,0), ScrollingDirection=Y, ScrollBarThickness=4 }` + `UIListLayout`. Children use width scale 1 and fixed/auto heights.

## Grid of cards
`UIGridLayout.CellSize = UDim2.new(1/cols, -((cols-1)*gap)/cols, 0, cardH)`, `CellPadding = UDim2.fromOffset(gap, gap)`; parent `AutomaticSize = Y`, `Size = (1,0,0,0)`.

## Text blocks
Paragraph: `TextWrapped=true`, `AutomaticSize=Y`, `Size=UDim2.new(1,0,0,0)`, `TextTruncate=None`. One-liners: fixed height `ceil(size*1.25)`, `TextTruncate=AtEnd` (and make the box wide enough - the lint warns when truncation would happen).
Scaled text: `TextScaled=true` + `UITextSizeConstraint{MinTextSize=12, MaxTextSize=N}`.

## Chips / rows
Horizontal UIListLayout with `VerticalAlignment=Center`; fixed-width children; the flexible child gets `Size=UDim2.new(1,-(sum of others + gaps),1,0)`.

## Centering on big screens
Main frame (not scrolling) with `UIListLayout.VerticalAlignment = Center` keeps content centered instead of top-heavy.

## Overlays
Toast host: `AnchorPoint (0.5,0)`, `Position (0.5,0,0,pad+header+gap)`, `AutomaticSize=Y`, `ZIndex=50`, own UIListLayout, max 3 cards (destroy the oldest). Keep the bottom corners free for Roblox touch controls. Modal: full-size dim Frame (BackgroundTransparency 0.45, Active=true) + centered panel with UISizeConstraint.

## Known limits of the bundled lint
Runtime-created UI, tweened positions, `UIFlexItem`, `UIPageLayout`, 3D/Billboard/Surface GUIs and values that depend on game state are not simulated.
