# Automatic Failure Learning Reference

## Trigger contract
Normal engineering interactions are sufficient to start learning evaluation. Explicit learning commands are optional and never required.

Trigger examples:
- user says an implementation is wrong/broken;
- user reports a concrete runtime or source failure;
- assistant finds a defect during audit;
- a repair is required;
- a known lesson is violated;
- a previous fix fails again.

## Event record
Capture only evidence actually available:
`event_id, trigger_type, failure_class, source_locations, user_feedback, observed_behavior, root_cause, repair, verification_status, lesson_candidate_id, persistence_status`.

Do not fabricate runtime observations, user confirmation, or file locations.

## Decision flow
`SIGNAL → SOURCE CHECK → ROOT CAUSE → REPAIR → CONTAMINATION CHECK → POST-REPAIR SOURCE TRUTH → REGRESSION → GENERALIZE? → DEDUPE/CONFLICT → CANDIDATE/PROMOTION → PERSIST → RETRIEVAL/PREVENTION`

## Generalization decision
Persist a reusable rule when the defect describes a repeatable engineering condition and has an actionable prevention/detection check. Keep context-specific issues in project context. Keep preferences in user claims. Keep trivial fixes in failure history unless later evidence shows a broader pattern.

## Regression decision
A recurrence is a learned-pattern regression only when the prior lesson was applicable and the current implementation reproduced the same pattern despite the prevention mechanism. Otherwise classify it as a new failure or known failure as appropriate.

## Evidence boundary
User feedback is evidence that a failure was reported. It is not automatically evidence that the proposed root cause or generalized lesson is correct. Source evidence, repair evidence, regression evidence, runtime evidence, and cross-implementation evidence remain independent.
