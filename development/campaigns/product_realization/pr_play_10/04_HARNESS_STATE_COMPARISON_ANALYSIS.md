# 04 — Harness State-Comparison Analysis

PR-PLAY-10 · 2026-10-30 America/New_York · evidence_scope: structural_only.

Previously analysis.compare unwrapped snapshots, removed documented envelope/trace bookkeeping,
and compared fixed allowed session/world field names. runtime_scene_overlays was absent.
It distinguished accepted from rejected openings and required one turn/log increment, but did
not inspect overlay entries, declarations, scene ownership, additions/removals or native adoption.
Thus any changed overlay was unexpected, including authorized authored opening projection.
runner stopped before T1 when opening_state_comparison.integrity became false.

Now compare accepts the actual opening response as supporting evidence and delegates overlay
analysis to tools.playtest.overlays. The response session mirror is not the source of truth:
original persistent snapshots and pinned scene content are compared. Required support includes
hard validation, native accepted authority, scene_opening resolution, active scene consistency,
new persisted adoption receipt, proposal counts/mode and exact expected projection. Empty
active-scene initialization can be recognized separately. Other overlays must be unchanged.
No unconditional field allowance. Unknown / missing evidence stays a stop condition.

Ordinary-turn evaluation also emits overlay-specific comparison and stops on changed overlays
whose authority has not been established. Unchanged valid overlays persist. We do not infer
ordinary-turn mutation authority from a successful HTTP response or a shape-only receipt.
Diagnostics retain bounded values, omission counts/hashes, scene IDs, classifications and reasons;
raw snapshots remain preserved. example_improved_state_difference.json is an actual example.
