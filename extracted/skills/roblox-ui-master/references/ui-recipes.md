# UI recipes (all use the helpers from ui-kit.luau: make, panel, label, row, column, pad, round, outline, tween, pressFeedback, drawIcon)

## 1. HUD bar (health / energy) - top-left, below the top bar (keep bottom corners free for touch controls)
```lua
local gui = make("ScreenGui", { Name = "Hud", ResetOnSpawn = false, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, playerGui) -- default insets: below the top bar
local hud = panel(gui, { Name = "HudPanel", Size = UDim2.fromOffset(220, 56) })
hud.Position = UDim2.fromOffset(12, 12)
pad(hud, 10, 8, 10, 8)
column(hud, 6)
local function bar(parent, name, color, order)
	local track = make("Frame", { Name = name .. "Track", Size = UDim2.new(1, 0, 0, 10), BackgroundColor3 = THEME.dark, BorderSizePixel = 0, LayoutOrder = order }, parent)
	round(track, 5)
	local fill = make("Frame", { Name = name .. "Fill", Size = UDim2.new(1, 0, 1, 0), BackgroundColor3 = color, BorderSizePixel = 0 }, track)
	round(fill, 5)
	return function(alpha) tween(fill, 0.2, { Size = UDim2.new(math.clamp(alpha, 0, 1), 0, 1, 0) }) end
end
local setHealth = bar(hud, "Health", THEME.success, 1)
local setEnergy = bar(hud, "Energy", THEME.cyan, 2)
```

## 2. Shop / inventory grid (scrolls, never overflows)
```lua
local scroller = make("ScrollingFrame", { Name = "Items", Size = UDim2.new(1, 0, 1, 0), BackgroundTransparency = 1, BorderSizePixel = 0,
	CanvasSize = UDim2.new(0, 0, 0, 0), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y, ScrollBarThickness = 4 }, parent)
make("UIGridLayout", { CellSize = UDim2.fromOffset(96, 112), CellPadding = UDim2.fromOffset(8, 8), SortOrder = Enum.SortOrder.LayoutOrder }, scroller)
for i, item in ipairs(items) do
	local slot = make("TextButton", { Name = "Slot" .. i, Text = "", AutoButtonColor = false, BackgroundColor3 = THEME.panelLight, BorderSizePixel = 0, LayoutOrder = i }, scroller)
	round(slot, 12); pressFeedback(slot)
	-- icon area + name + price as children (labels with fixed heights, TextTruncate AtEnd)
end
```

## 3. Modal dialog (dim backdrop + centered panel)
```lua
local modal = make("Frame", { Name = "ConfirmModal", Size = UDim2.new(1, 0, 1, 0), BackgroundColor3 = THEME.dark, BackgroundTransparency = 0.45, Active = true, ZIndex = 100 }, gui)
local box = panel(modal, { Name = "ConfirmBox", Size = UDim2.new(0.8, 0, 0, 0) })
box.AutomaticSize = Enum.AutomaticSize.Y
box.AnchorPoint = Vector2.new(0.5, 0.5); box.Position = UDim2.new(0.5, 0, 0.5, 0)
make("UISizeConstraint", { MinSize = Vector2.new(260, 0), MaxSize = Vector2.new(420, 400) }, box)
pad(box, 16, 16, 16, 16); column(box, 12)
-- title label, paragraph label (TextWrapped + AutomaticSize.Y), button row: two 44px-high buttons in a horizontal UIListLayout
```

## 4. Tabs
Horizontal UIListLayout of tab buttons (height 40) + one content Frame per tab; switching only toggles `Visible`. Keep tab state in one `activeTab` variable; do not create connections inside the switch function.

## 5. Progress / XP bar
Track (height 8, radius 4, `dark`) + fill sized by scale `(alpha,0,1,0)` + `UIGradient`. Update with `tween(fill, 0.25, {Size = ...})`.

## 6. Toast host (transient, never blocks input)
Frame anchored top-center below the header (`AnchorPoint (0.5,0)`), `AutomaticSize = Y`, own vertical UIListLayout, `ZIndex = 50`; each toast fades in, lives 3-4 s, fades out, `Destroy()`. Max 3 at once (destroy the oldest, number new cards with an increasing LayoutOrder).

## 7. Leaderboard / list
Vertical UIListLayout inside a ScrollingFrame; rows are fixed-height Frames (36-44) with a horizontal UIListLayout: rank (40px), name (flexible: `UDim2.new(1, -(40+80+16), 1, 0)`), score (80px, right aligned).

## 8. Settings toggle
Row (height 44): label (flexible) + switch (52x28, radius 14): track Frame + knob Frame (20x20); toggle by tweening knob `Position` between `UDim2.fromOffset(4, 4)` and `UDim2.fromOffset(28, 4)` and track color. Switch is a TextButton (>= 40px hit area via an invisible 52x44 button).

## 9. Loading screen
Full-size dim Frame, centered label + 240x8 progress bar; on completion tween transparency to 1 then `Destroy()` (never leave a "Loading" element behind).

## 10. Notification badge on an icon
Small 16x16 circle anchored top-right of the icon holder (`AnchorPoint (1,0)`, `Position (1,2,0,-2)`), name it `...Badge`; text >= 12px only if it fits, otherwise a plain dot.
