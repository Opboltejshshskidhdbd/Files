---
name: roblox-ui-master
description: Build, redesign, review or debug Roblox UI (ScreenGui, HUD, menus, shop, inventory, dialogs, toasts, leaderboards, settings; mobile-first and responsive). Produces polished, correctly sized UI that never sits under the Roblox top bar, never overlaps itself, always delivers the complete code in the final reply, and is checked by the bundled multi-viewport layout lint plus Level 3 validation.
---
# ROBLOX UI MASTER v1.1

Use for ANY request that creates or changes Roblox user interface ("make a UI", "menu", "HUD", "shop", "inventory", "crazy UI", "fix my GUI", "mobile UI", "responsive", "animations for my UI"). Runs together with the normal Level 1/2/3 engineering gate; it adds a UI gate on top.

## 0. DELIVERY CONTRACT (non-negotiable)
The final reply of a UI task MUST contain the complete, copy-pasteable code.
1. Never finish a turn with only a preview, design description, bullet list of features or a validation claim. If code was not delivered, deliver it in the next sentence - do not wait for the user to ask "code do".
2. Final reply layout, in this order: (a) one line: what it is and the style; (b) WHERE TO PASTE (exact Explorer path and script class); (c) the FULL code; (d) validation receipt (real numbers only); (e) what is demo/placeholder and where to wire real data; (f) honest limits.
3. If the host can create files, create the file and present it AND still print the code (or parts) when the user is on chat/mobile. Long code: split into PART 1/2/3 inside the same reply, each part complete lines - never truncate, never "rest is similar".
4. Never claim a check passed unless it ran in this turn. Say "not run" when a tool was unavailable.

## 1. Workflow (all steps, in order)
1. BRIEF: if the user says "your choice / crazy / best", pick a strong style yourself and go - do not ask questions.
2. TOKENS: palette (>= 6 colors), max 2 fonts, type scale, 8px spacing grid, radius, motion durations -> `references/ui-design-system.md`.
3. LAYOUT PLAN: write a short region tree BEFORE code (ScreenGui -> Root(padding) -> list/grid containers) for the 3 screen classes below. Anything that must not overlap lives in the same UIListLayout/UIGridLayout/ScrollingFrame.
4. CODE with the kit in `references/ui-kit.luau` (make, panel, label, row, column, pad, round, outline, drawIcon, tween, pressFeedback, toast). Golden example: `references/example-neon-nexus.client.luau`. Recipes: `references/ui-recipes.md`.
5. UI LINT: `python scripts/ui_lint.py <file> --png <dir>` (all 5 viewports). Fix every FAIL, review every WARN, max 3 loops. If Python is unavailable say "UI lint not run" and walk `references/ui-qa-checklist.md` manually.
6. LEVEL 1/2/3: call `validate_external_luau` with `context:"client"` (and `modules` for multi-file). Fix errors; keep warnings you consciously accept.
7. DELIVER per section 0. Include the lint and Level 3 numbers.

## 2. Screen classes (decide with workspace.CurrentCamera.ViewportSize, rebuild or relayout on change)
| class | when | pad / gap | header | nav | side panel | columns | notes |
|---|---|---|---|---|---|---|---|
| portrait | available width < 560 or width < height | 8 / 8 | 48 | 44-48 | hidden (stats move into scroll column) | 2 | main column is a ScrollingFrame |
| compact | width < 1000 or height < 480 (side panel only when width >= 760) | 8 / 8 | 48 | 48-52 | 190 or hidden | 4 | phone landscape: usable height is only ~300 after the top bar; hero/cards heights are fluid (clamped) |
| full | otherwise | 16 / 12 | 64 | 64 | 260 | 4 | no scrolling, content centered vertically, heights clamped so big screens do not stretch |
"available" = the ScreenGui area, not the raw viewport. Test viewports used by the lint: phone-small 640x360, phone-landscape 800x360, phone-large 932x430, phone-portrait 360x780, tablet 1024x768, laptop 1366x768, desktop 1920x1080.

## 3. Hard rules (each maps to a lint rule)
1. SAFE AREA: keep the ScreenGui's DEFAULT insets: `IgnoreGuiInset = false` and do NOT set `ScreenInsets`. NEVER use `Enum.ScreenInsets.TopbarSafeInsets` for normal UI: it confines the ScreenGui to the thin top-bar strip beside the Roblox buttons (confirmed on device: the layout collapsed to a ~10px sliver and every ScrollingFrame clipped its content). Never put text/buttons under the Roblox logo/menu/chat cluster (top-left 172x58); `IgnoreGuiInset = true` only for non-interactive full-bleed backdrops. [ui.screeninsets_topbar_strip, ui.collapsed_container, ui.topbar_overlap]
1b. USE THE REAL AREA: compute sizes from the available area (`ViewportSize` minus `GuiService:GetGuiInset().Y`), then re-check with `gui.AbsoluteSize` (`gui:GetPropertyChangedSignal("AbsoluteSize")`, rebuild only if the layout key changes). Make heights fluid (`math.clamp(fraction * bodyHeight, min, max)`) so the UI fills the screen: a main UI that covers < ~70% of the screen on phones/tablets is a defect unless it is a deliberate HUD. [ui.footprint]
2. NO OVERLAP: regions are siblings in a UIListLayout/UIGridLayout or children of a ScrollingFrame. Absolute Position is for single anchored items only (orb, badge, toast host). Never anchor a row to the bottom edge (`Position Y = (1, -N)`) next to a panel sized with scale: they collide on short screens. [ui.overlap, ui.covered, ui.panel_overlap]
3. SIZES: scale + constraints. No container with a fixed pixel size >= 90% of a phone viewport. Use UISizeConstraint / UIAspectRatioConstraint; keep the design inside the screen class table. [ui.fixed_size_too_big, ui.offscreen, ui.overflow_parent]
4. SCROLL, DON'T SQUEEZE: on small classes the content column is a `ScrollingFrame` with `AutomaticCanvasSize = Y`, `ScrollingDirection = Y`. [ui.offscreen]
5. TEXT: effective size >= 12 px (body 13-14). Fixed-size labels must fit: wrap + AutomaticSize.Y for paragraphs; TextScaled only with `UITextSizeConstraint` (Min >= 12). Prefer short labels over shrinking. [ui.text_overflow, ui.text_truncated, ui.text_small]
6. TOUCH: every button >= 40x40 px (44 ideal). [ui.touch_target]
7. ICONS: no emoji, no symbol glyphs (they render as empty boxes on some devices). Draw icons with Frames (`drawIcon`) or use verified assets. NEVER invent `rbxassetid://` ids; keep real ids in an AssetManifest. [ui.glyph_icon, asset.*, emoji.*]
8. CONTRAST: body text >= 4.5:1, never below 3:1. [ui.contrast]
9. INPUT: hover is not available on touch. Every hover effect needs a press feedback (MouseButton1Down/Up or Activated). Use `Activated` for clicks.
10. CONNECTIONS: one connection per object; rebuild functions `Destroy()` the previous ScreenGui; never `Connect` the same object repeatedly in a loop or event handler. [connect-in-loop, connection-leak]
11. ANIMATION: TweenService (looping tweens with repeat -1 for pulses); no per-frame loops for decoration; no `while true` for UI.
12. STRUCTURE: set `Parent` last; `ResetOnSpawn=false` for persistent menus; `ZIndexBehavior=Sibling`; use `LayoutOrder` with `SortOrder.LayoutOrder`; name every instance.
13. OVERLAYS (toast/modal/tooltip): named `...Toast/...Modal/...Overlay`; toasts go top-center under the header (max 3, transient). Keep the bottom-left (thumbstick) and bottom-right (jump button) corners free on touch devices; a full-screen menu needs a close button; modals add a dim backdrop and are the only interactive layer.
14. DATA: demo values live in one `DEMO` table and are labelled; real values come from one state table. No fake claims (fake ping, fake player counts).
15. DEFAULTS: always set `Size` (Roblox default 200x50 is rarely intended) and `BorderSizePixel=0`. [ui.default_size]
16. CONSOLE/GAMEPAD (when relevant): `Selectable` buttons and a sensible `SelectionImageObject`.
17. Do not encode state by color alone (add text/shape).

## 4. Visual polish rules
- 8px grid; radius 10-16 on panels, 8-12 on controls; 1px UIStroke at ~0.5 transparency; glass = solid dark base with `BackgroundTransparency` 0.1-0.2 (Roblox has no real blur).
- Max 2 accent colors + 1 highlight; accent used for state/primary action only.
- Title font Gotham Black, labels Gotham Bold, body Gotham; ALL CAPS only for short labels.
- Visual hierarchy: one hero element, supporting cards equal in size, secondary info muted.
- Motion: 120-180 ms ease-out for hover/press, 250-300 ms for appear/disappear, ambient pulses 1.5-2.5 s Sine; never animate layout containers.
- Empty/loading/error states are part of the design (skeleton or muted text).

## 5. Anti-patterns -> fix
| symptom (seen in real output) | fix |
|---|---|
| title hidden under Roblox top bar | `IgnoreGuiInset = false`, leave `ScreenInsets` unset (default insets) |
| bottom cards cover hero text/CTA | cards live in the same vertical UIListLayout (or ScrollingFrame) as the hero |
| toast sits on top of cards | toast host top-center under the header, max 3, transient, own UIListLayout |
| UI collapsed to a ~10px strip, only one panel visible, ScrollingFrame scrolls inside a sliver | remove `ScreenInsets = TopbarSafeInsets`; check negative-offset Size math (`1, -N`) against the real parent size |
| ⚡ 📱 shown as boxes | drawIcon(kind) from Frames |
| UI cut at the bottom on phones | fixed offsets -> scale + ScrollingFrame; compact class |
| tiny unreadable text after shrinking | compact class with its own TextSize; never rely on UIScale shrink |
| every button animates but touch does nothing | add MouseButton1Down/Up tween + Activated handler |

## 6. Unverified Roblox facts (hard rule)
Never encode Roblox behavior you are not certain about. If a design depends on semantics such as `ScreenInsets`, `GuiInset`, `TextScaled` limits, `ZIndex`/`DisplayOrder` interplay, safe areas or controls layout, verify it in the official documentation (web search) BEFORE using it; if you cannot verify, do not use it - use the default, or isolate it behind one constant and tell the user to test on a device. The bundled lint/engine rests on assumptions too; a device recording can falsify them. A wrong assumption in a "golden example" is copied everywhere - this already happened once with `TopbarSafeInsets`.
After delivery, invite a device check: ask for a screenshot/screen recording; extract frames, compare against the layout plan, and fix (this loop found the TopbarSafeInsets collapse).

## 7. What you may claim
UI lint = estimate of the layout from the code (not Roblox itself); runtime-created/tweened layout and unresolved values are skipped (reported as coverage). Level 3 = external static validator, not the official compiler. Say the UI "passes the bundled layout lint on 5 viewports and Level 3 validation" - never "pixel-perfect" or "tested on device" unless a device screenshot/recording was actually provided and reviewed.

## References
`references/ui-design-system.md` | `references/ui-layout-rules.md` | `references/ui-recipes.md` | `references/ui-kit.luau` | `references/example-neon-nexus.client.luau` | `references/ui-lint-guide.md` | `references/ui-qa-checklist.md` | `references/known-failures.md`
