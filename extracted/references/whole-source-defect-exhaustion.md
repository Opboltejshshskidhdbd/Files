# Whole-Source Defect Exhaustion & False-Pass Prevention

## Mandatory gate
After every meaningful repair, do not treat the reported occurrence as the defect boundary. Identify the root-cause class, reload current source, exhaust relevant manifestations across the whole affected source, attempt adversarial falsification, run an independent second pass, then reconcile every PASS claim with current source.

## Defect record
Preserve, when evidence exists:

```text
FailurePattern
RootCause
AffectedFiles
AffectedRegions
KnownOccurrences
SearchStrategy
RepairStrategy
RemainingOccurrences
UnresolvedOccurrences
FalsificationAttempt
FalsificationResult
SecondPassResult
FinalStatus
```

Never invent occurrence counts. Use `NOT PROVABLE` when exact counting cannot be established.

## Root-cause pattern first
Treat compiler/runtime text as a symptom. For syntax errors such as `<eof> expected near 'end'`, inspect the structural class: orphan/missing `end`, malformed branch/loop/function/callback closure, nested control-flow imbalance, or generated-boundary corruption. Search equivalent manifestations, not only the literal message or original line.

## Exhaustion sequence
1. Reload CURRENT source after repair.
2. Re-scan the entire affected file.
3. Re-scan related files and duplicated implementations.
4. Search equivalent root-cause manifestations.
5. Trace relevant control-flow/lifecycle/protocol boundaries.
6. Inspect before/after repaired regions and generated/reformatted regions.
7. Count discovered/repaired/remaining/unresolved occurrences when provable.
8. Run repair-contamination checks.
9. Perform an adversarial falsification attempt tied to the repaired failure.
10. Perform an independent second-pass audit that does not simply reuse the first conclusion.
11. Reconcile PASS claims with current `file:line` evidence.

If any required step cannot be performed, report `BLOCKED — VERIFICATION NOT AVAILABLE`; do not silently convert it to PASS.

## Falsification
Every meaningful repair requires exactly one evidence-backed result for each required falsification attempt: `SURVIVED` or `FALSIFIED`. FALSIFIED blocks PASS and returns the workflow to root cause → repair → exhaustion → falsification.

## Repair-induced defect check
Structural rewrites must also preserve required behavior and check authority, networking, lifecycle, UI, VFX, SFX, animation, camera, input, persistence, cleanup, and performance where applicable. Syntax cleanliness alone is never enough.

## Claim/source consistency
Authority order:
1. current executable source
2. actual compiler/runtime output
3. reproducible test artifacts
4. source-level audit evidence
5. generated audit report
6. README
7. previous assistant claims

No current-source evidence means no PASS. Contradictions between source and documentation are defects; source wins.

## Required repair report
```text
## REPAIR RESULT
Original failure:
Root cause:
Files inspected:
Occurrences discovered:
Occurrences repaired:
Occurrences remaining:
Occurrences unresolved:
Related patterns checked:
Repair-induced defects:
Falsification attempt:
Falsification result: SURVIVED / FALSIFIED
Second-pass audit: PASSED / FAILED / BLOCKED
Source-truth consistency: PASSED / FAILED
Runtime verification: VERIFIED / UNVERIFIED
Final status: REPAIRED / STATICALLY VERIFIED / RUNTIME VERIFIED / PARTIALLY VERIFIED / FAILED / BLOCKED

## LEARNING
Failure generalized: YES / NO
Lesson:
Prevention rule:
Persistence: ACTUAL STATUS ONLY
Shared learning: ACTUAL STATUS ONLY
```

## Multi-occurrence benchmark
A benchmark source must contain one obvious occurrence, one less-obvious occurrence, and one equivalent manifestation; optionally include a repair-induced defect. Fixing only the obvious occurrence fails. Passing requires root-cause detection, relevant occurrence exhaustion, falsification, second-pass audit, and source-truth reconciliation.

## Truth boundary
Static evidence never becomes runtime evidence without actual runtime artifacts. Package files, READMEs, prior messages, and claimed audits are not runtime proof.
