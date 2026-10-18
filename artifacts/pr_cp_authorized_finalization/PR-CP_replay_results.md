# PR-CP replay results

Source: recorded PR-CO provider text under `artifacts/pr_co_gameplay_viability/evidence/`.
No provider calls. Replay entry: `tests/test_pr_cp_authorized_finalization.py` through `preserve_valid_or_regenerate` with `regenerate=None`.

## Target A — NPC preference

Player: whether the Guard Captain prefers standing in the rain or watching from indoors.

Authorized resolution: no new world fact. Gesture and preference are ordinary speech. Scene still contains the visible gate facts.

Narration candidate (PR-CO): the captain answers that he prefers the dry watch, calls the rain no blessing, and gives a small gesture.

Before: claim rows included an entity-existence match on "guard". Envelope audit added `undeclared_consequential_claim`. `unauthorized_resolution_decision_fact` discarded the reply. Final emission was unrelated gate-banner narration.

After: initial generation seals. Text contains "dry watch" and "blessing". Banner fallback is absent. `why` is `initial_hard_valid`.

## Target B — authored patrol answer

Player: "Captain, what do you know about the missing patrol?"

Authorized resolution: social topic `social_frontier_gate_guard_captain_patrol`, text "A patrol went missing near the old milestone." Resolver marks the topic revealed before narration.

Narration candidate: that sentence plus "That's all I can confirm for now." A second candidate adds the trading crossroads and says the patrol has not returned.

Before: the milestone sentence matched `patrol_route_or_geography` and was undeclared because the topic was not on the decision. The certainty clause failed `unauthorized_certainty_upgrade` and `unauthorized_evidential_relation`. The whole reply became a refusal while the topic stayed revealed.

After: final text is `Guard Captain mutters, "Word is, A patrol went missing near the old milestone."` Provenance is the safe projection of the selected topic. "Confirm for now", "crossroads", and "have not returned" are absent.

## Target C — visible notice board

Player examines the existing notice board.

Authorized resolution: visible and journal fact "A notice board lists new taxes, curfews, and a posted warning about a missing patrol."

Narration candidate: a paraphrase using edicts, urgent, and freshly posted, and a second candidate inventing twelve names, yesterday, east-road orders, and annotations.

Before: `notice_roster_history` matched the authorized sentence itself. Final emission said nothing further could be established.

After: invented roster, dates, names, and orders do not survive. Final text states taxes, curfews, and the missing patrol. The loose paraphrase's extra words (edicts, freshly posted, urgent) do not survive. The exact authored notice sentence seals as `initial_hard_valid`.

## Resulting state

No scene mutation from rejected extras. The patrol topic remains the resolver's revealed topic, and the player-facing line now states that same sentence.
