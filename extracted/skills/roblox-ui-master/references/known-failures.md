# Known failures seen on real devices (keep this list growing)

## 1. ScreenInsets = TopbarSafeInsets collapses the whole UI (confirmed on device, landscape phone)
- Symptom: header fine, everything below it is a ~10px strip; only auto-height panels (side stats) are visible; the main ScrollingFrame scrolls inside a sliver; the UI starts right of the Roblox buttons and covers a fraction of the screen.
- Cause: `TopbarSafeInsets` confines the ScreenGui to the top-bar strip; `UDim2.new(1, 0, 1, -(header+gap))` then becomes ~0 or negative.
- Fix: never set ScreenInsets for normal UI; keep `IgnoreGuiInset = false`. Lint: ui.screeninsets_topbar_strip / ui.collapsed_container. Worker rule: screeninsets-topbar-strip.
- Origin: this plugin's own earlier guidance was wrong (an unverified assumption). Rule 6 of SKILL.md exists because of this.

## 2. Bottom row absolute-positioned over scaled panels (v1 NEON NEXUS)
- Symptom: module cards cover hero text and the CTA button; toast sits on the cards; title under the Roblox buttons; emoji icons render as boxes.
- Fix: one vertical list (or ScrollingFrame) holds hero + cards; default insets; drawn icons. Lint: ui.covered, ui.panel_overlap, ui.topbar_overlap, ui.glyph_icon.

## 3. Long labels in narrow boxes
- Symptom: "Players in this..." truncated in the side panel. Fix: short labels ("Players"), or wrap + AutomaticSize.Y. Lint: ui.text_truncated.

## 4. A lint that cannot parse the file must not pass
- Symptom: a typed file (`number?`) made the layout engine bail out and the summary read 0 FAIL. Fix: ui.layout_unchecked is now a FAIL; never say "lint passed" in that case.
