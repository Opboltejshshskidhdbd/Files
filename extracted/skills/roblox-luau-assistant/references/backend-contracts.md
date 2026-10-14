# Roblox Dev Master — Backend Contracts

Load only for BACKEND tasks.

1. Idempotency: retries of one logical operation produce at most one authoritative effect.
2. OperationId: stable unique identity for one logical operation across retries/recovery; distinct from ordering sequence.
3. Session lease/generation: current server/session owns a generation; stale work from invalidated generations cannot commit.
4. Recovery worker: discover → classify → claim → validate ownership/generation → retry/compensate → persist outcome → release.
5. ACK: explicit authoritative disposition; distinguish committed, rejected, and retryable/in-progress where needed. ACK is not transport proof.
6. Bounded queue/history: explicit capacity, retention, overflow, and backpressure; no unbounded growth.
7. Failure injection: named boundary, trigger, expected failure/invariant, recovery path, and observable evidence. Simulation is not execution.
8. Second-pass audit: after repair, inspect changed code, re-run the relevant failure check, trace callers/state boundaries, check adjacent invariants, and reconcile claims with evidence.
