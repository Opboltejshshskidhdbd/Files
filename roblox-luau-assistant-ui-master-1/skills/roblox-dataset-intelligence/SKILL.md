---
name: roblox-dataset-intelligence
description: Evidence-gated dataset audit for Roblox knowledge quality, provenance, syntax validity, duplicates, conflicts, obsolete APIs, and retrieval quality.
---
# ROBLOX DEV MASTER — Dataset Intelligence v2.0

## Quality gate
`SOURCE → EXTRACT CLAIM → CLASSIFY → SYNTAX-CHECK CODE-BEARING FIELDS → DEDUPE → CONFLICT CHECK → CURRENTNESS CHECK → EVIDENCE STATUS → PROMOTION`

Never inflate dataset size for its own sake.

## Source classes
Keep distinct: official Roblox, official Luau, Roblox-authored, DevForum, community, playground/syntax resource, user example, unverified claim.

## Claim separation
Every entry must distinguish:
- generic Lua behavior
- Luau language behavior
- Roblox-specific behavior
- Studio behavior
- implementation pattern/opinion
- runtime-observed behavior

## API currentness
Preserve source date/crawl date when available, deprecated status, replacement API, confidence, scope, and evidence. Old examples do not outrank current official documentation.

## Code-bearing validation
Use the existing custom parser for code-bearing fields only. Narrative text is not code. Parser success is not runtime/API correctness.

## Conflicts
Never silently merge contradictory claims. Preserve conflict state until authority, version, scope, or implementation evidence resolves it.

## Retrieval
Prefer one high-quality representative per near-duplicate cluster and retrieve only relevant knowledge. Rank by source authority, evidence, applicability, currentness, and conflict state.
