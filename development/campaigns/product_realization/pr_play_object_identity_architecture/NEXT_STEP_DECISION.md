# Exactly one next executable milestone

Milestone decision: `pr_play_object_identity_architecture` -> **`pr_play_object_instance_identity` — Stable Identity for Existing Inventory Singletons**.

Implement only stable core identity for already existing, explicitly selected quantity-one inventory records, with durable revision and mint provenance, pure readers and repeat-safe migration. This is the smallest meaningful foundation: two identical imported daggers can become distinguishable physical instances and remain so after reorder and reload. It is an implementation cycle, not another broad investigation.

## Required files / bounded integration

- Proposed `game/object_instances.py`: identity/reference validation, explicit singleton migration and read-only lookup. No physical resolver or second inventory.
- `game/api.py`: one explicit import/bootstrap/migration call site under existing runtime commit scope. Do not allocate on ordinary GET/inspection.
- `game/storage.py`: only if needed to make the explicit migration write atomic and fault-safe; reuse load/save_character and real snapshot APIs.
- `game/state_authority.py`, `docs/state_authority_model.md`: explicitly name narrow world_state semantic ownership of character-held object identity; no new domain, no blanket character mechanics authority.
- `game/importers/pf_json_importer.py` / `game/defaults.py`: only an agreed creation/import boundary if necessary. Do not replace legacy IDs, alter PF stats or mint possessions from attack rows.
- New focused identity tests under tests/, cycle-local evidence/reports/handoff. Existing fixtures stay frozen. Prefer migration outside pure importer so content normalization does not own campaign identity.

## Acceptance tests

1. Legacy singleton can be read without writes; explicit migration assigns campaign-scoped opaque instance_id, revision=0 and provenance once.
2. Identical legacy IDs/names on two singleton rows receive distinct IDs; repeating migration preserves IDs/provenance; reorder/rename preserves identity.
3. Invalid migrated IDs/revisions, duplicate instance IDs, campaign mismatch, stack/unknown quantity reject before any write. Existing valid IDs are never silently regenerated.
4. Unknown fields, old id/name/quantity/usable, inventory order and character mechanics survive migration. No extra possessions or scene state appears.
5. Real save/load and create_snapshot/load_snapshot restore identical identity, revision and provenance. Snapshot fault/character save fault does not report success or leave partial migration.
6. Existing T04/T05/pre-seal/T06 negative and 93 physical/persistence authority controls pass provider-free. Compare the same established 425 selection if integration touches its protected boundaries, reporting existing failure identities without repair credit.
7. Production-data write guard and protected fixture/source manifests remain intact; no live provider client or retry.

Acceptance is identity/persistence foundation only. Original T06 remains unsupported; no inscription success, equipment, mud or later-inscription inspection claim.

## Exclusions and rollback

Exclude marking/removal, T06 parser/routing changes, new materials/clothing, equipment simulation, stack splitting/merging, transfer, NPC loot, scene registry, experimental physical activation, ruleset loader and additional rulesets, crafting, physics, provider changes, unrelated cleanup and baseline repairs.

Migration is explicit and additive. Keep pre-migration snapshot and originals, validate detached data before save, and restore on failure under the existing scope. For release rollback, disable the migration caller while preserving already allocated IDs; do not erase them or hand-modified object state. Historical binaries may drop unknown fields; do not run incompatible writers against migrated saves. Crash/multi-process transaction guarantees are deferred and must not be claimed by exception fault tests.

No production implementation is authorized in the current architecture cycle. Stop after this decision and handoff.
