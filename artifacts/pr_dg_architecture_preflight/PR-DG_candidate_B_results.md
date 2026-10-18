# PR-DG Candidate B Results

Hand-authored plans. No planner call. A plan is not an outcome.

The validator requires `authority` = `non_authoritative_proposal`, the closed operation and resolver enums, at most four steps, and an acyclic `depends_on`. Forbidden fields (`hit_points`, `roll`, `hidden_facts`, `world_flags`, `narration_prose`, `commitment_status`, and the rest of the drop list) reject the step that carries them. A cleared catalog id marks the plan ambiguous and stops before steps. The contract selector outranks `proposed_resolver`.

On scenarios 1–9 the gold plan is one step that names the same utterance A used. The mechanical tuple matches A.

| # | Status | Transaction | Steps |
|---|---|---|---|
| 1 S1 | completed | atomic_per_resolver_call | s1:committed |
| 2 S2 | completed | atomic_per_resolver_call | s1:committed |
| 3 F1 | completed | atomic_per_resolver_call | s1:committed |
| 4 H1 | completed | atomic_per_resolver_call | s1:committed |
| 5 M1 | completed | atomic_per_resolver_call | s1:committed |
| 6 O1 | completed | atomic_per_resolver_call | s1:committed |
| 7 K1 | completed | atomic_per_resolver_call | s1:committed |
| 8 B1 | completed | atomic_per_resolver_call | s1:committed |
| 9 C1 | completed | atomic_per_resolver_call | s1:committed |
| 10 compound | partial | partially_committed | approach:committed; pry:unsupported |
| 11 ambiguous | completed | rejected_before_execution |  |
| 12 courier | completed | atomic_per_resolver_call | s1:committed |
| 13 declared_canon | completed | rejected_before_execution |  |
| 14 mechanical_dump | completed | rejected_before_execution |  |

The compound plan commits the approach and returns `unsupported` for the pry, because the pry sentence selects `generation`. The board stays. Transaction: `partially_committed`.

The ambiguous, declared-canon, and HP-dump gold plans set `uncertainty.ambiguous` and have no actions. No step runs. The shared tick still happens, matching chat's order.

Illegal plans on scenarios 10, 13, and 14 carry hit points, hidden facts, and world flags. Those steps are rejected. HP, flags, and clue ids do not change.

This does not show that a live model would emit these plans.
