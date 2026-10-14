# Roblox-Native Knowledge Expansion v1.0

## Purpose
This reference turns documentation retrieval into structured engineering knowledge instead of bulk page ingestion. It is a routing and evidence contract, not a claim that every listed fact is universally true in every runtime context.

## Source hierarchy
1. Roblox Creator Hub / official Roblox documentation
2. Official Roblox Engine API reference
3. Official Luau documentation / grammar / language reference
4. Roblox-authored technical material
5. Roblox DevForum technical material with credible evidence
6. Strong community engineering references
7. Online Luau syntax resources/playgrounds
8. User-provided examples
9. Unverified claims

Higher authority wins only when scope and version match. Conflicts must remain visible until resolved; never silently overwrite a conflicting lower-level claim.

## Knowledge-item schema
Every promoted fact should carry:
- `knowledge_id`
- `domain` (`ENGINE_API`, `STUDIO`, `LUAU`, `ROBLOX_LUAU`, `ARCHITECTURE`, `NETWORKING`, `SECURITY`, `LIFECYCLE`, `PERSISTENCE`, `UI`, `PHYSICS`, `STREAMING`, `PERFORMANCE`, `PRESENTATION`, `DEBUGGING`)
- `claim`
- `scope`
- `source_url`
- `source_type`
- `source_section`
- `crawl_or_observation_date` when available
- `evidence_status`
- `confidence`
- `deprecated`
- `replacement` when documented
- `constraints`
- `security_implications`
- `performance_implications`
- `common_misuse`
- `counterexamples_or_non_applicability`

## Current official anchors
The following anchors were checked against official documentation during the 1.10.0 upgrade:

- Services: `https://create.roblox.com/docs/scripting/services`
  - Services expose built-in engine functionality.
  - `WaitForChild()` is important because Roblox does not guarantee loading order and streaming complicates availability.
  - Common scripting services include TweenService, MarketplaceService, RunService, SoundService, and CollectionService.
  - DataStoreService is for persistent data; MemoryStoreService for frequent/ephemeral data; MessagingService for cross-server communication.

- Properties and attributes: `https://create.roblox.com/docs/scripting/attributes`
  - Attributes are custom per-Instance data.
  - Replication order is not guaranteed; client access patterns should account for this.
  - Use `SetAttribute()` / `GetAttribute()` for scripted attribute access.

- PlayerGui: `https://create.roblox.com/docs/reference/engine/classes/PlayerGui`
  - PlayerGui contains a player's displayed GUI hierarchy.
  - ScreenGui descendants of PlayerGui display on the player's screen.
  - PlayerGui is automatically inserted into a Player when the player joins.

- ProximityPrompt: `https://create.roblox.com/docs/reference/engine/classes/ProximityPrompt`
  - ProximityPrompt is an Instance for 3D interaction prompts.
  - It can be parented to a BasePart, Attachment, or Model with PrimaryPart configured.
  - Triggered and hold/input events exist; ProximityPromptService can centralize prompt handling.

- ProximityPromptService: `https://create.roblox.com/docs/reference/engine/classes/ProximityPromptService`
  - Provides global prompt events and enable/visibility controls.
  - Useful for centralized prompt behavior instead of duplicated per-prompt handlers.

- CollectionService: `https://create.roblox.com/docs/reference/engine/classes/CollectionService`
  - Tags are strings applied to Instances and replicate to clients.
  - CollectionService can register behavior around tagged groups and provides added/removed signals.

- RunService: `https://create.roblox.com/docs/reference/engine/classes/RunService`
  - Provides server/client/studio context checks and runtime step events.
  - Event choice should follow the required timing phase; do not default every loop to Heartbeat.

- Data stores: `https://create.roblox.com/docs/cloud-services/data-stores`
  - DataStoreService stores persistent data across sessions.
  - Server Scripts access data stores; client LocalScripts cannot directly access them.
  - Studio API-service access can affect live data and should be isolated to test versions.

- Script capabilities: `https://create.roblox.com/docs/scripting/capabilities`
  - Roblox exposes capability requirements for classes, methods, properties, and events.
  - Capability-aware API reasoning is part of current Roblox engineering knowledge.

## Retrieval behavior
Retrieve the smallest relevant set of facts. Prefer an official fact that directly constrains implementation over a large generic tutorial. Preserve source provenance in audit output for important claims.

## Currentness
For API recommendations, check deprecation/current replacement information before using an older example. Historical examples remain useful as failure evidence but do not outrank current official documentation.

## Non-authority boundary
A DevForum post, playground, code snippet, or model memory can suggest a pattern. It does not by itself establish an engine guarantee. Runtime behavior must be verified separately.
