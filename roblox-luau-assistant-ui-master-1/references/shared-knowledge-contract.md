# Shared Collective Engineering Knowledge — Contract

## Current capability boundary

The installed Roblox Dev Master package currently has package/source persistence and personal/project learning instructions, but no verified cross-user synchronization backend, authenticated shared datastore, or cross-user retrieval API in the inspected source.

Therefore:

`SHARED PERSISTENCE: UNAVAILABLE / UNVERIFIED`

This document is an architecture contract, not evidence that a global service exists.

## Data model

```text
SharedLesson {
  lesson_id
  scope = SHARED
  category
  origin_type
  evidence_status
  created_at
  updated_at
  version
  generalized_rule
  root_cause
  prevention_rule
  detection_rule
  applicability
  non_applicability
  evidence_summary
  verification_history
  supersedes
  superseded_by
  conflict_ids
  independent_evidence_count
  implementation_count
  cross_user_evidence
}
```

No raw project source, identity, private path, secret, token, private URL, or private conversation is required by this schema.

## Required backend semantics when one exists

A real implementation must support authorized write, durable persistence, authorized read by another user/session, versioning, provenance, privacy filtering, dedupe, conflict handling, regression/evidence recording, and failure isolation.

A local file, plugin package, README, prompt, or skill file does not satisfy cross-user persistence.

## API contract

```text
submitCandidateLesson(candidate) -> persisted candidate or explicit failure
getRelevantSharedLessons(query) -> authorized generalized lessons
recordEvidence(lesson_id, evidence) -> updated evidence or explicit failure
promoteLesson(lesson_id, status) -> promotion result
recordConflict(lesson_id, conflict_id) -> conflict result
supersedeLesson(lesson_id, replacement_id) -> version relation
recordRegression(lesson_id, regression) -> updated lesson history
recordApplication(lesson_id, application) -> application evidence
```

Every operation must fail closed on invalid authorization/privacy/evidence/schema and must not block normal local engineering when unavailable.

## Verification rule

Do not claim cross-user transfer until a test demonstrates:
`User A write → durable shared persistence → User B read → B application → evidence returned`.
