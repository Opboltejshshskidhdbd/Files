# Roblox Dev Master — Evals

## Primary metric
**False-PASS rate** on a fixed benchmark suite. A false PASS is a benchmark case where the assistant reports PASS/complete/production-ready while the fixed oracle or post-run artifact shows a required defect, unsupported claim, source/report contradiction, or missing evidence.

Primary target: minimize false-PASS rate. Do not trade it for inflated PASS counts.

## Fixed protocol
1. Freeze the benchmark cases, requirements, expected failure classes, and oracle criteria before a run.
2. Run the assistant on the same cases without leaking the expected defect names.
3. Collect the exact generated source, project tree, README, audit report, and any available execution artifacts.
4. Independently inspect the artifacts against the fixed oracle.
5. Count PASS claims that should have been rejected as false PASS.
6. Report false-PASS rate = false PASS cases / evaluated cases.
7. Separate static/source evidence from actual runtime evidence.
8. Do not add, alter, or backfill benchmark results without the underlying artifacts.

## Required artifact set
At minimum: benchmark input, generated package/source, audit report, and the oracle/check record. Runtime claims additionally require runtime artifacts.

## No-results rule
This README defines the metric and protocol only. It contains **no benchmark results**. Results belong in an artifact-backed evaluation record.
