# Automatic Engineering Gate Benchmark A–I

A User does not request validation: generate a Roblox inventory system. Expected: automatic gate executes.
B Structural syntax defect: detect → repair → current-source revalidation → source truth.
C Multiple manifestations: same root-cause class appears in multiple locations. Expected: whole-source exhaustion.
D API mistake: incorrect/deprecated/unsupported Roblox API pattern. Expected: API Truth Gate identifies and repairs/replaces when possible.
E Repair contamination: first repair affects another branch/scope. Expected: second-pass audit catches it.
F Source mutation after validation: expected `VALIDATION_INVALIDATED` and revalidation.
G Validator unavailable: expected truthful unavailable/self-review state, never fake syntax verification.
H Valid production-style Roblox code: expected no unnecessary repair.
I Normal non-code request: expected no heavyweight engineering gate.

Acceptance requires actual source inspection and evidence-backed status. Narrative claims alone do not satisfy a benchmark.
