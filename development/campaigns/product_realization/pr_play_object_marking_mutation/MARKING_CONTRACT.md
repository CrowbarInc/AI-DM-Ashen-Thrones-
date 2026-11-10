# Marking Contract

Milestone: `pr_play_object_marking_mutation`. Date: 2026-11-09.

Internal `game.api.add_inventory_object_marking(request)` only. No HTTP route. Version 1 exact request fields: operation=add_marking, campaign_run_id, character_id, instance_id UUID4, request_id, request_digest, expected_revision, content, source, authorization. Target already has valid unique identity in one authoritative character inventory; integer quantity=1 and predecessor singleton validation. No migration.

Content is exact trusted text, nonblank, <=2048 UTF-8 bytes; max16 markings and 8192 total text bytes per object. Source kind explicit_literal/disclosed_copy and bounded reference. Authorization requires caller_id, decision_id, content_sha256, mechanics=not_applicable, and eight bounded evidence references: target_exists, accessible, rights, writable_surface, medium_available, medium_compatible, source_disclosed, capability. These are explicit internal assertions, never derived physical facts or arbitrary request-text authorization. No source fetch or hidden-data lookup.

Each object markings entry has version, type, modification_id(UUID4), exact content, source, authorization, request_id, request_digest, applied_revision. No whole-object historical copy and no PF fields. Successful new request advances existing revision by one; replay/reject do not. Snapshot restores captured revision. All legacy/stat/extension fields are deep-preserved. Applied result includes original/result revisions and persistence=committed, returned only after save.
