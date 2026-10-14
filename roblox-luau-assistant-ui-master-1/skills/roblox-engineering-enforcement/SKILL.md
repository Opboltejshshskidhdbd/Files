---
name: roblox-engineering-enforcement
description: Strict default proof/rejection layer for Roblox code generation with Level 1 Engineering Gate, Level 2 bundled parser, Level 3 external Luau validator, API Truth Gate, whole-source defect exhaustion, exact-source verification, and false-PASS prevention.
---
# ROBLOX DEV MASTER — Engineering Enforcement v1.15.0

## Required order
`REQUIRE → AUTHORITATIVE KNOWLEDGE → IMPLEMENT → LEVEL 1 WHOLE-SOURCE AUDIT → LEVEL 2 BUNDLED PARSER → LEVEL 3 EXTERNAL VALIDATOR WHEN HOST-CALLABLE → API TRUTH → DEFECT DETECTION → ACTUAL SOURCE REPAIR → RELOAD → LEVEL 1/2/3 REVALIDATION → WHOLE-SOURCE EXHAUSTION → CONTAMINATION CHECK → ADVERSARIAL FALSIFICATION → INDEPENDENT SECOND PASS → SOURCE/HASH RECONCILIATION → LEARNING IF QUALIFIED → REPORT`

## Level separation
Level 1 is engineering self-audit. Level 2 is the bundled structural/syntax parser and is not the official Luau compiler. Level 3 is an independently hosted external Luau validation service and is not described as the official Roblox compiler.

## Level 3 PASS requirements
Only emit `EXTERNAL_VALIDATION_PASSED` when the external endpoint was actually called successfully against the exact source hash and returned `valid:true`. No narrative claim, local mock, Level 2 pass, or API documentation can substitute for that evidence.

## Failure states
External timeout/network/HTTP failure/malformed response/unsupported-size request → `EXTERNAL_VALIDATION_UNAVAILABLE`. Source mutation after a result → `EXTERNAL_VALIDATION_INVALIDATED`. `valid:false` → `EXTERNAL_VALIDATION_FAILED`; after 3 repair attempts with remaining errors → `NOT_VERIFIED`.

## Whole-source / repair rule
A diagnostic is not the repair. Patch the actual current source, reload it, rerun applicable Level 1 and Level 2, then Level 3. Search related manifestations and check repair contamination before delivery.

## Runtime boundary
External static validation does not prove Roblox runtime correctness or complete type correctness. Never claim runtime verification without actual runtime artifacts.

## UI delivery gate
UI work additionally requires: (1) `scripts/ui_lint.py` run on the final source with 0 FAIL (or the remaining FAILs listed honestly), (2) Level 3 with `context:"client"`, (3) the complete code in the final reply. A turn that ends with only a UI preview/description or a validation summary is a defect: deliver the code immediately. UI lint is a layout estimate, not a device test - never claim pixel-perfect or device-tested without real screenshots/recordings.
UI layout lint must run to completion: `ui.layout_unchecked` is a FAIL, not a pass. Never use Roblox behavior you could not verify (e.g. ScreenInsets); ask for a device recording after delivery.
