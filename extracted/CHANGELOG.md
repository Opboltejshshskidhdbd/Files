# Changelog

## 1.15.1-ui-master (device-feedback fix)
- CORRECTION: the UI Master guidance and the golden example used `ScreenInsets = Enum.ScreenInsets.TopbarSafeInsets`. On a real device that confines the ScreenGui to the top-bar strip: header visible, everything else collapsed to a ~10px sliver, ScrollingFrame clipping all content. Removed everywhere; default insets (`IgnoreGuiInset=false`, no ScreenInsets) are now required.
- Lint v2.1: models ScreenInsets/IgnoreGuiInset regions; new rules `ui.screeninsets_topbar_strip`, `ui.collapsed_container`, `ui.footprint`, `ui.layout_unchecked` (an unparsable file is now a FAIL, never a silent pass), `ui.screeninsets_nondefault`; consequential findings are hidden behind the root cause; parser fixed for optional types (`number?`); `ScreenGui.AbsoluteSize` modelled; 7 viewports (adds 640x360 and 932x430).
- Golden example NEON NEXUS v3: default insets, fluid sizes from the real available area, AbsoluteSize self-correction, narrow phones hide the side panel, toast top-center (max 3), no truncated labels.
- Skill v1.1: fluid-size rule, "unverified Roblox facts" hard rule, device-feedback loop, `references/known-failures.md`.
- Worker v4.2: rule `screeninsets-topbar-strip`.

## 1.15.0-ui-master
- New skill `roblox-ui-master`: delivery contract (always output the full code), design tokens, responsive screen classes, hard UI rules, recipes, reusable kit (`references/ui-kit.luau`) and a golden example (responsive NEON NEXUS v2).
- `scripts/ui_lint.py` v2 + `ui_parse.py` / `ui_interp.py` / `ui_layout.py`: symbolic execution of UI-building Luau and a layout engine that checks 5 viewports (overlap, covered text, off-screen, top-bar overlap, text overflow/size, touch targets, contrast, fixed-pixel layouts, glyph icons). Keeps all legacy rules (emoji in logs, fabricated asset ids, loading never hidden, unguarded Init). 22 unit tests (`tests/test_ui_lint.py`).
- Worker v4.1 (`cloudflare/worker-single.js`): `connect-in-loop` no longer fires for per-item connections (each button's own MouseEnter), optional-parameter idioms no longer trigger `arg-count`, plus everything from v4 (verdict, modules/context arguments, remote contracts).
- Main + enforcement skills: UI section and UI delivery gate.

## 1.14.2-worker-mcp
- Default MCP is now the Cloudflare Worker itself: `https://luau-validator.oboltr895.workers.dev/mcp` (Streamable HTTP, no Render cold start). Local stdio server kept as `mcp.local.example.json`; Render SSE is legacy.
- Worker (`worker-single.js`) fixes: `@native`/`@checked` attributes, `5.` number literals, ~30 more Roblox services (no false `unknown-service`), CORS for MCP, `/health`, `/mcp`.

## 1.14.1-mcp-fix
### Fixed
- Plugin did not appear in `@` mention / "Try in chat" did nothing: manifests are now consistent (same version, `skills` and `mcpServers` declared, 3 short starter prompts), junk files (`.codex-plugin.json.tmp`, `.github_dummy`, `__pycache__`) removed.
- MCP: the remote Render SSE server (code not in this package, cold starts, SSE) was a single point of failure. Added a bundled local stdio MCP server `mcp/luau_validator_mcp.py` (tools: `validate_external_luau`, `validate_luau_syntax`, `server_status`). Remote config kept as `mcp.remote.example.json`.
- Level 2 parser: parenthesised expressions `(a + b) / c`, `(f or g)()` and dotted/method function names `function A.b.c:d()` were wrongly reported as syntax errors.
- `scripts/validate_dataset.py` ignored the dataset's `output` field (reported 0 entries) and crashed on dict results.
- CI workflow validated Python files as Luau (always failed); now runs the test-suite.
- Skill docs no longer contradict each other about whether Level 3 is callable.

## 1.13.0-external — Level 3 External Luau Validation
Added Level 3 external client, receipts, hash invalidation, 3-attempt repair contract.
