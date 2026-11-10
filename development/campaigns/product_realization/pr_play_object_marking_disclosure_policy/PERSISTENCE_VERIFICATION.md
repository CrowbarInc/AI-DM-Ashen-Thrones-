# Persistence Verification

Milestone: `pr_play_object_marking_disclosure_policy`. Date: 2026-11-09.

observation_timeline.json uses real atomic character save/load and create_snapshot/load_snapshot. Apply A and B with visible classification, capture pre-removal snapshot, remove A through existing API, observe B only, save/reload and observe identical B-only result. An old pre-removal grant cannot inspect the changed target. Restore empty/pre-removal/post-removal snapshots: permitted values are respectively [], [A,B], [B]. Fresh corresponding context is established against each restored state. Removed A remains in historical receipt evidence but never in current projection. Snapshot rollback consults its own active state, not future external receipts/knowledge. IDs, metadata, revisions and original receipt semantics are retained. Read/save/snapshot storage infrastructure is unchanged; existing single-process/multi-file rollback limitations persist.
