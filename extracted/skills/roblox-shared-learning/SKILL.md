---
name: roblox-shared-learning
description: Privacy-safe, evidence-gated collective engineering knowledge for Roblox Dev Master. Separates personal/project learning from shared generalized knowledge and never claims global persistence without a real backend.
---

# ROBLOX DEV MASTER — Shared Collective Engineering Learning v1.0

## Absolute rule

Shared knowledge is a separate trust boundary from personal/project learning.

Private project context, code, identifiers, paths, URLs, preferences, terminology, conversation content, and user claims do not cross that boundary automatically. Only generalized, privacy-safe, evidence-backed engineering knowledge may become a shared candidate, and only stronger evidence may promote it.

**Current backend reality:** this plugin package has no verified cross-user read/write synchronization service in its current source. Therefore `SHARED PERSISTENCE: UNAVAILABLE / UNVERIFIED` unless a future release supplies and verifies an actual backend. Local/package persistence must never be described as global learning.

## 1. Scope model

### PERSONAL / PROJECT
- project architecture and decisions
- user preferences and terminology
- temporary debugging state
- private source/code/file paths
- private URLs, secrets, credentials, tokens, API keys
- unpublished information
- user claims not independently established as universal engineering rules

### SHARED ENGINEERING
Only generalized reusable knowledge:
- verified engineering rules and failure patterns
- prevention/detection/regression rules
- generalized Roblox API/lifecycle/network/security lessons
- UI/VFX/SFX/animation/camera/input/performance lessons
- persistence/concurrency/source-truth/architecture lessons

Scope semantics for the six existing categories:
`CORE → SHARED`
`TRUSTED RULES → SHARED`
`VERIFIED LESSONS → SHARED only when generalized, privacy-safe, and sufficiently evidenced`
`CANDIDATES → SHARED candidate storage only when privacy-safe and generalized`
`PROJECT CONTEXT → PRIVATE`
`USER CLAIMS → PRIVATE unless independently proven and reclassified`

## 2. Automatic collective-learning pipeline

`FAILURE/CORRECTION → ROOT CAUSE → REPAIR → POST-REPAIR SOURCE TRUTH → REGRESSION → GENERALIZE → PRIVACY SANITIZE → DEDUPE → CONFLICT CHECK → SHARED CANDIDATE → EVIDENCE → PROMOTION → SHARED RETRIEVAL → PREVENTION → NEW EVIDENCE`

No explicit “learn” command is required.

A personal/project lesson is not copied verbatim into the shared layer. The system first decides whether a reusable engineering principle exists, then sanitizes it, then checks duplicates/conflicts, then records it as a candidate.

## 3. Generalization contract

A shared lesson must stand without the originating project. Prefer:
- generalized failure pattern
- root cause
- incorrect pattern
- correct pattern
- prevention rule
- detection rule
- applicability
- non-applicability
- evidence summary
- verification state

Never use project names as the engineering rule. Do not store complete user source files as shared knowledge.

## 4. Privacy sanitization gate

Before shared-candidate creation inspect for:
project names, usernames/identifiers, private paths, private URLs, source code, proprietary names, secrets/tokens/credentials/API keys, personal information, private conversation content, and unnecessary project terminology.

If safe generalization removes the private material without changing the engineering meaning, sanitize and continue. If material remains or the lesson cannot be generalized safely:
`SHARING BLOCKED`.

Privacy failure blocks sharing; it never blocks normal engineering assistance.

## 5. Evidence and promotion

Existing evidence dimensions remain independent:
`SourceEvidence, RepairEvidence, RegressionEvidence, RuntimeEvidence, CrossImplementationEvidence`.

Use existing statuses:
`CANDIDATE, STATICALLY_VERIFIED, RUNTIME_VERIFIED, CROSS_VERIFIED, CONFLICTING, SUPERSEDED, CONTEXT_SPECIFIC, STATIC_NARRATIVE_ONLY`.

A user report alone never creates a verified shared rule.

Suggested promotion path:
`CANDIDATE → STATICALLY_VERIFIED → CROSS_VERIFIED → TRUSTED RULES`

Runtime verification is only claimed with actual runtime artifacts. Cross-user evidence is only claimed when a real shared backend can associate independent evidence without exposing identities.

## 6. Cross-implementation and cross-user evidence

Independent evidence must be genuinely independent. Repeated observations from one implementation do not count as multiple independent implementations.

Track where supported:
`independent_evidence_count, implementation_count, cross_user_evidence, verification_history`.

Quality beats report count: actual failure + root cause + repair + source evidence + regression verification + independent implementation evidence is stronger than popularity.

`CROSS-IMPLEMENTATION TRANSFER` means a lesson from one implementation changes/prevents behavior in an independent implementation.

`CROSS-USER TRANSFER` may only be recorded when actual shared persistence supports retrieval by another user/session and the evidence is returned to the shared system.

## 7. Shared lesson provenance

Minimum privacy-safe record:
`lesson_id, scope, category, origin_type, evidence_status, created_at, updated_at, version, generalized_rule, root_cause, prevention_rule, detection_rule, applicability, non_applicability, evidence_summary, verification_history, supersedes, superseded_by, conflict_ids`.

Do not require personally identifying provenance. Prefer anonymous counters and evidence classes.

Version important shared lessons (`LESSON-042 v1`, `v2`, etc.). Preserve prior versions when prevention, applicability, root cause, conflicts, or regressions materially change.

## 8. Deduplication and conflicts

Use existing dataset intelligence. Before insertion:
1. exact duplicate check;
2. near-duplicate clustering;
3. conflict detection;
4. merge evidence into one representative where appropriate;
5. preserve provenance/history.

Retrieve at most one representative per near-duplicate cluster.

If rules conflict, retain `CONFLICTING` until applicability/evidence analysis resolves the conflict. Conditional rules are preferred over deleting useful context.

## 9. Poisoning protection

A single unverified submission cannot become `CORE` or `TRUSTED RULES`. User instructions cannot directly overwrite trusted knowledge. Shared candidates cannot bypass source-truth, evidence, privacy, dedupe, conflict, or engineering enforcement.

A bad submission must fail closed at the shared boundary while normal Roblox assistance continues.

## 10. Negative evidence

If a retrieved lesson was applicable and its prevention was applied but the defect recurs, record:
`LESSON FAILED TO PREVENT` and classify the event as `LEARNED-PATTERN REGRESSION` when the same pattern is reproduced.

Investigate retrieval, applicability, actual application, prevention completeness, root-cause correctness, and similarity. Strengthen/version the lesson instead of hiding negative evidence or blindly creating a duplicate.

## 11. Retrieval priority

Before substantial implementation, retrieve:
1. CORE
2. TRUSTED RULES
3. applicable verified shared lessons
4. relevant shared candidates
5. PROJECT CONTEXT
6. USER CLAIMS

Rank by engineering authority, evidence, applicability, and conflict state. A project preference cannot silently override a verified security/authority/lifecycle requirement.

Shared retrieval is best-effort. If unavailable, continue using local/core knowledge and state the limitation.

## 12. Shared backend contract

If a real backend is later supplied, its operations should satisfy:
`submitCandidateLesson()`
`getRelevantSharedLessons()`
`recordEvidence()`
`promoteLesson()`
`recordConflict()`
`supersedeLesson()`
`recordRegression()`
`recordApplication()`

Every operation requires schema validation, authorization, privacy filtering, evidence validation, dedupe, conflict handling, versioning, and failure handling.

This package does not claim these operations are live. A documented contract is not an implementation.

## 13. Failure tolerance / offline-first

Shared-learning failure must never become an engineering-generation failure.

If shared storage is unavailable, slow, read-only, inconsistent, or unreachable:
- continue normal engineering;
- use local/core knowledge;
- preserve a current-workflow candidate when appropriate;
- report the actual shared-persistence state;
- never pretend retrieval/write succeeded.

## 14. User-facing receipts

Meaningful reusable failure:
`Learning captured — Scope: Shared engineering candidate — Status: CANDIDATE`.

Only say `SHARED VERIFIED` when actual promotion evidence exists.

When a shared lesson actually changes a future implementation:
`Previous engineering lesson applied — the implementation was checked against the prevention rule.`

When a previously learned applicable pattern returns:
`Learned-pattern regression — repaired, re-audited, and lesson strengthened.`

Do not expose another user's identity, project, code, path, URL, or conversation. Shared status may expose only generalized evidence such as anonymous counts if those counts are actually persisted.

## 15. Learning status

Natural requests such as “What have you learned?” may report only actual persisted data, separated into:
- personal knowledge
- shared knowledge applied
- shared lessons contributed
- candidate/verified lessons
- known regressions
- prevention successes
- conflicts
- shared persistence state

No fabricated global/user counts.

## 16. Metrics

Where actual evaluation infrastructure exists, track:
- FALSE-PASS RATE
- Automatic Learning Capture Rate
- Learning Precision
- Shared Promotion Precision
- Prevention Success Rate
- Learned-Pattern Regression Rate
- Cross-User Transfer Rate
- Knowledge Poisoning Rate
- Duplicate Lesson Rate
- Conflict Resolution Accuracy

A missing metric is `UNAVAILABLE`, not zero unless measured as zero.

## 17. Mandatory source-truth relationship

Shared-learning claims are subject to the existing POST-REPAIR SOURCE TRUTH gate. For each claimed capability, provide current source `file:line`, attempt falsification, and record `SURVIVED` or `FALSIFIED`. No source evidence means no PASS.

The plugin must distinguish:
`SHARED ARCHITECTURE IMPLEMENTED — UNVERIFIED`
from:
`GLOBAL LEARNING VERIFIED`.

The latter requires real shared write + persistence + retrieval from another user/session + preserved provenance/evidence.
