# Level 1 + Level 2 Syntax Learning Contract

## Level 1 — AI self-audit
Inspect the complete final source, not just a reported line. Check block balance, declarations, callbacks, tables, delimiters, strings/long strings, operators, Luau type syntax, generics/type packs, interpolation, generated truncation, accidental comment corruption, duplicate endings, and code after returns.

## Level 2 — custom parser
Use the existing `scripts/luau_syntax.py` and its regression tests. It is a custom structural/lexical validator, not the official Luau compiler and not a Roblox runtime verifier.

## Failure-to-learning pipeline
`SYNTAX FAILURE → REPRODUCE → ROOT CAUSE → REPAIR ACTUAL SOURCE → REVALIDATE → SECOND PASS → GENERALIZE → REGRESSION RULE → LEARNING RECEIPT`

Do not learn literal line repairs such as “line 428 needs end”. Learn structural causes such as composition-induced block mismatch.

## Syntax evidence statuses
- `SYNTAX_REPRODUCED`
- `SYNTAX_REPAIRED`
- `SYNTAX_REVALIDATED`
- `SYNTAX_REGRESSION_ADDED`

These are evidence attributes, not replacements for the global evidence statuses.

## Learning receipt
A genuine syntax lesson must record:
`failure_class, root_cause, actual_repair, source_truth_confirmation, validation_result, regression_status, generalization, prevention_rule, evidence_status, reusable`

## Failed repair learning
Record whether a repair introduced another defect, whether equivalent occurrences remained, and whether the pattern later recurred. Failed attempts are useful evidence only after privacy sanitization and source-truth verification.
