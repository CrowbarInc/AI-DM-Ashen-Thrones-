# 05 — Feature-Gate Strategy

Three modes, one new flag:

- Both flags off: legacy routing.
- `ASHEN_UNIFIED_SEMANTIC_PLANNING` on and the candidate flag off: existing R6 semantic planner.
- Both on: host-constrained candidates.

The candidate flag defaults off. Traces record `routing_mode`. Turning the flag off returns the next turn to the semantic planner. `plan_proposer` remains the test seam for that planner and is not consulted while candidate mode is on.
