# Real Luau Validation — Three-Level Truth Model

## Levels
1. `LEVEL 1 — ENGINEERING SELF-AUDIT / ENGINEERING GATE`
2. `LEVEL 2 — BUNDLED ROBLOX DEV MASTER LUAU STRUCTURAL/SYNTAX PARSER`
3. `LEVEL 3 — EXTERNAL LUAU VALIDATOR API`
4. Roblox runtime remains a separate evidence boundary.

Level 2 is not the official Luau compiler. Level 3 is independently hosted and is not described as the official Roblox compiler.

## Level 3 endpoint
`POST https://luau-validator.oboltr895.workers.dev/validate`

Request: `{"code":"<EXACT LUAU SOURCE>"}`

The exact source string is frozen and hashed before transport. No pre-validation formatting, minification, comment removal, or repair is allowed.

## Current host truth
The package contains an executable Python HTTP client at `scripts/external_luau_validator.py`. The inspected Plugin Creator host exposes package mutation/inspection but no generic HTTP/process execution action and no validator-specific MCP action. Therefore:

- `LEVEL_3_CLIENT_PACKAGED = YES`
- `LEVEL_3_ENDPOINT_CONFIGURED = YES`
- `LEVEL_3_HOST_CALLABLE = NOT PROVEN`
- `LEVEL_3_VALIDATION_ENFORCED_IN_ORDINARY_GENERATION = NOT PROVEN`

Until a real approved host bridge invokes the POST and returns the receipt, the plugin must report `EXTERNAL_VALIDATION_UNAVAILABLE` or `HOST_BLOCKED`, never a fabricated Level 3 PASS.

## Exact-source gate
`LEVEL 1 → LEVEL 2 → FREEZE/HASH → LEVEL 3 WHEN CALLABLE → API TRUTH → REPAIR → LEVEL 1/2/3 REVALIDATION → WHOLE-SOURCE EXHAUSTION → FALSIFICATION → SECOND PASS → FINAL HASH MATCH → DELIVERY`.

Any mutation after a Level 3 result invalidates that result.

## Security / execution
The Level 3 client sends source to the configured external validation service. It does not execute generated Roblox game code locally. The external service's own execution/analysis behavior is outside the package's runtime boundary.
