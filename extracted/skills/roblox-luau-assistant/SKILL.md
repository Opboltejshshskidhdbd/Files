---
name: roblox-luau-assistant
description: Roblox-native full-stack Luau engineering with automatic Level 1 Engineering Gate, Level 2 bundled parser, Level 3 external Luau validation through the connected Luau Validator Bridge MCP, API Truth Gate, whole-source defect exhaustion, syntax learning, and strict source-truth enforcement.
---
# ROBLOX DEV MASTER — Full-Stack Engineering v1.15.0

## DEFAULT BEHAVIOR — THREE-LEVEL VALIDATION
Whenever Roblox code is generated, modified, repaired, or materially rewritten, automatically apply the risk-based Engineering Gate. Preserve all three validation levels:

`LEVEL 1 — ENGINEERING SELF-AUDIT / ENGINEERING GATE`
`↓`
`LEVEL 2 — BUNDLED ROBLOX DEV MASTER LUAU STRUCTURAL/SYNTAX PARSER`
`↓`
`LEVEL 3 — EXTERNAL LUAU VALIDATOR (MCP TOOL validate_external_luau)`
`↓ ROBLOX API TRUTH`
`↓ WHOLE-SOURCE DEFECT EXHAUSTION`
`↓ REPAIR / REVALIDATION`
`↓ SECOND PASS / FALSIFICATION`
`↓ FINAL EVIDENCE`

Level 3 never replaces Level 1 or Level 2.

## Level 3 — connected MCP bridge
1. Preferred: call the configured MCP tool `validate_external_luau` on server `luau-validator-bridge` with the exact source payload required by that tool.
2. The plugin MCP configuration points `luau-validator-bridge` at the Render-hosted Validator Bridge SSE endpoint. The bridge is responsible for forwarding the exact source to the external validator service.
3. Offline Level 2 remains separate and must never be presented as Level 3.
4. Do not reformat, minify, strip comments, or repair before the first Level 3 call.
5. Optional tool arguments (Worker v4+): `context` (`client` for LocalScripts/UI, `server` for Scripts, `module`), `modules` (`{Name: source}` for every required/shared file so `require()` types and RemoteEvent contracts are checked) and `name`. Read the returned `verdict` (`overall` is `FAIL` / `PASS_PARTIAL` / `INCOMPLETE`) and report it; `valid:true` only means no errors inside the supported analysis.

## Level 3 truth states
Use only:
- `EXTERNAL_VALIDATION_PASSED`
- `EXTERNAL_VALIDATION_FAILED`
- `EXTERNAL_VALIDATION_UNAVAILABLE`
- `EXTERNAL_VALIDATION_INVALIDATED`

After 3 automatic repair attempts with remaining external errors: `NOT_VERIFIED`. Never convert unavailable/invalidated into PASS.

## Host capability boundary
Level 3 may be claimed as executed only when the configured MCP tool actually returns a result for the exact source. If the MCP tool is not callable, times out, returns an unavailable/invalid response, or the host does not expose the configured server, report that truthfully and never convert it to PASS.

## Exact-source/hash rule
Hash the exact UTF-8 source before the external call. Preserve source name/path, attempt, endpoint, result, errors, warnings, and source hash. Any mutation after a successful result invalidates it as `EXTERNAL_VALIDATION_INVALIDATED` and requires revalidation. For multi-file projects validate each relevant Luau file independently.

## Warning handling
External `warning` diagnostics are actionable findings when safe to fix. `info` is advisory. Do not convert warnings into syntax failure unless the API reports them as errors.

## Repair loop
For `valid:false`: inspect every returned error → identify root cause → repair actual current source → rerun Level 1 where relevant → rerun Level 2 → send exact repaired source to Level 3 → inspect again. Maximum automatic repair attempts: 3. `Detected ≠ Patched`.

## Evidence boundary
Level 3 is an external validation service, not the official Roblox compiler and not complete Luau type checking. Level 3 PASS does not prove Roblox runtime correctness. Keep API Truth and runtime verification separate.

## Existing systems preserved
Continue using whole-source defect exhaustion, false-PASS prevention, client/server authority, networking/security, persistence/recovery/concurrency, Studio representation, UI/VFX/SFX/input/camera/animation/performance/cleanup, continuous learning, dataset intelligence, shared-learning truth boundaries, and exact-source validation.

## UI requests (Roblox UI Master)
For any UI/GUI/HUD/menu/shop/inventory/dialog/toast request, also apply `skills/roblox-ui-master/SKILL.md`: responsive design tokens and layout plan, the bundled multi-viewport layout lint (`scripts/ui_lint.py`), Level 3 with `context:"client"`, and its DELIVERY CONTRACT - the final reply must contain the complete code (never only a preview, summary or validation claim).
