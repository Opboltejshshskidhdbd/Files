--!strict
-- Reproduction of the defects seen in the NEON NEXUS screen recording (phone landscape)
local Players = game:GetService("Players")
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local function make(class, props, parent)
	local inst = Instance.new(class)
	for k, v in pairs(props) do (inst :: any)[k] = v end
	inst.Parent = parent
	return inst
end
local function corner(p, r) make("UICorner", {CornerRadius = UDim.new(0, r)}, p) end

local gui = make("ScreenGui", {Name = "NeonNexus", IgnoreGuiInset = true, ResetOnSpawn = false, ZIndexBehavior = Enum.ZIndexBehavior.Sibling}, playerGui)
local root = make("Frame", {Name = "Root", Size = UDim2.new(1, -24, 1, -16), Position = UDim2.new(0, 12, 0, 8), BackgroundTransparency = 1}, gui)

-- header (title sits at x=18 => under the Roblox logo/menu/chat buttons)
local header = make("Frame", {Name = "Header", Size = UDim2.new(1, 0, 0, 64), BackgroundColor3 = Color3.fromRGB(16, 18, 34)}, root)
corner(header, 14)
make("TextLabel", {Name = "Title", Text = "NEON NEXUS", Size = UDim2.new(0, 260, 0, 30), Position = UDim2.new(0, 18, 0, 6), BackgroundTransparency = 1, TextColor3 = Color3.fromRGB(255, 255, 255), TextSize = 26, Font = Enum.Font.GothamBlack, TextXAlignment = Enum.TextXAlignment.Left}, header)
make("TextLabel", {Name = "Sub", Text = "COMMAND INTERFACE // ONLINE", Size = UDim2.new(0, 260, 0, 16), Position = UDim2.new(0, 18, 0, 38), BackgroundTransparency = 1, TextColor3 = Color3.fromRGB(0, 240, 255), TextSize = 11, Font = Enum.Font.GothamBold, TextXAlignment = Enum.TextXAlignment.Left}, header)
local credits = make("Frame", {Name = "Credits", Size = UDim2.new(0, 190, 0, 48), Position = UDim2.new(1, -330, 0, 8), BackgroundColor3 = Color3.fromRGB(26, 28, 52)}, header)
make("TextLabel", {Name = "CreditsValue", Text = "12,840", Size = UDim2.new(1, 0, 1, 0), BackgroundTransparency = 1, TextColor3 = Color3.fromRGB(255, 255, 255), TextSize = 20, Font = Enum.Font.GothamBold}, credits)

-- left dock with glyph icons
local dock = make("Frame", {Name = "Dock", Size = UDim2.new(0, 64, 1, -84), Position = UDim2.new(0, 0, 0, 76), BackgroundColor3 = Color3.fromRGB(16, 18, 34)}, root)
corner(dock, 14)
for i, glyph in ipairs({"⌂", "◆", "⚡", "📱", "⚙"}) do
	make("TextButton", {Name = "Nav" .. i, Text = glyph, Size = UDim2.new(0, 44, 0, 44), Position = UDim2.new(0, 10, 0, 8 + (i - 1) * 54), BackgroundColor3 = Color3.fromRGB(36, 38, 70), TextColor3 = Color3.fromRGB(255, 255, 255), TextSize = 22}, dock)
end

-- hero panel (scale height) and bottom cards (fixed offset from bottom) => they collide on short screens
local hero = make("Frame", {Name = "Hero", Size = UDim2.new(0.55, 0, 1, -84), Position = UDim2.new(0, 76, 0, 76), BackgroundColor3 = Color3.fromRGB(16, 18, 34)}, root)
corner(hero, 14)
make("TextLabel", {Name = "HeroTitle", Text = "READY TO\nBREAK THE LIMIT.", Size = UDim2.new(0, 330, 0, 90), Position = UDim2.new(0, 22, 0, 40), BackgroundTransparency = 1, TextColor3 = Color3.fromRGB(255, 255, 255), TextSize = 32, Font = Enum.Font.GothamBlack, TextXAlignment = Enum.TextXAlignment.Left}, hero)
make("TextLabel", {Name = "HeroText", Text = "Your command center is synchronized. Choose a module and make something impossible.", Size = UDim2.new(0, 330, 0, 40), Position = UDim2.new(0, 22, 0, 140), BackgroundTransparency = 1, TextColor3 = Color3.fromRGB(170, 175, 205), TextSize = 13, TextWrapped = true, TextXAlignment = Enum.TextXAlignment.Left}, hero)
make("TextButton", {Name = "Cta", Text = "ENTER NEXUS", Size = UDim2.new(0, 170, 0, 44), Position = UDim2.new(0, 22, 0, 200), BackgroundColor3 = Color3.fromRGB(0, 240, 255), TextColor3 = Color3.fromRGB(10, 10, 30), TextSize = 16, Font = Enum.Font.GothamBold}, hero)

local right = make("Frame", {Name = "Right", Size = UDim2.new(0.3, 0, 1, -84), Position = UDim2.new(1, -250, 0, 76), BackgroundColor3 = Color3.fromRGB(16, 18, 34)}, root)
corner(right, 14)
make("TextLabel", {Name = "Level", Text = "LEVEL 27", Size = UDim2.new(1, -30, 0, 28), Position = UDim2.new(0, 15, 0, 28), BackgroundTransparency = 1, TextColor3 = Color3.fromRGB(255, 255, 255), TextSize = 22, Font = Enum.Font.GothamBlack, TextXAlignment = Enum.TextXAlignment.Left}, right)
make("TextLabel", {Name = "Live", Text = "LIVE SYSTEMS", Size = UDim2.new(1, -30, 0, 16), Position = UDim2.new(0, 15, 0, 120), BackgroundTransparency = 1, TextColor3 = Color3.fromRGB(150, 155, 190), TextSize = 11, TextXAlignment = Enum.TextXAlignment.Left}, right)

-- bottom module cards: absolute from the bottom edge
local cards = make("Frame", {Name = "Cards", Size = UDim2.new(1, -88, 0, 80), Position = UDim2.new(0, 76, 1, -150), BackgroundColor3 = Color3.fromRGB(22, 24, 44)}, root)
corner(cards, 14)
for i, label in ipairs({"01 INVENTORY", "02 QUESTS", "03 MARKET", "04 EVENT"}) do
	make("TextButton", {Name = "Card" .. i, Text = label, Size = UDim2.new(0.23, 0, 0, 56), Position = UDim2.new(0.01 + (i - 1) * 0.245, 0, 0, 12), BackgroundColor3 = Color3.fromRGB(30, 32, 60), TextColor3 = Color3.fromRGB(255, 255, 255), TextSize = 12, Font = Enum.Font.GothamBold}, cards)
end

-- toast bottom right
local toast = make("Frame", {Name = "SystemPulse", Size = UDim2.new(0, 250, 0, 56), Position = UDim2.new(1, -262, 1, -70), BackgroundColor3 = Color3.fromRGB(20, 22, 40)}, root)
make("TextLabel", {Name = "ToastText", Text = "Nexus Interface synchronized.", Size = UDim2.new(1, -20, 1, 0), Position = UDim2.new(0, 10, 0, 0), BackgroundTransparency = 1, TextColor3 = Color3.fromRGB(255, 255, 255), TextSize = 12}, toast)
