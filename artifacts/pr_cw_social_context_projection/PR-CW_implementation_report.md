# PR-CW Implementation Report

Decision: G - INCONCLUSIVE.
One projection in `game.gm.build_messages` reduces provider context after existing envelope
selection and instruction deduplication. Full state and validators remain unchanged.
Scene, NPC, history, policy, GM decision, recipe, and authority constraints are retained;
inactive opening/progression scaffolding and duplicate planner branches are compacted.

| Fixture | Before Bytes | After Bytes | Reduction |
|---|---:|---:|---:|
| PR-CQ-T1 | 123173 | 110809 | 10.04% |
| captain_preference | 119182 | 109091 | 8.47% |
| baker_preference | 107260 | 97225 | 9.36% |
| subjective_opinion | 116839 | 106748 | 8.64% |
| followup | 109596 | 99225 | 9.46% |
| recent_history | 117188 | 107099 | 8.61% |
| P1 | 91460 | 91460 | 0.0% |
| P2 | 98425 | 98425 | 0.0% |
| P3 | 93257 | 93257 | 0.0% |
| negative_9 | 124870 | 124870 | 0.0% |
| negative_10 | 115837 | 115837 | 0.0% |
| negative_11 | 116910 | 116910 | 0.0% |
| negative_12 | 116180 | 116180 | 0.0% |

Bytes sum effective system/user content. Developer messages: none. Tokens use char/4
estimates because tiktoken is unavailable; no dependencies installed or live savings claimed.
Five adversarial families are already accepted by full-context validation and remain accepted
with reduced context. This inherited gap prevents the requested universal rejection proof.
No validator was altered. Implementation is reviewable but not certified for rollout here.
Live provider calls: 0. Production saves unchanged. Dirty worktree preserved.
