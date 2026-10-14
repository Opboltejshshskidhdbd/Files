# Level 3 External Luau Validation Benchmark A–J

A. Valid source: Level 1 + Level 2 + actual Level 3 POST pass where host bridge exists.
B. Broken source: actual Level 3 POST returns `valid:false` and diagnostics are preserved.
C. Repairable defect: actual source changes, then Level 1/2/3 revalidate.
D. Warning: API warning is surfaced and remains distinct from syntax failure.
E. API unavailable: timeout/network/HTTP/malformed response => `EXTERNAL_VALIDATION_UNAVAILABLE`, never PASS.
F. Mutation: source hash mismatch => `EXTERNAL_VALIDATION_INVALIDATED` and revalidation required.
G. Multi-file: each relevant file has an independent receipt/source hash.
H. 200KB boundary: oversize input is handled truthfully without fabricated API diagnostics.
I. Warning-only valid source: warnings do not become errors.
J. Regression: existing Level 1 and Level 2 files/behavior remain present and truthful.

Completion requires executed evidence for every claim. If the host cannot make the external POST, mark that part UNVERIFIED/HOST_BLOCKED rather than simulating it.
