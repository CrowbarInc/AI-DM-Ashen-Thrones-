# Implementation

Milestone: `pr_play_object_instance_identity`. Date: 2026-11-09.

game.object_instances: IdentityResult, inspect_object_identity, ensure_object_instance_identity; internal validators cover old shape/metadata/scope/duplicates. Detached candidate replaces exactly the selected row (including alias defense). game.api.migrate_inventory_object_identity reloads authoritative state in the existing ordered_turn lane, checks campaign and expected selected row, delegates staging, saves only assigned candidates under runtime_commit_scope. No HTTP endpoint, AI action, importer normalization or read hook. game.state_authority recognizes only assign_inventory_identity for this owner and denies other operations/domains; blanket domain mutability is not granted.

Existing character and snapshot persistence reused unchanged; no parallel database. UI allowlists/renderers are unchanged. T06, equipment, modification, transfer, stacking, crafting, scene/NPC objects and ruleset mechanics excluded.

Architecture reconciliation: approved field/location/owner preserved. API expected_item is a concurrency selection guard, never the ID seed. No storage rewrite was necessary for scoped exception guarantees; crash safety deferred as authorized by this request.
