# Migration Safety

Milestone: `pr_play_object_instance_identity`. Date: 2026-11-09.

Explicit selection of an existing dict row, nonblank string id/name, exact integer quantity=1 (booleans/floats/strings excluded), boolean usable. No stack expansion, narrative/attack/scene/NPC promotion. Existing reserved identity fields require a complete valid record; unrelated reserved provenance is ambiguous and refused without overwriting. Unknown nonreserved metadata is preserved.

Full current row equality guards stale selections; concurrent explicit requests serialize in the same FIFO lane and only one can mint. Repeat with refreshed selection returns existing bytes. Duplicate scan validates all declared identities in the authoritative host. UUID generation collision rejects, no regeneration loop. Invalid input produces rejected result with no candidate. Unknown fields/statistics remain untouched. Conflicting legacy provenance refuses instead of replacement.

Faults injected before save, after partial write and after complete write all restore original character bytes and raise. Snapshot creation and restore faults preserve current identity; API verifies rollback bytes on error and surfaces operational uncertainty if restoration fails. No success result escapes a failed save. Caller input remains detached.

One authoritative character.json inventory per runtime store; duplicate scanning covers every declared identity in that host only. No authoritative multi-character/world registry exists; broader host indexing belongs to the later transfer/host-integration phase. UUID4 generation is collision resistant and checked against this host; no campaign-wide all-object uniqueness claim. Existing writer and exception rollback remain best effort, not crash-atomic or multi-process. Historical binaries stripping unknown keys are incompatible writers.
