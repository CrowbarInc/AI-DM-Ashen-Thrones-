# Identity Contract

Milestone: `pr_play_object_instance_identity`. Date: 2026-11-09.

Opaque canonical lowercase UUID4 `instance_id`; integer nonnegative `revision` (new records 0); `provenance` version 1 with campaign_run_id, explicit mint operation_id and source host/legacy_id. Canonical reference is (campaign_run_id, instance_id). Placement/actor association derives from the enclosing character inventory. Existing definition/legacy ID and all other fields remain intact.

Explicit selection of an existing dict row, nonblank string id/name, exact integer quantity=1 (booleans/floats/strings excluded), boolean usable. No stack expansion, narrative/attack/scene/NPC promotion. Existing reserved identity fields require a complete valid record; unrelated reserved provenance is ambiguous and refused without overwriting. Unknown nonreserved metadata is preserved.

Validation/assignment are pure staging operations with structured legacy/existing/assigned/rejected results. Repeated migration preserves ID/revision/provenance and does not save. Malformed/partial/unsupported/cross-campaign metadata and duplicate identities reject without replacement. Mint operation is provenance, not a global durable request cache. Source legacy ID is mint lineage, never a mutable identity seed. Unknown ruleset extensions are opaque.
