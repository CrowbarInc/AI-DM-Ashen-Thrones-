# CURRENT REVIEW

**PR-BV**

**MODE: TURN-LOCAL REALIZATION OPERATION PROJECTION**

**MODEL/API CALLS: ZERO**

## Status

**PR-BR: CLOSED.**

**PR-BU: CLOSED.**

**PR-BT: PAUSED / BT-C.**

No commit. No push. No live model call.

## Decision

**A — OPERATION PROJECTION READY FOR MICRO LIVE.**

Representation: `decision_facing_answer_recipe.turn_operation`, with `response_operation`, `declaration_expectation`, `semantic_ceiling`, and one `instruction`. `projection_only: true`. `authority_owner: "gm_resolution_decision"`.

## Projections

| Probe | Response operation | Declaration expectation | Semantic ceiling |
| --- | --- | --- | --- |
| P1 | `bounded_interpretation` | `optional_bounded_inference` | `interpret_observations_not_unauthorized_cause` |
| P2 | `incidental_dialogue` | `reply_not_required` | `transient_dialogue_not_durable_fact` |
| P3 | `player_hypothesis_discussion` | `hypothesis_discussion_not_required` | `conditional_hypothesis_not_established` |

P1 interprets listed observations and does not explain an unauthorized cause, actor, time, or history. A bounded inference may be proposed or left in narration. It does not authorize a new world fact.

P2 puts the reply in narration. The reply is not declared as a world fact. No durable preference or history is authorized merely by answering. Listed claims may still be restated.

P3 discusses the player's hypothesis conditionally and does not establish the hypothesis, an actor, a motive, a tool, or timing. No declaration is required merely to discuss it. Inference stays off.

## Controls

Consequential control: `consequential_realization` / `required_for_authorized_realization` / `authorized_consequential_state_only`. An interlocutor on that turn does not remove the declaration. P2's no-declaration result is turn-local.

Generalization: G1 matches P2, G2 matches P1, G3 matches P3, G5 is `direct_observation`. All eight matrix rows match.

Projection-only: yes. Authority owner: `gm_resolution_decision`.

## Provider

| Probe | Before | After | Net | Savings vs PR-BS | Percent of prior reduction retained |
| --- | ---: | ---: | ---: | ---: | ---: |
| P1 | 97,812 | 98,442 | +630 | 12,008 | 95.02% |
| P2 | 110,405 | 111,060 | +655 | 10,378 | 94.06% |
| P3 | 99,752 | 100,389 | +637 | 10,276 | 94.16% |

`turn_operation` itself is 523 / 526 / 509 characters.

## Tests

Focused PR-BV tests: **10 passed, 0 failed.**

Broader regression: **271 passed, 1 failed, 272 total.**

The failure is the known obsolete `test_pr_bt_provider_requests_remove_at_least_12000_chars_each`. P2 savings are 10,378 characters. The assertion was already red. It was not changed.

## C18

**PASS. ACCEPTED == SEALED == EMITTED.**

`test_raw_chat_accepts_authorized_fact_and_seals_it` passed. Continuation 18: 21 passed. Structured chat path: 11 passed.

## Unchanged

- System prompt changed: **NO.** 9,564 characters.
- Response schema changed: **NO.**
- Validator changed: **NO.**
- Retry changed: **NO.**
- Canonical authority changed: **NO.**

## Deferred

P1 request-classification anomaly: **DEFERRED.**

The damage question is still stripped from model-facing player text and survives in `requested_answer`. Response policy was not edited.

## Next

A three-probe PR-BV micro-live on the same P1, P2, and P3 wording. Not run here.

## Reports

- `PR-BV_turn_local_realization_operation_projection.md`
- `PR-BV_operation_projection_matrix.json`
- `PR-BV_operation_projection_snapshots.md`
- `PR-BV_operation_projection_derivation.md`
