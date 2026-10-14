# Roblox Dev Master — Backend Contracts

**Scope:** Load this contract **only for BACKEND tasks**: persistence, trading, economy, inventory authority, transactions, distributed state, recovery, session leases/generations, durable idempotency, or backend-heavy networking. Presentation/simple tasks should not load it merely because these terms exist elsewhere.

These definitions are semantic contracts for engineering and auditing. Implementations may vary, but an implementation must preserve the stated invariants.

## 1. Idempotency

**Definition:** Repeating the same logical operation request one or more times must not cause more than one authoritative effect for that operation.

**Invariant:** For a durable operation identity, retries converge to one committed outcome rather than duplicating mutation, reward, reservation, purchase, trade, or inventory change.

Idempotency is not the same as packet ordering or sequence checking. It must survive the retry/failure window that the feature claims to survive; for durable operations this normally means persistence-backed or otherwise durable state.

Audit: operation identity, duplicate detection, outcome storage/replay behavior, commit ordering, crash/retry behavior, and cleanup/retention policy.

## 2. OperationId

**Definition:** `OperationId` is a unique identifier for one logical authoritative operation, generated before the operation is submitted and carried across retries/recovery for that same operation.

**Required properties:** unique within the scope needed to prevent collisions; stable across retries of the same logical operation; not reused for a different logical operation; associated with the operation's authoritative outcome/state.

Do not confuse `OperationId` with a per-connection sequence number. Sequence numbers describe ordering/replay boundaries; OperationId identifies a logical operation across retry/recovery boundaries.

## 3. Session leases and generations

**Session lease:** a server-owned claim that a particular server/session instance currently has authority to mutate a player's durable state.

**Generation:** a monotonically advancing session identity/version associated with that lease. A mutation must carry or resolve against the currently valid generation before it can commit.

**Invariant:** once a lease is invalidated or superseded, stale work from the old generation must not mutate the newly owned session state.

Lifecycle: acquire → validate/renew while active → invalidate on release/timeout/shutdown → ensure stale work cannot commit. Generation checks must participate in mutation/recovery boundaries, not merely logging.

## 4. Recovery workers

A recovery worker is an executable process that repairs operations left incomplete by crashes, timeouts, disconnects, or partial failures.

Required lifecycle:
**discover → classify → claim → validate ownership/generation → retry or compensate → persist outcome → finalize/release**.

Claims must be bounded and concurrency-safe. A worker must not finalize work it does not own or mutate state belonging to a stale session generation. Retries must remain idempotent.

## 5. ACK semantics

An ACK is an explicit protocol response that communicates the server's authoritative disposition of a request/operation.

At minimum distinguish: accepted/committed, rejected/invalid, and retryable/in-progress outcomes when the protocol needs them. An ACK is not proof of success unless its status means the authoritative mutation committed.

ACKs must map to the correct request/OperationId, must not cause duplicate mutation when retried, and must have a defined behavior when the client reconnects or misses an ACK. Do not equate an ACK with a transport-level delivery guarantee.

## 6. Bounded queues and history

A bounded queue/history has an explicit maximum capacity, retention/eviction rule, and overflow behavior.

**Invariant:** memory/work cannot grow without a defined upper bound under sustained input or failure.

When full, behavior must be explicit: reject, shed, coalesce, expire, or otherwise apply a documented policy. History used for replay protection must define retention relative to the sequence/OperationId validity window. Backpressure/rate limits must protect the queue rather than merely report overload after unbounded growth.

## 7. Failure injection

Failure injection is a deliberate, controlled simulation of a failure at a named boundary to verify recovery and invariants.

A useful injection specifies: trigger point, deterministic condition, expected failure, expected invariant, expected recovery path, and observable evidence. Examples include failure after validation but before commit, after durable write but before ACK, lease invalidation during work, worker crash during retry, or queue overflow.

Failure injection is not a claim of actual execution unless the injection was really run. If tooling is unavailable, report SIMULATED FAILURE ANALYSIS or NOT_EXECUTED honestly.

## 8. Second-pass audit

The second-pass audit occurs **after implementation or a repair**, against the changed implementation rather than only the original design.

Minimum scope for a complex/backend repair:
1. Re-run the originally failing scenario or equivalent evidence check.
2. Trace affected callers and state boundaries.
3. Check the repaired invariant and adjacent invariants.
4. Check for regressions in retry/idempotency, authority, lifecycle, persistence, protocol, and recovery where applicable.
5. Reconcile status with actual evidence.

A second-pass audit is not a prose reread. It must inspect the changed code path and relevant evidence.
