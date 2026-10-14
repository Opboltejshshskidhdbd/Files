import os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import ui_lint

FIX = os.path.join(HERE, 'fixtures')
HDR = 'local sg = Instance.new("ScreenGui")\nsg.Parent = game.Players.LocalPlayer.PlayerGui\n'

def read(name):
    with open(os.path.join(FIX, name), encoding='utf-8') as fh:
        return fh.read()

def run(code, viewports=None):
    return ui_lint.lint(code, 'test.luau', viewports)

def rules(code, sev=None, viewports=None):
    return {f['rule'] for f in run(code, viewports) if sev is None or f['severity'] == sev}

class FixtureTests(unittest.TestCase):
    def test_buggy_neon_nexus_is_caught(self):
        r = ui_lint.lint(read('neon_nexus_buggy.luau'), 'neon_nexus_buggy.luau')
        fails = {f['rule'] for f in r if f['severity'] == 'FAIL'}
        for want in ('ui.covered', 'ui.topbar_overlap', 'ui.glyph_icon', 'ui.panel_overlap', 'ui.offscreen', 'ui.text_overflow'):
            self.assertIn(want, fails, want)
    def test_user_v2_topbar_strip_bug_is_caught(self):
        # real plugin output that collapsed to a ~10px sliver on device (ScreenInsets = TopbarSafeInsets)
        r = ui_lint.lint(read('user_nexus_v2.luau'), 'user_nexus_v2.luau')
        fails = {f['rule'] for f in r if f['severity'] == 'FAIL'}
        self.assertIn('ui.screeninsets_topbar_strip', fails)
        self.assertTrue(any(f['rule'] == 'ui.consequential_hidden' for f in r))
    def test_fixed_neon_nexus_is_clean(self):
        r = ui_lint.lint(read('NeonNexus.client.luau'), 'NeonNexus.client.luau')
        bad = [f for f in r if f['severity'] in ('FAIL', 'WARN')]
        self.assertEqual(bad, [], bad)

class LayoutRules(unittest.TestCase):
    def test_two_texts_overlap(self):
        code = HDR + '''
local f = Instance.new("Frame"); f.Size = UDim2.fromOffset(300, 200); f.Parent = sg
local a = Instance.new("TextLabel"); a.Text = "Hello world"; a.Size = UDim2.fromOffset(200, 40); a.Position = UDim2.fromOffset(10, 10); a.Parent = f
local b = Instance.new("TextLabel"); b.Text = "Other text"; b.Size = UDim2.fromOffset(200, 40); b.Position = UDim2.fromOffset(20, 20); b.Parent = f'''
        self.assertTrue(rules(code, 'FAIL', ['desktop']) & {'ui.overlap', 'ui.covered'})   # default TextLabel background is opaque => 'covered'
        transparent = code.replace('a.Parent = f', 'a.BackgroundTransparency = 1; a.Parent = f').replace('b.Parent = f', 'b.BackgroundTransparency = 1; b.Parent = f')
        self.assertIn('ui.overlap', rules(transparent, 'FAIL', ['desktop']))
    def test_list_layout_prevents_overlap(self):
        code = HDR + '''
local f = Instance.new("Frame"); f.Size = UDim2.fromOffset(300, 200); f.Parent = sg
local l = Instance.new("UIListLayout"); l.Padding = UDim.new(0, 8); l.Parent = f
for i = 1, 3 do local t = Instance.new("TextLabel"); t.Text = "Row " .. i; t.Size = UDim2.new(1, 0, 0, 30); t.Parent = f end'''
        self.assertEqual(rules(code, 'FAIL', ['desktop']), set())
    def test_covered_by_panel(self):
        code = HDR + '''
local a = Instance.new("TextLabel"); a.Text = "Important"; a.Size = UDim2.fromOffset(120, 30); a.Position = UDim2.fromOffset(50, 100); a.Parent = sg
local p = Instance.new("Frame"); p.Size = UDim2.fromOffset(300, 100); p.Position = UDim2.fromOffset(20, 80); p.Parent = sg'''
        self.assertIn('ui.covered', rules(code, 'FAIL', ['desktop']))
    def test_offscreen(self):
        code = HDR + 'local f = Instance.new("Frame"); f.Size = UDim2.fromOffset(1100, 640); f.Parent = sg'
        r = rules(code, 'FAIL', ['phone-landscape'])
        self.assertIn('ui.offscreen', r); self.assertIn('ui.fixed_size_too_big', r)
    def test_topbar_overlap_only_when_inset_ignored(self):
        bad = 'local sg = Instance.new("ScreenGui"); sg.IgnoreGuiInset = true; sg.Parent = game.Players.LocalPlayer.PlayerGui\nlocal t = Instance.new("TextLabel"); t.Text = "TITLE"; t.Size = UDim2.fromOffset(200, 30); t.Position = UDim2.fromOffset(10, 8); t.Parent = sg'
        self.assertIn('ui.topbar_overlap', rules(bad, 'FAIL', ['phone-landscape']))
        good = bad.replace('sg.IgnoreGuiInset = true', 'sg.IgnoreGuiInset = false')
        self.assertNotIn('ui.topbar_overlap', rules(good, None, ['phone-landscape']))
    def test_text_overflow_and_scaled_ok(self):
        t = HDR + 'local t = Instance.new("TextLabel"); t.Text = "A very long label that cannot fit"; t.TextSize = 20; t.Size = UDim2.fromOffset(100, 30); t.Parent = sg'
        self.assertIn('ui.text_overflow', rules(t, 'FAIL', ['desktop']))
        ok = t.replace('t.Parent = sg', 't.TextWrapped = true; t.Size = UDim2.fromOffset(100, 120); t.Parent = sg')
        self.assertNotIn('ui.text_overflow', rules(ok, None, ['desktop']))
    def test_small_text_and_touch_target(self):
        code = HDR + 'local b = Instance.new("TextButton"); b.Text = "OK"; b.TextSize = 9; b.Size = UDim2.fromOffset(20, 20); b.Parent = sg'
        r = rules(code, 'FAIL', ['phone-landscape'])
        self.assertIn('ui.text_small', r); self.assertIn('ui.touch_target', r)
    def test_contrast(self):
        code = HDR + 'local f = Instance.new("Frame"); f.Size = UDim2.fromOffset(200, 60); f.BackgroundColor3 = Color3.fromRGB(30, 30, 30); f.Parent = sg\nlocal t = Instance.new("TextLabel"); t.Text = "Low contrast"; t.TextColor3 = Color3.fromRGB(40, 40, 40); t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(1, 1); t.Parent = f'
        self.assertIn('ui.contrast', rules(code, None, ['desktop']))
    def test_breakpoint_uses_viewport(self):
        code = HDR + '''
local vp = workspace.CurrentCamera.ViewportSize
local f = Instance.new("Frame"); f.Parent = sg
if vp.X < 700 then f.Size = UDim2.new(1, 0, 0, 100) else f.Size = UDim2.fromOffset(2500, 100) end'''
        self.assertNotIn('ui.offscreen', rules(code, None, ['phone-portrait']))
        self.assertIn('ui.offscreen', rules(code, None, ['desktop']))
    def test_helper_function_and_loop(self):
        code = HDR + '''
local function make(class, props, parent)
  local i = Instance.new(class)
  for k, v in pairs(props) do i[k] = v end
  i.Parent = parent
  return i
end
local root = make("Frame", {Size = UDim2.fromScale(1, 1)}, sg)
for i = 1, 3 do make("TextLabel", {Text = "Same spot", Size = UDim2.fromOffset(100, 30)}, root) end'''
        self.assertIn('ui.overlap', rules(code, 'FAIL', ['desktop']))
    def test_grid_and_scrolling(self):
        code = HDR + '''
local s = Instance.new("ScrollingFrame"); s.Size = UDim2.fromOffset(300, 200); s.AutomaticCanvasSize = Enum.AutomaticSize.Y; s.Parent = sg
local g = Instance.new("UIGridLayout"); g.CellSize = UDim2.fromOffset(90, 90); g.Parent = s
for i = 1, 12 do local c = Instance.new("TextButton"); c.Text = "Item " .. i; c.Parent = s end'''
        self.assertEqual(rules(code, 'FAIL', ['desktop']), set())
    def test_destroyed_nodes_ignored(self):
        code = HDR + 'local a = Instance.new("TextLabel"); a.Text = "x"; a.Size = UDim2.fromOffset(500, 500); a.Parent = sg; a:Destroy()'
        self.assertEqual(rules(code, 'FAIL', ['phone-landscape']), set())
    def test_allow_overlap_directive(self):
        code = '-- ui-lint: allow-overlap\n' + HDR + '''
local a = Instance.new("TextLabel"); a.Text = "A"; a.Size = UDim2.fromOffset(100, 40); a.Parent = sg
local b = Instance.new("TextLabel"); b.Text = "B"; b.Size = UDim2.fromOffset(100, 40); b.Parent = sg'''
        self.assertNotIn('ui.overlap', rules(code, None, ['desktop']))
    def test_glyph_icon(self):
        code = HDR + 'local b = Instance.new("TextButton"); b.Text = "\u26a1"; b.Size = UDim2.fromOffset(44, 44); b.Parent = sg'
        self.assertIn('ui.glyph_icon', rules(code, 'FAIL', ['desktop']))
    def test_oop_component(self):
        code = HDR + '''
local Card = {}; Card.__index = Card
function Card.new(parent, text)
  local self = setmetatable({}, Card)
  self.frame = Instance.new("TextLabel"); self.frame.Text = text; self.frame.Size = UDim2.fromOffset(100, 30); self.frame.Parent = parent
  return self
end
Card.new(sg, "one"); Card.new(sg, "two")'''
        self.assertIn('ui.overlap', rules(code, 'FAIL', ['desktop']))

class InsetSemantics(unittest.TestCase):
    STRIP = 'local sg = Instance.new("ScreenGui")\nsg.ScreenInsets = Enum.ScreenInsets.TopbarSafeInsets\nsg.Parent = game.Players.LocalPlayer.PlayerGui\nlocal root = Instance.new("Frame"); root.Size = UDim2.fromScale(1, 1); root.Parent = sg\nlocal l = Instance.new("UIListLayout"); l.Parent = root\nlocal h = Instance.new("Frame"); h.Size = UDim2.new(1, 0, 0, 48); h.Parent = root\nlocal b = Instance.new("Frame"); b.Size = UDim2.new(1, 0, 1, -56); b.Parent = root\nlocal t = Instance.new("TextLabel"); t.Text = "Hello"; t.Size = UDim2.new(1, 0, 0, 30); t.Parent = b'
    def test_topbar_safe_insets_is_a_fail(self):
        self.assertIn('ui.screeninsets_topbar_strip', rules(self.STRIP, 'FAIL', ['phone-landscape']))
    def test_default_insets_are_fine(self):
        ok = self.STRIP.replace('sg.ScreenInsets = Enum.ScreenInsets.TopbarSafeInsets\n', '')
        self.assertNotIn('ui.screeninsets_topbar_strip', rules(ok, None, ['phone-landscape']))
    def test_collapsed_scrolling_frame(self):
        code = HDR + 'local s = Instance.new("ScrollingFrame"); s.Size = UDim2.new(1, 0, 0, 4); s.Parent = sg\nlocal t = Instance.new("TextLabel"); t.Text = "Hidden"; t.Size = UDim2.fromOffset(200, 40); t.Parent = s'
        self.assertIn('ui.collapsed_container', rules(code, 'FAIL', ['desktop']))
    def test_negative_size_math_collapses(self):
        code = HDR + 'local p = Instance.new("Frame"); p.Size = UDim2.new(1, 0, 0, 40); p.Parent = sg\nlocal body = Instance.new("Frame"); body.Size = UDim2.new(1, 0, 1, -900); body.ClipsDescendants = true; body.Parent = sg\nlocal t = Instance.new("TextLabel"); t.Text = "Hidden"; t.Size = UDim2.fromOffset(200, 40); t.Parent = body'
        self.assertIn('ui.collapsed_container', rules(code, 'FAIL', ['phone-landscape']))
    def test_absolute_size_is_modelled(self):
        code = HDR + 'local s = sg.AbsoluteSize\nlocal f = Instance.new("Frame"); f.Size = UDim2.fromOffset(s.X + 500, 40); f.Parent = sg'
        self.assertIn('ui.offscreen', rules(code, None, ['phone-landscape']))

class LegacyRules(unittest.TestCase):
    def test_emoji_in_log(self):
        self.assertIn('emoji.in_log', rules('print("\u2705 ready")'))
    def test_repeated_and_suspicious_asset_ids(self):
        code = 'local a = "rbxassetid://1234567890"\nlocal b = "rbxassetid://1234567890"\nlocal c = "rbxassetid://1234567890"\nlocal d = "rbxassetid://1111111"'
        r = rules(code, 'FAIL'); self.assertIn('asset.repeated_id', r); self.assertIn('asset.suspicious_id', r)
    def test_loading_never_hidden_and_unguarded_init(self):
        code = 'local l = Instance.new("TextLabel")\nl.Text = "Loading"\nlocal m = {}\nm:Init()'
        r = rules(code, 'WARN'); self.assertIn('ui.loading_never_hidden', r); self.assertIn('lifecycle.unguarded_init', r)
    def test_unparseable_file_is_a_fail_not_a_silent_pass(self):
        r = run('local x = = =')
        self.assertTrue(any(f['rule'] == 'ui.layout_unchecked' and f['severity'] == 'FAIL' for f in r))
    def test_optional_types_parse(self):
        code = HDR + 'local function f(a: number?, b: {[string]: any}?): string? return nil end\nlocal x = (f(1) :: string?)\nlocal t = Instance.new("TextLabel"); t.Text = "ok"; t.Size = UDim2.fromOffset(100, 30); t.Parent = sg'
        self.assertFalse(any(f['rule'] == 'ui.layout_unchecked' for f in run(code, ['desktop'])))
    def test_no_ui_in_file(self):
        r = run('print("hello")')
        self.assertFalse([f for f in r if f['severity'] == 'FAIL'])

if __name__ == '__main__':
    unittest.main(verbosity=1)
