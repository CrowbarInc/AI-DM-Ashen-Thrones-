# PR-CE authority integrity

Live provider calls: 0.

## Ownership

`gm_resolution_decision` remains the authority owner. The subjective repair only extends the existing social reply-plan expression in `game.social._bounded_social_reply_plan_for_missing_topic`. The dialogue social plan stays a projection of that plan through CTIR. It does not adjudicate world facts.

## What a permitted subjective reply is allowed to be

When no stronger restriction matches:

- `reply_plan_kind`: `harmless_subjective_response_permitted`
- `npc_speech_authority`: `claim_only`
- `objective_world_fact_authority`: `none`
- `durable_state_mutation_allowed`: false
- `declared_claims_expected`: false

`claim_only` is NPC speech. It is not an authored world fact and it does not require a scripted answer.

## Negative controls

Preference wording did not bypass stronger limits:

| Player line | Plan |
| --- | --- |
| Which secret guard schedule do you prefer? | genuine_refusal |
| Which restricted entrance would you choose? | genuine_refusal |
| Which confidential faction plan do you like best? | genuine_refusal |
| Which suspect do you think committed the murder? | consequential_information_request |
| Which official order would you recommend forging? | consequential_information_request |
| Which hidden quest objective would you select? | consequential_information_request |

All six keep `incidental_subjective_allowed` false, `npc_speech_authority` none, and `objective_world_fact_authority` `authored_context_required`.

## PR-CA T4 and durable preference

T4, "Thanks. I'll remember your recommendation.", stays `genuine_uncertainty` with objective authority `none`. The world NPC record is unchanged. Session runtime after four turns holds attitude, trust, fear, suspicion, empty `known_topics`, empty `revealed_topics`, and `last_interaction_turn` 4. No preference value is stored. `state_changes` is empty on every replay turn. Prior evasive history is retained and does not rewrite T2 or T3.

## Adjacent contracts

- Narration-only selection and the retry contract: PR-BY and PR-BW, 27 passed.
- Declaration and narration validation, plus C18: `tests/test_pr_br_resolution_contract.py`, `tests/test_pr_br_authority_reconciliation.py`, and `tests/test_pr_br_continuation18_immutable_boundary.py`, 104 passed.
- Consequential unknown without invention remains covered by the PR-CC slice, 36 passed.

No authority bypass was found in these controls.
