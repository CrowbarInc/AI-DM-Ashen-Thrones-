# PR-BR targeted live-validation repair

Deterministic repair of the three second-live failures: qualifier false positive, movement decision disagreement, and mixed-intent loss. No gameplay or model calls.

Exact model/API call count for this repair: **0**.

## Turn 1 root cause

`_EVENT_SITE_RE` treated `happened|occurred|befell|took place` as an event site when `here|there|inside|in silence` appeared anywhere inside a 48-character window. In "when it happened, and who might be responsible remain unseen here," `happened` and `here` fell inside that window.

The cause slot was unresolved. `_UNKNOWN_SLOT_RE` did not treat "remain unseen" as unknown, so the slot looked filled. `_AGENT_FILL_RE` matched "What caused." The location reason was returned. Bounded preservation trusts the violation list, so it deleted the authorized uncertainty sentence and kept the separate missing-patrol sentence.

## Qualifier semantics

Before: unknownness was inferred from lexical proximity. A deictic `here` near `happened` was a location assertion.

After: an event site is the complement of the verb. "It happened here" and "It happened here?" still match. "When it happened remains unknown from what we can see here" does not. Cause, actor, and time slots that the decision already marks unresolved stay unknown when the sentence says the slot remains unseen, unknown, or unestablished. Preservation still deletes only sentences the audit marks unauthorized. The uncertainty sentence is no longer in that list.

A direct question is not a consequential assertion. Clarification questions such as "Are you asking about the new curfew, the missing patrol, or something else posted on the notice board?" are no longer scored as notice-roster history after the sentence splitter cuts them out of their quotation. Qualifier and departure-exit checks still run before that exemption.

## Narrator lead versus NPC claim

A hedged sentence with an ungrounded definite and no speaker, quotation, or hearsay verb is `unsupported_narrator_lead`. "You might compare this disruption with changes around the missing patrol's notice" is removed. "You might look again at the jammed sluice gate" is not, because the sluice is in the authorized ground.

"Mirelle says, …" and "Mira suspects …" stay `npc_claim`. Belief and speech verbs count as a source. Narrator hedging does not.

A quotation whose closing mark is split onto the next sentence is not treated as attributed testimony by itself. Treating every opening quote as an authorized claim made an unauthored meeting-place quote valid and cleared C18's ungrounded-rule reject. That broader reading was not kept.

## Travel pipeline

Before: the contract and `GMResolutionDecision` were built before the travel resolver. `carry_authoritative_contract` kept that decision when the contract id matched. A later attach returned early. The resolver could commit `active_scene_id` while the decision stayed `consequentially_unresolved` with `permitted_state_mutations = []`, and narration still saw only departure facts.

After: `_apply_authoritative_resolution_state_mutation` still commits the scene. `reconcile_movement_decision` then copies the resolver result into the existing decision. It does not choose the destination.

- Resolved `scene_transition` / `travel`: outcome `state_mutation`, location mutation `source_scene_id -> target_scene_id`, destination visible facts tagged `destination_fact`, destination exits tagged `destination_exit`, prior scene facts tagged `departure_fact` or `departure_exit`.
- Unresolved or failed movement: location mutations stripped, outcome unresolved, constraint "Do not narrate arrival."

## Departure and destination provenance

A present-tense onward use of a departure exit ("a stair leads upward", "further exploration") that overlaps the departure exit and not the destination is `departure_exit_reused_as_destination_exit`. A destination exit is available only when that exit is authored on the destination. Departure texture can remain, with scene role `departure_fact` or `departure_exit`. Non-exit departure texture is not hard-rejected unless it is reused as a present onward exit.

## Mixed-intent architecture

The Resolution Contract still has one `operation`. `construction.executable_obligations` records `primary`, `mutation_owner`, `sequence`, and at most the other committed act. Interaction Obligation copies that record. The decision adds "Acknowledge the committed social act ({act})" when the supporting act is social. Narration of eight or more words that omits the supporting social act fails `supporting_obligation_unacknowledged`.

Travel detection reuses declared-travel patterns and the immediate verb-plus-preposition shape, plus "on my way to …" and "cross …". "Leave the runner and step up to the guard" and "walk over to the cloth merchant" are not scene travel.

## Primary versus supporting, sequence, ownership

| Utterance | Primary | Mutation owner | Supporting |
| --- | --- | --- | --- |
| I thank Mirelle for the warning, then head for the eastern courtyard. | travel | travel | thank |
| I tell the guard I'll return, then cross the bridge. | travel | travel | tell |
| I thank Nessa and go to the gate. | travel | travel | thank |
| I ask Nessa who owns the warehouse while walking to the gate. | social | travel | travel |
| On my way to the gate, I ask Nessa whether she saw the courier. | social | travel | travel |
| I ask Nessa whether I should go to the gate. | none | none | none |
| If Nessa agrees, I'll go to the gate. | none (conditional) | none | none |
| I might head to the gate later. | none (`intended_later` via existing C22) | none | none |

When a committed travel obligation is recorded, the travel stage may run under a social resolver, and a movement action is not a contract contradiction. One travel stage writes the scene. The social act is a narration obligation, not a second state write. Courtesy does not create new discourse state.

## Six scene-transition regressions

`tests/test_scene_transition_authority.py` passes, including:

1. `test_chat_mixed_farewell_and_declared_travel_overrides_dialogue_lock` — travel primary, farewell supporting, scene changes.
2. `test_actionable_lead_declared_travel_authoritative_arrival_and_lead_metadata` — declared travel arrives; lead metadata stays non-authoritative for the move.
3. `test_declared_travel_unresolved_movement_no_social_no_scene_change` — unresolved movement, no scene change.
4. `test_declared_travel_eastern_square_disambiguates_against_prior_milestone_lead` — named destination wins over the prior lead.
5. `test_combined_prior_lead_affirmed_waste_gpt_scene_proposal_non_authoritative` — GPT scene proposal does not replace the resolver.
6. `test_unresolved_alternate_destination_with_prior_old_milestone_lead_no_substitution` — unresolved alternate destination is not replaced by the old lead.

Travel does not win every mixed line. Farewell-only and approach-to-a-person lines stay social.

## Live Turn 7 and the inverse

`test_turn7_thanks_is_supporting_and_travel_is_primary` — primary travel, sequence social then travel, supporting thank, decision location mutation to `eastern_courtyard`, "You thank Mirelle and cross into the eastern courtyard." passes, the same arrival without thanks fails.

`test_inverse_mixed_intent_keeps_social_primary_and_committed_travel` — ask-while-walking keeps social primary and travel as the mutation owner. There is one travel mutation, not two resolvers writing the scene.

## Modality contrasts

"Whether I should go", "If Nessa agrees, I'll go", and "I might head to the gate later" record no travel mutation. "I thank Nessa and go to the gate" records travel plus thanks. These use `committed_world_text` and `ask_governs_embedded_act`. No second modality parser.

## Second-live passes and previous repairs

Continuation 12–27, decision slices 1–3, live-attachment repair, resolution-contract, outcome precedence, interpretation proposal, and model-interpretation tests pass. That covers the repaired negation and multi-sentence paths, decision attachment, content clarification ("When did that start?" stays a clarification), and approach-to-person social turns that must not become travel.

Bounded incidental improvisation tests pass.

## Suite

480 passed, 2 failed, 482 collected. Zero model calls. Tests monkeypatch `game.api.call_gpt`.

The two failures are in `tests/test_authoritative_lead_provenance_social_prose_non_ingestion.py`:

- `test_general_http_informational_social_prose_mints_no_lead` — the clerk's trestle/coal-loft sentence is an ungrounded operational rule whose closing quote is split off. The audit removes it. Authorizing every opening quote as testimony also authorized an unauthored meeting place and cleared the C18 ungrounded-rule failure, so that reading was reverted.
- `test_calibration_http_captain_answer_does_not_mint_narration_ctx` — narration is kept. CTIR records `guard_captain`. A later `rebuild_active_scene_entities` clears the interaction target because that id is not in the scene roster (`gate_guard`). The `synchronize_scene_addressability` call sites in `game/api.py` are unchanged from HEAD.

## Files

- `game/gm_resolution_decision.py` — event-site complement, unknown slots, narrator-lead versus attributed claim, interrogatives, movement reconciliation, supporting-act audit.
- `game/player_commitment.py` — `executable_obligations`, `committed_travel_recorded`.
- `game/resolution_contract.py` — stores the obligation record; operation unchanged.
- `game/ordinary_semantic_ownership.py` — travel stage and movement contradiction consult the recorded obligation.
- `game/live_resolution.py` — obligation metadata copies the record.
- `game/api.py` — travel stage receives the contract; reconcile runs after the authoritative scene commit.
- `tests/test_pr_br_qualifier_movement_mixed_intent.py` — new deterministic coverage.

## Known limitations

- A supporting social act is a narration constraint. The social engine does not also mutate state on a travel-owned turn.
- Acknowledgment is enforced only when the narration has at least eight words, so the scene-transition stubs that return "Narration." still pass.
- Bare "then leave" without `to`/`for`/`cross` may not record travel.
- "I might head to the gate later" is `intended_later` because existing C22 checks "later" before contemplated. It does not move.
- Split quotations are not inferred back together. Doing so by treating every opening quote as a claim reopened harder authority failures.

## Recommendation

A. LOCALIZED DEFECTS ARE REPAIRED; PROCEED TO SMALL MULTI-TURN LIVE VALIDATION
