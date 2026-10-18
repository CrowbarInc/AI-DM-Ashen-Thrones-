# PR-DB Three-Turn Continuity

Deterministic replay through `play_turn` in `tests/test_pr_db_speaker_grounding.py`. No provider calls. Fresh frontier-gate session. Turn 1 establishes the captain. Turns 2 and 3 do not repeat the name.

| Turn | Text | Resolver | Contract interlocutor | Social target | Obligation interlocutor | Allowed speakers | Active target after | Discourse | Entry reason | Reply plan |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Guard Captain, do you prefer standing watch in the rain, or somewhere dry? | social | guard_captain | guard_captain, resolved | guard_captain | [guard_captain] | guard_captain | guard_captain | spoken_vocative_address | harmless_subjective_response_permitted |
| 2 | Does the rain make it harder to keep watch? | social | guard_captain | guard_captain, resolved | guard_captain | [guard_captain] | guard_captain | guard_captain | active_interlocutor_followup | genuine_uncertainty |
| 3 | Does it get any easier after a while? | social | guard_captain | guard_captain, resolved | guard_captain | [guard_captain] | guard_captain | guard_captain | active_interlocutor_followup | genuine_uncertainty |

Obligation mode on each turn: `grounded_information_request`.

Finalization for these social kinds calls `update_after_resolved_action` with continuity preserved. The active target is still `guard_captain` after turn 3.

Turn 1 is the only turn whose reply plan is `harmless_subjective_response_permitted`. Turns 2 and 3 stay `genuine_uncertainty`, so reduced context is not selected for them.
