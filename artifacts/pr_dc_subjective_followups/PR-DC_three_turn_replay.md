# PR-DC Three-Turn Replay

LIVE CALLS: 0

Replay is `play_turn` in `tests/test_pr_dc_subjective_followups.py` and `artifacts/pr_dc_subjective_followups/_after.json`. Fresh frontier-gate session. Turn 1 names the captain. Turns 2 and 3 do not.

## Before

| Turn | Text | Resolver | Interlocutor | Reply plan | Speech authority | Speakers | Active target | Entry |
|---|---|---|---|---|---|---|---|---|
| 1 | Guard Captain, do you prefer standing watch in the rain, or somewhere dry? | social | guard_captain | harmless_subjective_response_permitted | claim_only | [guard_captain] | guard_captain | spoken_vocative_address |
| 2 | Does the rain make it harder to keep watch? | social | guard_captain | genuine_uncertainty | none | [guard_captain] | guard_captain | active_interlocutor_followup |
| 3 | Does it get any easier after a while? | social | guard_captain | genuine_uncertainty | none | [guard_captain] | guard_captain | active_interlocutor_followup |

Obligation mode on each turn: `grounded_information_request`.

## After

| Turn | Resolver | Interlocutor | Reply plan | Incidental subjective | Speech authority | Objective facts | Speakers | Active target after | Discourse |
|---|---|---|---|---|---|---|---|---|---|
| 1 | social | guard_captain | harmless_subjective_response_permitted | true | claim_only | none | [guard_captain] | guard_captain | guard_captain |
| 2 | social | guard_captain | harmless_subjective_response_permitted | true | claim_only | none | [guard_captain] | guard_captain | guard_captain |
| 3 | social | guard_captain | harmless_subjective_response_permitted | true | claim_only | none | [guard_captain] | guard_captain | guard_captain |

Turn 1's classification is unchanged. Turns 2 and 3 move from `genuine_uncertainty` to the existing claim-only plan. Reply kind becomes `answer`. The hint becomes the harmless-subjective hint: bounded personal speech, not authored world truth, durable preference, inventory, declared claim, or state mutation.

`durable_state_mutation_allowed` and `declared_claims_expected` stay false. One speaker remains `guard_captain`. Finalization still leaves the active interaction target on `guard_captain`.

## Reduced context

`build_messages` selects `provider_context_projection.mode` `harmless_social_incidental_dialogue_v1` for all three turns. The projector predicates in `game/gm.py` were not edited and were not bypassed.

The assassination follow-up and the missing-patrol question do not select that projection. Their serialized hashes match the baseline.
