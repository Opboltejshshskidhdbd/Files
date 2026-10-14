# Roblox API Truth Gate

## Default behavior
Whenever generated code materially depends on Roblox Engine APIs, automatically verify the relevant API claims. The user does not need to request API checking.

## Authority hierarchy
1. Roblox Creator Hub / official Roblox documentation
2. official Roblox Engine API reference
3. official Luau documentation for language behavior
4. Roblox-authored technical material
5. credible Roblox DevForum evidence
6. strong community engineering sources
7. unverified/user-provided claims

## Verification dimensions
For each material API claim, check where documented:
- existence
- class/service identity
- property/method/event/callback identity
- capitalization
- parameters and return behavior
- server/client execution context
- lifecycle implications
- current/deprecated/legacy status
- documented replacement
- supported usage constraints

## Uncertainty
If the authoritative source does not establish a detail, use `API_UNVERIFIED` or `API_BEHAVIOR_UNVERIFIED`. Do not invent parameters, return values, events, service members, or guarantees. Prefer a verified alternative when possible; otherwise disclose the limitation.

## Documentation vs source truth
API documentation establishes what Roblox documents. It does not establish that the generated implementation uses the API correctly. Therefore perform both:
`API TRUTH + CURRENT SOURCE TRUTH`.

## Community evidence
A DevForum observation can identify a useful pattern or bug, but it does not become an engine guarantee without sufficient authoritative/corroborating evidence. Preserve conflicts instead of silently choosing.

## Currentness
Prefer current official documentation. Do not automatically reject a still-valid legacy API solely for age, but do not present deprecated APIs as modern recommendations without qualification.
