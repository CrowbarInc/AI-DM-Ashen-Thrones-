# PR-DC Adversarial Validation

LIVE CALLS: 0

Hard validation was replayed on the rain-difficulty and getting-used-to-it resolutions after those resolutions had become claim-only and had selected reduced context. The sealer is `run_preserve_if_valid` with a narration-only candidate. `tests/test_pr_dc_subjective_followups.py::test_pr_dc_followup_projection_does_not_weaken_hard_validation` covers both player lines.

## Rejected

Each rejected line has `hard_valid` false, `unauthorized_resolution_decision_fact` in the reasons, and player-facing text different from the candidate.

| Category | Candidate |
|---|---|
| Invented biography | The guard captain was born in Blackharbor and served for twenty years. |
| Invented geography | The old milestone lies east beyond the trading crossroads. |
| Hidden information | A secret tunnel runs beneath the gate into the keep. |
| Unauthorized NPC action | The captain unlocks the gate and lets you pass. |
| Unsupported certainty | The captain confirms that bandits murdered the missing patrol. |
| Unauthorized discovery | You discover a hidden map beneath the notice board. |
| Unauthorized state change | The captain gives you ten gold coins and a signed entry permit. |

## Accepted

Each accepted line stays `hard_valid` true and is emitted unchanged.

| Category | Candidate |
|---|---|
| Harmless preference | The guard captain says, "I prefer a dry watch." |
| Ordinary subjective impression | The guard captain says, "I like the square best after rain." |
| Qualified personal difficulty | The guard captain says, "The rain does make the watch harder for me." |
| Bounded incidental characterization | The guard captain shrugs and nods. |

## Inherited suites

PR-CX `tests/test_pr_cx_authority_assurance.py`: 9 passed / 0 failed. Biography, geography, hidden information, NPC action, and discovery still reject on both full and reduced context. Preference, opinion, characterization, and grounded observation still pass.

PR-CW adversarial and smuggled-declaration tests are inside `tests/test_pr_cw_social_context_projection.py`: 39 passed / 0 failed. Smuggled `declared_claims` still reject. Objective tax facts, unsupported certainty, and state-change narration in that file still reject.

Immutable boundary: 21 passed. C19 hard authority: 11 passed. C19 free text: 5 passed. Bounded improvisation consequential claims: 5 passed.

No validator predicate was removed or loosened.
