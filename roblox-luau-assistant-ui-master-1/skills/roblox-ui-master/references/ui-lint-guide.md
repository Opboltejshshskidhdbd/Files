# UI lint guide (scripts/ui_lint.py)

```
python scripts/ui_lint.py MyUi.client.luau --png out/            # all viewports + preview PNGs
python scripts/ui_lint.py MyUi.client.luau --viewports phone-landscape,desktop
python scripts/ui_lint.py MyUi.client.luau --map                  # print computed rectangles
python scripts/ui_lint.py MyUi.client.luau --json                 # machine readable
python scripts/ui_lint.py a.luau b.luau --all --fail-on-warn
```
Exit code 1 when any FAIL. When a root cause such as ui.screeninsets_topbar_strip is found, its consequential findings are hidden (`ui.consequential_hidden`): fix the cause first and re-run. Previews: red outlines = flagged nodes, red block top-left = Roblox top bar zone (only drawn when the ScreenGui ignores the inset).

## How it works
It parses the Luau, symbolically runs the UI-building code (helper functions, loops, tables, metatable classes, `Instance.new`, `workspace.CurrentCamera.ViewportSize` and `UserInputService.TouchEnabled` are modelled per viewport), rebuilds the Instance tree and computes rectangles (UDim2, AnchorPoint, UIListLayout, UIGridLayout, UIPadding, UISizeConstraint, UIAspectRatioConstraint, UIScale, AutomaticSize, ScrollingFrame canvas, text measurement). It is an ESTIMATE of the layout, not Roblox.

## Rules
| rule | sev | meaning | usual fix |
|---|---|---|---|
| ui.screeninsets_topbar_strip | FAIL | ScreenInsets = TopbarSafeInsets: the ScreenGui is only the top-bar strip, layout collapses | delete the ScreenInsets line (default insets) |
| ui.collapsed_container | FAIL/WARN | a container is ~0px but holds content (clipped: hidden) | fix Size math / insets (negative offsets vs real parent size) |
| ui.footprint | INFO/WARN | how much of the screen the main UI covers per viewport | fluid sizes from the real available area |
| ui.layout_unchecked | FAIL | the engine could not analyze the file: layout NOT verified | fix syntax / simplify; never report "lint passed" |
| ui.topbar_overlap | FAIL | text/button under logo/menu/chat (ScreenGui ignores the inset) | IgnoreGuiInset=false (default insets) |
| ui.screeninsets_nondefault | WARN | any other explicit ScreenInsets value | verify on device / remove |
| ui.covered | FAIL | text/button/image hidden by a panel drawn above it | same layout container, or fix ZIndex/regions |
| ui.overlap | FAIL | two readable/clickable things on the same spot | list/grid layout |
| ui.panel_overlap | FAIL/WARN | panels stacked on panels | separate regions; overlays named ...Toast/...Overlay |
| ui.offscreen | FAIL/WARN | content outside the screen | scale sizes, ScrollingFrame, compact class |
| ui.overflow_parent | FAIL/WARN | child sticks out of its panel (clipped if ClipsDescendants) | resize/relayout |
| ui.fixed_size_too_big | FAIL | pixel-sized container >= 90% of phone viewport | scale + UISizeConstraint |
| ui.text_overflow | FAIL/WARN | text wider/taller than its box | widen, wrap+AutomaticSize.Y, shorten |
| ui.text_truncated | WARN | text will end with "..." | widen or shorten |
| ui.text_small | FAIL/WARN | effective text < 12px (FAIL < 10) | raise TextSize / MinTextSize |
| ui.touch_target | FAIL/WARN | button < 24px (FAIL) / < 38px (WARN) on phones | 40-44px |
| ui.contrast | FAIL/WARN | text/background contrast < 3 (FAIL < 1.6) | adjust colors |
| ui.glyph_icon / emoji.* | FAIL/WARN | emoji or symbol used as an icon / in text or logs | drawn icons / ASCII logs |
| asset.* | FAIL/WARN | fabricated, repeated or inline asset ids | real ids in an AssetManifest |
| ui.default_size | WARN | no Size set (200x50 default) | set Size |
| ui.zindex_behavior | INFO | ScreenGui has no ZIndexBehavior | Sibling |
| ui.loading_never_hidden, lifecycle.unguarded_init | WARN | leftovers from generated code | hide/destroy, guard :Init() |
| ui.layout_coverage | INFO | what the engine understood / skipped | read it: skipped statements mean partial coverage |

Intentional overlap: name the node `...Overlay/...Toast/...Modal/...Glow/...Shadow/...Decor` or add `-- ui-lint: allow-overlap` (silences all overlap checks in the file - use sparingly).

## Reading results honestly
0 FAIL does not prove it looks good. Always say: "passes the bundled layout lint on 5 viewports (estimate)". If `ui.layout_coverage` reports skipped statements or "no UI tree", say that layout checks were partial/not possible.
