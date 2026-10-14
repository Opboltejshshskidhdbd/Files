# UI design system (tokens)

## Palette (choose one theme, keep all colors in a THEME table)
| role | NEON (default) | CLEAN | FOREST |
|---|---|---|---|
| panel | 16,18,38 | 245,246,250 | 22,32,26 |
| panelLight | 26,29,56 | 255,255,255 | 32,46,38 |
| stroke | 70,78,140 | 200,205,220 | 70,110,84 |
| primary | 0,229,255 | 40,110,255 | 120,220,140 |
| secondary | 139,92,246 | 120,80,240 | 240,200,90 |
| highlight | 255,92,170 | 255,110,90 | 255,140,80 |
| success | 70,230,140 | 40,180,110 | 120,220,140 |
| text | 240,244,255 | 22,26,40 | 236,244,236 |
| muted | 160,168,205 | 100,108,130 | 160,180,164 |
| dark (text on primary) | 8,10,24 | 255,255,255 | 10,20,12 |
Rules: text on panel >= 4.5:1; text on primary uses `dark`; never pure black backgrounds.

## Type scale (px)
caption/label 12 | body 13-14 | button 14-16 | subtitle 16 | title 20-24 | hero 28-36. Minimum 12 everywhere. Line height ~1.15-1.25 (use `LineHeight` 1.0-1.1 for dense UI).
Fonts: `Enum.Font.GothamBlack` titles, `GothamBold` labels/buttons, `Gotham` body. (Custom fonts only via real `Font.fromName`/asset ids.)

## Spacing / shape
Spacing: 4, 8, 12, 16, 24, 32. Padding inside panels 12-16 (8 on compact). Gap between regions 12 (8 on compact).
Radius: panel 14, card 14, control 10-12, pill = height/2. Stroke 1px, transparency 0.5-0.6; hover 0.1-0.2.
Elevation without shadows: slightly lighter panel + stroke + subtle `UIGradient` (rotation 90, white -> 190,195,230).

## Motion
hover/press 0.08-0.15 s Quad Out | appear 0.25-0.3 s | disappear 0.3 s | pulse 1.6 s Sine InOut repeat -1 reverse.
Press feedback: `UIScale` 1 -> 0.96 on MouseButton1Down, back on Up.

## Component sizes (px)
nav button 40-48 | header 48 (compact) / 64 (full) | card height 72-74 (compact) / 100-110 (full) | progress bar 8 | avatar 28 | toast 44 high x 250 wide.
