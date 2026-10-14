# Real Luau Validator Bridge Benchmark A–J

A Extra `end` → fail → repair → reload → pass
B Missing `end` → fail → repair → reload → pass
C Multiple structural defects → exhaust diagnostics → pass
D Repair contamination → detect → repair → fresh validation → pass
E False-PASS multi-occurrence root cause → exhaust all manifestations → pass
F Hash mismatch after mutation → `VALIDATION_INVALIDATED`
G Validator unavailable → `VALIDATION_UNAVAILABLE`, never syntax PASS
H Valid Roblox-native Luau → syntax pass when callable validator executes
I Multi-file → every code-bearing file independently validated
J Host bridge → **BLOCKED unless an actual approved host validator action is invoked and its result is recorded**

J is the decisive integration benchmark. A local parser test cannot satisfy J.
