# UI QA checklist (use when the lint cannot run, and as the final self-review)

Safe area
- [ ] IgnoreGuiInset = false and ScreenInsets NOT set (never TopbarSafeInsets); a full-bleed backdrop is the only exception and is non-interactive
- [ ] nothing readable/clickable in the top-left 172x58 zone

Layout
- [ ] every region is inside a UIListLayout / UIGridLayout / ScrollingFrame; no bottom-anchored row next to scaled panels
- [ ] sizes: scale + constraints; no pixel container >= 90% of 800x360
- [ ] the main column scrolls on compact/portrait (AutomaticCanvasSize = Y)
- [ ] compact (800x360) fits: header 48 + gap 8 + body ~230px; portrait (360 wide) has no horizontal overflow
- [ ] large screens: content centered, no giant empty top-heavy layout
- [ ] the main UI uses >= ~70% of the screen on phones/tablets (fluid clamped heights, sizes from the real available area / gui.AbsoluteSize)
- [ ] after a layout rebuild the previous ScreenGui is destroyed; the AbsoluteSize re-check cannot loop

Text
- [ ] all text >= 12px effective; paragraphs wrap with AutomaticSize.Y; one-liners fit or are intentionally truncated
- [ ] contrast >= 4.5:1 for body text

Input
- [ ] every button >= 40x40; hover effects also have press feedback; clicks use Activated
- [ ] no Connect inside loops on a shared object; rebuild functions Destroy the old GUI

Assets and icons
- [ ] no emoji/symbol icons; icons drawn or verified assets; no invented rbxassetid

Polish
- [ ] one theme table, 2 fonts max, 8px spacing, consistent radius/stroke
- [ ] hover/press/appear animations short (0.08-0.3 s); looping tweens only for ambient accents
- [ ] demo values clearly marked and wired through one table

Delivery
- [ ] complete code in the final reply (or all parts), paste location stated, validation numbers real, limits stated
- [ ] no unverified Roblox behavior used (ScreenInsets etc.); device test requested (screenshot/recording)
