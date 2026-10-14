# Roblox Dev Master — v1.4.0 → v1.5.0-docs Coverage Matrix

Baseline: original `roblox-luau-assistant.zip` v1.4.0. This documentation pass does not modify the dataset.

| v1.4.0 source rule/section | v1.5.0-docs location | Disposition |
|---|---|---|
| Core standard / Roblox-native target | Main §1 | Preserved/restructured |
| Complexity scaling | Main §2 | Expanded into four explicit levels + routing |
| Mandatory engineering pipeline | Main §3; Enforcement §2 | Preserved; proof responsibility moved to enforcement |
| Full-stack runtime model | Main §4; Enforcement §2 | Preserved |
| Roblox-native architecture/services | Main §4; Enforcement §5 | Preserved |
| Instances as first-class runtime state | Main §5; Enforcement §6 | Preserved |
| UI engineering | Main §6; Enforcement §7 | Preserved |
| VFX engineering | Main §7; Enforcement §8 | Preserved |
| Audio/SFX engineering | Main §7; Enforcement §8 | Preserved |
| Animation engineering | Main §7; Enforcement §8 | Preserved |
| Camera engineering | Main §7; Enforcement §8 | Preserved |
| Input engineering | Main §8; Enforcement §9 | Preserved |
| Character/world/physics | Main §8; Enforcement §9 | Preserved |
| Replication/authority | Main §9; Enforcement §9 | Preserved |
| Gameplay feel | Main §10; Enforcement §5/8 | Preserved |
| Asset/content pipeline | Main §13; Enforcement §5/8 | Preserved |
| Full-stack implementation completeness | Main §10; Enforcement §4/5 | Preserved |
| Presentation call-graph audit | Main §11; Enforcement §2/5 | Preserved |
| Performance | Main §12; Enforcement §10 | Preserved |
| API accuracy/authority hierarchy | Main §13; Enforcement §11 | Preserved + dataset disclaimer strengthened |
| Existing backend systems | Main §14; Enforcement §12 + backend-contracts | Preserved; precise definitions centralized |
| Adversarial full-stack review | Enforcement §13 | Preserved |
| Final audit gate | Enforcement §14 | Preserved |
| No fake testing | Enforcement §15 | Preserved and strengthened with NOT_EXECUTED |
| Response contract | Enforcement §16 | Preserved as reporting discipline |
| Enforcement: detected-but-not-patched failure | Enforcement §3 | Preserved |
| Enforcement status systems | Enforcement §4 | Preserved |
| Enforcement hierarchy/Studio contract | Enforcement §5 | Preserved |
| Enforcement lifecycle/resource ownership | Enforcement §6 | Preserved |
| Enforcement UI/VFX/audio/animation/camera | Enforcement §7–8 | Preserved |
| Enforcement physics/replication | Enforcement §9 | Preserved |
| Enforcement visual performance | Enforcement §10 | Preserved |
| Enforcement backend semantics | Enforcement §12; backend-contracts | Centralized, not dropped |
| Enforcement adversarial backend cases | Enforcement §13 | Preserved + explicit queue/history/session cases |
| Enforcement regression rule | Enforcement §16 | Preserved |
| v1.0/v1.1 inherited behavior references | Main §14; backend-contracts | Dangling reference removed; semantics centralized |
| Idempotency | backend-contracts §1 | Newly precise definition |
| OperationId | backend-contracts §2 | Newly precise definition |
| Session leases/generations | backend-contracts §3 | Newly precise definition |
| Recovery workers | backend-contracts §4 | Newly precise definition |
| ACK semantics | backend-contracts §5 | Newly precise definition |
| Bounded queues/history | backend-contracts §6 | Newly precise definition |
| Failure injection | backend-contracts §7 | Newly precise definition |
| Second-pass audit | backend-contracts §8 | Newly precise definition |
| Dataset authority statement | Main §13; Enforcement §11 | Updated exactly per request |
| Continuous learning integration | Existing `roblox-continuous-learning/SKILL.md` | Unchanged in this docs-only pass |
| Dataset intelligence integration | Existing `roblox-dataset-intelligence/SKILL.md` | Unchanged except no dataset-file mutation |

## No-rule-drop statement

All v1.4.0 main/enforcement engineering rules are represented in the new main/enforcement structure or explicitly centralized in `references/backend-contracts.md`. The matrix is the required traceability artifact for the documentation merge.
