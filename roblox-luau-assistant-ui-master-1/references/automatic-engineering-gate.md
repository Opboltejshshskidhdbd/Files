# Automatic Engineering Gate — Three-Level Validation

## Purpose
This gate is default behavior for Roblox code generation, modification, repair, and material rewrites.

## Risk routing
### LOW
Simple isolated Luau change. Run Level 1, Level 2, Level 3 when host-callable, plus relevant API checks.

### MEDIUM
UI, interaction, client/server, or multi-script feature. Run Level 1, Level 2, Level 3 when host-callable, API truth, architecture, security, lifecycle, cleanup, and source-truth checks.

### HIGH
Persistence, economy, trading, marketplace, combat authority, cross-server state, or complex concurrency. Run the full pipeline with all applicable engineering checks, Level 1/2/3, repair/revalidation, adversarial falsification, and second pass.

## Mandatory ladder
`LEVEL 1 ENGINEERING SELF-AUDIT → LEVEL 2 BUNDLED LUAU PARSER → LEVEL 3 EXTERNAL LUAU VALIDATOR → ROBLOX API TRUTH → WHOLE-SOURCE DEFECT EXHAUSTION → REPAIR / REVALIDATE → SECOND PASS / FALSIFICATION → FINAL EVIDENCE`

If Level 3 is not host-callable, Level 1 and Level 2 may still execute, but the result must explicitly say `LEVEL 3 UNAVAILABLE`; it is never silently promoted to PASS.

## Level 3 repair contract
For external `valid:false`: inspect every error, identify root cause, patch actual current source, reload, rerun applicable Level 1 and Level 2, send the exact repaired source to Level 3, and inspect the new result. Maximum automatic repair attempts: 3. Remaining errors after attempt 3 => `NOT_VERIFIED`.

## Warning contract
External warnings are actionable when safe. `info` is advisory. Warnings do not become errors unless the API reports them as errors.

## Source truth
Freeze and hash exact source before external validation. Any source mutation afterward produces `EXTERNAL_VALIDATION_INVALIDATED` and requires fresh validation. Validate each relevant file independently in multi-file work.

## Receipt
Track validation level, validator, endpoint, source hash, attempt, status, error/warning counts, diagnostics, timestamp, source-truth status, and evidence status. API-returned data must remain distinguishable from generated metadata.

## Final-source contract
Delivery must correspond to the source that was actually audited and validated. Static external validation does not prove Roblox runtime correctness or complete type checking.
