# Proposed minimal object-instance contract

Milestone: `pr_play_object_identity_architecture`. Design only. These names do not assert existing classes or fields.

## Record and reference

Keep current legacy `id`, `name`, `quantity`, `usable` untouched. An explicitly promoted quantity-one inventory row gains `instance_id` (UUID allocated by the core), `revision` (nonnegative integer), and compact `provenance` (campaign ID, minting operation/request, source binding). Presence of these fields declares a version-one singleton record. Definition reference and markings are optional. Do not put empty capability/equipment/history trees on every row.

Canonical reference is `(campaign_run_id, instance_id)`. Revision is a concurrency token, not part of identity. Never derive ID from label, list index, PF equipment key, mutable location or request text. Identity is stable under rename, container transfer, scene change, different ruleset and reload. A restored campaign branch uses its own state namespace; requests from a different branch cannot apply to it.

Optional definition ref is `{ruleset_id, package_id, package_version, local_id}` or a campaign-authored template ref. It is immutable content lineage, not an owning record. Materialized instance state may override descriptive defaults only through explicit operations. No mutable campaign state is written into an imported definition.

## Placement, ownership and equipment

Placement is one tagged relationship: actor custody, scene placement, or containment in another instance. Initially actor placement is derived from the enclosing character inventory rather than duplicated on every row. The read model reports it with host provenance. Legal ownership is a separate optional rights relationship; taking an NPC's object does not silently transfer legal ownership. Unknown ownership stays unknown.

Later noncarried instances use a proposed `world.world_state.object_instances` collection (world owner/storage), with explicit placement. Scene templates bind to those records through a runtime binding in scene_state; do not edit authored scene JSON. Containment derives current scene through its parent, rejects cycles and unresolved parents, and distinguishes physical access from possession rights. Generic equipment relation is wearing/wielding/holding relative to an actor; PF-specific slots stay in extensions. A sleeve reference is `{instance_id: clothing, part: "left_sleeve"}` validated against established garment parts; it does not mint a detachable object.

One instance has **exactly one authoritative host**. A move from character inventory to world storage removes the source and inserts the identical record with unchanged ID/state in the destination under the same transaction, increments revision for placement, and updates bindings. No independent registry copy exists. Rebuild a read-only ID-to-host index after load; duplicate IDs or multiple hosts cause rejection/reconciliation, never last-writer-wins. Actor possession not yet supported by a host cannot be claimed as completed transfer. NPC custody can use world instance placement, with the NPC record remaining a reader.

## State and capabilities

Initial persistent state is a bounded `markings` collection attached to the instance; each entry has stable marking ID, part, exact text, medium/evidence reference, source provenance and creation operation. A label need not be simulated as a physical inscription. Capabilities are resolved from immutable definition/campaign instance facts and adapter-approved exceptions; missing writeability is unknown. Keep derived capabilities out of persisted duplicates. Material, compatible medium or a special writable surface is expanded only when an action requires it.

Ruleset extensions are optional namespaced blobs with validation/versioning. Inert unknown extension data is preserved on transfer/reload; interpretation cannot grant hidden capabilities. Mutable condition/damage/effect fields are deferred until their owners and expiry semantics are defined.

## Migration decisions

- First phase migrates only existing, positively selected quantity-one rows with valid old shape. Zero, fractional, unknown and stacked quantities are explicitly ineligible; no silent stack expansion. No minted physical item for an attack-only row.
- Future splitting of a stack atomically decrements a homogeneous stack and mints a singleton with lineage. A uniquely marked singleton cannot merge back into an unmarked stack. Deferred, not an incidental side effect of first identity migration.
- Repeated migration preserves existing ID/revision/provenance. Duplicate IDs, malformed migrated fields or cross-campaign data reject before writes. Legacy duplicate `id` strings remain allowed; unique instance IDs disambiguate them.
- Reads are pure: merely inspecting legacy inventory does not allocate IDs. Explicit migration/import/bootstrap commits are the only initial allocation sites. Unknown keys remain preserved through migration/save.
- Reimport requires an explicit old/new mapping or user resolution. Matching names, `gear_1`, or row order must not silently replace existing instances.
- Old saves remain readable without migration. A new migration commits once; schema/capability metadata prevents older writers from stripping migrated state. Compatibility with an unmodified historical binary is not promised.

The schema remains small: identity/revision/provenance only for promoted objects, optional definition and state when needed. Uninteracted background pebbles remain authored scenery. A pebble picked up becomes an instance only through acquisition authority, which is outside the first cycle.
