---
name: roblox-continuous-learning
description: Evidence-gated automatic engineering learning for Roblox Dev Master, including Level 3 external validator failures, source-truth verification, privacy-safe generalization, regressions, and canonical persistence.
---
# ROBLOX DEV MASTER — Continuous Learning v5.0

Learning remains automatic, but retrieval alone is never learning.

## External-validator learning evidence
A Level 3 diagnostic may enter learning only after:
`DETECT → REPRODUCE → ACTUAL SOURCE REPAIR → LEVEL 1/2 REVALIDATION → LEVEL 3 REVALIDATION → SECOND PASS → SOURCE-TRUTH CONFIRMATION → GENERALIZE → DEDUPE/CONFLICT → PRIVACY FILTER → PERSIST`

Never learn directly from an unavailable, malformed, unverified, or simulated external result. Preserve API-returned diagnostics separately from Dev Master-generated metadata.

## Existing pipeline preserved
`FAILURE/CORRECTION → CLASSIFY → ROOT CAUSE → REPRODUCE → REPAIR ACTUAL SOURCE → CURRENT-SOURCE RELOAD → WHOLE-SOURCE DEFECT EXHAUSTION → REPAIR CONTAMINATION → ADVERSARIAL FALSIFICATION → SECOND-PASS AUDIT → POST-REPAIR SOURCE TRUTH → REGRESSION → GENERALIZE → EVIDENCE → DEDUPE/CONFLICT → PRIVACY FILTER → PERSIST → FUTURE RETRIEVAL → PREVENTION → REGRESSION`

## Privacy
Generalize engineering failure, not private project details. Do not persist private user source, identifiers, URLs, credentials, tokens, or paths.

## Canonical store
`skills/roblox-continuous-learning/LEARNED_KNOWLEDGE.md` remains the sole canonical persisted lesson store.

## Truth statuses
Keep `CANDIDATE`, `STATICALLY_VERIFIED`, `RUNTIME_VERIFIED`, `CROSS_VERIFIED`, `CONFLICTING`, `SUPERSEDED`, `CONTEXT_SPECIFIC`, `STATIC_NARRATIVE_ONLY` separate. External validation does not equal runtime verification.
